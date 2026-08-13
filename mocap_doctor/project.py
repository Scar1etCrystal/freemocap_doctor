import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

from .presets import EXPECTED_FPS, OBJECT_NAMES, fixed_object_name_matches
from .workflow import STEP_INDEX


_ACTION_PREVIEWS = {}
_RESTORE_WORK_PATH = None
_RESTORE_RESUME_STEP_ID = ""
_RESTORE_RESET_STEP_ID = ""
_RESTORE_MESSAGE = ""

# Bump when saved projects need their workflow state adjusted on load; add a
# migration branch in _migrate_project_schema for each previous version.
SCHEMA_VERSION = 1


@persistent
def _migrate_project_schema(_dummy):
    try:
        scene = bpy.context.scene
        if not hasattr(scene, "mocap_doctor"):
            return
        settings = scene.mocap_doctor
        if not settings.initialized or settings.schema_version >= SCHEMA_VERSION:
            return
        # 0 -> 1: the "fingers" step was inserted between mmd_bake and
        # export_prep, so files saved past that point need current_step + 1.
        fingers_index = STEP_INDEX.get("fingers", 14)
        if settings.schema_version < 1 and settings.current_step >= fingers_index:
            settings.current_step += 1
        settings.schema_version = SCHEMA_VERSION
    except Exception as exc:
        print(f"[MoCap Doctor] schema migration failed: {exc}")


def register_handlers():
    if _migrate_project_schema not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_migrate_project_schema)


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _safe_name(value):
    return re.sub(r"[^\w\-.]+", "_", value, flags=re.UNICODE).strip("._") or "mocap_project"


def ensure_fps(scene):
    changed = scene.render.fps != EXPECTED_FPS or scene.render.fps_base != 1.0
    scene.render.fps = EXPECTED_FPS
    scene.render.fps_base = 1.0
    return changed


def sync_scene_range(scene, settings):
    settings.mocap_frame_start = int(scene.frame_start)
    settings.mocap_frame_end = int(scene.frame_end)


def apply_project_range(scene, settings):
    scene.frame_start = int(settings.mocap_frame_start)
    scene.frame_end = int(settings.mocap_frame_end)


def project_data_dir(work_filepath):
    work = Path(work_filepath)
    return work.parent / ".mocap_doctor" / _safe_name(work.stem)


