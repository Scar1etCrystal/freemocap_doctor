from contextlib import contextmanager
import json
import math
from pathlib import Path

import bpy
from bpy.app.handlers import persistent
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper

from . import project
from . import annotation
from . import planted_indicators
from .core import contacts as core_contacts
from .core import export as core_export
from .core import source as core_source
from .core import target as core_target
from .core.ranges import diff_ranges
from .presets import (
    EXPECTED_FPS,
    MMD_ARM_FK_BONES,
    MMD_CENTER_BONE,
    MMD_ARM_TWIST_BONES,
    MMD_ELBOW_BONES,
    MMD_LEG_FK_BONES,
    MMD_ROOT_BONE,
    MMR_COPY_CONSTRAINT_NAME,
    MMR_LEG_CONSTRAINTS,
    OBJECT_NAMES,
    SOURCE_BONES,
    TARGET_FOOT_IK,
    fixed_object_name_matches,
    resolve_mmd_foot_ik,
    resolve_mmd_hand_bones,
)
from .workflow import STEPS, STEP_INDEX, clamp_step, step_at


_CONVERTED_ANNOTATION_AREAS = {}
_PENDING_ANNOTATION_GROUP = ""
_PENDING_ANNOTATION_ATTEMPTS = 0


def _snapshot_nla_filters(area):
    dopesheet = getattr(area.spaces.active, "dopesheet", None)
    if dopesheet is None:
        return {}
    values = {}
    for name in (
        "show_only_selected",
        "show_hidden",
        "filter_text",
        "use_filter_invert",
        "filter_collection",
    ):
        if hasattr(dopesheet, name):
            values[name] = getattr(dopesheet, name)
    return values


def _restore_nla_filters(area, values):
    dopesheet = getattr(area.spaces.active, "dopesheet", None)
    if dopesheet is None:
        return
    for name, value in values.items():
        try:
            setattr(dopesheet, name, value)
        except (AttributeError, ReferenceError, TypeError):
            pass


def _restore_annotation_area(screen):
    if screen is None:
        return False
    snapshot = _CONVERTED_ANNOTATION_AREAS.pop(screen.as_pointer(), None)
    if not snapshot:
        return False
    area = next(
        (item for item in screen.areas if item.as_pointer() == snapshot["pointer"]),
        None,
    )
    if area is None:
        return False
    original_type = snapshot.get("type", "NLA_EDITOR")
    if original_type != "NLA_EDITOR":
        area.type = original_type
        original_ui_type = snapshot.get("ui_type", "")
        if original_ui_type:
            try:
                area.ui_type = original_ui_type
            except (AttributeError, TypeError):
                pass
    else:
        _restore_nla_filters(area, snapshot.get("filters", {}))
    area.tag_redraw()
    return True


def _restore_all_annotation_areas():
    wm = getattr(bpy.context, "window_manager", None)
    screens = []
    if wm is not None:
        for window in wm.windows:
            if window.screen not in screens:
                screens.append(window.screen)
    for screen in screens:
        _restore_annotation_area(screen)
    # A closed workspace/window can invalidate its Area pointer.  It cannot be
    # restored, but it also cannot leave a visible NLA editor behind.
    _CONVERTED_ANNOTATION_AREAS.clear()


def _annotation_step_for_group(channel_group):
    return "contacts" if str(channel_group).upper() == "FOOT" else "hand_ranges"


def _activate_annotation_editor_impl(scene, screen, channel_group):
    """Open or reuse one editor without overwriting its original snapshot."""

    requested_step_id = _annotation_step_for_group(channel_group)
    if getattr(scene, "mcd_annotation_mode", False):
        annotation.commit_track_reassignments(scene, rebuild=False)
    if requested_step_id == "contacts":
        planted_indicators.require_source(scene)
    if screen is None:
        raise RuntimeError("当前窗口没有可用工作区")
    key = screen.as_pointer()
    snapshot = _CONVERTED_ANNOTATION_AREAS.get(key)
    area = None
    if snapshot:
        area = next(
            (item for item in screen.areas if item.as_pointer() == snapshot["pointer"]),
            None,
        )
    if area is None:
        timelines = [
            item
            for item in screen.areas
            if item.type == "DOPESHEET_EDITOR" and getattr(item, "ui_type", "") == "TIMELINE"
        ]
        if timelines:
            area = min(timelines, key=lambda item: item.height)
        else:
            area = next((item for item in screen.areas if item.type == "NLA_EDITOR"), None)
        if area is None:
            raise RuntimeError("当前工作区没有 Timeline 或 NLA Editor")
        snapshot = {
            "pointer": area.as_pointer(),
            "type": area.type,
            "ui_type": getattr(area, "ui_type", ""),
            "filters": _snapshot_nla_filters(area) if area.type == "NLA_EDITOR" else {},
        }
        _CONVERTED_ANNOTATION_AREAS[key] = snapshot

    converted = area.type != "NLA_EDITOR"
    if converted:
        area.type = "NLA_EDITOR"

    step_id = _annotation_step_for_group(channel_group)
    if step_id == "contacts":
        active_channel = annotation.CHANNEL_FOOT_L_EFFECTIVE
    else:
        active_channel = annotation.CHANNEL_HAND_L_MANUAL
    settings = scene.mocap_doctor
    settings.annotation_step_id = step_id
    scene.mcd_annotation_active_channel = active_channel
    annotation.ensure_working_ranges_initialized(scene, step_id)
    if scene.mcd_annotation_has_pending_in and (
        scene.mcd_annotation_pending_channel not in annotation.visible_channels(scene)
    ):
        scene.mcd_annotation_has_pending_in = False
        annotation.clear_pending_marker(scene)
    if not scene.mcd_annotation_mode:
        scene.mcd_annotation_mode = True
    else:
        annotation.rebuild_projection(scene, active_channel=active_channel)
    annotation.configure_nla_area(area, scene)
    annotation.select_only_channel(scene, active_channel)
    if step_id == "contacts":
        planted_indicators.activate(scene)
    else:
        planted_indicators.cleanup(scene)
    for item in screen.areas:
        item.tag_redraw()
    return area, converted, step_id


def _activate_annotation_editor(scene, screen, channel_group):
    """Transactional wrapper for editor conversion and group switching."""

    was_open = bool(getattr(scene, "mcd_annotation_mode", False))
    old_step_id = scene.mocap_doctor.annotation_step_id
    old_active_channel = getattr(scene, "mcd_annotation_active_channel", "")
    screen_key = screen.as_pointer() if screen is not None else None
    had_snapshot = screen_key in _CONVERTED_ANNOTATION_AREAS if screen_key is not None else False
    try:
        return _activate_annotation_editor_impl(scene, screen, channel_group)
    except Exception:
        planted_indicators.cleanup(scene)
        scene.mocap_doctor.annotation_step_id = old_step_id
        if old_active_channel:
            scene.mcd_annotation_active_channel = old_active_channel
        if was_open:
            annotation.rebuild_projection(scene, active_channel=old_active_channel or None)
        if not had_snapshot and screen is not None:
            _restore_annotation_area(screen)
        if not was_open and getattr(scene, "mcd_annotation_mode", False):
            annotation.exit_annotation_mode(scene)
            scene.mocap_doctor.annotation_step_id = ""
        raise


def _cancel_pending_annotation_open():
    global _PENDING_ANNOTATION_GROUP, _PENDING_ANNOTATION_ATTEMPTS
    _PENDING_ANNOTATION_GROUP = ""
    _PENDING_ANNOTATION_ATTEMPTS = 0
    if bpy.app.timers.is_registered(_finish_pending_annotation_open):
        try:
            bpy.app.timers.unregister(_finish_pending_annotation_open)
        except (RuntimeError, ValueError):
            pass


def _finish_pending_annotation_open():
    global _PENDING_ANNOTATION_GROUP, _PENDING_ANNOTATION_ATTEMPTS
    if not _PENDING_ANNOTATION_GROUP:
        return None
    wm = getattr(bpy.context, "window_manager", None)
    window = getattr(bpy.context, "window", None)
    if window is None and wm is not None and wm.windows:
        window = wm.windows[0]
    try:
        if window is None or window.screen is None or window.scene is None:
            raise RuntimeError("恢复后窗口尚未就绪")
        group = _PENDING_ANNOTATION_GROUP
        _activate_annotation_editor(window.scene, window.screen, group)
        window.scene.mocap_doctor.current_step = STEP_INDEX[_annotation_step_for_group(group)]
        window.scene.mocap_doctor.status_message = "已保留现有标注；请补充或调整手部坏区间"
        _cancel_pending_annotation_open()
        return None
    except Exception as exc:
        _PENDING_ANNOTATION_ATTEMPTS += 1
        if _PENDING_ANNOTATION_ATTEMPTS < 12:
            return 0.25
        if window is not None and window.scene is not None and hasattr(window.scene, "mocap_doctor"):
            window.scene.mocap_doctor.status_message = f"检查点已恢复，但无法自动打开标注编辑器：{exc}"
        _cancel_pending_annotation_open()
        return None


@persistent
def _resume_annotation_after_load(_dummy):
    if _PENDING_ANNOTATION_GROUP and not bpy.app.timers.is_registered(_finish_pending_annotation_open):
        bpy.app.timers.register(_finish_pending_annotation_open, first_interval=0.25)


def _request_annotation_after_restore(channel_group):
    global _PENDING_ANNOTATION_GROUP, _PENDING_ANNOTATION_ATTEMPTS
    _PENDING_ANNOTATION_GROUP = str(channel_group).upper()
    _PENDING_ANNOTATION_ATTEMPTS = 0


def cleanup_annotation_sessions():
    _restore_all_annotation_areas()
    # During Extension install/enable Blender temporarily exposes
    # ``bpy.data`` as ``_RestrictData``.  Cleanup is also called from
    # unregister(), so do not assume the main database is available.
    for scene in getattr(bpy.data, "scenes", ()):
        if getattr(scene, "mcd_annotation_mode", False):
            annotation.exit_annotation_mode(scene)
        if hasattr(scene, "mocap_doctor"):
            scene.mocap_doctor.annotation_step_id = ""
        planted_indicators.cleanup(scene)


@persistent
def _cleanup_annotation_before_load(_dummy):
    cleanup_annotation_sessions()


def _require_object(settings, attribute, object_type=None, exact_name=None):
    obj = getattr(settings, attribute, None)
    if obj is None:
        raise RuntimeError(f"缺少对象：{attribute}")
    if object_type and obj.type != object_type:
        raise RuntimeError(f"{obj.name} 不是 {object_type} 对象")
    if exact_name and not fixed_object_name_matches(obj.name, exact_name):
        raise RuntimeError(f"只支持固定对象 {exact_name}（允许 Blender 重名后缀 .001/.002），当前为 {obj.name}")
    return obj


