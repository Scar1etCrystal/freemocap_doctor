# 新工具开发简报（dev worker 必读，读完直接开工）

你在给 MoCap Doctor 的 agent 层加一个/几个**写工具 + 配套读工具**。下面是
所有你需要的事实——**别自己逆向代码找约定**，这里写的都实测过。

## 0. 环境（照抄命令，别发明）

| 东西 | 位置 |
|---|---|
| 你的 git worktree（只在这里改代码） | `/home/sb/mcd_wt/<你的名>`（分支 `dev/<你的名>`） |
| 套件根（kit） | `/home/sb/remote_kit_1.7.1` |
| 你的私有扩展目录 | `/home/sb/remote_kit_1.7.1/sandbox/ext_<你的名>` |
| fixture（e2e 用，只读，测试从不存盘） | `/home/sb/remote_kit_1.7.1/sandbox/work/fixture_1499.blend` |

```bash
W=/home/sb/mcd_wt/<你的名>; KIT=/home/sb/remote_kit_1.7.1
export MCD_CLONE=$W
export MCD_EXT_DIR=$KIT/sandbox/ext_<你的名>
bash $KIT/tools/mcd.sh deploy-private                    # 把 $W/mocap_doctor 同步进私有扩展目录
bash $KIT/tools/mcd.sh e2e $W/tests/e2e_<工具>.py         # 跑你的 e2e（排队拿 Blender 锁）
bash $KIT/tools/mcd.sh e2e $W/tests/e2e_anatomy.py        # 回归：17/17
bash $KIT/tools/mcd.sh e2e $W/tests/e2e_perfix.py         # 回归：17/17
bash $KIT/tools/mcd.sh e2e $W/tests/e2e_accent.py         # 回归：8/8
bash $KIT/tools/mcd.sh run /path/to/script.py             # 跑任意后台脚本（探查用）
```

- **内存铁律**：机器 8GB，同一时刻只许 1 个 Blender。**永远只通过 mcd.sh 启动
  Blender**（它排队、查内存、留全量日志在 `$KIT/logs/`）。别直接敲 `blender`，
  别起 headless 服务（socket 验证是另一个阶段）。
- 一次 Blender 跑 2–5 s（载入 + 测试），别人在跑时你会排队几秒，正常。
- 改完代码**必须先 deploy-private 再跑**，否则测的是旧代码。
- 只改你 scope 里的文件。`agent_bridge.py` / `agent_ops.py` / `agent_pose.py`
  **一律只读**——插件机制已经接好，你不需要碰它们。缺接口就在汇报里写"需要"，
  不要自己改共享文件。
- 完成后在你的 worktree 里 `git add` 你的文件、`git commit`（标题前缀 `[任务3]`
  或 `[任务4]`），**不要 push、不要 merge**——协调者合并。

## 1. 单位与约定（违反即错）

- 角度：一切对外的 metrics / 参数用**度**。四元数 `(w,x,y,z)`。位置米。30fps。
- `frame_range` **含两端**。你的工具**只许写 frame_range 以内的帧**（读可以越界，
  比如重叠工具要读 t−delay）。这是并发租约的前提：scope = bones × frame_range。
- 世界：前方 = **−Y**，上 = +Z，左右镜像面 = X=0。
- **骨骼旋转模式不统一（实测）**：`upper_arm_fk.* / forearm_fk.*` 是 **Euler XYZ**，
  `shoulder.*` 是 **Euler YXZ**；hand/手指/spine/neck/head/腿是 QUATERNION。
  只写 `rotation_quaternion` 的代码在手臂上**静默无效**。所以：**写入一律走
  `agent_pose.pose_deltas` + `agent_pose.write_pose`**，它按骨的模式写对的通道。
- **腿是 IK 模式**（`thigh_parent.L["IK_FK"]=0`）：`thigh_fk/shin_fk` 有 key 但改了
  看不见；腿的有效控制骨是 `foot_ik.L/R`（位置+旋转）。手臂是 FK（`IK_FK=1`）。
