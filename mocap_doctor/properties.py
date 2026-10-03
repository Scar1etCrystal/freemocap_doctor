import json

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from .presets import DEFAULTS, EXPECTED_FPS


def _update_mocap_start(settings, context):
    scene = getattr(context, "scene", None)
    if scene is not None and settings.mocap_frame_start <= settings.mocap_frame_end:
        scene.frame_start = int(settings.mocap_frame_start)


def _update_mocap_end(settings, context):
    scene = getattr(context, "scene", None)
    if scene is not None and settings.mocap_frame_end >= settings.mocap_frame_start:
        scene.frame_end = int(settings.mocap_frame_end)


def _agent_fix_strip(settings, item):
    """Locate (track, strip) for a fix row - op_id first, track name as backup."""
    from .core import agent_bridge, agent_ops
    scene = getattr(bpy.context, "scene", None)
    rig = agent_bridge._rig_armature(settings, scene)
    if rig is None:
        return None, None
    if item.op_id:
        for op in agent_ops.list_ops(agent_bridge._data_dir(settings)):
            if op["id"] == item.op_id:
                return agent_ops.find_op_strip(rig, op)
    anim = getattr(rig, "animation_data", None)
    if anim is not None and item.track:
        for tr in anim.nla_tracks:
            if tr.name == item.track:
                for s in tr.strips:
                    if not item.strip or s.name == item.strip:
                        return tr, s
    return None, None


def _agent_fix_error(exc, what):
    """Surface drag-time failures in the panel instead of swallowing them."""
    try:
        from .core import agent_bridge
        agent_bridge._STATUS["last_error"] = f"{what}: {exc!r}"
    except Exception:
        pass


_quiet = False        # 程序化设置带 update 的属性时抑制回调（显示值同步用）
_batching = False     # 批量拖动时抑制逐条 frame_set（12 条 × 全场景重算会卡死拖动）


def set_quietly(settings, prop, value):
    """设置属性但不触发其 update 回调——同步批量滑块的显示值用，
    回写会把勾选行各不相同的力度抹平。"""
    global _quiet
    _quiet = True
    try:
        setattr(settings, prop, value)
    finally:
        _quiet = False


def _update_fix_index(settings, context):
    """用户点了另一行 = 退出批量模式（清空勾选）。

    程序化改索引（sync 重建列表）走 set_quietly，不会误清。"""
    if _quiet:
        return
    for item in settings.agent_fixes:
        if item.selected:
            item.selected = False


def _update_fix_selected(item, context):
    """勾选变化 → 批量滑块/眼睛的显示值跟上该行当前值（静默，不回写）。"""
    if _quiet or not item.selected:
        return
    settings = getattr(getattr(context, "scene", None), "mocap_doctor", None)
    if settings is None:
        return
    set_quietly(settings, "agent_batch_exponent", item.exponent)
    set_quietly(settings, "agent_batch_muted", item.muted)


def _update_fix_exponent(item, context):
    """Per-fix strength: rewrite that strip's delta curves to delta^value.

    strip.influence caps at 1.0, so real strength means scaling the rotation
    angle inside the action - axis-angle scaling keeps direction, adds gain."""
    try:
        from .core import agent_ops
        settings = getattr(getattr(context, "scene", None), "mocap_doctor", None)
        _track, strip = _agent_fix_strip(settings, item)
        if strip is None:
            return
        agent_ops.set_strip_exponent(strip, float(item.exponent))
        scene = getattr(context, "scene", None)
        if scene is not None and not _batching:
            scene.frame_set(scene.frame_current)
    except Exception as exc:
        _agent_fix_error(exc, "力度")


def _update_fix_muted(item, context):
    """Per-fix A/B: mute just this fix's track."""
    try:
        settings = getattr(getattr(context, "scene", None), "mocap_doctor", None)
        track, _strip = _agent_fix_strip(settings, item)
        if track is None:
            return
        track.mute = bool(item.muted)
        scene = getattr(context, "scene", None)
        if scene is not None and not _batching:
            scene.frame_set(scene.frame_current)
    except Exception as exc:
        _agent_fix_error(exc, "静音")