def _require_action(owner, label):
    action = getattr(getattr(owner, "animation_data", None), "action", None)
    if action is None:
        raise RuntimeError(f"{label} 没有活动 Action")
    return action


def _require_no_nla(owner, label):
    animation_data = getattr(owner, "animation_data", None)
    if animation_data and len(animation_data.nla_tracks) > 0:
        raise RuntimeError(f"{label} 存在 NLA Track；请先合并或移除，避免与活动 Action 叠加")


def _source_constraint_empty_targets(armature):
    """Return exact Empty objects used by source pose constraints."""

    targets = {}
    for pose_bone in armature.pose.bones:
        for constraint in pose_bone.constraints:
            target = getattr(constraint, "target", None)
            if target is not None and getattr(target, "type", None) == "EMPTY":
                targets[target.name] = target
    return list(targets.values())


def _object_is_ancestor(candidate, descendant):
    parent = getattr(descendant, "parent", None)
    while parent is not None:
        if parent == candidate:
            return True
        parent = parent.parent
    return False


def _remove_source_constraint_empties(armature, targets):
    """Remove baked source drivers without deleting unrelated scene objects."""

    target_names = {target.name for target in targets if target is not None}
    protected_names = set(OBJECT_NAMES.values())
    removable = []
    skipped = []
    for target in targets:
        if target is None or target.name not in bpy.data.objects:
            continue
        reason = ""
        if target.name in protected_names or bool(target.get("mcd_annotation_helper")):
            reason = "protected_object"
        elif getattr(target, "library", None) is not None:
            reason = "linked_library_object"
        elif _object_is_ancestor(target, armature):
            reason = "armature_ancestor"
        elif any(child.name not in target_names for child in target.children):
            reason = "has_unrelated_children"
        if reason:
            skipped.append({"name": target.name, "reason": reason})
        else:
            removable.append(target)

    def hierarchy_depth(obj):
        depth = 0
        parent = obj.parent
        while parent is not None:
            depth += 1
            parent = parent.parent
        return depth

    removed = []
    for target in sorted(removable, key=hierarchy_depth, reverse=True):
        name = target.name
        bpy.data.objects.remove(target, do_unlink=True)
        removed.append(name)
    return {"removed": removed, "skipped": skipped}


def _validate_correction_transform(correction):
    if correction.parent is not None:
        raise RuntimeError("全局校正 Empty 必须是顶层对象")
    if any(abs(float(value) - 1.0) > 1.0e-6 for value in correction.scale):
        raise RuntimeError("全局校正 Empty 必须保持单位缩放")
    action = getattr(getattr(correction, "animation_data", None), "action", None)
    if action and any(curve.data_path == "scale" for curve in action.fcurves):
        raise RuntimeError("全局校正 Empty 不能带缩放动画")


def _ensure_no_pending_preview(settings, step_id=None):
    if not settings.preview_step_id:
        return
    if step_id and settings.preview_step_id == step_id and settings.preview_action:
        if not project.rollback_action_preview(bpy.context.scene):
            raise RuntimeError("无法重建已保存的 Action 预览；请先丢弃并恢复检查点")
        return
    raise RuntimeError("请先接受或丢弃当前预览，再运行其他步骤")


def _require_restore_before_rerun(scene, step_id):
    record = project.find_step_record(scene.mocap_doctor, step_id, create=False)
    if record is not None and record.status in {"ACCEPTED", "STALE"}:
        if step_id == "hand_ranges":
            raise RuntimeError(
                "手部标注已提交；请到“手部区间修复”页面点击“返回修改坏区间（保留现有标注）”"
            )
        label = step_at(STEP_INDEX.get(step_id, 0)).label
        raise RuntimeError(f"此步骤已经提交；请使用“恢复到‘{label}’执行前”后再运行")


def _begin_structure_preview(scene, step_id):
    settings = scene.mocap_doctor
    _ensure_no_pending_preview(settings, step_id)
    recovery = project.create_checkpoint(scene, f"{step_id}_before")
    settings.preview_step_id = step_id
    settings.preview_restore_checkpoint = str(recovery)
    settings.preview_owner_name = ""
    settings.preview_base_action = ""
    settings.preview_action = ""
    project.record_step(scene, step_id, "PREVIEW", "等待人工检查")
    return recovery


def _record_report(scene, step_id, report, status, message, params=None):
    path = project.write_report(scene, step_id, report)
    project.record_step(
        scene,
        step_id,
        status,
        message,
        artifact_path=str(path),
        parameter_hash=project.parameter_hash(params or report.get("params", {})),
    )
    return path


def _planted_ranges(scene):
    return {
        "L": annotation.get_channel_ranges(scene, annotation.CHANNEL_FOOT_L_EFFECTIVE),
        "R": annotation.get_channel_ranges(scene, annotation.CHANNEL_FOOT_R_EFFECTIVE),
    }


def _validate_mmd_identity(settings):
    root = _require_object(settings, "model_root", "EMPTY", OBJECT_NAMES["model_root"])
    armature = _require_object(settings, "mmd_armature", "ARMATURE", OBJECT_NAMES["mmd_armature"])
    rig = _require_object(settings, "mmr_rig", "ARMATURE", OBJECT_NAMES["mmr_rig"])
    if armature.parent != root:
        raise RuntimeError("原生 MMD Armature 不在固定 Teto MMD Root 下")
    marker = getattr(root, "mmd_type", "")
    if marker not in {None, "", "ROOT"}:
        raise RuntimeError("Teto 根对象不是 mmd_tools ROOT")
    if marker != "ROOT" and not hasattr(root, "mmd_root"):
        raise RuntimeError("无法确认 Teto 的 mmd_tools 根结构")
    missing = [
        name
        for name in (MMD_ROOT_BONE, MMD_CENTER_BONE, *MMD_LEG_FK_BONES)
        if name not in armature.pose.bones
    ]
    if missing:
        raise RuntimeError("MMD 骨骼结构不匹配：" + ", ".join(missing))
    foot_ik = {side: resolve_mmd_foot_ik(armature, side) for side in ("L", "R")}
    if not all(foot_ik.values()):
        raise RuntimeError("无法通过 mmd_tools 元数据确认左右足 IK")
    mesh = _require_object(settings, "target_mesh", "MESH", OBJECT_NAMES["target_mesh"])
    if mesh.parent != armature:
        raise RuntimeError("Teto Mesh 不在固定原生 MMD Armature 下")
    armature_modifiers = [modifier for modifier in mesh.modifiers if modifier.type == "ARMATURE"]
    if not any(getattr(modifier, "object", None) == armature for modifier in armature_modifiers):
        raise RuntimeError("Teto Mesh 的 Armature Modifier 未指向固定 MMD 骨架")
    return root, armature, rig, foot_ik


def _validate_mmd_constraint_mapping(settings):
    _root, armature, rig, foot_ik = _validate_mmd_identity(settings)
    constrained = []
    errors = []
    for bone_name, (constraint_type, subtarget) in MMR_LEG_CONSTRAINTS.items():
        bone = armature.pose.bones.get(bone_name)
        constraint = bone.constraints.get(MMR_COPY_CONSTRAINT_NAME) if bone else None
        valid = (
            constraint is not None
            and constraint.type == constraint_type
            and getattr(constraint, "target", None) == rig
            and getattr(constraint, "subtarget", "") == subtarget
            and not constraint.mute
            and abs(float(constraint.influence) - 1.0) < 1.0e-6
            and getattr(constraint, "owner_space", "WORLD") == "WORLD"
            and getattr(constraint, "target_space", "WORLD") == "WORLD"
            and getattr(constraint, "mix_mode", "REPLACE") == "REPLACE"
            and getattr(constraint, "is_valid", True)
            and subtarget in rig.pose.bones
        )
        if not valid:
            errors.append(bone_name)
    if errors:
        raise RuntimeError("MMR 腿部约束与 arue Teto 基准不一致：" + ", ".join(errors))
    invalid_targets = []
    for bone in armature.pose.bones:
        for constraint in bone.constraints:
            if (
                getattr(constraint, "target", None) != rig
                or constraint.mute
                or float(constraint.influence) <= 0.0
            ):
                continue
            subtarget = getattr(constraint, "subtarget", "")
            if not subtarget or subtarget not in rig.pose.bones or not getattr(constraint, "is_valid", True):
                invalid_targets.append(f"{bone.name} -> {subtarget or '<空>'}")
            constrained.append(bone)
    if invalid_targets:
        raise RuntimeError("MMR 约束目标损坏：" + ", ".join(invalid_targets))
    constrained = list({bone.name: bone for bone in constrained}.values())
    if not constrained:
        raise RuntimeError("没有检测到 MMR 到 MMD 的复制约束")
    return armature, rig, foot_ik, constrained


def _bone_has_range_keys(action, bone_name, frame_start, frame_end):
    prefix = f'pose.bones["{bone_name}"]'
    curves = [curve for curve in action.fcurves if curve.data_path.startswith(prefix)]
    has_start = any(
        abs(float(point.co.x) - int(frame_start)) < 0.001
        for curve in curves
        for point in curve.keyframe_points
    )
    has_end = any(
        abs(float(point.co.x) - int(frame_end)) < 0.001
        for curve in curves
        for point in curve.keyframe_points
    )
    return bool(curves) and has_start and has_end


def _action_has_range_keys(action, frame_start, frame_end):
    points = [point for curve in action.fcurves for point in curve.keyframe_points]
    if not points:
        return False
    minimum = min(float(point.co.x) for point in points)
    maximum = max(float(point.co.x) for point in points)
    return minimum <= int(frame_start) and maximum >= int(frame_end)


def _action_bone_names(action, armature):
    """Return pose bones represented by an Action, independent of constraints."""

    if action is None or armature is None:
        return set()
    return {
        bone.name
        for bone in armature.pose.bones
        if action_has_any_bone_curve(action, [bone.name])
    }


def _validate_mmd_action(
    action,
    foot_ik,
    frame_start,
    frame_end,
    expected_bones=(),
    require_clean_fk=False,
):
    required = [MMD_ROOT_BONE, foot_ik["L"], foot_ik["R"]]
    required.extend(name for name in expected_bones if name not in required)
    missing = [
        name
        for name in required
        if not _bone_has_range_keys(action, name, frame_start, frame_end)
    ]
    if missing:
        preview = ", ".join(missing[:12])
        if len(missing) > 12:
            preview += f" 等 {len(missing)} 根"
        raise RuntimeError("Bake 输出缺少覆盖起止帧的骨骼曲线：" + preview)
    remaining_fk = [name for name in MMD_LEG_FK_BONES if action_has_any_bone_curve(action, [name])]
    if require_clean_fk and remaining_fk:
        raise RuntimeError("仍有腿 FK 曲线：" + ", ".join(remaining_fk))
    return remaining_fk