- 手指（`f_index.01.L`、`thumb.01.L`…）在骨树上不是 `hand_fk` 的子骨（中间隔着
  `ORG-hand.L` 等 Rigify 机制骨），**链深度用 `agent_pose.depth_in`**（它按"语义
  父骨"算，已处理 MCH/ORG 中转）。
- 可见姿态 = 基底 + 其它所有 delta strip。**delta 一律相对"可见姿态"算**
  （`sample_visible` 读到的就是它），这样叠在别人修复之上也是精确的。
  `reapply` 会先把本 op 的旧 strip 挪出时间窗再调你的重解函数——你读到的
  可见姿态里不含自己的旧输出，不用特殊处理。
- 源骨架 `Armature`/`f_avg_*` 是废案，**只写 `RIG-*` 上的控制骨**。
- RIG 角色名→骨名（`bones` 参数两者都收）：`hips→torso_root, spine1→spine_fk,
  spine2→spine_fk.001, spine3→spine_fk.003, neck, head, left_shoulder→shoulder.L,
  left_upper_arm→upper_arm_fk.L, left_forearm→forearm_fk.L, left_hand→hand_fk.L,
  left_foot→foot_ik.L, finger_l_index1→f_index.01.L, finger_l_thumb1→thumb.01.L`（R 同理）。
  桥里 `ctx["resolve_bones"](names)` 帮你映射。

## 2. agent_pose API（已测：四元数骨与 Euler 骨往返误差 ≤0.00003°）

```python
from . import agent_ops, agent_pose as P
P.strip_window(frame_range) -> (a, b, frames_list)        # 校验 ≥2 帧
P.resolve_pose_bones(armature, names) -> [names]           # 不存在就抛 "scope 越界"
P.chain_preset("arm.L"|"arm_nofingers.L"|"fingers.L"|"spine"|"spine_head"|"leg.L", armature) -> [bones 根→梢]
P.depth_in(armature, bone, members) -> int                 # 语义链深度（0=链根）
P.semantic_parent(armature, bone) / P.semantic_ancestors(...)
P.sample_visible(scene, armature, bones, frames, world=False)
   -> {"frames", "quat":{b:(T,4)}, "loc":{b:(T,3)}, "euler":{b:(T,3) 弧度, 仅Euler骨},
       "mode":{b:模式}, "mat":{b:(T,4,4) 骨架空间矩阵, world=True 时}}   # 一次扫帧取全部骨
P.pose_deltas(armature, sample, desired_quat={b:(T,4)}, desired_loc={b:(T,3)},
              strength=1.0, index_slice=None) -> (scalars, quats, info)
   # sample 必须是 desired 所基于的那次可见采样；sample 比写窗宽时用 index_slice 截取
P.write_pose(armature, strip_name, frame_start, scalars, quats, blend=4, track_name=None) -> (track, strip)
# 四元数数学（全部向量化，wxyz）：
P.qmul, P.qconj, P.slerp(q0,q1,t), P.qpow(q,t), P.qangle_deg(a,b),
P.quat_to_rotvec, P.rotvec_to_quat, P.quat_to_mat, P.mat_to_quat, P.quat_continuous
P.resample_quats(q, frame0, float_times) / P.resample_vec(...)   # 浮点帧时间重采样（slerp）
P.angular_speed_deg(q) -> (T,) 度/帧 ; P.smooth(x, width)
P.detect_events(speed, onset_frac=0.15, stop_frac=0.12) -> {"peak","onset","stop","peak_speed"}（索引）
P.motion_axis(q_from, q_to) -> (局部单位轴, 角度°)          # rel = conj(q_from)⊗q_to
P.smoothstep(x)
P.mirror_name("hand_fk.L") -> "hand_fk.R" ; P.mirror_flip(armature, src, dst) -> F (3×3, det −1)
P.mirror_local(q, loc, F) -> (q', loc')      # 局部镜像 R' = Fᵀ R F，本 RIG 上 F≈diag(-1,1,1) 误差<2e-5
```