def _update_batch_exponent(settings, context):
    """批量力度：一条滑块写进所有勾选行。逐条写曲线，最后只刷一次帧。"""
    if _quiet:
        return
    global _batching
    _batching = True
    try:
        for item in settings.agent_fixes:
            if item.selected:
                item.exponent = settings.agent_batch_exponent
    except Exception as exc:
        _agent_fix_error(exc, "批量力度")
    finally:
        _batching = False
    scene = getattr(context, "scene", None)
    if scene is not None:
        try:
            scene.frame_set(scene.frame_current)
        except Exception:
            pass


def _update_batch_muted(settings, context):
    """批量静音：勾选行的轨一起 mute/unmute。"""
    if _quiet:
        return
    global _batching
    _batching = True
    try:
        for item in settings.agent_fixes:
            if item.selected:
                item.muted = settings.agent_batch_muted
    except Exception as exc:
        _agent_fix_error(exc, "批量静音")
    finally:
        _batching = False
    scene = getattr(context, "scene", None)
    if scene is not None:
        try:
            scene.frame_set(scene.frame_current)
        except Exception:
            pass


STEP_STATUS_ITEMS = (
    ("PENDING", "未执行", ""),
    ("PREVIEW", "预览中", ""),
    ("ACCEPTED", "已接受", ""),
    ("STALE", "已失效", ""),
    ("FAILED", "失败", ""),
)