def _active_mmr_constraints(armature, rig):
    return [
        constraint
        for bone in armature.pose.bones
        for constraint in bone.constraints
        if getattr(constraint, "target", None) == rig
        and not constraint.mute
        and float(constraint.influence) > 0.0
    ]


def _mmr_driven_bone_names(armature, rig):
    return sorted(
        {
            bone.name
            for bone in armature.pose.bones
            for constraint in bone.constraints
            if getattr(constraint, "target", None) == rig
        }
    )


def _mute_mmr_constraints(armature, rig):
    constraints = _active_mmr_constraints(armature, rig)
    for constraint in constraints:
        constraint.mute = True
    return len(constraints)


def _write_hand_annotation_report(scene):
    automatic = {
        "L": [list(item) for item in annotation.get_channel_ranges(scene, annotation.CHANNEL_HAND_L_AUTO)],
        "R": [list(item) for item in annotation.get_channel_ranges(scene, annotation.CHANNEL_HAND_R_AUTO)],
    }
    final_ranges = {
        "L": [list(item) for item in annotation.get_channel_ranges(scene, annotation.CHANNEL_HAND_L_MANUAL)],
        "R": [list(item) for item in annotation.get_channel_ranges(scene, annotation.CHANNEL_HAND_R_MANUAL)],
    }
    report = {
        "schema_version": "mocap_doctor_hand_ranges_v2",
        "frame_range": [scene.mocap_doctor.mocap_frame_start, scene.mocap_doctor.mocap_frame_end],
        "automatic_seed_ranges": automatic,
        "final_ranges": final_ranges,
        # Kept for readers of the v1 report schema.
        "manual_ranges": final_ranges,
    }
    return _record_report(scene, "hand_ranges", report, "PREVIEW", "手部坏区间等待提交")


def _write_effective_contact_report(scene):
    settings = scene.mocap_doctor
    record = project.find_step_record(settings, "contacts", create=False)
    if record is None or not record.artifact_path or not Path(record.artifact_path).is_file():
        raise RuntimeError("找不到本次 planted 自动检测报告，请先运行检测")
    with Path(record.artifact_path).open("r", encoding="utf-8") as handle:
        raw_report = json.load(handle)
    additions = {}
    deletions = {}
    effective = _planted_ranges(scene)
    for side in ("L", "R"):
        foot = raw_report["feet"][side]
        raw = foot.get("raw", foot).get("planted_segments", ())
        changes = diff_ranges(raw, effective[side])
        additions[side] = changes["added"]
        deletions[side] = changes["removed"]
    final_report = core_contacts.apply_contact_overrides(
        raw_report,
        additions=additions,
        deletions=deletions,
        merge_gap=0,
        min_segment_len=1,
    )
    return _record_report(
        scene,
        "contacts",
        final_report,
        "PREVIEW",
        "最终 planted 区间等待提交",
        final_report.get("params", {}),
    )


def _settings(context):
    return context.scene.mocap_doctor


def _require_project(context):
    settings = _settings(context)
    if not settings.initialized:
        raise RuntimeError("请先创建 MoCap Doctor 工作项目")
    if context.scene.render.fps != EXPECTED_FPS or context.scene.render.fps_base != 1.0:
        raise RuntimeError("项目必须保持 30fps / fps_base 1.0")
    if settings.mocap_frame_end < settings.mocap_frame_start:
        raise RuntimeError("有效动捕结束帧不能早于开始帧")
    project.apply_project_range(context.scene, settings)
    return settings


def _default_template_path():
    current = Path(bpy.data.filepath) if bpy.data.filepath else None
    candidates = []
    if current:
        candidates.extend(
            [
                current.parent / "arue_teto.blend",
                current.parent / "blends" / "arue_teto.blend",
                current.parent.parent / "blends" / "arue_teto.blend",
            ]
        )
    for path in candidates:
        if path.is_file():
            return str(path)
    return ""


@contextmanager
def _active_armature(context, armature, pose=False):
    view_layer = context.view_layer
    selected = [obj for obj in view_layer.objects if obj.select_get()]
    active = view_layer.objects.active
    old_mode = active.mode if active else "OBJECT"
    try:
        if active and active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        armature.hide_set(False)
        armature.select_set(True)
        view_layer.objects.active = armature
        if pose:
            bpy.ops.object.mode_set(mode="POSE")
        yield
    finally:
        try:
            if view_layer.objects.active and view_layer.objects.active.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
        except RuntimeError:
            pass
        bpy.ops.object.select_all(action="DESELECT")
        for obj in selected:
            if obj.name in view_layer.objects:
                obj.select_set(True)
        if active and active.name in view_layer.objects:
            view_layer.objects.active = active
            if old_mode != "OBJECT":
                try:
                    bpy.ops.object.mode_set(mode=old_mode)
                except RuntimeError:
                    pass


def remove_bone_fcurves(action, bone_names):
    prefixes = tuple(f'pose.bones["{name}"]' for name in bone_names)
    removed = []
    for fcurve in list(action.fcurves):
        if fcurve.data_path.startswith(prefixes):
            removed.append((fcurve.data_path, fcurve.array_index))
            action.fcurves.remove(fcurve)
    return removed


def action_has_any_bone_curve(action, candidates):
    prefixes = tuple(f'pose.bones["{name}"]' for name in candidates)
    return any(fcurve.data_path.startswith(prefixes) for fcurve in action.fcurves)


def _pose_bone_vmd_name(pose_bone):
    metadata = getattr(pose_bone, "mmd_bone", None)
    japanese = str(getattr(metadata, "name_j", "") or "") if metadata else ""
    return japanese or pose_bone.name


def _bone_has_exportable_vmd_curve(action, pose_bone):
    prefix = f'pose.bones["{pose_bone.name}"]'
    rotation_path = {
        "QUATERNION": "rotation_quaternion",
        "AXIS_ANGLE": "rotation_axis_angle",
    }.get(pose_bone.rotation_mode, "rotation_euler")
    export_paths = {f"{prefix}.location", f"{prefix}.{rotation_path}"}
    return any(curve.data_path in export_paths for curve in action.fcurves)


def _keyed_vmd_name_collisions(armature, action):
    """Return VMD export names shared by multiple keyed pose bones."""

    by_export_name = {}
    for bone in armature.pose.bones:
        if not _bone_has_exportable_vmd_curve(action, bone):
            continue
        by_export_name.setdefault(_pose_bone_vmd_name(bone), []).append(bone.name)
    return {
        export_name: names
        for export_name, names in by_export_name.items()
        if len(names) > 1
    }


def _curve_covers_frame_range(curve, frame_start, frame_end):
    """Check that an F-curve can be evaluated throughout the motion range.

    MikuMikuRig's Bake may compress a dense result to a few Bezier keys.  A
    key on every frame is not needed for a valid VMD export: every required
    channel only needs keys on both sides of the requested frame range.
    """

    frames = [float(point.co.x) for point in curve.keyframe_points]
    return bool(frames) and min(frames) <= float(frame_start) + 0.001 and max(frames) >= float(frame_end) - 0.001


def _bone_has_complete_arm_animation(action, pose_bone, frame_start, frame_end):
    bone_name = pose_bone.name
    prefix = f'pose.bones["{bone_name}"]'

    def complete(data_path, indices):
        curves = {
            int(curve.array_index): curve
            for curve in action.fcurves
            if curve.data_path == f"{prefix}.{data_path}"
        }
        return all(
            index in curves
            and _curve_covers_frame_range(curves[index], frame_start, frame_end)
            for index in indices
        )

    rotation_path, rotation_indices = {
        "QUATERNION": ("rotation_quaternion", range(4)),
        "AXIS_ANGLE": ("rotation_axis_angle", range(4)),
    }.get(pose_bone.rotation_mode, ("rotation_euler", range(3)))
    rotation_complete = complete(rotation_path, rotation_indices)
    return complete("location", range(3)) and rotation_complete


def _sample_pose_bone_matrices(scene, armature, bone_names, frame_start, frame_end):
    samples = {}
    view_layer = bpy.context.view_layer
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        view_layer.update()
        samples[frame] = {
            name: armature.pose.bones[name].matrix.copy()
            for name in bone_names
        }
    return samples


def _maximum_matrix_sample_error(before, after):
    maximum = 0.0
    for frame, bones in before.items():
        for bone_name, matrix in bones.items():
            compared = after[frame][bone_name]
            maximum = max(
                maximum,
                max(
                    abs(float(matrix[row][column] - compared[row][column]))
                    for row in range(4)
                    for column in range(4)
                ),
            )
    return maximum


def _require_complete_arm_fk_animation(action, armature, frame_start, frame_end):
    """Require complete transform channels across the six physical arm bones."""

    missing = []
    for bone_name in MMD_ARM_FK_BONES:
        pose_bone = armature.pose.bones.get(bone_name)
        if pose_bone is None:
            missing.append(f"{bone_name}（骨骼不存在）")
        elif not _bone_has_complete_arm_animation(action, pose_bone, frame_start, frame_end):
            missing.append(bone_name)
    if missing:
        raise RuntimeError("上肢 Bake 不完整，不能导出 VMD：" + ", ".join(missing))


def _visual_bake_teto_arm_fk(scene, armature, action, frame_start, frame_end):
    """Bake the evaluated upper-arm/elbow/wrist result into real FK bones."""

    missing = [name for name in MMD_ARM_FK_BONES if armature.pose.bones.get(name) is None]
    if missing:
        raise RuntimeError("固定 Teto 缺少上肢骨骼：" + ", ".join(missing))
    if armature.animation_data is None or armature.animation_data.action is not action:
        raise RuntimeError("MMD Action 不是原生骨架的活动 Action，无法烘焙上肢")
    with _active_armature(bpy.context, armature, pose=True):
        bpy.ops.pose.select_all(action="DESELECT")
        for bone_name in MMD_ARM_FK_BONES:
            armature.pose.bones[bone_name].bone.select = True
        result = bpy.ops.nla.bake(
            frame_start=int(frame_start), frame_end=int(frame_end), step=1,
            only_selected=True, visual_keying=True, clear_constraints=False,
            clear_parents=False, use_current_action=True, clean_curves=False,
            bake_types={"POSE"},
        )
    if "FINISHED" not in result:
        raise RuntimeError("上肢 FK Visual Bake 没有成功完成")
    _require_complete_arm_fk_animation(action, armature, frame_start, frame_end)
    return {"bones": list(MMD_ARM_FK_BONES), "frame_range": [int(frame_start), int(frame_end)]}