delta 写入语义（`pose_deltas` 已处理，知道就行）：四元数骨写 `conj(cur)⊗desired`
（COMBINE 右乘），Euler 骨写 `to_euler(desired, compat=cur) − cur`（COMBINE 相加），
位置写 `desired − cur`。`strength` 缩放 delta（旋转=角度缩放）。strip 两端 `blend`
帧自动 taper 回原姿态——**你的有效改动区要离窗口两端 ≥ blend 帧**，否则被 taper 吃掉。

## 3. 插件契约（照这个骨架写，别发明新结构）

你的模块 `mocap_doctor/core/agent_<模块名>.py` 只需导出四个 dict，桥启动时自动载入：

```python
"""agent_xxx.py — <工具名们>（一句话说清干什么）。"""
from __future__ import annotations
import numpy as np
from . import agent_ops, agent_pose as P

def my_tool(scene, armature, *, bones, frame_range, strength=1.0, blend=4,
            op_mode="preview", data_dir=None, track_name=None,
            dry_run=False, record=True, **opts):
    a, b, frames = P.strip_window(frame_range)
    bones = P.resolve_pose_bones(armature, bones)
    smp = P.sample_visible(scene, armature, bones, frames)      # 一次扫帧
    desired = {bn: ... for bn in bones}                          # 你的数学：(T,4) 局部旋转
    scalars, quats, info = P.pose_deltas(armature, smp, desired_quat=desired,
                                         strength=strength)
    metrics = {"bones": info, ...}                               # 全部用度/帧号
    params = {"bones": list(bones), "frame_range": [a, b], "strength": strength,
              "blend": blend, **opts}                            # 全部输入！reapply 靠它
    if dry_run:
        return {"dry_run": True, "params": params, "metrics": metrics, "frames": [a, b]}
    track, strip = P.write_pose(armature, f"agent_mytool_{a}_{b}", a, scalars, quats,
                                blend=blend, track_name=track_name)
    op = agent_ops._new_op("my_tool", params, (a, b), strip.name, op_mode,
                           metrics, track=track.name)
    return agent_ops._record(data_dir, op) if (data_dir and record) else op

def _names(ctx, args):            # bones（角色名或骨名）或 chain 预设
    if args.get("chain"):
        return P.chain_preset(args["chain"], ctx["armature"])
    return ctx["resolve_bones"](args.get("bones") or [])

def _tool_my_tool(ctx, **args):   # 桥层薄壳：socket 调用到这里
    names = _names(ctx, args)
    args = {k: v for k, v in args.items() if k not in ("bones", "chain")}
    op = my_tool(ctx["scene"], ctx["armature"], bones=names,
                 data_dir=ctx["data_dir"], **args)
    if not op.get("dry_run"):
        ctx["after_write"](op["frames"])
    return op

def _scope_my_tool(ctx, args):    # 并发租约用：会写哪些骨 × 哪些帧
    return [(_names(ctx, args), (int(args["frame_range"][0]), int(args["frame_range"][1])))]

def _reapply_my_tool(armature, base_action, *, params, frame_range, status, scene, track_name):
    p = dict(params); p["frame_range"] = frame_range
    return my_tool(scene, armature, op_mode=status, data_dir=None,
                   track_name=track_name, record=False, **p)

TOOLS = {"my_tool": _tool_my_tool}
WRITE_SCOPES = {"my_tool": _scope_my_tool}
TUNABLE = {"my_tool": [{"key": "strength", "kind": "float", "min": 0.0, "max": 2.0},
                       {"key": "blend", "kind": "int", "min": 0, "max": 40},
                       {"key": "frame_range", "kind": "range"}]}
REAPPLY = {"my_tool": _reapply_my_tool}
```

