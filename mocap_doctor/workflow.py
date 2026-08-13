from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowStep:
    id: str
    label: str
    stage: str
    mutates_scene: bool
    description: str


STEPS = (
    WorkflowStep("project", "创建项目", "项目", True, "建立工作副本、30fps 和基线检查点"),
    WorkflowStep("source_bake", "源骨架 Bake", "源数据", True, "烘焙有效动捕范围"),
    WorkflowStep("source_analyze", "源动作诊断", "源数据", False, "生成手部异常提示"),
    WorkflowStep("hand_ranges", "手部坏区间", "源数据", False, "NLA 标注左右手坏段"),
    WorkflowStep("hand_repair", "手部区间修复", "源数据", True, "整条手臂链区间插值"),
    WorkflowStep("smooth", "轻度旋转平滑", "源数据", True, "抑制高频旋转噪声"),
    WorkflowStep("source_floor", "源骨架穿地修复", "源数据", True, "通过 pelvis Z 修正穿地"),
    WorkflowStep("contacts", "Planted 检测与修订", "源数据", False, "自动检测并编辑最终区间"),
    WorkflowStep("retarget", "ARP/MMR 重定向", "重定向", True, "人工重定向并记录里程碑"),
    WorkflowStep("global_correction", "Teto 全局扶正", "目标模型", True, "创建全局校正 Empty"),
    WorkflowStep("tilt", "Foot IK 倾斜修复", "目标模型", True, "只压制倾斜轴"),
    WorkflowStep("target_floor", "Teto Mesh 穿地修复", "目标模型", True, "扫描最低点并轻微抬升"),
    WorkflowStep("foot_lock", "脚滑分析与 XY Lock", "目标模型", True, "按最终 planted 锁 XY"),
    WorkflowStep("mmd_bake", "MMD Visual Bake", "导出", True, "安全检测后自动 Bake"),
    WorkflowStep("fingers", "手指动作替换", "导出", True, "删除手指坏数据并写入放松手型"),
    WorkflowStep("export_prep", "VMD 导出准备", "导出", True, "烘根补偿、删腿 FK、加地面偏移"),
    WorkflowStep("export", "导出 VMD", "导出", False, "调用 mmd_tools 导出"),
)

STEP_INDEX = {step.id: index for index, step in enumerate(STEPS)}


def clamp_step(index):
    return max(0, min(int(index), len(STEPS) - 1))


def step_at(index):
    return STEPS[clamp_step(index)]