def ensure_project_directories(settings):
    root = Path(settings.data_directory)
    for name in ("checkpoints", "reports", "recovery", "logs", "tmp"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def atomic_write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def write_report(scene, step_id, data):
    """Write an immutable, sequential JSON artifact inside the project."""

    settings = scene.mocap_doctor
    root = ensure_project_directories(settings) / "reports"
    safe_step = _safe_name(step_id)
    sequence = 0
    while True:
        path = root / f"{sequence:04d}_{safe_step}.json"
        if not path.exists():
            break
        sequence += 1
    atomic_write_json(path, data)
    return path


def save_manifest(scene):
    settings = scene.mocap_doctor
    if not settings.initialized or not settings.data_directory:
        return
    atomic_write_json(
        Path(settings.data_directory) / "project.json",
        {
            "schema_version": "mocap_doctor_project_v1",
            "state_authority": "blend_scene",
            "updated_at": _utc_now(),
            "project_uuid": settings.project_uuid,
            "project_name": settings.project_name,
            "original_filepath": settings.original_filepath,
            "work_filepath": settings.work_filepath,
            "expected_fps": EXPECTED_FPS,
            "frame_start": settings.mocap_frame_start,
            "frame_end": settings.mocap_frame_end,
            "current_step": settings.current_step,
            "objects": {
                name: getattr(getattr(settings, name), "name", None)
                for name in ("source_armature", "model_root", "mmr_rig", "mmd_armature", "target_mesh", "correction_empty")
            },
            "annotations": [
                {
                    "uid": item.uid,
                    "channel": item.channel,
                    "frame_start": int(item.frame_start),
                    "frame_end": int(item.frame_end),
                    "source": item.source,
                }
                for item in getattr(scene, "mcd_annotation_ranges", ())
            ],
            "annotation_channels": {
                "FOOT_L_EFFECTIVE": {
                    "initialized": bool(scene.get("mcd_foot_l_effective_initialized", False))
                },
                "FOOT_R_EFFECTIVE": {
                    "initialized": bool(scene.get("mcd_foot_r_effective_initialized", False))
                },
            },
            "steps": [
                {
                    "step_id": item.step_id,
                    "status": item.status,
                    "checkpoint": item.checkpoint,
                    "artifact_path": item.artifact_path,
                    "parameter_hash": item.parameter_hash,
                    "message": item.message,
                }
                for item in settings.steps
            ],
        },
    )


def find_step_record(settings, step_id, create=True):
    for item in settings.steps:
        if item.step_id == step_id:
            return item
    if not create:
        return None
    item = settings.steps.add()
    item.step_id = step_id
    return item


def record_step(scene, step_id, status, message="", checkpoint="", artifact_path="", parameter_hash=""):
    settings = scene.mocap_doctor
    item = find_step_record(settings, step_id)
    item.status = status
    item.message = message
    if checkpoint:
        item.checkpoint = checkpoint
        settings.last_checkpoint = checkpoint
    if artifact_path:
        item.artifact_path = artifact_path
    if parameter_hash:
        item.parameter_hash = parameter_hash
    save_manifest(scene)
    return item


def mark_downstream_stale(scene, step_id):
    settings = scene.mocap_doctor
    index = STEP_INDEX.get(step_id, -1)
    for item in settings.steps:
        if STEP_INDEX.get(item.step_id, -1) > index and item.status in {"ACCEPTED", "PREVIEW"}:
            item.status = "STALE"
    save_manifest(scene)


def parameter_hash(data):
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def discover_known_objects(scene):
    settings = scene.mocap_doctor
    for attr, name in OBJECT_NAMES.items():
        if hasattr(settings, attr):
            obj = bpy.data.objects.get(name)
            if obj is None:
                candidates = [
                    item
                    for item in bpy.data.objects
                    if fixed_object_name_matches(item.name, name)
                ]
                # Auto-discovery is conservative when multiple imported Teto
                # copies exist; the user can choose the intended one manually.
                obj = candidates[0] if len(candidates) == 1 else None
            if obj is not None:
                setattr(settings, attr, obj)
    return {
        attr: getattr(settings, attr)
        for attr in ("source_armature", "model_root", "mmr_rig", "mmd_armature", "target_mesh", "correction_empty")
    }


def checkpoint_path(settings, label):
    root = ensure_project_directories(settings)
    sequences = []
    for item in (root / "checkpoints").glob("*.blend"):
        match = re.match(r"^(\d+)_", item.name)
        if match:
            sequences.append(int(match.group(1)))
    sequence = max(sequences, default=-1) + 1
    return root / "checkpoints" / f"{sequence:04d}_{_safe_name(label)}.blend"


def create_checkpoint(scene, label):
    settings = scene.mocap_doctor
    if not settings.initialized:
        raise RuntimeError("Project is not initialized")
    path = checkpoint_path(settings, label)
    result = bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True, relative_remap=True)
    if "FINISHED" not in result:
        raise RuntimeError(f"Unable to create checkpoint: {path}")
    settings.last_checkpoint = str(path)
    return path


def create_accepted_checkpoint(scene, step_id, message="预览已接受", label=None):
    """Persist a checkpoint that already contains its accepted StepRecord."""

    settings = scene.mocap_doctor
    path = checkpoint_path(settings, label or step_id)
    previous_steps = [
        {
            "step_id": item.step_id,
            "status": item.status,
            "checkpoint": item.checkpoint,
            "artifact_path": item.artifact_path,
            "parameter_hash": item.parameter_hash,
            "message": item.message,
        }
        for item in settings.steps
    ]
    previous_last = settings.last_checkpoint
    try:
        record_step(scene, step_id, "ACCEPTED", message, str(path))
        mark_downstream_stale(scene, step_id)
        result = bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True, relative_remap=True)
        if "FINISHED" not in result:
            raise RuntimeError(f"Unable to create checkpoint: {path}")
    except Exception:
        settings.steps.clear()
        for values in previous_steps:
            item = settings.steps.add()
            for name, value in values.items():
                setattr(item, name, value)
        settings.last_checkpoint = previous_last
        save_manifest(scene)
        raise
    settings.last_checkpoint = str(path)
    return path


def save_workfile(scene):
    settings = scene.mocap_doctor
    result = bpy.ops.wm.save_as_mainfile(filepath=settings.work_filepath, relative_remap=True)
    if "FINISHED" not in result:
        raise RuntimeError("Unable to save working file")
    save_manifest(scene)


def initialize_project(scene, work_filepath, target_template_path=""):
    settings = scene.mocap_doctor
    original = bpy.data.filepath
    work = str(Path(work_filepath).resolve())
    if original and Path(original).resolve() == Path(work).resolve():
        raise RuntimeError("Working copy must not overwrite the original file")
    result = bpy.ops.wm.save_as_mainfile(filepath=work, relative_remap=True)
    if "FINISHED" not in result:
        raise RuntimeError("Unable to create working file")
    settings.initialized = True
    settings.project_uuid = uuid.uuid4().hex
    settings.project_name = Path(work).stem
    settings.original_filepath = original
    settings.work_filepath = work
    settings.data_directory = str(project_data_dir(work))
    settings.target_template_path = target_template_path
    settings.current_step = 1
    settings.schema_version = SCHEMA_VERSION
    sync_scene_range(scene, settings)
    ensure_fps(scene)
    if settings.tilt_reference_frame == 0:
        settings.tilt_reference_frame = settings.mocap_frame_start
    ensure_project_directories(settings)
    discover_known_objects(scene)
    baseline = create_accepted_checkpoint(
        scene,
        "project",
        "工作副本和基线已创建",
        label="baseline",
    )
    settings.status_message = "项目已创建"
    save_workfile(scene)
    return baseline


