# 剧本 34：动作复制（motion_copy · 验收 compare_motion）

> 配合 `tools_io.md`。把一段（通常是手 k 好的）动作搬到：另一个时间段 / 另一侧（镜像）/
> 另一个部位。任务块会写：源骨或链、源帧段、目标（时间/侧/部位）。

## 先想清楚三件事

1. **空间** `space`：
   - `"local"`（默认，推荐）——复制**关节角**。时间平移、左右镜像手势都用它：结果跟着
     目标时刻身体的朝向走（人转了身，镜像的手势也跟着转）。
   - `"world"`——复制**世界朝向**（镜像面 X=0，前方 −Y）。只在"手必须在世界里指向同一个
     方向"时用；人转了身就会对不上身体。
2. **通道** `channels`：默认 `"rot"`（只转旋转）。`"rot+loc"` 连位置一起——**别用在
   hips/torso_root 上做时间平移**（会把角色瞬移到源时刻的位置）；`foot_ik` 这类 IK 控制骨
   复制脚步时才需要 `rot+loc`。
3. **模式** `mode`：`"replace"`（目标变成源）或 `"add"`（把源相对起始帧的**变化量**叠到目标
   现有动作上——比如给已有动作加一段抖手）。

## 步骤

1. **dry_run 预演**（不写任何东西）：
   ```
   /home/sb/remote_kit_1.7.1/tools/agent motion_copy '{"agent_id":"<ME>","chain":"arm.L","src_range":[405,450],
     "dst_start":405,"mirror":true,"dry_run":true}'
   ```
   看 `data.metrics.mirror_map`（实际 源→目标 映射）、`time_scale`、`notes`（警告，比如 IK 腿）。
   映射不对就改 `bone_map`，别硬写。
2. **认领目标**：`claim` 目标骨 × 目标窗口（时间平移时目标窗 = `[dst_start, dst_start+源长−1]`）。
   源只读，不用认领。
3. **写入**（去掉 dry_run，加 expect_version）。常用三种：
   ```
   # 时间平移：左臂 405–450 搬到 700 开始
   {"bones":["left_upper_arm","left_forearm","left_hand"],"src_range":[405,450],"dst_start":700}
   # 镜像到另一侧（同一时间段）
   {"chain":"arm.L","src_range":[405,450],"dst_start":405,"mirror":true}
   # 时间缩放进指定窗口（慢放/快放）
   {"bones":["left_hand"],"src_range":[405,450],"dst_range":[1000,1068]}
   ```
   跨部位：`"bone_map":{"spine_fk":"neck"}`（复制的是相同的关节局部旋转值）。
4. **验收**：把返回的 `data.metrics.verify.args` **原样**传给 `compare_motion`：
   ```
   /home/sb/remote_kit_1.7.1/tools/agent compare_motion '<verify.args 的 JSON>'
   ```
   `err_inner_deg < 0.05` = 到位（四元数骨有 ~0.005–0.03° 的 float32 噪声，正常）。
   自己写 compare_motion 时注意：**a 放目标窗、b 放源窗**（b 会被重采样到 a 的帧上；反过来
   对时间缩放的复制会二次插值，报出假误差）。
5. `list_ops` → `save` → `release`。

## 改位置/改参数（reapply，op_id 不变）

```
/home/sb/remote_kit_1.7.1/tools/agent reapply '{"agent_id":"<ME>","op_id":"<op_id>","overrides":{"dst_start":760}}'
```
也可以改 `frame_range`（= 目标窗，长度不同就自动时间缩放）、`mode`、`space`、`strength`、`blend`。

## 陷阱

- 有效区是目标窗 `[c+blend, d−blend]`（默认 blend=4），两端是过渡。
- 返回的 `params_echo.bones` 是**目标骨**（源骨在 `src_bones`）——effect_check 量的也是目标骨。
- 腿是 IK：复制 `leg.L`（FK 骨）写了看不见（notes 会提示）。复制脚步用
  `bones:["left_foot"]`（= foot_ik.L）+ `channels:"rot+loc"`。
- 拼写错的参数会被**直接拒绝**（比如 `mirorr`），按错误信息改。

## 报告
```
motion_copy <源>@[a,b] → <目标>@[c,d]（mirror=… space=… mode=…）：compare_motion err_inner=X°；op=<id>；看 c–d 帧
```