def _resolve_teto_hand_ik_helpers(armature):
    """Return Blender-only MMR hand helpers, keeping real wrists mandatory."""

    helpers = {}
    absent_sides = []
    for side in ("L", "R"):
        wrist, helper = resolve_mmd_hand_bones(armature, side)
        if wrist is None:
            raise RuntimeError(f"固定 Teto 缺少 {side} 侧真实手首骨骼")
        if helper is None:
            absent_sides.append(side)
        else:
            helpers[side] = helper.name
    return helpers, absent_sides


def _remove_mmr_hand_helper_constraints(armature, helper_names):
    """Remove constraints that would point at a helper being deleted."""

    removed = []
    helper_names = set(helper_names)
    for pose_bone in armature.pose.bones:
        for constraint in list(pose_bone.constraints):
            if getattr(constraint, "subtarget", "") not in helper_names:
                continue
            label = f"{pose_bone.name}:{constraint.name}"
            pose_bone.constraints.remove(constraint)
            removed.append(label)
    return removed


def _restore_teto_elbow_parents_and_remove_helpers(armature, helper_names):
    """Restore Teto's arm hierarchy, then delete MMR's temporary hand bones."""

    restored_parents = []
    deleted_helpers = []
    with _active_armature(bpy.context, armature, pose=False):
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = armature.data.edit_bones
        for side in ("L", "R"):
            elbow_name = MMD_ELBOW_BONES[side]
            twist_name = MMD_ARM_TWIST_BONES[side]
            upper_arm_name = f"腕.{side}"
            elbow = edit_bones.get(elbow_name)
            twist = edit_bones.get(twist_name)
            if elbow is None or twist is None:
                raise RuntimeError(f"固定 Teto 缺少 {side} 侧肘部或腕捩骨骼")
            parent = elbow.parent
            if parent == twist:
                continue
            if parent is None or parent.name != upper_arm_name:
                found = parent.name if parent else "无父级"
                raise RuntimeError(
                    f"{elbow_name} 的父级是 {found}，不是固定 Teto 的 {upper_arm_name} 或 {twist_name}；"
                    "为避免猜测性改骨，已停止导出"
                )
            elbow.parent = twist
            restored_parents.append({"bone": elbow_name, "from": upper_arm_name, "to": twist_name})
        for helper_name in helper_names:
            helper = edit_bones.get(helper_name)
            if helper is None:
                raise RuntimeError(f"准备删除的手 IK 辅助骨不存在：{helper_name}")
            children = [bone.name for bone in edit_bones if bone.parent == helper]
            if children:
                raise RuntimeError(
                    f"{helper_name} 仍有子骨骼（{', '.join(children)}），不能安全删除"
                )
            edit_bones.remove(helper)
            deleted_helpers.append(helper_name)
    return restored_parents, deleted_helpers


def _prepare_teto_mmr_hand_export_cleanup(
    scene,
    armature,
    action,
    frame_start,
    frame_end,
    *,
    matrix_tolerance=1.0e-4,
):
    """Convert MMR's temporary hand controls back into a portable Teto arm."""

    # MMD Bake already creates the physical arm keys. Re-baking here can
    # overwrite a valid manual Bake under MMR's altered elbow hierarchy.
    _require_complete_arm_fk_animation(action, armature, frame_start, frame_end)
    arm_bake = {
        "operation": "validated_existing_arm_fk_bake",
        "bones": list(MMD_ARM_FK_BONES),
        "frame_range": [int(frame_start), int(frame_end)],
    }
    arm_names = list(MMD_ARM_FK_BONES)
    original_frame = int(scene.frame_current)
    try:
        before = _sample_pose_bone_matrices(scene, armature, arm_names, frame_start, frame_end)
        helpers, absent_helpers = _resolve_teto_hand_ik_helpers(armature)
        helper_names = list(helpers.values())
        removed_constraints = _remove_mmr_hand_helper_constraints(armature, helper_names)
        removed_curves = {
            helper_name: len(remove_bone_fcurves(action, [helper_name]))
            for helper_name in helper_names
        }
        restored_parents, deleted_helpers = _restore_teto_elbow_parents_and_remove_helpers(
            armature, helper_names
        )
        bpy.context.view_layer.update()
        after = _sample_pose_bone_matrices(scene, armature, arm_names, frame_start, frame_end)
        maximum_error = _maximum_matrix_sample_error(before, after)
    finally:
        scene.frame_set(original_frame)
        bpy.context.view_layer.update()

    if maximum_error > float(matrix_tolerance):
        raise RuntimeError(
            "上肢 FK 兼容 Bake 后姿势发生变化，已阻止导出："
            f"最大矩阵误差 {maximum_error:.6g}"
        )
    return {
        "operation": "prepare_teto_mmr_hand_export_cleanup",
        "arm_fk_bake": arm_bake,
        "restored_elbow_parents": restored_parents,
        "deleted_hand_ik_helpers": deleted_helpers,
        "hand_ik_helper_not_present": absent_helpers,
        "removed_hand_helper_constraints": removed_constraints,
        "removed_helper_fcurves_by_bone": removed_curves,
        "removed_helper_fcurve_count": sum(removed_curves.values()),
        "maximum_arm_matrix_error": maximum_error,
    }


def _require_no_keyed_vmd_name_collisions(armature, action):
    collisions = _keyed_vmd_name_collisions(armature, action)
    if collisions:
        details = "; ".join(
            f"{export_name}: {', '.join(names)}"
            for export_name, names in sorted(collisions.items())
        )
        raise RuntimeError("仍有带关键帧的重复 VMD 骨名：" + details)
    return collisions


def _run_source_analyze(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "source_analyze")
    armature = _require_object(
        settings, "source_armature", "ARMATURE", OBJECT_NAMES["source_armature"]
    )
    thresholds = {
        "foot_contact_height_m": settings.source_diagnostic_contact_height,
        "foot_slide_speed_m_per_frame": settings.source_foot_slide_speed,
        "heel_slide_speed_m_per_frame": settings.source_heel_slide_speed,
        "hand_jump_m_per_frame": settings.source_hand_jump,
        "hips_jump_m_per_frame": settings.source_hips_jump,
    }
    report = core_source.analyze_source_motion(
        scene,
        armature,
        thresholds=thresholds,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
    )
    hints = {"L": [], "R": []}
    for issue in report.get("issues", ()):
        if issue.get("type") != "hand_jump":
            continue
        if issue.get("bone") == SOURCE_BONES["left_hand"]:
            hints["L"].extend(issue.get("frames", ()))
        elif issue.get("bone") == SOURCE_BONES["right_hand"]:
            hints["R"].extend(issue.get("frames", ()))
    scene["mcd_hand_l_manual_initialized"] = False
    scene["mcd_hand_r_manual_initialized"] = False
    annotation.set_hand_auto_hints(
        scene,
        "L",
        hints["L"],
        force_manual=True,
        rebuild=False,
    )
    annotation.set_hand_auto_hints(
        scene,
        "R",
        hints["R"],
        force_manual=True,
        rebuild=True,
    )
    path = _record_report(
        scene,
        "source_analyze",
        report,
        "ACCEPTED",
        f"诊断完成，生成 {len(hints['L']) + len(hints['R'])} 个手部提示区间",
        thresholds,
    )
    settings.current_step = STEP_INDEX["hand_ranges"]
    settings.status_message = "源动作诊断已完成"
    project.create_accepted_checkpoint(scene, "source_analyze", "源动作诊断已完成")
    return f"源诊断完成：{path.name}"


def _run_hand_repair(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "hand_repair")
    if scene.mcd_annotation_mode and settings.annotation_step_id == "hand_ranges":
        annotation.commit_track_reassignments(scene, rebuild=False)
    armature = _require_object(settings, "source_armature", "ARMATURE")
    _require_action(armature, "FreeMoCap 源骨架")
    ranges = {
        SOURCE_BONES["left_hand"]: annotation.get_channel_ranges(
            scene, annotation.CHANNEL_HAND_L_MANUAL
        ),
        SOURCE_BONES["right_hand"]: annotation.get_channel_ranges(
            scene, annotation.CHANNEL_HAND_R_MANUAL
        ),
    }
    if not any(ranges.values()):
        raise RuntimeError("最终手部坏区间为空")
    _ensure_no_pending_preview(settings, "hand_repair")
    action = project.begin_action_preview(scene, armature, "hand_repair")
    result = core_source.repair_hand_chain_ranges(
        scene,
        armature,
        action,
        ranges,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
    )
    if result.get("values_written", 0) <= 0:
        raise RuntimeError("没有找到可插值的手臂链 F-Curve")
    _record_report(scene, "hand_repair", result, "PREVIEW", "手部修复预览等待检查")
    return f"已修复 {result['processed_range_count']} 个手部区间"


def _run_smooth(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "smooth")
    armature = _require_object(settings, "source_armature", "ARMATURE")
    _require_action(armature, "FreeMoCap 源骨架")
    _ensure_no_pending_preview(settings, "smooth")
    action = project.begin_action_preview(scene, armature, "smooth")
    params = {
        "radius": settings.smooth_radius,
        "strength": settings.smooth_strength,
        "include_hands": settings.smooth_include_hands,
    }
    result = core_source.mild_rotation_smooth(
        scene,
        armature,
        action,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        **params,
    )
    _record_report(scene, "smooth", result, "PREVIEW", "旋转平滑预览等待检查", params)
    return f"已平滑 {result.get('changed_bone_count', len(result.get('changed_bones', ())))} 根骨骼"


def _run_source_floor(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "source_floor")
    armature = _require_object(settings, "source_armature", "ARMATURE")
    _require_action(armature, "FreeMoCap 源骨架")
    _ensure_no_pending_preview(settings, "source_floor")
    action = project.begin_action_preview(scene, armature, "source_floor")
    params = {
        "floor_z": settings.source_floor_z,
        "tolerance": settings.source_floor_tolerance,
        "target_clearance": settings.source_floor_clearance,
        "max_lift_per_frame": settings.source_floor_max_lift,
        "strength": settings.source_floor_strength,
        "smooth_radius": settings.source_floor_smooth_radius,
        "max_correction_delta_per_frame": settings.source_floor_max_delta,
    }
    result = core_source.repair_source_pelvis_floor_v2(
        scene,
        armature,
        action,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        **params,
    )
    _record_report(scene, "source_floor", result, "PREVIEW", "源骨架穿地修复等待检查", params)
    return f"源地面修复影响 {result.get('changed_frames', 0)} 帧"