def begin_action_preview(scene, owner, step_id):
    if owner is None:
        raise RuntimeError("Animation owner is missing")
    settings = scene.mocap_doctor
    if settings.preview_step_id:
        if not settings.preview_action:
            raise RuntimeError("A structural preview is waiting for review")
        if not rollback_action_preview(scene):
            raise RuntimeError("Unable to restore the existing Action preview")
    recovery = create_checkpoint(scene, f"{step_id}_before")
    if not owner.animation_data:
        owner.animation_data_create()
    base = owner.animation_data.action
    preview = base.copy() if base else bpy.data.actions.new(f"MD_PREVIEW_{step_id}_{owner.name}")
    if base:
        preview.name = f"MD_PREVIEW_{step_id}_{base.name}"
    owner.animation_data.action = preview
    _ACTION_PREVIEWS[scene.as_pointer()] = {"owner": owner, "base": base, "preview": preview, "step_id": step_id}
    settings.preview_step_id = step_id
    settings.preview_owner_name = owner.name
    settings.preview_base_action = base.name if base else ""
    settings.preview_action = preview.name
    settings.preview_restore_checkpoint = str(recovery)
    record_step(scene, step_id, "PREVIEW", "等待人工检查")
    return preview


def recover_action_preview(scene):
    """Rebuild an Action preview transaction after a saved-file reload."""

    settings = scene.mocap_doctor
    if not settings.preview_action or not settings.preview_owner_name:
        return False
    owner = bpy.data.objects.get(settings.preview_owner_name)
    preview = bpy.data.actions.get(settings.preview_action)
    base = bpy.data.actions.get(settings.preview_base_action) if settings.preview_base_action else None
    if settings.preview_base_action and base is None:
        return False
    if owner is None or preview is None or not owner.animation_data:
        return False
    if owner.animation_data.action != preview:
        return False
    _ACTION_PREVIEWS[scene.as_pointer()] = {
        "owner": owner,
        "base": base,
        "preview": preview,
        "step_id": settings.preview_step_id,
    }
    return True


def rollback_action_preview(scene):
    settings = scene.mocap_doctor
    data = _ACTION_PREVIEWS.get(scene.as_pointer())
    if data is None and settings.preview_action:
        recover_action_preview(scene)
    data = _ACTION_PREVIEWS.pop(scene.as_pointer(), None)
    if data is None and settings.preview_action:
        return False
    if data:
        owner, preview = data["owner"], data["preview"]
        if owner and owner.animation_data:
            owner.animation_data.action = data["base"]
        if preview and preview.users == 0:
            bpy.data.actions.remove(preview)
    settings.preview_step_id = ""
    settings.preview_owner_name = ""
    settings.preview_base_action = ""
    settings.preview_action = ""
    settings.preview_restore_checkpoint = ""
    return data is not None


def accept_action_preview(scene, message="预览已接受"):
    data = _ACTION_PREVIEWS.get(scene.as_pointer())
    if not data and recover_action_preview(scene):
        data = _ACTION_PREVIEWS.get(scene.as_pointer())
    if not data:
        raise RuntimeError("There is no active Action preview")
    settings = scene.mocap_doctor
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
    old_name = data["preview"].name
    data["preview"].name = f"MD_{data['step_id']}_{old_name}"
    settings.preview_step_id = ""
    settings.preview_owner_name = ""
    settings.preview_base_action = ""
    settings.preview_action = ""
    settings.preview_restore_checkpoint = ""
    try:
        checkpoint = create_accepted_checkpoint(scene, data["step_id"], message)
    except Exception:
        data["preview"].name = old_name
        for name, value in preview_fields.items():
            setattr(settings, name, value)
        raise
    _ACTION_PREVIEWS.pop(scene.as_pointer(), None)
    save_workfile(scene)
    return checkpoint


def apply_restored_step_state(
    scene,
    *,
    resume_step_id="",
    reset_step_id="",
    message="",
):
    settings = scene.mocap_doctor
    if resume_step_id in STEP_INDEX:
        settings.current_step = STEP_INDEX[resume_step_id]
    if reset_step_id:
        reset_index = STEP_INDEX.get(reset_step_id, -1)
        reset_record = find_step_record(settings, reset_step_id, create=False)
        if reset_record is not None:
            reset_record.status = "PENDING"
            reset_record.message = "等待重新执行"
        for record in settings.steps:
            if (
                STEP_INDEX.get(record.step_id, -1) > reset_index
                and record.status in {"ACCEPTED", "PREVIEW"}
            ):
                record.status = "STALE"
    settings.status_message = message or "已恢复检查点"


