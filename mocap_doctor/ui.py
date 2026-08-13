import bpy
from bpy.types import Panel

from . import annotation, project
from .presets import EXPECTED_FPS
from .workflow import STEPS, step_at


def _range_count(scene, channels):
    return sum(len(annotation.get_channel_ranges(scene, channel)) for channel in channels)


def _draw_run(layout, step_id, text="运行预览", icon="PLAY"):
    operator = layout.operator("mocap_doctor.run_step", text=text, icon=icon)
    operator.step_id = step_id


def _draw_message(layout, message, icon="INFO", width=34):
    text = str(message or "")
    if not text:
        return
    for index in range(0, len(text), width):
        layout.label(text=text[index : index + width], icon=icon if index == 0 else "NONE")


class MD_PT_Main(Panel):
    bl_idname = "MD_PT_main"
    bl_label = "MoCap Doctor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MoCap Doctor"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.mocap_doctor

        if not settings.initialized:
            layout.label(text="打开 FreeMoCap 源文件后创建工作副本", icon="FILE_BLEND")
            layout.operator("mocap_doctor.create_project", icon="DUPLICATE")
            receiver_box = layout.box()
            receiver_box.label(text="VMD 接收模板（MMR 模板专用）", icon="TOOL_SETTINGS")
            receiver_box.operator(
                "mocap_doctor.prepare_receiver_template",
                text="准备接收模板（导入 VMD 前先执行一次）",
                icon="GHOST_DISABLED",
            )
            return

        step = step_at(settings.current_step)
        header = layout.column(align=True)
        header.label(text=f"{step.stage}  ·  {settings.current_step + 1}/{len(STEPS)}")
        header.label(text=step.label, icon="ANIM")
        record = project.find_step_record(settings, step.id, create=False)
        if record is not None:
            icons = {
                "PENDING": "TIME",
                "PREVIEW": "HIDE_OFF",
                "ACCEPTED": "CHECKMARK",
                "STALE": "ERROR",
                "FAILED": "CANCEL",
            }
            header.label(text=record.message or record.status, icon=icons.get(record.status, "INFO"))
        if (
            settings.current_step > 0
            and not settings.preview_step_id
            and record is not None
            and record.status in {"ACCEPTED", "STALE", "FAILED"}
        ):
            redo = header.operator(
                "mocap_doctor.restore_before_step",
                text=f"恢复到“{step.label}”执行前",
                icon="LOOP_BACK",
            )
            redo.step_id = step.id

        info = layout.box()
        fps_ok = scene.render.fps == EXPECTED_FPS and scene.render.fps_base == 1.0
        row = info.row(align=True)
        row.label(text=f"{scene.render.fps} fps", icon="CHECKMARK" if fps_ok else "ERROR")
        if not fps_ok:
            row.operator("mocap_doctor.ensure_fps", text="修正为 30")
        row = info.row(align=True)
        row.prop(settings, "mocap_frame_start", text="开始")
        row.prop(settings, "mocap_frame_end", text="结束")
        row = info.row(align=True)
        start = row.operator("mocap_doctor.set_range_boundary", text="当前帧设为开始")
        start.boundary = "START"
        end = row.operator("mocap_doctor.set_range_boundary", text="当前帧设为结束")
        end.boundary = "END"

        body = layout.column(align=True)
        body.enabled = not settings.busy
        self.draw_step(context, body, step.id)

        if settings.preview_step_id:
            preview = layout.box()
            preview_record = project.find_step_record(
                settings, settings.preview_step_id, create=False
            )
            preview_failed = preview_record is not None and preview_record.status == "FAILED"
            if preview_failed:
                preview.alert = True
                preview.label(text="执行失败", icon="ERROR")
                if preview_record.message:
                    _draw_message(preview, preview_record.message)
                preview.operator(
                    "mocap_doctor.discard_preview",
                    text="丢弃失败结果并恢复",
                    icon="LOOP_BACK",
                )
            else:
                preview.label(text="等待人眼检查", icon="HIDE_OFF")
                row = preview.row(align=True)
                row.operator("mocap_doctor.accept_preview", icon="CHECKMARK")
                row.operator("mocap_doctor.discard_preview", icon="LOOP_BACK")

        if settings.status_message:
            status = layout.box()
            _draw_message(status, settings.status_message)

        navigation = layout.row(align=True)
        navigation.enabled = not settings.preview_step_id and not settings.busy
        previous = navigation.operator(
            "mocap_doctor.navigate_step",
            text="上一步",
            icon="TRIA_LEFT",
        )
        previous.delta = -1
        navigation.label(text=f"浏览 {settings.current_step + 1}/{len(STEPS)}")
        following = navigation.operator(
            "mocap_doctor.navigate_step",
            text="下一步",
            icon="TRIA_RIGHT",
        )
        following.delta = 1

    def draw_step(self, context, layout, step_id):
        scene = context.scene
        settings = scene.mocap_doctor

        if step_id == "project":
            layout.label(text="工作副本与基线检查点已建立", icon="CHECKMARK")
            layout.operator("mocap_doctor.discover_objects", icon="VIEWZOOM")

        elif step_id == "source_bake":
            layout.prop(settings, "source_armature", text="源骨架")
            layout.label(text="仅处理上方有效动捕范围")
            layout.operator("mocap_doctor.source_bake", icon="ACTION")

        elif step_id == "source_analyze":
            layout.prop(settings, "source_diagnostic_contact_height", text="脚接近地面高度")
            layout.prop(settings, "source_foot_slide_speed", text="足部每帧位移（m/帧）")
            layout.prop(settings, "source_heel_slide_speed", text="脚跟每帧位移（m/帧）")
            layout.prop(settings, "source_hand_jump", text="手部跳变阈值（m/帧）")
            layout.prop(settings, "source_hips_jump", text="骨盆跳变阈值（m/帧）")
            _draw_run(layout, step_id, "生成源动作诊断", "VIEWZOOM")

        elif step_id == "hand_ranges":
            count = _range_count(
                scene,
                (annotation.CHANNEL_HAND_L_MANUAL, annotation.CHANNEL_HAND_R_MANUAL),
            )
            layout.label(text=f"已标注 {count} 个手部坏区间")
            operator = layout.operator(
                "mocap_doctor.enter_annotation_mode",
                text="标注坏区间",
                icon="NLA",
            )
            operator.channel_group = "HAND"

        elif step_id == "hand_repair":
            _draw_run(layout, step_id, "修复已标注手部区间")
            layout.operator(
                "mocap_doctor.revise_hand_ranges",
                text="返回修改坏区间（保留现有标注）",
                icon="LOOP_BACK",
            )

        elif step_id == "smooth":
            layout.prop(settings, "smooth_strength", text="强度")
            layout.prop(settings, "smooth_radius", text="半径（帧）")
            layout.prop(settings, "smooth_include_hands", text="包含手和前臂")
            _draw_run(layout, step_id)

        elif step_id == "source_floor":
            layout.prop(settings, "source_floor_z", text="地面 Z")
            layout.prop(settings, "source_floor_strength", text="强度")
            layout.prop(settings, "source_floor_tolerance", text="容差")
            layout.prop(settings, "source_floor_clearance", text="离地间隙")
            layout.prop(settings, "source_floor_max_lift", text="单帧最大抬升")
            layout.prop(settings, "source_floor_smooth_radius", text="平滑半径")
            layout.prop(settings, "source_floor_max_delta", text="帧间最大变化（m/帧）")
            _draw_run(layout, step_id)

        elif step_id == "contacts":
            layout.prop(settings, "contact_height", text="接触高度")
            layout.prop(settings, "contact_xy_speed", text="XY 速度阈值（m/帧）")
            layout.prop(settings, "contact_moving_xy_speed", text="移动判定速度（m/帧）")
            layout.prop(settings, "contact_vertical_speed", text="垂直速度阈值（m/帧）")
            layout.prop(settings, "contact_anchor_drift", text="最大锚点漂移")
            layout.prop(settings, "contact_min_segment_len", text="最短区间")
            layout.prop(settings, "contact_merge_gap", text="合并间隔")
            layout.prop(settings, "contact_penetration_tolerance", text="穿地诊断容差")
            _draw_run(layout, step_id, "重新检测 Planted", "VIEWZOOM")
            count = _range_count(
                scene,
                (annotation.CHANNEL_FOOT_L_EFFECTIVE, annotation.CHANNEL_FOOT_R_EFFECTIVE),
            )
            layout.label(text=f"当前有效区间 {count} 个")
            operator = layout.operator(
                "mocap_doctor.enter_annotation_mode",
                text="编辑 planted 区间",
                icon="NLA",
            )
            operator.channel_group = "FOOT"
            layout.operator("mocap_doctor.reset_effective_contacts", icon="FILE_REFRESH")

        elif step_id == "retarget":
            layout.prop(settings, "target_template_path", text="Teto 模板（仅记录路径）")
            layout.label(text="使用 ARP/MMR 完成重定向并保持绝对帧号")
            operator = layout.operator("mocap_doctor.create_checkpoint", text="重定向完成，记录里程碑", icon="BOOKMARKS")
            operator.label = "retarget"
            operator.step_id = "retarget"
            layout.operator("mocap_doctor.discover_objects", icon="VIEWZOOM")

        elif step_id == "global_correction":
            layout.prop(settings, "model_root", text="Teto 根对象")
            layout.prop(settings, "mmr_rig", text="MMR Rig")
            layout.prop(settings, "global_rot_x", text="旋转 X")
            layout.prop(settings, "global_rot_y", text="旋转 Y")
            layout.prop(settings, "global_rot_z", text="旋转 Z")
            _draw_run(layout, step_id)

        elif step_id == "tilt":
            layout.prop(settings, "tilt_reference_frame", text="参考帧")
            layout.prop(settings, "tilt_strength", text="强度")
            row = layout.row(align=True)
            row.prop(settings, "tilt_damp_x", text="X", toggle=True)
            row.prop(settings, "tilt_damp_y", text="Y", toggle=True)
            row.prop(settings, "tilt_damp_z", text="Z", toggle=True)
            _draw_run(layout, step_id)

        elif step_id == "target_floor":
            layout.prop(settings, "target_mesh", text="Teto Mesh")
            layout.prop(settings, "target_floor_z", text="地面 Z")
            layout.prop(settings, "target_floor_strength", text="强度")
            layout.prop(settings, "target_floor_tolerance", text="容差")
            layout.prop(settings, "target_clearance", text="离地间隙")
            layout.prop(settings, "target_floor_max_lift", text="单帧最大抬升")
            layout.prop(settings, "target_floor_smooth_radius", text="平滑半径")
            layout.prop(settings, "target_floor_max_delta", text="帧间最大变化（m/帧）")
            layout.prop(settings, "target_vertex_sample_step", text="顶点采样步长")
            layout.prop(settings, "target_visible_only", text="只扫描可见 Mesh")
            layout.prop(settings, "target_reset_existing_z", text="重建校正 Z 曲线")
            layout.label(text="运行时 Blender 可能暂时无响应")
            _draw_run(layout, step_id)

        elif step_id == "foot_lock":
            layout.prop(settings, "lock_min_xy_range", text="最小修复漂移")
            layout.prop(settings, "lock_anchor_mode", text="锚点")
            layout.prop(settings, "lock_blend_frames", text="缓入缓出")
            layout.prop(settings, "lock_trim", text="裁掉段首尾")
            layout.prop(settings, "drift_min_segment_len", text="漂移分析最短区间")
            layout.prop(settings, "lock_min_segment_len", text="锁定最短区间")
            row = layout.row(align=True)
            row.prop(settings, "lock_x", text="X", toggle=True)
            row.prop(settings, "lock_y", text="Y", toggle=True)
            row.prop(settings, "lock_z", text="Z", toggle=True)
            _draw_run(layout, step_id)

        elif step_id == "mmd_bake":
            layout.prop(settings, "mmd_armature", text="原生 MMD 骨架")
            layout.prop(settings, "mmr_rig", text="MMR Rig")
            layout.prop(settings, "mmd_bake_mode", text="Bake 策略")
            if settings.mmd_bake_mode == "AUTO_IF_SAFE":
                layout.operator("mocap_doctor.mmd_bake", icon="ACTION")
            layout.operator("mocap_doctor.validate_manual_mmd_bake", icon="CHECKMARK")
            layout.operator("mocap_doctor.cleanup_leg_fk", icon="BONE_DATA")

        elif step_id == "export_prep":
            layout.prop(settings, "vmd_floor_offset", text="VMD 地面 Z 偏移")
            reminder = layout.box()
            reminder.label(text="MMR 手部导出清理", icon="ARMATURE_DATA")
            reminder.label(text="确认上肢已烘到“腕 / 肘 / 手首”后再清理。")
            reminder.label(text="再恢复肘部层级，删除 Blender 编辑用手 IK。")
            reminder.label(text="只修改这份工作文件；确认后会创建恢复检查点。")
            layout.operator("mocap_doctor.prepare_vmd_export", text="确认并生成 VMD 导出预览", icon="MODIFIER")

        elif step_id == "export":
            layout.label(text="确认 MMR 约束已禁用，隐藏 RIG 后动作仍正常")
            layout.label(text="回导 VMD 请使用从未建立 MMR 的干净 Teto 模板", icon="INFO")
            layout.prop(settings, "vmd_export_path", text="VMD 文件")
            layout.operator("mocap_doctor.export_vmd", text="导出 VMD", icon="EXPORT")