PARAMETER_DESCRIPTIONS = {
    "mocap_frame_start": "真正动作的第一帧；更早的标定板动作会保留，但不会参与处理。",
    "mocap_frame_end": "真正动作的最后一帧；更晚的内容不会参与处理。",
    "source_armature": "动捕源骨架（GVHMR 导入的 SMPL 骨架，或旧版 FreeMoCap 骨架），通常由插件自动识别。",
    "source_profile": "源数据的骨骼命名体系。自动识别会按骨架上的骨骼名判断，识别失败或识别错误时再手动指定。",
    "target_template_path": "只记录你用于重定向的干净 Teto/MMR 模板文件路径；插件不会自动从这里导入模型。",
    "gvhmr_take_dir": (
        "GVHMR 那条 take 的原始输出目录（里面有 hamer/merged.pkl 与 hamer/*_hamer_data.pkl）。"
        "导入前的「源手部修复」用它定位要改写的 pkl。"
    ),
    "source_pkl_frame_start": (
        "GVHMR 的 pkl 第 1 帧对应当前工作文件的第几帧。PoseCapture 从导入时的当前帧开始放置动作，"
        "默认 1（即 pkl 第 1 帧落在工作文件第 1 帧）。填错会让手部坏段整体偏移。"
    ),
    "hand_pkl_strategy": (
        "手动标注段使用的修复策略；auto 时自动检测段按各自建议策略、纯手标段按 bridge。"
    ),
    "hand_pkl_channel": "修复写回哪些通道：手腕（腕部朝向）、手指（15 关节手型）或两者。",
    "model_root": "当前场景中 Teto 模型最外层的 mmd_tools Root 空物体，不是 MMR Rig 或骨架。",
    "mmr_rig": "接收重定向动作的 MikuMikuRig 控制骨架。",
    "mmd_armature": "最终 Bake 并导出 VMD 的 Teto 原生 MMD 骨架。",
    "target_mesh": "用于检查模型最低点与穿地的 Teto 网格对象。",
    "correction_empty": "插件创建的整体扶正和抬升控制对象，通常无需手动选择。",

    "source_floor_z": "源动作使用的世界坐标地面 Z 高度。",
    "source_floor_tolerance": "允许忽略的小幅穿地深度，范围内不会修复。",
    "source_floor_clearance": "修复后脚底希望保留的最小离地间隙。",
    "source_floor_max_lift": "整体升降的安全上限：整平量超过它就会被截断，防止地面估计跑飞。",
    "source_floor_strength": "实际应用整平量的比例；1 表示把地面完全整平。",
    "source_floor_window": "估计地面时前后参考的帧数。太小会跟着跳起来，太大跟不上缓慢漂移。",
    "source_floor_smooth_radius": "对骨盆抬升曲线进行平滑时前后参考的帧数。",
    "source_floor_max_delta": "单位：m/帧；相邻帧抬升量允许的最大变化，避免骨盆突然跳动。",
    "contact_height": "脚底距地面不高于该值时才可能判定为 planted。",
    "contact_xy_speed": "单位：m/帧；成为 planted 候选时允许的最大相邻帧水平位移。",
    "contact_moving_xy_speed": "单位：m/帧；超过该相邻帧水平位移时标记为贴地移动，而不是稳定 planted。",
    "contact_vertical_speed": "单位：m/帧；成为 planted 候选时允许的最大相邻帧垂直位移。",
    "contact_min_segment_len": "短于该帧数的 planted 区间会被丢弃。",
    "contact_merge_gap": "间隔不超过该帧数的相邻 planted 区间会合并。",
    "contact_anchor_drift": "脚相对区间起始位置允许的最大水平漂移。",
    "contact_penetration_tolerance": "脚低于地面超过该深度时才报告穿地。",
    "global_rot_x": "整体扶正时绕世界 X 轴旋转的角度。",
    "global_rot_y": "整体扶正时绕世界 Y 轴旋转的角度。",
    "global_rot_z": "整体扶正时绕世界 Z 轴旋转的角度。",
    "tilt_reference_frame": "脚掌朝向正确、用作倾斜基准的帧。",
    "tilt_strength": "倾斜压制强度：0 保持原旋转，1 完全压回参考倾斜。",
    "tilt_damp_axis": "是否压制该旋转轴；Z 通常关闭以保留脚尖朝向。",
    "target_floor_z": "扶正后目标模型使用的世界坐标地面 Z 高度。",
    "target_clearance": "修复后模型网格与地面之间保留的最小间隙。",
    "target_floor_tolerance": "允许忽略的小幅模型穿地深度。",
    "target_floor_max_lift": "单帧最多允许整体抬高模型的距离。",
    "target_floor_strength": "实际应用计算抬升量的比例。",
    "target_floor_smooth_radius": "对整体抬升曲线进行平滑时前后参考的帧数。",
    "target_floor_max_delta": "单位：m/帧；相邻帧整体抬升允许的最大变化。",
    "target_vertex_sample_step": "每隔多少个顶点采样；越大越快，但可能漏掉最低点。",
    "target_visible_only": "只扫描当前可见的模型部件，忽略隐藏网格。",
    "target_reset_existing_z": "重新计算前移除旧的校正 Z 曲线，避免重复叠加。",
    "lock_trim": "锁定前从 planted 区间首尾各裁掉的过渡帧数。",
    "drift_min_segment_len": "参与脚部漂移分析所需的最短区间长度。",
    "lock_min_segment_len": "裁掉首尾后仍需达到的最短锁定区间长度。",
    "lock_blend_frames": "锁定区间前后用于渐入和渐出的帧数。",
    "pelvis_correction_max": (
        "骨盆修约逐帧允许的最大躯干下沉/抬升量（m）。planted 段内按源骨架腿长比逐帧"
        "重解骨盆高度、写进 torso_root：腿长被拉大导致膝不够弯/脚被骨盆带离地面时，"
        "身体下沉让腿恢复弯度、脚够回地面。0 = 关闭。超出此量的帧按上限截断并在报告计数。"
    ),
    "lock_anchor_mode": "锁定位置的取法：中位数最抗噪，第一帧保持落脚点，中间帧取区间中部。",
    "lock_min_xy_range": "区间水平漂移小于该值时不修复；调低会锁定更多区间。",
    "lock_axis": "是否锁定脚 IK 的该位置轴；Z 通常关闭。整段是否修复由水平漂移决定，脚在原地悬空的段会被整段跳过——那种飘要用贴地锁定解决。",
    "ground_smooth_radius": "对非腾空段的贴地修正曲线做平滑时前后参考的帧数；把台阶变成缓坡。腾空段不受影响。",
    "ground_max_delta": (
        "单位：m/帧；非腾空段修正曲线相邻帧允许的最大变化，防止身体因贴地突然上下跳。"
        "腾空段按物理弹道重建，不受这个限速约束（真实起跳速度远大于它）。"
    ),
    "vmd_floor_offset": "导出前写入全ての親的固定 Z 偏移；负值下移，正值上移。",
    "vmd_export_path": "VMD 文件的完整保存位置；省略 .vmd 后缀时插件会自动补上。",
    "mmd_bake_mode": "自动模式仅在固定结构全部通过时 Bake；手动模式由用户 Bake 后再验证和清理。",
}