@persistent
def _finish_restore(_dummy):
    global _RESTORE_WORK_PATH, _RESTORE_RESUME_STEP_ID, _RESTORE_RESET_STEP_ID, _RESTORE_MESSAGE
    if not _RESTORE_WORK_PATH:
        return
    target = _RESTORE_WORK_PATH
    if _finish_restore in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_finish_restore)
    attempts = {"count": 0}

    def save_back():
        global _RESTORE_WORK_PATH, _RESTORE_RESUME_STEP_ID, _RESTORE_RESET_STEP_ID, _RESTORE_MESSAGE
        attempts["count"] += 1
        try:
            scene = bpy.context.scene
            if hasattr(scene, "mocap_doctor"):
                settings = scene.mocap_doctor
                settings.work_filepath = target
                apply_restored_step_state(
                    scene,
                    resume_step_id=_RESTORE_RESUME_STEP_ID,
                    reset_step_id=_RESTORE_RESET_STEP_ID,
                    message=_RESTORE_MESSAGE,
                )
            result = bpy.ops.wm.save_as_mainfile(filepath=target, relative_remap=True)
            if "FINISHED" not in result:
                raise RuntimeError("Blender 未能把检查点另存回工作文件")
            if hasattr(scene, "mocap_doctor"):
                save_manifest(scene)
            _RESTORE_WORK_PATH = None
            _RESTORE_RESUME_STEP_ID = ""
            _RESTORE_RESET_STEP_ID = ""
            _RESTORE_MESSAGE = ""
            return None
        except Exception as exc:
            if attempts["count"] < 3:
                return 0.5
            if hasattr(bpy.context.scene, "mocap_doctor"):
                bpy.context.scene.mocap_doctor.status_message = f"恢复检查点后保存失败：{exc}"
            _RESTORE_WORK_PATH = None
            _RESTORE_RESUME_STEP_ID = ""
            _RESTORE_RESET_STEP_ID = ""
            _RESTORE_MESSAGE = ""
            print(f"[MoCap Doctor] restore save failed: {exc}")
            return None

    bpy.app.timers.register(save_back, first_interval=0.1)


def restore_checkpoint(
    checkpoint,
    work_filepath,
    *,
    resume_step_id="",
    reset_step_id="",
    message="",
):
    global _RESTORE_WORK_PATH, _RESTORE_RESUME_STEP_ID, _RESTORE_RESET_STEP_ID, _RESTORE_MESSAGE
    checkpoint = str(Path(checkpoint).resolve())
    if not Path(checkpoint).is_file():
        raise FileNotFoundError(checkpoint)
    settings = bpy.context.scene.mocap_doctor
    recovery_root = ensure_project_directories(settings) / "recovery"
    sequences = []
    for item in recovery_root.glob("*.blend"):
        match = re.match(r"^(\d+)_", item.name)
        if match:
            sequences.append(int(match.group(1)))
    recovery = recovery_root / f"{max(sequences, default=-1) + 1:04d}_before_restore.blend"
    recovery_result = bpy.ops.wm.save_as_mainfile(
        filepath=str(recovery), copy=True, relative_remap=True
    )
    if "FINISHED" not in recovery_result:
        raise RuntimeError("无法创建恢复前安全副本，已取消检查点恢复")
    _RESTORE_WORK_PATH = str(Path(work_filepath).resolve())
    _RESTORE_RESUME_STEP_ID = str(resume_step_id)
    _RESTORE_RESET_STEP_ID = str(reset_step_id)
    _RESTORE_MESSAGE = str(message)
    if _finish_restore not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_finish_restore)
    try:
        result = bpy.ops.wm.open_mainfile(filepath=checkpoint, load_ui=False)
        if "FINISHED" not in result:
            raise RuntimeError("Blender 未能打开检查点")
    except Exception:
        _RESTORE_WORK_PATH = None
        _RESTORE_RESUME_STEP_ID = ""
        _RESTORE_RESET_STEP_ID = ""
        _RESTORE_MESSAGE = ""
        if _finish_restore in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(_finish_restore)
        raise


def unregister_handlers():
    global _RESTORE_WORK_PATH, _RESTORE_RESUME_STEP_ID, _RESTORE_RESET_STEP_ID, _RESTORE_MESSAGE
    if _finish_restore in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_finish_restore)
    if _migrate_project_schema in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_migrate_project_schema)
    _RESTORE_WORK_PATH = None
    _RESTORE_RESUME_STEP_ID = ""
    _RESTORE_RESET_STEP_ID = ""
    _RESTORE_MESSAGE = ""