def _run_contacts(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "contacts")
    _ensure_no_pending_preview(settings)
    armature = _require_object(settings, "source_armature", "ARMATURE")
    params = {
        "floor_z": settings.source_floor_z,
        "contact_height": settings.contact_height,
        "planted_xy_speed": settings.contact_xy_speed,
        "moving_xy_speed": settings.contact_moving_xy_speed,
        "max_vertical_speed": settings.contact_vertical_speed,
        "min_segment_len": settings.contact_min_segment_len,
        "merge_gap": settings.contact_merge_gap,
        "max_anchor_drift": settings.contact_anchor_drift,
        "penetration_tolerance": settings.contact_penetration_tolerance,
    }
    report = core_contacts.detect_contacts_v2(
        scene,
        armature,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        **params,
    )
    for side in ("L", "R"):
        raw = report["feet"][side]["raw"]["planted_segments"]
        annotation.set_planted_auto_ranges(
            scene,
            side,
            raw,
            initialize_effective=True,
            rebuild=side == "R",
        )
    path = _record_report(
        scene,
        "contacts",
        report,
        "PREVIEW",
        "自动 planted 已更新；请检查最终区间",
        params,
    )
    return f"Planted 检测完成：{path.name}"


def _run_global_correction(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "global_correction")
    model_root = _require_object(
        settings, "model_root", "EMPTY", OBJECT_NAMES["model_root"]
    )
    rig = _require_object(settings, "mmr_rig", "ARMATURE", OBJECT_NAMES["mmr_rig"])
    _begin_structure_preview(scene, "global_correction")
    correction = core_target.ensure_global_correction_empty(
        OBJECT_NAMES["correction_empty"], collection=scene.collection
    )
    settings.correction_empty = correction
    degrees = tuple(
        math.degrees(value)
        for value in (settings.global_rot_x, settings.global_rot_y, settings.global_rot_z)
    )
    result = core_target.apply_global_correction(
        model_root, rig, correction, rotation_degrees=degrees
    )
    _record_report(
        scene,
        "global_correction",
        result,
        "PREVIEW",
        "Teto 全局扶正等待检查",
        {"rotation_degrees": degrees},
    )
    return "Teto 全局扶正预览已生成"


def _run_tilt(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "tilt")
    rig = _require_object(settings, "mmr_rig", "ARMATURE", OBJECT_NAMES["mmr_rig"])
    _require_action(rig, "MMR Rig")
    _ensure_no_pending_preview(settings, "tilt")
    action = project.begin_action_preview(scene, rig, "tilt")
    params = {
        "reference_frame": settings.tilt_reference_frame,
        "strength": settings.tilt_strength,
        "damp_axes": (settings.tilt_damp_x, settings.tilt_damp_y, settings.tilt_damp_z),
    }
    result = core_target.damp_foot_ik_tilt(
        scene,
        rig,
        action,
        foot_bones=tuple(TARGET_FOOT_IK.values()),
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        **params,
    )
    _record_report(scene, "tilt", result, "PREVIEW", "Foot IK 倾斜修复等待检查", params)
    return "Foot IK 倾斜修复预览已生成"


def _run_target_floor(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "target_floor")
    model_root = _require_object(
        settings, "model_root", "EMPTY", OBJECT_NAMES["model_root"]
    )
    correction = _require_object(
        settings, "correction_empty", "EMPTY", OBJECT_NAMES["correction_empty"]
    )
    _validate_correction_transform(correction)
    _ensure_no_pending_preview(settings, "target_floor")
    action = project.begin_action_preview(scene, correction, "target_floor")
    params = {
        "floor_z": settings.target_floor_z,
        "target_clearance": settings.target_clearance,
        "tolerance": settings.target_floor_tolerance,
        "max_lift_per_frame": settings.target_floor_max_lift,
        "strength": settings.target_floor_strength,
        "smooth_radius": settings.target_floor_smooth_radius,
        "max_delta_per_frame": settings.target_floor_max_delta,
        "visible_only": settings.target_visible_only,
        "vertex_sample_step": settings.target_vertex_sample_step,
        "reset_existing_z_curve": settings.target_reset_existing_z,
    }
    result = core_target.repair_mesh_floor_lift_v3_safe(
        scene,
        model_root,
        correction,
        action=action,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        **params,
    )
    _record_report(scene, "target_floor", result, "PREVIEW", "Teto Mesh 穿地修复等待检查", params)
    return f"Mesh 地面修复影响 {result.get('changed_frames', 0)} 帧"


def _run_foot_lock(context, settings):
    scene = context.scene
    _require_restore_before_rerun(scene, "foot_lock")
    planted = _planted_ranges(scene)
    if not any(planted.values()):
        raise RuntimeError("最终 planted 区间为空，请先完成接触区间修订")
    rig = _require_object(settings, "mmr_rig", "ARMATURE", OBJECT_NAMES["mmr_rig"])
    _require_action(rig, "MMR Rig")
    drift = core_target.analyze_foot_ik_drift(
        scene,
        rig,
        planted,
        foot_bones=TARGET_FOOT_IK,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        trim_segment_ends=settings.lock_trim,
        min_segment_len=settings.drift_min_segment_len,
    )
    _ensure_no_pending_preview(settings, "foot_lock")
    action = project.begin_action_preview(scene, rig, "foot_lock")
    params = {
        "trim_segment_ends": settings.lock_trim,
        "min_segment_len": settings.lock_min_segment_len,
        "blend_frames": settings.lock_blend_frames,
        "anchor_mode": settings.lock_anchor_mode,
        "min_local_xy_range": settings.lock_min_xy_range,
        "lock_x": settings.lock_x,
        "lock_y": settings.lock_y,
        "lock_z": settings.lock_z,
    }
    repair = core_target.lock_foot_ik_xy(
        scene,
        rig,
        action,
        planted,
        foot_bones=TARGET_FOOT_IK,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        **params,
    )
    report = {"operation": "analyze_and_lock_teto_foot_ik", "drift_before": drift, "repair": repair}
    _record_report(scene, "foot_lock", report, "PREVIEW", "脚滑 XY Lock 等待检查", params)
    return f"XY Lock 修复 {repair.get('repaired_count', 0)} 个区间"


def _run_export_prep(context, settings):
    scene = context.scene
    if not bool(scene.get("mcd_hand_ik_export_confirmed", False)):
        raise RuntimeError("请先确认 MMR 手部导出清理提醒，再生成 VMD 导出预览")
    _require_restore_before_rerun(scene, "export_prep")
    model_root, armature, rig, foot_ik = _validate_mmd_identity(settings)
    correction = _require_object(
        settings, "correction_empty", "EMPTY", OBJECT_NAMES["correction_empty"]
    )
    if model_root.parent != correction or rig.parent != correction:
        raise RuntimeError("Teto MMD Root 与 MMR Rig 必须共同位于全局校正 Empty 下")
    _validate_correction_transform(correction)
    if _active_mmr_constraints(armature, rig):
        raise RuntimeError("仍有活动的 MMR 到 MMD 约束；请先完成并接受 MMD Bake")
    action = _require_action(armature, "原生 MMD Armature")
    _require_no_nla(armature, "原生 MMD Armature")
    _validate_mmd_action(
        action,
        foot_ik,
        settings.mocap_frame_start,
        settings.mocap_frame_end,
    )
    _begin_structure_preview(scene, "export_prep")
    baked = core_export.bake_global_correction_to_all_parent(
        scene,
        armature,
        correction,
        action=action,
        bone_name=MMD_ROOT_BONE,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
        reset_correction=True,
    )
    cleaned = core_export.remove_teto_leg_fk_curves(
        action, bone_names=MMD_LEG_FK_BONES
    )
    hand_export_cleanup = _prepare_teto_mmr_hand_export_cleanup(
        scene,
        armature,
        action,
        settings.mocap_frame_start,
        settings.mocap_frame_end,
    )
    _require_no_keyed_vmd_name_collisions(armature, action)
    offset = core_export.apply_vmd_floor_z_offset(
        scene,
        armature,
        action=action,
        bone_name=MMD_ROOT_BONE,
        z_offset=settings.vmd_floor_offset,
        frame_start=settings.mocap_frame_start,
        frame_end=settings.mocap_frame_end,
    )
    _validate_mmd_action(
        action,
        foot_ik,
        settings.mocap_frame_start,
        settings.mocap_frame_end,
        require_clean_fk=True,
    )
    report = {
        "operation": "prepare_teto_vmd_export",
        "global_correction_bake": baked,
        "leg_fk_cleanup": cleaned,
        "mmr_hand_export_cleanup": hand_export_cleanup,
        "floor_offset": offset,
        "validated_foot_ik": foot_ik,
    }
    _record_report(
        scene,
        "export_prep",
        report,
        "PREVIEW",
        "VMD 导出准备等待隐藏 MMR 检查",
        {"vmd_floor_offset": settings.vmd_floor_offset},
    )
    return (
        f"导出预览已生成，删除 {cleaned['removed_fcurve_count']} 条腿 FK 曲线、"
        f"{hand_export_cleanup['removed_helper_fcurve_count']} 条手 IK 辅助曲线"
    )


RUN_STEP_HANDLERS = {
    "source_analyze": _run_source_analyze,
    "hand_repair": _run_hand_repair,
    "smooth": _run_smooth,
    "source_floor": _run_source_floor,
    "contacts": _run_contacts,
    "global_correction": _run_global_correction,
    "tilt": _run_tilt,
    "target_floor": _run_target_floor,
    "foot_lock": _run_foot_lock,
    "export_prep": _run_export_prep,
}


class MD_OT_PrepareVMDExport(Operator):
    bl_idname = "mocap_doctor.prepare_vmd_export"
    bl_label = "确认并生成 VMD 导出预览"
    bl_description = "将手 IK 驱动的可见上肢动作烘到腕、肘、手首后再生成导出预览"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=560)

    def draw(self, context):
        layout = self.layout
        layout.label(text="将清理此工作文件中 MMR 创建的手部编辑控制。", icon="INFO")
        layout.label(text="会先确认上肢已烘到普通的“腕 / 肘 / 手首”骨骼，")
        layout.label(text="再恢复肘部层级，并删除只供 Blender 编辑使用的手 IK 骨。")
        layout.separator()
        layout.label(text="不会修改 PMX，也不会修改原始 Teto 模板。", icon="CHECKMARK")
        layout.label(text="会先创建检查点；丢弃预览即可完整恢复。", icon="LOOP_BACK")

    def execute(self, context):
        scene = context.scene
        scene["mcd_hand_ik_export_confirmed"] = True
        try:
            return bpy.ops.mocap_doctor.run_step("EXEC_DEFAULT", step_id="export_prep")
        finally:
            scene.pop("mcd_hand_ik_export_confirmed", None)