# Blender's VELOCITY unit is meters per second and does not use scene FPS.
# These algorithms compare adjacent 30fps samples, so m/frame values remain
# unitless in RNA and expose their domain unit explicitly in the UI text.
LENGTH_PROPERTY_NAMES = frozenset(
    {
        "source_floor_z",
        "source_floor_tolerance",
        "source_floor_clearance",
        "source_floor_max_lift",
        "contact_height",
        "contact_anchor_drift",
        "contact_penetration_tolerance",
        "target_floor_z",
        "target_clearance",
        "target_floor_tolerance",
        "target_floor_max_lift",
        "lock_min_xy_range",
        "pelvis_correction_max",
        "vmd_floor_offset",
    }
)
PER_FRAME_DISTANCE_PROPERTY_NAMES = frozenset(
    {
        "source_floor_max_delta",
        "contact_xy_speed",
        "contact_moving_xy_speed",
        "contact_vertical_speed",
        "target_floor_max_delta",
        "ground_max_delta",
    }
)
FACTOR_PROPERTY_NAMES = frozenset(
    {
        "source_floor_strength",
        "tilt_strength",
        "target_floor_strength",
    }
)
ANGLE_PROPERTY_NAMES = frozenset({"global_rot_x", "global_rot_y", "global_rot_z"})


class MD_PG_StepRecord(PropertyGroup):
    step_id: StringProperty()
    status: EnumProperty(items=STEP_STATUS_ITEMS, default="PENDING")
    checkpoint: StringProperty(subtype="FILE_PATH")
    artifact_path: StringProperty(subtype="FILE_PATH")
    parameter_hash: StringProperty()
    message: StringProperty()


class MD_PG_AgentFixItem(PropertyGroup):
    """One row of the agent fix list - mirrors an op log entry + live NLA state."""

    op_id: StringProperty()
    label: StringProperty()
    strip: StringProperty()
    track: StringProperty()
    status: StringProperty()      # preview / committed / lost / unregistered
    frames: StringProperty()
    alive: BoolProperty(
        default=True,
        description="场景里还有对应的 strip；没有时力度/静音都无从施加",
    )
    exponent: FloatProperty(
        name="力度", description="delta^value；>1 超量修正，<1 减弱",
        default=1.0, min=0.0, max=2.0, precision=2,
        update=_update_fix_exponent,
    )
    muted: BoolProperty(
        name="静音", description="单独关掉这条修复看对比",
        default=False, update=_update_fix_muted,
    )
    selected: BoolProperty(
        name="选中", description="勾选后底部滑块/按钮批量作用于所有选中行",
        default=False, update=_update_fix_selected,
    )


_param_quiet = False    # 同步参数镜像时抑制 update 回调（同 _quiet 的分项版）


def _update_param(item, context):
    """参数控件改动 → 交给 agent_bridge 防抖重写（同轨删旧写新）。"""
    global _param_quiet
    if _quiet or _param_quiet:
        return
    try:
        from .core import agent_bridge
        kind = item.kind
        if kind == "float":
            value = float(item.fval)
        elif kind == "int":
            value = int(item.ival)
        elif kind == "range":
            value = [int(item.ival), int(item.ival2)]
        elif kind == "choice":
            value = item.sval
        elif kind == "object":
            value = item.obj.name if item.obj else ""
            if item.sval != value:          # sval 做持久镜像（重载后取回对象）
                _param_quiet = True
                try:
                    item.sval = value
                finally:
                    _param_quiet = False
        else:
            return
        agent_bridge.schedule_param_apply(item.op_id, item.key, value)
    except Exception as exc:
        _agent_fix_error(exc, "参数")