- `TUNABLE` 的 kind 只有 `float/int/choice(带 options)/object/range`。只放"强度类"
  参数（面板滑块用），结构参数（bones/bone_map）不放。
- 返回 op dict（有 `id`/`strip` 键）→ 桥自动包成标准响应信封；dry_run 返回的
  dict 原样放进 `data`。
- 写入失败一律 `raise RuntimeError("<中文说清原因>，<下一步怎么做>")`——
  错误信息就是给 agent 的提示，要能照着改参数。
- strip 名必须以 `agent_` 开头（is_agent_track_name 靠它），格式 `agent_<短工具名>_<a>_<b>`。

## 4. e2e 测试要求

写 `tests/e2e_<工具>.py`，照 `tests/e2e_anatomy.py` 的套路：

```python
import os, sys, bpy, addon_utils, numpy as np
addon_utils.enable("bl_ext.user_default.mocap_doctor")
from bl_ext.user_default.mocap_doctor.core import agent_bridge, agent_ops, agent_pose as P
RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), str(detail))); print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}")
scene = bpy.context.scene; settings = scene.mocap_doctor
rig = settings.mmr_rig or next(o for o in scene.objects if o.type == "ARMATURE" and o.name.startswith("RIG-"))
settings.mmr_rig = rig
data_dir = os.path.join(os.path.dirname(bpy.data.filepath), "e2e_<工具>_data")
os.makedirs(data_dir, exist_ok=True); settings.data_directory = data_dir
oplog = os.path.join(data_dir, "agent_ops.json")
if os.path.exists(oplog): os.remove(oplog)
def call(tool, **args):                       # 走桥：顺便验证注册链
    return agent_bridge._dispatch({"tool": tool, "args": args})
... checks ...
fails = [r for r in RESULTS if not r[1]]
print(f"\n==== {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS ====")
for n, _o, d in fails: print(f"FAIL {n}: {d}")
sys.exit(1 if fails else 0)
```

每个写工具至少验证：
1. 走 `call()`（桥）写入成功，`ok=True`，op 在 `list_ops` 里，`status=preview`，strip/track 名以 `agent_` 开头。
2. **独立复测**：写完重新 `sample_visible`（或你的读工具）量结果，数值达标（见各工具验收）。
   **不许用求解器自己的中间量自证。**
3. 窗口外帧完全不变（误差 < 0.01°）；两端 taper 帧可以有过渡。
4. 四元数骨 **和** Euler 骨（手臂）都覆盖到。
5. `reapply`（`agent_ops.reapply(data_dir, rig, op_id, scene=scene, **overrides)`）改一个参数：
   op_id 不变、同轨只剩 1 条 strip、params 合并、结果随参数变化。
6. `dry_run=True` 不写任何 strip。
7. `revert` 后可见姿态回到写入前（< 0.01°）。

**挑测试帧段**：fixture 1–1499 帧。先用 `mcd.sh run` 跑一个探查脚本：对目标骨链
`sample_visible` 全段，算 `angular_speed_deg`，找"前后有静止、中间有明显动作
（峰值 > 3°/帧）"的段落，把帧号硬编码进 e2e（测试要确定性、单个 < 30 s）。

## 5. 交付 + 汇报（不变通）

```
[任务N] <工具名们>
改：<文件:函数 清单>（应只有你的模块 + 你的 e2e）
测：<你的 e2e 结果行 ==== X/X PASS ====> + anatomy 17/17 perfix 17/17 accent 8/8
数：<关键指标，如 err_inner=0.00° / 预备反向 14.2°（峰值 95° 的 15%）/ 起点 412→414>
坑：<踩到的语义/环境坑，留给写提示词的人>
socket 用法：<一段可以直接给 sonnet agent 的调用示例 JSON（含推荐参数和验收看哪个数）>
```