class MD_OT_RunStep(Operator):
    bl_idname = "mocap_doctor.run_step"
    bl_label = "运行当前 MoCap Doctor 步骤"

    step_id: StringProperty()

    def execute(self, context):
        settings = _settings(context)
        old_current_step = settings.current_step
        handler = RUN_STEP_HANDLERS.get(self.step_id)
        if handler is None:
            self.report({"ERROR"}, f"步骤没有自动执行器：{self.step_id}")
            return {"CANCELLED"}
        try:
            _require_project(context)
            settings.status_message = f"正在运行 {step_at(STEP_INDEX[self.step_id]).label}；Blender 可能暂时无响应"
            message = handler(context, settings)
            settings.busy = False
            settings.status_message = message
            if self.step_id in {"source_analyze", "contacts"}:
                project.save_workfile(context.scene)
            self.report({"INFO"}, message)
            return {"FINISHED"}
        except Exception as exc:
            settings.current_step = old_current_step
            if settings.preview_step_id == self.step_id and settings.preview_action:
                project.rollback_action_preview(context.scene)
            settings.status_message = str(exc)
            project.record_step(context.scene, self.step_id, "FAILED", str(exc))
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        finally:
            settings.busy = False


class MD_OT_CreateProject(Operator, ExportHelper):
    bl_idname = "mocap_doctor.create_project"
    bl_label = "创建 MoCap Doctor 工作副本"
    bl_description = "保留原文件，创建固定工作文件和基线检查点"

    filename_ext = ".blend"
    filter_glob: StringProperty(default="*.blend", options={"HIDDEN"})

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({"ERROR"}, "请先保存或打开一个源 .blend 文件")
            return {"CANCELLED"}
        source = Path(bpy.data.filepath)
        self.filepath = str(source.with_name(source.stem + "_mocap_doctor_work.blend"))
        return super().invoke(context, event)

    def execute(self, context):
        old_step = context.scene.mocap_doctor.current_step
        try:
            baseline = project.initialize_project(
                context.scene,
                self.filepath,
                target_template_path=_default_template_path(),
            )
            self.report({"INFO"}, f"工作项目已创建，基线：{baseline.name}")
            return {"FINISHED"}
        except Exception as exc:
            context.scene.mocap_doctor.current_step = old_step
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_DiscoverObjects(Operator):
    bl_idname = "mocap_doctor.discover_objects"
    bl_label = "重新检测对象"

    def execute(self, context):
        found = project.discover_known_objects(context.scene)
        names = [key for key, value in found.items() if value]
        self.report({"INFO"}, "已检测：" + (", ".join(names) if names else "没有匹配对象"))
        settings = context.scene.mocap_doctor
        if settings.initialized:
            project.save_workfile(context.scene)
        return {"FINISHED"}


class MD_OT_EnsureFPS(Operator):
    bl_idname = "mocap_doctor.ensure_fps"
    bl_label = "设为 30fps"

    def execute(self, context):
        changed = project.ensure_fps(context.scene)
        if hasattr(context.scene, "mocap_doctor") and context.scene.mocap_doctor.initialized:
            project.save_workfile(context.scene)
        self.report({"INFO"}, "已设为 30fps" if changed else "场景已经是 30fps")
        return {"FINISHED"}


class MD_OT_SetRangeBoundary(Operator):
    bl_idname = "mocap_doctor.set_range_boundary"
    bl_label = "设置动捕范围边界"

    boundary: StringProperty(default="START")

    def execute(self, context):
        settings = _settings(context)
        frame = int(context.scene.frame_current)
        if self.boundary == "START":
            settings.mocap_frame_start = frame
            context.scene.frame_start = frame
        else:
            settings.mocap_frame_end = frame
            context.scene.frame_end = frame
        if settings.mocap_frame_end < settings.mocap_frame_start:
            self.report({"WARNING"}, "结束帧早于开始帧，请继续设置另一端")
        if settings.initialized:
            project.save_workfile(context.scene)
        return {"FINISHED"}


class MD_OT_SyncRangeFromScene(Operator):
    bl_idname = "mocap_doctor.sync_range_from_scene"
    bl_label = "读取场景范围"

    def execute(self, context):
        project.sync_scene_range(context.scene, _settings(context))
        if context.scene.mocap_doctor.initialized:
            project.save_workfile(context.scene)
        return {"FINISHED"}


def _navigation_status_message(settings, step_id):
    record = project.find_step_record(settings, step_id, create=False)
    if record is not None and record.status in {"ACCEPTED", "STALE", "FAILED"}:
        return "正在浏览已执行的过去步骤；项目数据没有回退"
    return ""


class MD_OT_NavigateStep(Operator):
    bl_idname = "mocap_doctor.navigate_step"
    bl_label = "仅浏览步骤页面"
    bl_description = "只切换面板页面，不恢复文件、撤销结果或改变步骤状态"

    delta: IntProperty(default=0)
    target: IntProperty(default=-1)

    def execute(self, context):
        settings = _settings(context)
        if settings.preview_step_id:
            self.report({"ERROR"}, "请先接受或丢弃当前预览")
            return {"CANCELLED"}
        settings.current_step = clamp_step(self.target if self.target >= 0 else settings.current_step + self.delta)
        # Future/unexecuted pages are harmless previews of their controls;
        # avoid showing a rollback warning when there is nothing to undo.
        settings.status_message = _navigation_status_message(
            settings,
            step_at(settings.current_step).id,
        )
        project.save_workfile(context.scene)
        return {"FINISHED"}


class MD_OT_RestoreBeforeStep(Operator):
    bl_idname = "mocap_doctor.restore_before_step"
    bl_label = "恢复并重新执行此步骤"
    bl_description = "恢复此步骤执行前的检查点，恢复完成后停留在此步骤；不会仅切换页面"

    step_id: StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            target_index = STEP_INDEX.get(self.step_id)
            if target_index is None:
                raise RuntimeError("未知工作流步骤")
            candidates = []
            for record in settings.steps:
                index = STEP_INDEX.get(record.step_id, -1)
                if index < target_index and record.status == "ACCEPTED" and record.checkpoint:
                    path = Path(record.checkpoint)
                    if path.is_file():
                        candidates.append((index, path))
            if not candidates:
                raise RuntimeError("找不到此步骤之前的已接受检查点")
            _index, checkpoint = max(candidates, key=lambda item: item[0])
            label = step_at(target_index).label
            project.restore_checkpoint(
                checkpoint,
                settings.work_filepath,
                resume_step_id=self.step_id,
                reset_step_id=self.step_id,
                message=f"已恢复到“{label}”执行前，可以重新运行",
            )
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_ReviseHandRanges(Operator):
    bl_idname = "mocap_doctor.revise_hand_ranges"
    bl_label = "返回修改坏区间"
    bl_description = "撤销手部修复结果但保留现有坏区间，恢复后直接回到坏区间标注页面"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            repair_record = project.find_step_record(
                settings,
                "hand_repair",
                create=False,
            )
            repair_was_accepted = repair_record is not None and repair_record.status in {
                "ACCEPTED",
                "STALE",
            }

            if repair_was_accepted:
                ranges_record = project.find_step_record(
                    settings,
                    "hand_ranges",
                    create=False,
                )
                checkpoint = Path(ranges_record.checkpoint) if ranges_record and ranges_record.checkpoint else None
                if checkpoint is None or not checkpoint.is_file():
                    raise RuntimeError("找不到包含现有手部标注的检查点")
                _request_annotation_after_restore("HAND")
                try:
                    project.restore_checkpoint(
                        checkpoint,
                        settings.work_filepath,
                        resume_step_id="hand_ranges",
                        reset_step_id="hand_ranges",
                        message="已保留现有标注；请补充或调整手部坏区间",
                    )
                except Exception:
                    _cancel_pending_annotation_open()
                    raise
                return {"FINISHED"}

            if settings.preview_step_id == "hand_repair" and settings.preview_action:
                if not project.rollback_action_preview(context.scene):
                    raise RuntimeError("无法撤销当前手部修复预览")
            if repair_record is not None:
                repair_record.status = "PENDING"
                repair_record.message = "等待重新执行"
            ranges_record = project.find_step_record(settings, "hand_ranges", create=False)
            if ranges_record is not None:
                ranges_record.status = "PENDING"
                ranges_record.message = "等待补充标注"
            project.mark_downstream_stale(context.scene, "hand_ranges")
            settings.current_step = STEP_INDEX["hand_ranges"]
            settings.status_message = "已保留现有标注；请补充或调整手部坏区间"
            project.save_workfile(context.scene)
            _activate_annotation_editor(context.scene, context.screen, "HAND")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_CreateCheckpoint(Operator):
    bl_idname = "mocap_doctor.create_checkpoint"
    bl_label = "记录当前状态"

    label: StringProperty(default="manual_milestone")
    step_id: StringProperty(default="")

    def execute(self, context):
        old_step = context.scene.mocap_doctor.current_step
        try:
            settings = _require_project(context)
            if self.step_id:
                _require_restore_before_rerun(context.scene, self.step_id)
                settings.current_step = clamp_step(STEP_INDEX.get(self.step_id, settings.current_step) + 1)
                path = project.create_accepted_checkpoint(
                    context.scene,
                    self.step_id,
                    "人工步骤已记录",
                    label=self.label,
                )
            else:
                path = project.create_checkpoint(context.scene, self.label)
            project.save_workfile(context.scene)
            settings.status_message = f"已记录检查点：{path.name}"
            self.report({"INFO"}, settings.status_message)
            return {"FINISHED"}
        except Exception as exc:
            context.scene.mocap_doctor.current_step = old_step
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_RestoreLastCheckpoint(Operator):
    bl_idname = "mocap_doctor.restore_last_checkpoint"
    bl_label = "恢复最近检查点"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            project.restore_checkpoint(settings.last_checkpoint, settings.work_filepath)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_SourceBake(Operator):
    bl_idname = "mocap_doctor.source_bake"
    bl_label = "运行源骨架 Bake 预览"
    bl_description = "按固定安全参数将 FreeMoCap 约束烘到源骨架"

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            _ensure_no_pending_preview(settings, "source_bake")
            armature = _require_object(
                settings, "source_armature", "ARMATURE", OBJECT_NAMES["source_armature"]
            )
            required_bones = set(SOURCE_BONES.values()) | {
                "shoulder.L",
                "upper_arm.L",
                "forearm.L",
                "shoulder.R",
                "upper_arm.R",
                "forearm.R",
            }
            missing = sorted(name for name in required_bones if name not in armature.pose.bones)
            if missing:
                raise RuntimeError("FreeMoCap 源骨架结构不匹配：" + ", ".join(missing))
            constraint_count = sum(len(bone.constraints) for bone in armature.pose.bones)
            if constraint_count == 0:
                raise RuntimeError("源骨架没有可 Bake 的 Pose 约束；若已 Bake 请进入下一步")
            source_driver_empties = _source_constraint_empty_targets(armature)
            before = _begin_structure_preview(context.scene, "source_bake")
            settings.busy = True
            settings.status_message = "正在 Bake；Blender 可能暂时无响应"
            with _active_armature(context, armature, pose=True):
                result = bpy.ops.nla.bake(
                    frame_start=settings.mocap_frame_start,
                    frame_end=settings.mocap_frame_end,
                    step=1,
                    only_selected=False,
                    visual_keying=True,
                    clear_constraints=True,
                    clear_parents=False,
                    use_current_action=True,
                    clean_curves=False,
                    bake_types={"POSE"},
                )
            if "FINISHED" not in result:
                raise RuntimeError("Blender Bake 没有成功完成")
            if not armature.animation_data or not armature.animation_data.action:
                raise RuntimeError("Bake 后源骨架仍没有 Action")
            baked_action = armature.animation_data.action
            missing_curves = [
                name
                for name in (SOURCE_BONES["pelvis"], SOURCE_BONES["left_hand"], SOURCE_BONES["right_hand"])
                if not _bone_has_range_keys(
                    baked_action,
                    name,
                    settings.mocap_frame_start,
                    settings.mocap_frame_end,
                )
            ]
            if missing_curves:
                raise RuntimeError("源 Bake 输出缺少覆盖起止帧的骨骼曲线：" + ", ".join(missing_curves))
            remaining_constraints = [
                f"{bone.name}:{constraint.name}"
                for bone in armature.pose.bones
                for constraint in bone.constraints
            ]
            if remaining_constraints:
                preview = "、".join(remaining_constraints[:8])
                raise RuntimeError("源 Bake 后仍有 Pose 约束，已拒绝清理牵引物体：" + preview)

            cleanup = _remove_source_constraint_empties(armature, source_driver_empties)
            removed_count = len(cleanup["removed"])
            skipped_count = len(cleanup["skipped"])
            message = f"Bake 完成并删除 {removed_count} 个牵引 Empty"
            if skipped_count:
                message += f"；{skipped_count} 个因安全检查保留"
            project.record_step(context.scene, "source_bake", "PREVIEW", message + "；请播放检查", str(before))
            settings.status_message = message + "，等待检查"
            return {"FINISHED"}
        except Exception as exc:
            settings.status_message = str(exc)
            if settings.preview_step_id == "source_bake":
                project.record_step(context.scene, "source_bake", "FAILED", str(exc))
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        finally:
            settings.busy = False


