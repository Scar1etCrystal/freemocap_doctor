# Session 2026-10-03 — 语义修复层 + 参数输入器 + mcd_base 一帧滞后大根因

## 本轮交付（v1.7.0）

- `core/agent_anatomy.py`：语义解剖探头。掌心（指根连线×手指向定面、
  指弯曲向定号，左右手免特判）、脚底（三点定面+小腿定号）、膝/肘前
  （夹角凸出向）、身体前方（脚尖+肩线+相机交叉）、单指、bone_axis 兜底。
  `frame_probe_fn` 提供逐帧世界方向函数。
- `hold_pose` 大改：`world_axis`/`secondary_axis` 吃任意局部向量或
  `"probe:<part>.<side>"`（**逐帧现推**，治"掌心相对手骨随帧变 71°"）；
  双轴解算（主轴对目标、次轴保持指向）治 180° 最小旋转病态翻手；
  单轴路径加 `flip_guard_deg` 护栏（>150° 跳过并计 `skipped_flip_frames`）；
  `dir_object`/`dir_mode`：目标方向可绑空物体（arrow=+Z 轴平行方向，
  aim=骨指向物体位置），k 帧即逐帧目标。
- `agent_ops.reapply(op_id, **overrides)`：同轨重写（同轨不允许时间重叠
  →先挪远旧 strip 再写新，失败挪回）；`TUNABLE_PARAMS` 每工具可调参数表
  （含 `when` 条件过滤）。
- 参数输入器（UI）：修复条目选中后展开参数控件（float/int/choice/object/
  range 五种 kind），properties 回调 → `agent_bridge.schedule_param_apply`
  → `_param_tick` 防抖 250ms 同轨重写；`dir_object` 绑定的空物体矩阵变化
  自动排队刷新。`mocap_doctor.agent_dir_create` 一键建 `mcd_dir_*` 箭头 /
  `mcd_aim_*` 指向点。
- socket 工具新增 `probe_anatomy`、`reapply`；docs/工具手册_agent.md +
  docs/反馈问题的方法.md。

## 本次挖出的最大根因（重要）

**`ensure_base_on_nla` 的 mcd_base strip 时间映射错位**：`strips.new("base",
max(1,int(f0)), action)` 在动作首帧 f0<1 时 strip 起点被钳到 1 而
action_frame_start 留 f0 → **整条基底滞后 1 帧求值**（action[f-1]）。
所有旧 op 的 delta 是 `conj(action[f])⊗desired` 打在滞后一帧的基上——
小 delta 看不出来（历史里那些"差几度"的残差很可能都是它），170° 翻转
直接炸成波浪残差。修法：`action_frame_start = frame_start`（sampled_t=f
恒等），已存在的旧 mcd_base 打开时自动纠正。

**用户可见影响**：老文件打开后动画整体前移 1 帧——这是修正（原来都晚一
帧），已写好的 delta 反而变准。

## 其他测试踩出的坑

- `mathutils.Vector()` 无参是 0 维向量，`sum(vecs, Vector())` 炸——
  用 `Vector((0,0,0))`。
- `Quaternion.angle` 是属性不是方法；两 quat 角差用
  `a.rotation_difference(b).angle`。
- 同轨 NLA strip **不允许时间重叠**（"no space to accommodate"）——
  reapply 必须先挪走旧 strip。
- `frames_data` 过滤掉 None 后再 zip(frames, data) 会把帧号对错——
  用 (frame, data) 元组携带。
- probe 复测报 `err_inner_deg`/`err_per_frame`：边缘 taper 帧保留原姿态
  是设计行为，err_max 会误报。
- 手指骨不在 hand_fk 链下（挂 `MCH-*_drv → ORG-hand`），但 ORG 链
  1:1 跟随——probe 几何推导照常成立；不过掌心相对 hand_fk 的局部轴
  随帧散布达 71.5°，均值轴不可用作逐帧目标 → probe: 协议轴。
- 同骨叠 op 时 stacking 近似：conj(base)⊗desired 叠旧 delta ≠ desired；
  测试里 E 必须放在没写过 delta 的干净骨上。

## e2e

`.blender_test_tmp/e2e_anatomy.py` 17/17（probe 各部位、双轴 180° 翻转
err_inner=0、手指保持、flip guard、reapply 同轨同名、dir_object 箭头驱动、
参数镜像）；e2e_perfix 17/17、e2e_accent 8/8 回归无退。