class MD_PT_Project(Panel):
    bl_idname = "MD_PT_project"
    bl_label = "项目与对象"
    bl_parent_id = "MD_PT_main"
    bl_options = {"DEFAULT_CLOSED"}
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MoCap Doctor"

    @classmethod
    def poll(cls, context):
        return context.scene.mocap_doctor.initialized

    def draw(self, context):
        layout = self.layout
        settings = context.scene.mocap_doctor
        layout.prop(settings, "source_armature", text="源骨架")
        layout.prop(settings, "model_root", text="Teto Root")
        layout.prop(settings, "target_mesh", text="Teto Mesh")
        layout.prop(settings, "mmr_rig", text="MMR Rig")
        layout.prop(settings, "mmd_armature", text="MMD Armature")
        layout.prop(settings, "correction_empty", text="校正 Empty")
        layout.operator("mocap_doctor.discover_objects", icon="VIEWZOOM")
        layout.operator("mocap_doctor.create_checkpoint", icon="BOOKMARKS")
        restore = layout.row()
        restore.enabled = bool(settings.last_checkpoint)
        restore.operator("mocap_doctor.restore_last_checkpoint", icon="LOOP_BACK")


class MD_PT_NLAAnnotation(Panel):
    bl_idname = "MD_PT_nla_annotation"
    bl_label = "MoCap Doctor 标注"
    bl_space_type = "NLA_EDITOR"
    bl_region_type = "UI"
    bl_category = "MoCap Doctor"

    @classmethod
    def poll(cls, context):
        return bool(getattr(context.scene, "mcd_annotation_mode", False))

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active_channel = annotation._context_track_channel(context) or scene.mcd_annotation_active_channel
        channel_row = layout.row(align=True)
        for definition in annotation.visible_track_definitions(scene):
            operator = channel_row.operator(
                "mcd.annotation_set_channel",
                text=definition["label"],
                depress=active_channel == definition["channel"],
            )
            operator.channel = definition["channel"]
        layout.label(text=f"当前帧 {scene.frame_current}")
        if scene.mcd_annotation_has_pending_in:
            pending = layout.box()
            label = annotation.TRACK_BY_CHANNEL[scene.mcd_annotation_pending_channel]["label"]
            pending.label(
                text=f"入点 {scene.mcd_annotation_pending_in} · {label}",
                icon="MARKER_HLT",
            )
            pending.operator("mcd.annotation_cancel_in", icon="X")
        row = layout.row(align=True)
        row.operator("mcd.annotation_mark_in", text="标记 / 覆盖入点", icon="PREV_KEYFRAME")
        row.operator("mcd.annotation_mark_out", text="标记 / 覆盖出点", icon="NEXT_KEYFRAME")
        layout.operator("mcd.annotation_split_current", text="在当前帧拆分", icon="MOD_EDGESPLIT")
        row = layout.row(align=True)
        row.operator("mcd.annotation_delete", text="删除所选区间", icon="TRASH")
        row.operator("mcd.annotation_locate", text="跳到所选区间", icon="VIEWZOOM")
        layout.operator("mcd.annotation_loop_selected", text="循环检查所选区间", icon="PLAY")
        layout.operator("mocap_doctor.exit_annotation_mode", icon="TIME")


CLASSES = (MD_PT_Main, MD_PT_Project, MD_PT_NLAAnnotation)


def register_ui():
    registered = []
    try:
        for cls in CLASSES:
            bpy.utils.register_class(cls)
            registered.append(cls)
    except Exception:
        for cls in reversed(registered):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass
        raise


def unregister_ui():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