class MD_OT_EnterAnnotationMode(Operator):
    bl_idname = "mocap_doctor.enter_annotation_mode"
    bl_label = "编辑区间"

    channel_group: StringProperty(default="HAND")

    def execute(self, context):
        try:
            _require_project(context)
            if self.channel_group == "FOOT":
                _require_restore_before_rerun(context.scene, "contacts")
                record = project.find_step_record(
                    context.scene.mocap_doctor, "contacts", create=False
                )
                if (
                    record is None
                    or not record.artifact_path
                    or not Path(record.artifact_path).is_file()
                ):
                    raise RuntimeError("请先运行 planted 自动检测，再打开区间标注")
            else:
                _require_restore_before_rerun(context.scene, "hand_ranges")
            was_open = bool(context.scene.mcd_annotation_mode)
            _area, converted, step_id = _activate_annotation_editor(
                context.scene,
                context.screen,
                self.channel_group,
            )
            action = "已切换到" if was_open else "已打开"
            label = "planted" if step_id == "contacts" else "手部"
            suffix = "（原 Timeline 已临时切换）" if converted else ""
            self.report({"INFO"}, f"{action}{label}标注{suffix}")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_ExitAnnotationMode(Operator):
    bl_idname = "mocap_doctor.exit_annotation_mode"
    bl_label = "保存标注并返回时间轴"

    def execute(self, context):
        scene = context.scene
        old_current_step = scene.mocap_doctor.current_step
        try:
            settings = scene.mocap_doctor
            step_id = settings.annotation_step_id
            annotation.commit_track_reassignments(scene, rebuild=False)
            if step_id == "contacts":
                _write_effective_contact_report(scene)
            elif step_id == "hand_ranges":
                _write_hand_annotation_report(scene)
            # Discard any native strip transform attempted after manually
            # unlocking a projection track; Scene ranges remain authoritative.
            annotation.rebuild_projection(scene)
            annotation.exit_annotation_mode(scene)
            planted_indicators.cleanup(scene)
            _restore_all_annotation_areas()
            settings.annotation_step_id = ""
            if step_id == "contacts":
                settings.current_step = STEP_INDEX["retarget"]
                project.create_accepted_checkpoint(scene, "contacts", "最终 planted 区间已提交")
            elif step_id == "hand_ranges":
                settings.current_step = STEP_INDEX["hand_repair"]
                project.create_accepted_checkpoint(scene, "hand_ranges", "手部坏区间已提交")
            settings.status_message = "区间标注已提交"
            project.save_workfile(scene)
            self.report({"INFO"}, settings.status_message)
            return {"FINISHED"}
        except Exception as exc:
            scene.mocap_doctor.current_step = old_current_step
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_ResetEffectiveContacts(Operator):
    bl_idname = "mocap_doctor.reset_effective_contacts"
    bl_label = "最终区间重置为自动结果"
    bl_description = "明确丢弃左右脚的人工 planted 修订，重新复制锁定的自动检测区间"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        try:
            _require_project(context)
            _require_restore_before_rerun(context.scene, "contacts")
            annotation.reset_planted_effective_to_auto(context.scene, "L", rebuild=False)
            annotation.reset_planted_effective_to_auto(context.scene, "R", rebuild=True)
            project.save_workfile(context.scene)
            self.report({"INFO"}, "最终 planted 已重置为本次自动结果")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_MMDBake(Operator):
    bl_idname = "mocap_doctor.mmd_bake"
    bl_label = "检测并运行 MMD Visual Bake"

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            if settings.mmd_bake_mode == "MANUAL":
                raise RuntimeError("当前策略为手动 Bake；完成后请点“检查手工 Bake 并清理 FK”")
            _ensure_no_pending_preview(settings, "mmd_bake")
            armature, rig, foot_ik, constrained = _validate_mmd_constraint_mapping(settings)
            rig_animation = rig.animation_data
            rig_action = _require_action(rig, "MMR Rig")
            if rig_animation and len(rig_animation.nla_tracks) > 0:
                raise RuntimeError("MMR Rig 存在 NLA Track；自动 Bake 只接受单一活动 Action")
            if not _action_has_range_keys(
                rig_action, settings.mocap_frame_start, settings.mocap_frame_end
            ):
                raise RuntimeError("MMR Rig Action 没有覆盖完整动捕范围")
            animation_data = armature.animation_data
            if animation_data and (
                animation_data.action is not None or len(animation_data.nla_tracks) > 0
            ):
                raise RuntimeError("原生 MMD 骨架已有 Action/NLA；为避免混写，请改用手动 Bake 回退")
            before = _begin_structure_preview(context.scene, "mmd_bake")
            settings.busy = True
            settings.status_message = "正在生成 MMD Visual Bake 预览"
            with _active_armature(context, armature, pose=True):
                bpy.ops.pose.select_all(action="DESELECT")
                selected_names = {bone.name for bone in constrained}
                selected_names.update((MMD_ROOT_BONE, foot_ik["L"], foot_ik["R"]))
                for bone_name in selected_names:
                    armature.pose.bones[bone_name].bone.select = True
                result = bpy.ops.nla.bake(
                    frame_start=settings.mocap_frame_start,
                    frame_end=settings.mocap_frame_end,
                    step=1,
                    only_selected=True,
                    visual_keying=True,
                    clear_constraints=False,
                    clear_parents=False,
                    use_current_action=False,
                    clean_curves=False,
                    bake_types={"POSE"},
                )
            if "FINISHED" not in result:
                raise RuntimeError("MMD Visual Bake 没有成功完成")
            action = armature.animation_data.action if armature.animation_data else None
            if not action:
                raise RuntimeError("MMD Bake 后没有生成 Action")
            _validate_mmd_action(
                action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                expected_bones=set(selected_names) | set(MMD_ARM_FK_BONES),
            )
            removed = remove_bone_fcurves(action, MMD_LEG_FK_BONES)
            _validate_mmd_action(
                action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                expected_bones=(set(selected_names) - set(MMD_LEG_FK_BONES)) | set(MMD_ARM_FK_BONES),
                require_clean_fk=True,
            )
            muted_count = _mute_mmr_constraints(armature, rig)
            if muted_count == 0:
                raise RuntimeError("Bake 后没有可禁用的 MMR 约束")
            project.record_step(
                context.scene,
                "mmd_bake",
                "PREVIEW",
                f"Bake 完成、禁用 {muted_count} 个 MMR 约束并删除 {len(removed)} 条腿 FK 曲线",
                str(before),
            )
            settings.status_message = f"MMD Bake 预览完成，已删 {len(removed)} 条腿 FK 曲线"
            return {"FINISHED"}
        except Exception as exc:
            settings.status_message = str(exc)
            if settings.preview_step_id == "mmd_bake":
                project.record_step(context.scene, "mmd_bake", "FAILED", str(exc))
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        finally:
            settings.busy = False