def sync_param_item(item, op_id, spec, value):
    """quiet-write：把 op params 里的一项刷进镜像条目（tick 同步用）。

    画面板不允许写 ID——本函数只给 fixlist/param 定时器调。"""
    global _param_quiet
    _param_quiet = True
    try:
        item.op_id = str(op_id)
        item.key = str(spec["key"])
        item.kind = str(spec["kind"])
        item.label = str(spec.get("label") or spec["key"])
        item.options = json.dumps(spec.get("options") or [])
        if item.kind == "float":
            item.fval = float(value) if value is not None else 0.0
        elif item.kind == "int":
            item.ival = int(value) if value is not None else 0
        elif item.kind == "range":
            pair = list(value or [0, 0])[:2]
            item.ival = int(pair[0])
            item.ival2 = int(pair[-1])
        elif item.kind == "choice":
            item.sval = "" if value is None else str(value)
        elif item.kind == "object":
            item.sval = "" if value is None else str(value)
            item.obj = bpy.data.objects.get(item.sval) if item.sval else None
    finally:
        _param_quiet = False


class MD_PG_AgentParam(PropertyGroup):
    """修复条目展开的一个参数控件镜像（源真值在 op log 的 params）。"""

    pkey: StringProperty()        # "op_id::key" 集合内唯一键
    op_id: StringProperty()
    key: StringProperty()
    kind: StringProperty()        # float / int / choice / object / range
    label: StringProperty()
    options: StringProperty()     # JSON list（choice 的候选）
    fval: FloatProperty(
        name="值", soft_min=-1000.0, soft_max=1000.0, precision=3,
        update=_update_param,
    )
    ival: IntProperty(
        name="值", soft_min=-100000, soft_max=100000,
        update=_update_param,
    )
    ival2: IntProperty(
        name="止", soft_min=-100000, soft_max=100000,
        update=_update_param,
    )
    sval: StringProperty(update=_update_param)
    obj: PointerProperty(
        name="方向物体", type=bpy.types.Object,
        description="mcd_dir_* 箭头=平行于箭头轴(+Z)；mcd_aim_*=指向物体",
        update=_update_param,
    )