class MD_OT_ValidateManualMMDBake(Operator):
    bl_idname = "mocap_doctor.validate_manual_mmd_bake"
    bl_label = "检查手工 Bake 并清理 FK"
    bl_description = "验证全ての親和左右足 IK 曲线，并自动删除六根腿 FK 曲线"

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            _root, armature, rig, foot_ik = _validate_mmd_identity(settings)
            source_action = _require_action(armature, "原生 MMD Armature")
            _require_no_nla(armature, "原生 MMD Armature")
            driven_bones = _mmr_driven_bone_names(armature, rig)
            if not driven_bones:
                # MMR's own manual Bake command may remove its constraints
                # after writing the MMD Action.  In that case the Action is
                # the authoritative evidence of which MMD bones were baked.
                driven_bones = _action_bone_names(source_action, armature)
                required_only = {
                    MMD_ROOT_BONE,
                    MMD_CENTER_BONE,
                    foot_ik["L"],
                    foot_ik["R"],
                }
                if not (set(driven_bones) - set(MMD_LEG_FK_BONES) - required_only):
                    raise RuntimeError("固定 Teto 骨架上没有 MMR 驱动骨，也没有可验证的 MMD Bake 骨骼曲线")
            _validate_mmd_action(
                source_action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                expected_bones=(set(driven_bones) - set(MMD_LEG_FK_BONES)) | set(MMD_ARM_FK_BONES),
            )
            _ensure_no_pending_preview(settings, "mmd_bake")
            _begin_structure_preview(context.scene, "mmd_bake")
            action = source_action
            removed = remove_bone_fcurves(action, MMD_LEG_FK_BONES)
            muted_count = _mute_mmr_constraints(armature, rig)
            _validate_mmd_action(
                action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                expected_bones=(set(driven_bones) - set(MMD_LEG_FK_BONES)) | set(MMD_ARM_FK_BONES),
                require_clean_fk=True,
            )
            report = {
                "operation": "validate_manual_mmd_bake",
                "action": action.name,
                "validated_bones": [MMD_ROOT_BONE, foot_ik["L"], foot_ik["R"], *MMD_ARM_FK_BONES],
                "removed_leg_fk_fcurves": len(removed),
                "muted_mmr_constraints": muted_count,
                "constraint_mapping_present": bool(_mmr_driven_bone_names(armature, rig)),
            }
            _record_report(
                context.scene,
                "mmd_bake",
                report,
                "PREVIEW",
                "手工 Bake 已验证并清理腿 FK，MMR→MMD 约束已禁用；请隐藏 MMR Rig 检查",
            )
            settings.status_message = "手工 MMD Bake 验证通过；MMR→MMD 约束已禁用，等待检查"
            return {"FINISHED"}
        except Exception as exc:
            if settings.preview_step_id == "mmd_bake":
                project.record_step(context.scene, "mmd_bake", "FAILED", str(exc))
            settings.status_message = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_CleanupLegFK(Operator):
    bl_idname = "mocap_doctor.cleanup_leg_fk"
    bl_label = "一键删除六个腿 FK 曲线"

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            _root, armature, rig, foot_ik = _validate_mmd_identity(settings)
            source_action = _require_action(armature, "原生 MMD Armature")
            _require_no_nla(armature, "原生 MMD Armature")
            driven_bones = _mmr_driven_bone_names(armature, rig)
            _validate_mmd_action(
                source_action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                expected_bones=set(driven_bones) - set(MMD_LEG_FK_BONES),
            )
            _ensure_no_pending_preview(settings, "mmd_bake")
            _begin_structure_preview(context.scene, "mmd_bake")
            action = source_action
            removed = remove_bone_fcurves(action, MMD_LEG_FK_BONES)
            _mute_mmr_constraints(armature, rig)
            _validate_mmd_action(
                action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                expected_bones=set(driven_bones) - set(MMD_LEG_FK_BONES),
                require_clean_fk=True,
            )
            settings.status_message = f"预览中：删除了 {len(removed)} 条腿 FK 曲线"
            self.report({"INFO"}, settings.status_message)
            return {"FINISHED"}
        except Exception as exc:
            if settings.preview_step_id == "mmd_bake":
                project.record_step(context.scene, "mmd_bake", "FAILED", str(exc))
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_AcceptPreview(Operator):
    bl_idname = "mocap_doctor.accept_preview"
    bl_label = "接受并进入下一步"

    def execute(self, context):
        settings = _settings(context)
        step_id = settings.preview_step_id
        if not step_id:
            self.report({"ERROR"}, "当前没有等待接受的预览")
            return {"CANCELLED"}
        try:
            old_step = settings.current_step
            record = project.find_step_record(settings, step_id, create=False)
            if record is not None and record.status == "FAILED":
                raise RuntimeError("此预览执行失败，只能丢弃并恢复检查点")
            if step_id == "mmd_bake":
                _root, armature, rig, _foot_ik = _validate_mmd_identity(settings)
                if _active_mmr_constraints(armature, rig):
                    raise RuntimeError("MMR→MMD 约束仍在生效，不能接受 Bake；请重新检查手工 Bake")
            next_step = clamp_step(STEP_INDEX.get(step_id, old_step) + 1)
            settings.current_step = next_step
            settings.status_message = "步骤已接受"
            if settings.preview_action:
                project.accept_action_preview(context.scene)
            else:
                preview_fields = {
                    name: getattr(settings, name)
                    for name in (
                        "preview_step_id",
                        "preview_owner_name",
                        "preview_base_action",
                        "preview_action",
                        "preview_restore_checkpoint",
                    )
                }
                settings.preview_step_id = ""
                settings.preview_restore_checkpoint = ""
                settings.preview_owner_name = ""
                settings.preview_base_action = ""
                settings.preview_action = ""
                try:
                    project.create_accepted_checkpoint(context.scene, step_id, "预览已接受")
                except Exception:
                    for name, value in preview_fields.items():
                        setattr(settings, name, value)
                    raise
                project.save_workfile(context.scene)
            return {"FINISHED"}
        except Exception as exc:
            settings.current_step = old_step
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_DiscardPreview(Operator):
    bl_idname = "mocap_doctor.discard_preview"
    bl_label = "丢弃预览"

    def execute(self, context):
        settings = _settings(context)
        step_id = settings.preview_step_id
        if not step_id:
            self.report({"ERROR"}, "当前没有预览")
            return {"CANCELLED"}
        checkpoint = settings.preview_restore_checkpoint
        if settings.preview_action:
            restored = project.rollback_action_preview(context.scene)
            if restored:
                project.record_step(context.scene, step_id, "PENDING", "预览已丢弃")
                settings.status_message = "已恢复预览前 Action"
                project.save_workfile(context.scene)
                return {"FINISHED"}
            if checkpoint:
                try:
                    project.restore_checkpoint(checkpoint, settings.work_filepath)
                    return {"FINISHED"}
                except Exception as exc:
                    self.report({"ERROR"}, str(exc))
                    return {"CANCELLED"}
        if not checkpoint:
            self.report({"ERROR"}, "找不到结构步骤的恢复检查点")
            return {"CANCELLED"}
        try:
            project.restore_checkpoint(checkpoint, settings.work_filepath)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


class MD_OT_ExportVMD(Operator):
    bl_idname = "mocap_doctor.export_vmd"
    bl_label = "导出 VMD"

    def execute(self, context):
        settings = _settings(context)
        try:
            _require_project(context)
            record = project.find_step_record(settings, "export_prep", create=False)
            if record is None or record.status != "ACCEPTED":
                raise RuntimeError("请先接受 VMD 导出准备预览")
            root, armature, rig, foot_ik = _validate_mmd_identity(settings)
            if _active_mmr_constraints(armature, rig):
                raise RuntimeError("仍有活动的 MMR 到 MMD 约束，不能导出")
            action = _require_action(armature, "原生 MMD Armature")
            _require_no_nla(armature, "原生 MMD Armature")
            _validate_mmd_action(
                action,
                foot_ik,
                settings.mocap_frame_start,
                settings.mocap_frame_end,
                require_clean_fk=True,
            )
            _require_no_keyed_vmd_name_collisions(armature, action)
            raw_path = str(settings.vmd_export_path or "").strip()
            if not raw_path:
                raise RuntimeError("请先指定 VMD 文件保存位置")
            filepath = Path(bpy.path.abspath(raw_path))
            if filepath.suffix.lower() != ".vmd":
                filepath = filepath.with_suffix(".vmd")
            if not filepath.parent.is_dir():
                raise RuntimeError(f"VMD 保存目录不存在：{filepath.parent}")
            previous_file = None
            if filepath.is_file():
                stat = filepath.stat()
                previous_file = (stat.st_mtime_ns, stat.st_size)

            # mmd_tools reads context.active_object inside execute().  Its file
            # browser can lose that object and then dereference None. Execute
            # directly with the validated MMD Root active instead.
            with _active_armature(context, root, pose=False):
                if not bpy.ops.mmd_tools.export_vmd.poll():
                    raise RuntimeError("mmd_tools 未启用，或 Teto 根对象不能导出 VMD")
                result = bpy.ops.mmd_tools.export_vmd(
                    "EXEC_DEFAULT",
                    filepath=str(filepath),
                    use_frame_range=True,
                )
            current_file = None
            if filepath.is_file():
                stat = filepath.stat()
                current_file = (stat.st_mtime_ns, stat.st_size)
            if "FINISHED" not in result or current_file is None or current_file == previous_file:
                raise RuntimeError("mmd_tools 未生成 VMD 文件；请查看系统控制台中的导出错误")
            settings.vmd_export_path = str(filepath)
            settings.status_message = f"VMD 已导出：{filepath}"
            project.save_workfile(context.scene)
            self.report({"INFO"}, settings.status_message)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


CLASSES = (
    MD_OT_PrepareVMDExport,
    MD_OT_RunStep,
    MD_OT_CreateProject,
    MD_OT_DiscoverObjects,
    MD_OT_EnsureFPS,
    MD_OT_SetRangeBoundary,
    MD_OT_SyncRangeFromScene,
    MD_OT_NavigateStep,
    MD_OT_RestoreBeforeStep,
    MD_OT_ReviseHandRanges,
    MD_OT_CreateCheckpoint,
    MD_OT_RestoreLastCheckpoint,
    MD_OT_SourceBake,
    MD_OT_EnterAnnotationMode,
    MD_OT_ExitAnnotationMode,
    MD_OT_ResetEffectiveContacts,
    MD_OT_MMDBake,
    MD_OT_ValidateManualMMDBake,
    MD_OT_CleanupLegFK,
    MD_OT_AcceptPreview,
    MD_OT_DiscardPreview,
    MD_OT_ExportVMD,
)


def register_operators():
    registered = []
    try:
        for cls in CLASSES:
            bpy.utils.register_class(cls)
            registered.append(cls)
        if _cleanup_annotation_before_load not in bpy.app.handlers.load_pre:
            bpy.app.handlers.load_pre.append(_cleanup_annotation_before_load)
        if _resume_annotation_after_load not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(_resume_annotation_after_load)
    except Exception:
        if _cleanup_annotation_before_load in bpy.app.handlers.load_pre:
            bpy.app.handlers.load_pre.remove(_cleanup_annotation_before_load)
        if _resume_annotation_after_load in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(_resume_annotation_after_load)
        for cls in reversed(registered):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass
        raise


def unregister_operators():
    _cancel_pending_annotation_open()
    if _cleanup_annotation_before_load in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(_cleanup_annotation_before_load)
    if _resume_annotation_after_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_resume_annotation_after_load)
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