class MD_PG_ProjectSettings(PropertyGroup):
    initialized: BoolProperty(default=False)
    project_uuid: StringProperty()
    project_name: StringProperty(default="MoCap Project")
    original_filepath: StringProperty(subtype="FILE_PATH")
    work_filepath: StringProperty(subtype="FILE_PATH")
    data_directory: StringProperty(subtype="DIR_PATH")
    target_template_path: StringProperty(subtype="FILE_PATH", description=PARAMETER_DESCRIPTIONS["target_template_path"])
    gvhmr_take_dir: StringProperty(subtype="DIR_PATH", description=PARAMETER_DESCRIPTIONS["gvhmr_take_dir"])
    source_pkl_frame_start: IntProperty(
        default=DEFAULTS["source_pkl_frame_start"],
        min=1,
        description=PARAMETER_DESCRIPTIONS["source_pkl_frame_start"],
    )
    current_step: IntProperty(default=0, min=0)
    schema_version: IntProperty(default=0, options={"HIDDEN"})
    expected_fps: IntProperty(default=EXPECTED_FPS, options={"HIDDEN"})
    mocap_frame_start: IntProperty(default=1, update=_update_mocap_start, description=PARAMETER_DESCRIPTIONS["mocap_frame_start"])
    mocap_frame_end: IntProperty(default=250, update=_update_mocap_end, description=PARAMETER_DESCRIPTIONS["mocap_frame_end"])
    status_message: StringProperty(default="尚未创建 MoCap Doctor 项目")
    busy: BoolProperty(default=False)
    preview_step_id: StringProperty()
    preview_owner_name: StringProperty()
    preview_base_action: StringProperty()
    preview_action: StringProperty()
    preview_restore_checkpoint: StringProperty(subtype="FILE_PATH")
    last_checkpoint: StringProperty(subtype="FILE_PATH")
    annotation_step_id: StringProperty()

    source_armature: PointerProperty(type=bpy.types.Object, description=PARAMETER_DESCRIPTIONS["source_armature"])
    source_profile: EnumProperty(
        items=(
            ("AUTO", "自动识别", "按骨架上的骨骼名自动判断来源（推荐）"),
            ("GVHMR", "GVHMR / SMPL", "PoseCapture 导入的 SMPL 骨架（f_avg_ / m_avg_ 前缀）"),
            ("FREEMOCAP", "FreeMoCap", "旧前端：pelvis / hand.L / heel.02.L 命名"),
        ),
        default="AUTO",
        description=PARAMETER_DESCRIPTIONS["source_profile"],
    )
    model_root: PointerProperty(type=bpy.types.Object, description=PARAMETER_DESCRIPTIONS["model_root"])
    mmr_rig: PointerProperty(type=bpy.types.Object, description=PARAMETER_DESCRIPTIONS["mmr_rig"])
    mmd_armature: PointerProperty(type=bpy.types.Object, description=PARAMETER_DESCRIPTIONS["mmd_armature"])
    target_mesh: PointerProperty(type=bpy.types.Object, description=PARAMETER_DESCRIPTIONS["target_mesh"])
    correction_empty: PointerProperty(type=bpy.types.Object, description=PARAMETER_DESCRIPTIONS["correction_empty"])

    agent_fixes: CollectionProperty(type=MD_PG_AgentFixItem)
    agent_fix_index: IntProperty(default=0, min=0,
                                  update=_update_fix_index)
    agent_batch_exponent: FloatProperty(
        name="批量力度", description="写进所有勾选的修复（delta^value）",
        default=1.0, min=0.0, max=2.0, precision=2,
        update=_update_batch_exponent,
    )
    agent_batch_muted: BoolProperty(
        name="批量静音", description="勾选行的轨一起 mute/unmute",
        default=False, update=_update_batch_muted,
    )
    agent_ops_rev: IntProperty(
        default=0, options={"HIDDEN"},
        description="op log 版本号：写/commit/revert 时 +1，面板据此重建列表",
    )
    agent_fixes_rev: IntProperty(default=-1, options={"HIDDEN"})
    agent_params: CollectionProperty(
        type=MD_PG_AgentParam,
        description="修复条目的可调参数镜像（由 fixlist 定时器从 op log 同步）",
    )

    hand_pkl_strategy: EnumProperty(
        items=(
            ("auto", "按检测建议", "自动检测段用各自建议策略；纯手标段按 bridge"),
            ("bridge", "桥接（slerp）", "段两端各取基准姿态，球面插值过渡"),
            ("hold", "保持", "整段钉在段前姿态，尾部缓出"),
            ("smooth", "平滑", "中值+高斯滤波去抖动"),
        ),
        default="auto",
        description=PARAMETER_DESCRIPTIONS["hand_pkl_strategy"],
    )
    hand_pkl_channel: EnumProperty(
        items=(
            ("both", "手腕+手指", "同时写回腕部朝向与 15 关节手型"),
            ("wrist", "仅手腕", "只改腕部朝向（body_pose 57:63）"),
            ("fingers", "仅手指", "只改 *_hand_pose 手型"),
        ),
        default="both",
        description=PARAMETER_DESCRIPTIONS["hand_pkl_channel"],
    )

    source_floor_z: FloatProperty(
        default=DEFAULTS["source_floor_z"],
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["source_floor_z"],
    )
    source_floor_tolerance: FloatProperty(
        default=DEFAULTS["source_floor_tolerance"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["source_floor_tolerance"],
    )
    source_floor_clearance: FloatProperty(
        default=DEFAULTS["source_floor_clearance"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["source_floor_clearance"],
    )
    source_floor_max_lift: FloatProperty(
        default=DEFAULTS["source_floor_max_lift"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["source_floor_max_lift"],
    )
    source_floor_strength: FloatProperty(
        default=DEFAULTS["source_floor_strength"],
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["source_floor_strength"],
    )
    source_floor_window: IntProperty(
        default=DEFAULTS["source_floor_window"],
        min=1,
        max=300,
        description=PARAMETER_DESCRIPTIONS["source_floor_window"],
    )
    source_floor_smooth_radius: IntProperty(default=DEFAULTS["source_floor_smooth_radius"], min=0, max=30, description=PARAMETER_DESCRIPTIONS["source_floor_smooth_radius"])
    source_floor_max_delta: FloatProperty(
        default=DEFAULTS["source_floor_max_delta"],
        min=0.0,
        subtype="NONE",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["source_floor_max_delta"],
    )

    contact_height: FloatProperty(
        default=DEFAULTS["contact_height"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["contact_height"],
    )
    contact_xy_speed: FloatProperty(
        default=DEFAULTS["contact_xy_speed"],
        min=0.0,
        subtype="NONE",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["contact_xy_speed"],
    )
    contact_moving_xy_speed: FloatProperty(
        default=DEFAULTS["contact_moving_xy_speed"],
        min=0.0,
        subtype="NONE",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["contact_moving_xy_speed"],
    )
    contact_vertical_speed: FloatProperty(
        default=DEFAULTS["contact_vertical_speed"],
        min=0.0,
        subtype="NONE",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["contact_vertical_speed"],
    )
    contact_min_segment_len: IntProperty(default=DEFAULTS["contact_min_segment_len"], min=1, description=PARAMETER_DESCRIPTIONS["contact_min_segment_len"])
    contact_merge_gap: IntProperty(default=DEFAULTS["contact_merge_gap"], min=0, description=PARAMETER_DESCRIPTIONS["contact_merge_gap"])
    contact_anchor_drift: FloatProperty(
        default=DEFAULTS["contact_anchor_drift"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["contact_anchor_drift"],
    )
    contact_penetration_tolerance: FloatProperty(
        default=DEFAULTS["contact_penetration_tolerance"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["contact_penetration_tolerance"],
    )

    global_rot_x: FloatProperty(default=DEFAULTS["global_rot_x"], subtype="ANGLE", unit="ROTATION", description=PARAMETER_DESCRIPTIONS["global_rot_x"])
    global_rot_y: FloatProperty(default=DEFAULTS["global_rot_y"], subtype="ANGLE", unit="ROTATION", description=PARAMETER_DESCRIPTIONS["global_rot_y"])
    global_rot_z: FloatProperty(default=DEFAULTS["global_rot_z"], subtype="ANGLE", unit="ROTATION", description=PARAMETER_DESCRIPTIONS["global_rot_z"])

    tilt_reference_frame: IntProperty(default=0, description=PARAMETER_DESCRIPTIONS["tilt_reference_frame"])
    tilt_strength: FloatProperty(
        default=DEFAULTS["tilt_strength"],
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["tilt_strength"],
    )
    tilt_damp_x: BoolProperty(default=True, description=PARAMETER_DESCRIPTIONS["tilt_damp_axis"])
    tilt_damp_y: BoolProperty(default=True, description=PARAMETER_DESCRIPTIONS["tilt_damp_axis"])
    tilt_damp_z: BoolProperty(default=False, description=PARAMETER_DESCRIPTIONS["tilt_damp_axis"])

    target_floor_z: FloatProperty(
        default=DEFAULTS["target_floor_z"],
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["target_floor_z"],
    )
    target_clearance: FloatProperty(
        default=DEFAULTS["target_clearance"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["target_clearance"],
    )
    target_floor_tolerance: FloatProperty(
        default=DEFAULTS["target_floor_tolerance"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["target_floor_tolerance"],
    )
    target_floor_max_lift: FloatProperty(
        default=DEFAULTS["target_floor_max_lift"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["target_floor_max_lift"],
    )
    target_floor_strength: FloatProperty(
        default=DEFAULTS["target_floor_strength"],
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["target_floor_strength"],
    )
    target_floor_smooth_radius: IntProperty(default=DEFAULTS["target_floor_smooth_radius"], min=0, max=30, description=PARAMETER_DESCRIPTIONS["target_floor_smooth_radius"])
    target_floor_max_delta: FloatProperty(
        default=DEFAULTS["target_floor_max_delta"],
        min=0.0,
        subtype="NONE",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["target_floor_max_delta"],
    )
    target_vertex_sample_step: IntProperty(default=DEFAULTS["target_vertex_sample_step"], min=1, max=100, description=PARAMETER_DESCRIPTIONS["target_vertex_sample_step"])
    target_visible_only: BoolProperty(default=True, description=PARAMETER_DESCRIPTIONS["target_visible_only"])
    target_reset_existing_z: BoolProperty(default=True, description=PARAMETER_DESCRIPTIONS["target_reset_existing_z"])

    lock_trim: IntProperty(default=DEFAULTS["lock_trim"], min=0, description=PARAMETER_DESCRIPTIONS["lock_trim"])
    drift_min_segment_len: IntProperty(default=DEFAULTS["drift_min_segment_len"], min=1, description=PARAMETER_DESCRIPTIONS["drift_min_segment_len"])
    lock_min_segment_len: IntProperty(default=DEFAULTS["lock_min_segment_len"], min=1, description=PARAMETER_DESCRIPTIONS["lock_min_segment_len"])
    lock_blend_frames: IntProperty(default=DEFAULTS["lock_blend_frames"], min=0, description=PARAMETER_DESCRIPTIONS["lock_blend_frames"])
    pelvis_correction_max: FloatProperty(default=DEFAULTS["pelvis_correction_max"], min=0.0, description=PARAMETER_DESCRIPTIONS["pelvis_correction_max"])
    lock_anchor_mode: EnumProperty(
        items=(("median", "中位数", ""), ("first", "第一帧", ""), ("middle", "中间帧", "")),
        default="median",
        description=PARAMETER_DESCRIPTIONS["lock_anchor_mode"],
    )
    lock_min_xy_range: FloatProperty(
        default=DEFAULTS["lock_min_xy_range"],
        min=0.0,
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["lock_min_xy_range"],
    )
    lock_x: BoolProperty(default=True, description=PARAMETER_DESCRIPTIONS["lock_axis"])
    lock_y: BoolProperty(default=True, description=PARAMETER_DESCRIPTIONS["lock_axis"])
    lock_z: BoolProperty(default=False, description=PARAMETER_DESCRIPTIONS["lock_axis"])

    ground_smooth_radius: IntProperty(
        default=DEFAULTS["ground_smooth_radius"],
        min=0,
        max=30,
        description=PARAMETER_DESCRIPTIONS["ground_smooth_radius"],
    )
    ground_max_delta: FloatProperty(
        default=DEFAULTS["ground_max_delta"],
        min=0.0,
        subtype="NONE",
        unit="NONE",
        description=PARAMETER_DESCRIPTIONS["ground_max_delta"],
    )

    vmd_floor_offset: FloatProperty(
        default=DEFAULTS["vmd_floor_offset"],
        subtype="DISTANCE",
        unit="LENGTH",
        description=PARAMETER_DESCRIPTIONS["vmd_floor_offset"],
    )
    vmd_export_path: StringProperty(subtype="FILE_PATH", description=PARAMETER_DESCRIPTIONS["vmd_export_path"])
    mmd_bake_mode: EnumProperty(
        items=(("AUTO_IF_SAFE", "检测通过才自动", ""), ("MANUAL", "始终手动", "")),
        default="AUTO_IF_SAFE",
        description=PARAMETER_DESCRIPTIONS["mmd_bake_mode"],
    )

    steps: CollectionProperty(type=MD_PG_StepRecord)


CLASSES = (MD_PG_StepRecord, MD_PG_AgentFixItem, MD_PG_AgentParam,
           MD_PG_ProjectSettings)


def register_properties():
    registered = []
    try:
        for cls in CLASSES:
            bpy.utils.register_class(cls)
            registered.append(cls)
        bpy.types.Scene.mocap_doctor = PointerProperty(type=MD_PG_ProjectSettings)
    except Exception:
        if hasattr(bpy.types.Scene, "mocap_doctor"):
            del bpy.types.Scene.mocap_doctor
        for cls in reversed(registered):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass
        raise


def unregister_properties():
    if hasattr(bpy.types.Scene, "mocap_doctor"):
        del bpy.types.Scene.mocap_doctor
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
