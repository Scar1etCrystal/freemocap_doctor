# ai动捕修复2

## 🧑‍💻 User

我使用freemocap，用提前录好的手机视频多摄像头动捕，第一步同步视频，使用音频方式同步，报这个错[2026-06-16T20:04:09.280197] [Δt:0.003003s] [    INFO] [skelly_synchronize.utils.get_video_files] [get_video_files:get_video_file_list():24] [PID:4416:MainProcess TID:14016:Dummy-4 ] 6 videos found in folder
2026-06-16 20:04:09,280 - skelly_synchronize.utils.get_video_files - INFO - 6 videos found in folder
[2026-06-16T20:04:09.310225] [Δt:0.031028s] [   ERROR] [freemocap.gui.qt.workers.synchronize_videos_thread_worker] [synchronize_videos_thread_worker:run():66] [PID:4416:MainProcess TID:14016:Dummy-4 ] Something went wrong while synchronizing videos
Traceback (most recent call last):
  File "F:\mocap\mocap\Lib\site-packages\freemocap\gui\qt\workers\synchronize_videos_thread_worker.py", line 50, in run
    self.output_folder_path = synchronize_videos_from_audio(
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\skelly_synchronize.py", line 135, in synchronize_videos_from_audio
    f"All videos are {check_list_values_are_equal(synchronized_video_framecounts)} frames long"
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\tests\utilities\check_list_values_are_equal.py", line 19, in check_list_values_are_equal
    raise Exception(f"list values are not equal, list is {input_list}")
Exception: list values are not equal, list is [2503, 2503, 2025, 2025, 2025, 2503]
2026-06-16 20:04:09,310 - freemocap.gui.qt.workers.synchronize_videos_thread_worker - ERROR - Something went wrong while synchronizing videos
Traceback (most recent call last):
  File "F:\mocap\mocap\Lib\site-packages\freemocap\gui\qt\workers\synchronize_videos_thread_worker.py", line 50, in run
    self.output_folder_path = synchronize_videos_from_audio(
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\skelly_synchronize.py", line 135, in synchronize_videos_from_audio
    f"All videos are {check_list_values_are_equal(synchronized_video_framecounts)} frames long"
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\tests\utilities\check_list_values_are_equal.py", line 19, in check_list_values_are_equal
    raise Exception(f"list values are not equal, list is {input_list}")
Exception: list values are not equal, list is [2503, 2503, 2025, 2025, 2025, 2503]
[2026-06-16T20:04:09.314228] [Δt:0.005004s] [   ERROR] [freemocap.gui.qt.workers.synchronize_videos_thread_worker] [synchronize_videos_thread_worker:run():67] [PID:4416:MainProcess TID:14016:Dummy-4 ] list values are not equal, list is [2503, 2503, 2025, 2025, 2025, 2503]
Traceback (most recent call last):
  File "F:\mocap\mocap\Lib\site-packages\freemocap\gui\qt\workers\synchronize_videos_thread_worker.py", line 50, in run
    self.output_folder_path = synchronize_videos_from_audio(
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\skelly_synchronize.py", line 135, in synchronize_videos_from_audio
    f"All videos are {check_list_values_are_equal(synchronized_video_framecounts)} frames long"
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\tests\utilities\check_list_values_are_equal.py", line 19, in check_list_values_are_equal
    raise Exception(f"list values are not equal, list is {input_list}")
Exception: list values are not equal, list is [2503, 2503, 2025, 2025, 2025, 2503]
2026-06-16 20:04:09,314 - freemocap.gui.qt.workers.synchronize_videos_thread_worker - ERROR - list values are not equal, list is [2503, 2503, 2025, 2025, 2025, 2503]
Traceback (most recent call last):
  File "F:\mocap\mocap\Lib\site-packages\freemocap\gui\qt\workers\synchronize_videos_thread_worker.py", line 50, in run
    self.output_folder_path = synchronize_videos_from_audio(
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\skelly_synchronize.py", line 135, in synchronize_videos_from_audio
    f"All videos are {check_list_values_are_equal(synchronized_video_framecounts)} frames long"
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\skelly_synchronize\tests\utilities\check_list_values_are_equal.py", line 19, in check_list_values_are_equal
    raise Exception(f"list values are not equal, list is {input_list}")
Exception: list values are not equal, list is [2503, 2503, 2025, 2025, 2025, 2503]
Traceback (most recent call last):
[2026-06-16T20:04:09.321235] [Δt:0.005005s] [    INFO] [freemocap.gui.qt.workers.synchronize_videos_thread_worker] [synchronize_videos_thread_worker:run():72] [PID:4416:MainProcess TID:14016:Dummy-4 ] Synchronizing Videos Complete
  File "F:\mocap\mocap\Lib\site-packages\freemocap\gui\qt\widgets\import_videos_wizard.py", line 228, in _handle_video_synchronization_finished
2026-06-16 20:04:09,321 - freemocap.gui.qt.workers.synchronize_videos_thread_worker - INFO - Synchronizing Videos Complete
    for path in get_video_paths(path_to_video_folder=self.synchronize_videos_thread_worker.output_folder_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\freemocap\utilities\get_video_paths.py", line 8, in get_video_paths
    list_of_video_paths = list(Path(path_to_video_folder).glob("*.mp4")) + list(
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python311\Lib\pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "E:\python311\Lib\pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python311\Lib\pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not NoneType
Traceback (most recent call last):
  File "F:\mocap\mocap\Lib\site-packages\freemocap\gui\qt\widgets\import_videos_wizard.py", line 228, in _handle_video_synchronization_finished
    for path in get_video_paths(path_to_video_folder=self.synchronize_videos_thread_worker.output_folder_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\mocap\mocap\Lib\site-packages\freemocap\utilities\get_video_paths.py", line 8, in get_video_paths
    list_of_video_paths = list(Path(path_to_video_folder).glob("*.mp4")) + list(
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python311\Lib\pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "E:\python311\Lib\pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python311\Lib\pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not NoneType


---
## 🤖 Assistant

这个报错的原因非常明确。我们可以把错误信息拆解开来看：

### 1. 核心报错原因
在日志的中间有一段：
> `Exception: list values are not equal, list is[2503, 2503, 2025, 2025, 2025, 2503]`

Freemocap 的 `skelly_synchronize` 模块在完成音频同步、并试图裁剪视频后，会检查所有输出的视频**总帧数是否完全一致**。但是，你的 6 个视频在同步后的帧数不统一：其中三个是 2503 帧，另外三个是 2025 帧。因为帧数不一致，程序抛出了异常并中断。

### 2. 连锁报错原因
在日志结尾有一段：
> `TypeError: expected str, bytes or os.PathLike object, not NoneType`

这是因为前面的同步步骤失败了，没有生成正确的输出文件夹路径（路径变成了空值 `NoneType`），所以下一步准备读取视频路径时就崩溃了。这只是一个连带错误，**解决上面的帧数问题，这个错误就会自动消失。**

---

### 为什么会出现帧数不一致？如何解决？

手机录制的视频在用于多摄像头动捕时，最容易出现以下两个问题，你可以按照下面的方案逐一解决：

#### 💡 解决方案一：解决手机视频的“可变帧率 (VFR)”问题（最常见原因）
现在的智能手机（尤其是 iPhone 和部分安卓机）默认录制的是**可变帧率 (Variable Frame Rate, VFR)** 的视频。这会导致即便录制时间相同，总帧数也会不一样。Freemocap 严格要求所有视频必须是**恒定帧率 (Constant Frame Rate, CFR)**。
*   **做法**：在将视频导入 Freemocap 之前，先使用软件将所有视频转换为**恒定帧率**（例如强制统一为 30 fps 或 60 fps）。
*   **工具推荐**：
    *   **HandBrake (免费开源)**：导入视频，在“Video”标签页中，将 Framerate (FPS) 手动设定为 `30` 或 `60`，并且**一定要勾选 "Constant Framerate" (恒定帧率)**，然后重新导出。
    *   **FFmpeg**：如果你熟悉命令行，可以通过指令 `ffmpeg -i input.mp4 -r 30 -vsync cfr -c:a copy output.mp4` 来转换。

#### 💡 解决方案二：检查视频的重合时长
音频同步会寻找 6 个视频中声音重合（比如拍手）的地方作为起点，然后向后截取。
*   如果其中有几台手机“提前停止录制”了，导致它们的总时长本来就比其他手机短很多，同步工具截取后的总帧数也会不一致。
*   **做法**：确保 6 段视频录制的是同一段完整的过程，没有哪一段因为断电或误触提前停止。

#### 💡 解决方案三：手动同步与裁剪（终极备用方案）
如果 Freemocap 的自动音频同步一直失败（对于复杂环境噪音或不同型号手机经常发生），强烈建议你使用视频剪辑软件（如剪映、Premiere Pro、DaVinci Resolve）进行手动预处理：
1. 把 6 个视频拖入剪辑软件的不同轨道。
2. 通过波形图或画面（比如打板、拍手的瞬间）把它们完全对齐。
3. 使用裁切工具，把 6 个视频的**开头和结尾切成完全一样齐**（确保总时长一模一样）。
4. 将这 6 个视频按照**相同的帧率（如固定的 30fps 或 60fps）**分别导出。
5. 在 Freemocap 中，直接跳过“同步(Synchronize)”步骤，把这 6 个已经处理好的视频作为“已经同步好的视频”导入使用。

**总结建议**：先去检查一下原始视频是否是手机录制的原片。如果是，先用 HandBrake 把它们全部转换成统一的恒定帧率，再放进 Freemocap 里进行音频同步，大概率就能直接成功了。

---
## 🧑‍💻 User

ffmpeg我有，命令行没问题，写个拖拽执行的bat脚本

---
## 🤖 Assistant

既然你对命令行没问题并且配置好了 FFmpeg，用 `bat` 脚本做批量拖拽处理是最方便的。

这里为你写了一个拖拽执行的 `.bat` 脚本。它会自动把你拖入的所有视频转换为 **恒定帧率 (CFR)**，并且不会压缩掉你的画质（保证动捕精度）。

### 1. 制作 bat 脚本

1. 在电脑上新建一个文本文件（例如 `转恒定帧率.txt`）。
2. 将下面的代码复制粘贴进去：

```bat
@echo off
:: 设置控制台为UTF-8编码，防止中文乱码
chcp 65001 >nul

echo =======================================================
echo     视频转恒定帧率 (CFR) 脚本 - For FreeMoCap
echo =======================================================
echo.

:: 检查是否拖入了文件
if "%~1"=="" (
    echo [错误] 请选中你的视频文件，然后直接拖拽到此 .bat 文件图标上！
    pause
    exit /b
)

:: 【修改帧率】默认转为 30 fps。如果你原视频是 60 fps，请把这里的 30 改成 60
set FPS=30

:loop
:: 如果处理完毕，跳转到结束
if "%~1"=="" goto end

echo 正在处理: "%~nx1"
echo 目标帧率: %FPS% fps
echo.

:: FFmpeg 执行核心命令
:: -c:v libx264: 重新编码视频流修复VFR
:: -preset fast: 较快的编码速度
:: -crf 18     : 极高质量，几乎无损（数值越低画质越好，18是肉眼无损的黄金值）
:: -r %FPS%    : 强制恒定帧率
:: -c:a copy   : 复制音频流（不做重新编码，保证声音和原来一模一样，利于Freemocap对齐）
ffmpeg -i "%~1" -c:v libx264 -preset fast -crf 18 -r %FPS% -c:a copy "%~dpn1_CFR%~x1" -y

echo.
echo -------------------------------------------------------
:: shift命令用于将参数左移，开始处理下一个拖拽进来的文件
shift
goto loop

:end
echo.
echo =======================================================
echo    处理完成！所有视频已生成以 "_CFR" 结尾的新文件。
echo =======================================================
pause
```

3. 保存文件，并将文件后缀名从 `.txt` 修改为 `.bat`（例如改成 `转恒定帧率.bat`）。

---

### 2. 使用方法

1. 选中你用来动捕的 **6 个原始手机视频**。
2. 将这 6 个视频**直接拖拽**到这个 `.bat` 文件的图标上放开。
3. 脚本会弹出一个黑框（CMD 窗口）开始逐个处理。
4. 处理完成后，在你原来的视频文件夹里，会自动生成 6 个带有 `_CFR` 后缀的新视频（例如 `原视频_CFR.mp4`）。

### 3. 后续操作
直接把这 6 个新生成的 `_CFR.mp4` 视频导入到 FreeMoCap 中，再次运行同步。所有视频就会处于绝对一致的帧率环境下，同步后由于时长（总帧数）一致，刚才的 `list values are not equal` 报错就会彻底解决。

---
## 🧑‍💻 User

结果我已经重定向好了，腿部改成了ik，没别的变动，我运行了一些网上的修复脚本，有改善，但还是有很多我叫不出名字的问题，我看网上有人用codex配合Blender api自动修复，能不能基于社群现有经验案例，给我一套ai agent自动修动捕结果的方案？编程啥的我都会。不要调用工具，使用自己的知识或者内部自带的搜索功能

---
## 🤖 Assistant

根据社群里实际跑通的几种思路（blender-mcp、Codex + bpy subprocess、Claude Code 配合 socket bridge 等），我把整套 AI Agent 自动修动捕的方案拆成五层给你。这套架构的核心理念是：**让 LLM 当"导演"，而不是让它自己写正则去搓骨骼**。LLM 负责判断和决策，真正的脏活累活交给一个稳定的 Python 工具箱。

---

## 一、总体架构

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent (Codex/Claude)              │
│        "看指标 → 选工具 → 调参 → 验证 → 下一个"           │
└────────────────────┬────────────────────────────────────┘
                     │ JSON-RPC / MCP / stdio
┌────────────────────▼────────────────────────────────────┐
│              Blender Bridge (常驻 bpy 进程)              │
│  - Analyzer：纯数值指标检测，不依赖视觉                  │
│  - Toolbox：原子修复函数（每个函数只做一件事）           │
│  - State：当前 armature、action、帧范围、IK 链           │
└─────────────────────────────────────────────────────────┘
```

关键决策：**别让 agent 直接写 bpy 代码**。它会幻觉 API、写出破坏性的脚本、改错骨骼名。让它**只能调用你预先定义好的工具函数**，参数是结构化的 JSON。这是社群里现在效果最稳的范式。

---

## 二、Blender Bridge 的两种实现选择

**方案 A：用现成的 blender-mcp（推荐）**
GitHub 上 ahujasid/blender-mcp 已经做好了 MCP server，Claude/Cursor/Codex 都能直接接。你只需要在它的 server 里**注册自己的工具函数**就行。

**方案 B：自己写 socket bridge（更可控）**
在 Blender 内启动一个 modal operator，跑个 TCP socket（比如 9876 端口）。外部 agent 通过 JSON 协议发消息：
```json
{"tool": "analyze_foot_contact", "args": {"foot_bone": "foot.L"}}
```
Blender 内执行后返回结果。Agent 在 Blender 外（独立进程）跑，可以随便用 OpenAI/Anthropic SDK。

我个人更推荐方案 B，因为你对协议完全可控，调试方便，而且 Blender 卡住也不影响 agent。

---

## 三、Analyzer 层（最关键的一层，决定整套系统的天花板）

**核心原则：用纯数值指标量化"哪里出了问题"，绝不让 agent 看图判断。** 视觉判断慢、贵、不准。下面这些指标用 numpy 几行就能算：

| 问题类型 | 检测方法 | 阈值参考 |
|---------|---------|---------|
| 脚滑 | 脚部骨骼水平速度 vs 高度（脚贴地时 v 应≈0） | v_xy > 0.05 m/f 且 z < 0.03 |
| 穿地/浮空 | 脚跟 z 坐标分布直方图 | min(z) < -0.02 或地板 z 抖动 |
| 高频抖动 | 每条 fcurve 的二阶差分能量 / FFT 高频分量占比 | 高频占比 > 30% |
| 关节闪现/popping | 帧间位置差的 outlier 检测（z-score > 4） | 单帧跳变 > 平均的 5 倍 |
| 膝/肘过伸或反折 | 三点夹角（hip-knee-ankle） | 角度 > 178° 或 < 5° |
| 骨骼长度漂移 | 每帧测 head→tail 距离的方差 | std/mean > 1% |
| 漂移累积 | hips 中心在静止段的低频分量 | 低通后位移 > 0.1m |
| 手部丢失帧 | 关键点置信度（freemocap 输出的 npy） | confidence < 0.3 |

把这些写成一组 `analyze_*` 函数，每个都返回**问题帧区间列表 + 严重程度评分**。Agent 拿到的就是结构化的"病历"：

```json
{
  "issues": [
    {"type": "foot_slide", "bone": "foot.L", "frames": [120, 165], "severity": 0.78},
    {"type": "jitter", "bone": "hand.R", "frames": [0, 2025], "severity": 0.45, "freq_band": "8-15Hz"},
    {"type": "knee_hyperextension", "bone": "shin.R", "frames": [340, 360], "max_angle": 181.3}
  ]
}
```

---

## 四、Toolbox（原子修复函数）

每个工具**只做一件事**，参数明确，幂等可回滚。社群常用的一套：

```python
# 平滑类
smooth_butterworth(bones, frames, cutoff_hz=6, order=4)   # 低通滤波，对动捕最友好
smooth_gaussian(bones, frames, sigma=2)
decimate_fcurve(bones, ratio=0.3)                          # 减关键帧

# 脚部类
detect_foot_contacts(foot_bone, height_thresh, vel_thresh) # 返回接触帧
foot_lock(foot_bone, contact_frames)                       # 接触段强制锁住XYZ
floor_align(armature, target_z=0)                          # 整体平移使最低脚=地面

# 关节类
clamp_joint_angle(bone_chain, min_deg, max_deg)            # 防止过伸
fix_bone_length(armature)                                  # 强制每帧骨长=rest骨长（IK效果）
add_ik_with_pole(chain, target, pole, pole_angle)
bake_ik_to_fk() / bake_fk_to_ik()

# 噪声/缺失
gap_fill_interpolate(bone, frames, mode='bezier')
remove_outliers(fcurve, z_thresh=4)                        # 单帧闪现
median_filter(bones, frames, window=5)

# 根运动
extract_root_motion(hips, mode='xy')                       # 把水平位移挪到 root
zero_root_motion(frames)                                   # 原地动画

# 工具类
snapshot()                                                 # 存当前 action 副本，方便回滚
restore(snapshot_id)
diff_metrics(before, after)                                # 修完之后给 agent 看效果
```

写这些函数时一定要做的事：**每个函数前自动 snapshot**，agent 改坏了能 `restore`。这一步能让整套系统从"经常崩"变成"放心试"。

---

## 五、Agent 主循环（Plan-Act-Verify）

伪代码：

```python
state = bridge.call("snapshot")
issues = bridge.call("analyze_all")

for iteration in range(MAX_ITER):
    if not issues or all(i.severity < 0.2 for i in issues):
        break
    
    # 让 LLM 选下一步
    plan = llm.chat(
        system=SYSTEM_PROMPT,        # 解释每个工具的用途和适用场景
        user={
            "current_issues": issues,
            "history": action_log,    # 之前做过啥、效果如何
            "available_tools": TOOL_SCHEMA
        }
    )
    # plan 是一个 tool_call：{"tool": "smooth_butterworth", "args": {...}}
    
    snap = bridge.call("snapshot")
    result = bridge.call(plan.tool, plan.args)
    new_issues = bridge.call("analyze_all")
    
    # 验证：如果整体严重程度上升了，回滚
    if total_severity(new_issues) > total_severity(issues) * 1.05:
        bridge.call("restore", snap)
        action_log.append({"plan": plan, "outcome": "reverted"})
    else:
        issues = new_issues
        action_log.append({"plan": plan, "outcome": "kept", "delta": diff})
```

**这个循环里有几个反复踩坑后总结的经验：**

1. **一次只改一个问题**。让 LLM "全盘考虑、一次性修复"基本必崩。
2. **必须有回滚**。没有 snapshot 的方案做几轮就会把动画搞乱。
3. **修复顺序很重要**，可以在 system prompt 里硬编码这个推荐顺序：
   ① 骨长归一 → ② 高频去抖（butterworth 6Hz）→ ③ 异常值剔除 → ④ 脚部接触检测 + foot lock → ⑤ 关节角度 clamp → ⑥ 地面对齐 → ⑦ 根运动提取
4. **指标要持续上报给 LLM**。它必须看到"我上一步做了 X，severity 从 0.78 降到 0.31"，否则会重复尝试同一种工具。
5. **限制工具调用次数**（比如 30 次），并设计"放弃当前 issue"的退出条件。

---

## 六、System Prompt 关键片段

给你一段可以直接用的核心 prompt 风格：

```
你是动捕清理工程师。你只能通过调用工具操作 Blender，不能写代码。
你看到的"病历"是 analyzer 给出的客观指标，severity 越高越严重。

工作准则：
1. 每次只针对一个 issue，调用一个工具。
2. 优先级：骨长 > 抖动 > 异常值 > 脚部 > 关节角 > 根运动。
3. 调参从保守值开始（如 cutoff=8Hz），观察效果再决定是否更激进。
4. 如果一种工具对同一 bone 连续两次没改善，换思路。
5. butterworth 优于 gaussian，因为对相位影响小。
6. foot_lock 之前一定要先 detect_foot_contacts。
7. 如果 severity 没降反升，下一轮就回滚。
```

---

## 七、几个实战提醒

- **freemocap 的原始 npy 别丢**。里面有每个关键点的 confidence，是 gap_fill 决策的金矿。把它一并加载到 Blender，作为 custom property 挂在骨骼上。
- **重定向之后再修，比修原始动捕再重定向效果差**。原因是重定向会引入新的扭转误差。如果你已经退不回去了，就在你当前 IK rig 上加一层 NLA "修复层"，原数据保留在底层。
- **butterworth 滤波** Blender 4.1+ 的 Graph Editor 内置了，bpy 也有 `bpy.ops.graph.butterworth_smooth`，这是社群验证下来对动捕最友好的滤波器。
- **vision 反馈不是不能用**，而是放在最后做"验收"：渲染 4 个角度的预览，让多模态 LLM 看一眼"还有没有明显问题"，作为 analyzer 的兜底。但**别**让它进主循环。
- **Codex / Claude Code 这类 coding agent**，你可以让它在迭代过程中**临时写新的 analyzer 或 tool**（比如发现某种你没预设的问题模式），把这个能力放在主循环外作为"扩展工具箱"的子流程，这是社群里最近比较火的玩法（self-extending agent）。

---

## 八、最小可行版本（建议你先这么搭）

不用一上来就全套。先做一个能跑通的最小闭环：

1. Blender 内一个 socket server，暴露 3 个工具：`analyze_jitter`、`smooth_butterworth`、`snapshot/restore`。
2. 外部一个 50 行的 Python 脚本，调用 OpenAI/Anthropic API，给它这 3 个工具的 schema。
3. 拿你现在这个动画跑一遍，验证回路通了。
4. 然后按上面 toolbox 的清单一个一个加工具，每加一个就测试。

这样两三天能出第一版可用的，之后就是不停加工具和调 prompt 的事了。

需要的话我可以接着帮你写 socket bridge 的骨架代码，或者其中某一类 analyzer 的具体实现（比如脚部接触检测）。

---
## 🧑‍💻 User

我会编程，会Blender基本操作，但是对骨骼系统只有基本了解，对动画、动捕专业不了解。刚才最近的这轮对话没有经过网络搜索，可能现在已经有更好的方案，请你查证一下（例如，和Blender通讯的最佳方式是不是方案 B：自己写 socket bridge（更可控）？）我使用的agent软件是Hermes，我对这个agent软件还不熟悉。我要用来动捕的模型是deepseekv4 pro，它的逻辑能力过关，但是对动捕、Blender具体细节的世界知识不足。上轮对话建议我先从最简单的开始，让我们开始吧，你自己选择最合适的工作流。补充：我现在的动捕数据是我本人跑出来的，是三个手机摄像头光学动捕，数据修正后（ai说修完再重定向更好），我要重定向到arue式重音teto模型上，重定向过程中我发现我作为男性比teto设定中1.6m更高，二次元模型腿比较长，最后就是我截图中的这个情况：我的骨盆比她还略低一点点，肩膀比她高且宽，手更长，以后我会让很多不同的人参与动捕。我提前看了一下原始数据，偶尔有突然的跳变，最明显问题是脚在浮动，脚尖时不时插进地里；手部动捕不可靠，有时候手掌卡在一个人体关节不可能达到的位置，旋转角不动（就像是跟着人平移）。另外，动捕出来原始数据都是fk，对吧？上次重定向，ai建议我重定向的时候，重定向到mmd模型的脚部ik，其他不变。如果我们对原始数据的脚部fk改好了，到时候重定向还要不要这一步？我想不管有没有重定向的时候改到ik，由于骨长什么的不一样，是不是原始数据不滑步了，重定向以后还会滑？但是上次对话又说重定向之前就修比较好。freemocap的原始数据我全部留着，我对用里面npy置信度当做评判标准的这点尤其感兴趣，不过是不是不应该最开始就加进去？

---
## 🤖 Assistant

先说明一下：我这里**不能实时联网搜索/查证最新 GitHub 或社群帖子**，所以不能假装我刚刚查了网络。但我可以基于截至我知识范围内的 Blender/MCP/LLM-agent/动捕清理实践，给你一个更稳的路线。你的情况我建议**不要一上来做 socket bridge**，也不要一开始就让 Hermes/DeepSeek 直接写 bpy 修动画。我们先做一个可验证、可回滚、可批处理的最小闭环。

---

# 结论先说

## 1. Blender 通讯方式：我现在不建议你第一步用自写 socket bridge

上轮我说「方案 B 自写 socket bridge 更可控」，这话在长期系统里没错，但**不适合你现在第一步**。

你现在的约束是：

- Hermes 你还不熟；
- 使用的模型 DeepSeek v4 pro 逻辑强，但 Blender/动捕细节知识不足；
- 你的问题不是单一 bug，而是动捕清理 + 重定向 + MMD 模型比例差异；
- 你会编程，所以更适合先建立一套**确定性工具链**。

所以我建议当前工作流是：

> **第一阶段：Blender 批处理脚本 + JSON 报告 + 人/Agent 审阅**  
> **第二阶段：Hermes 根据 JSON 报告调用固定工具**  
> **第三阶段：如果 Hermes 支持 MCP，再接 blender-mcp；如果不支持，再考虑 socket bridge**

也就是先别管实时通信，先用：

```bash
blender --background your_scene.blend --python mocap_doctor.py -- config.json
```

这种方式。

它的优点是：

- 稳；
- 可复现；
- 不怕 Blender socket 卡死；
- 不依赖 Hermes 是否支持 MCP；
- 每一步都有输入输出文件；
- 方便你以后批量处理很多人的动捕数据。

---

# 2. 你的问题应该分成两层修，不是「原始修完就万事大吉」

你问得非常关键：

> 原始数据脚不滑，重定向以后还会不会滑？

答案是：**会，可能还会。**

因为脚滑至少有三类来源：

## A. 原始动捕脚滑

比如 FreeMoCap 识别脚尖/脚踝抖动，脚部关键点浮动、插地、跳变。

这应该在**原始数据阶段**修。

## B. 重定向比例导致的脚滑

你本人比 Teto 高，肩宽、臂长、腿长比例都不同。即使源动作脚是稳定的，映射到 Teto 后，因为腿长、骨盆高度、足底位置不同，也可能重新出现脚滑。

这应该在**目标模型阶段**修。

## C. IK/FK 解算导致的脚滑

MMD 模型通常有脚 IK、足 IK、足首、つま先 IK 等结构。你如果把源 FK 直接塞给目标 FK，脚可能不稳定；如果强行接到 IK，又可能膝盖方向、足尖旋转、骨盆高度出问题。

这应该在**重定向阶段和最终 baking 阶段**修。

所以正确策略不是「修原始」或者「修重定向后」二选一，而是：

> **原始阶段修数据质量问题，目标阶段修接触和比例问题。**

推荐流水线：

```text
FreeMoCap 原始数据
    ↓
源骨架清理：
    - 跳变修复
    - 高频抖动平滑
    - 手部异常检测
    - 粗略地面对齐
    ↓
重定向到 Teto/MMD
    ↓
目标模型修复：
    - 脚 IK 锁定
    - 目标地面对齐
    - 骨盆高度调整
    - 膝盖 pole / IK 方向修正
    - 手部二次约束或废弃不可信旋转
    ↓
导出 VMD / FBX / Blender Action
```

---

# 3. FreeMoCap 原始数据是 FK 吗？

严格说，要看你说的是哪一层。

FreeMoCap 的本质输出更接近：

> **每帧人体关键点的 3D 坐标轨迹**

也就是头、肩、肘、腕、髋、膝、踝、脚尖等点在三维空间的位置。

这不是传统动画里的 FK，也不是 IK，而是**点云/骨架关键点运动**。

但是当它进入 Blender rig 后，通常会被转换成：

- 骨骼位置；
- 骨骼旋转；
- 每帧 keyframe；
- 看起来像一套 FK 动画。

所以你可以理解为：

> 原始 FreeMoCap 数据不是 FK；  
> 但导入 Blender 后，多数情况下你看到/编辑的是 FK 风格的骨骼动画。

这也解释了为什么脚容易浮：  
脚的位置是由一堆估计点和骨骼旋转推导出来的，并没有天然的「脚踩在地面上」这个约束。

---

# 4. 脚部 FK 改好了，重定向时还要不要转到 MMD 脚 IK？

我建议：

> **要。最终目标模型上还是应该使用 MMD 的脚 IK 做最后一层脚部稳定。**

原因：

- 源骨架脚不滑 ≠ 目标模型脚不滑；
- Teto 腿长、脚长、骨盆高度跟你本人不同；
- MMD 模型本来就是围绕 IK 脚控来设计的；
- 如果最终要导出 VMD，MMD 的脚 IK 体系更自然；
- 目标模型脚底接触应该由目标模型自己的足底位置决定。

所以推荐：

```text
源数据阶段：
    修脚部异常，但不要过度 foot lock
    目标：让源数据没有明显跳变/噪声

重定向阶段：
    身体主干、手臂可以先 FK
    腿部目标使用 IK 或至少最终 bake 到 IK 控制骨

目标修复阶段：
    对 MMD 脚 IK 做 foot lock / floor lock / toe fix
```

一句话：

> 源骨架修「数据可信度」，目标骨架修「动画接触真实感」。

---

# 5. 关于你截图里的比例问题

你描述的是：

- 你本人男性，实际更高；
- Teto 设定大约 1.6m；
- 二次元模型腿长比例大；
- 你重定向后骨盆比她还略低；
- 肩比她高且宽；
- 手更长。

这说明你目前的重定向方式很可能在使用**源骨架的绝对骨盆高度/肩宽/臂长**，而不是将动作归一化到目标模型比例。

理想情况应该是：

```text
源数据提供：
    - 动作趋势
    - 关节角度
    - 重心变化
    - 接触时机

目标模型决定：
    - 骨盆默认高度
    - 肩宽
    - 手臂长度
    - 腿长
    - 脚底到地面的距离
```

也就是说，重定向时不能简单把你的肩、手、骨盆世界坐标硬塞给 Teto。

尤其是 MMD/二次元模型，比例差异大，应该更偏向：

- 使用源骨架的**旋转/姿态**；
- 根骨位移做尺度归一化；
- 脚接触在目标模型上重新解算。

---

# 6. 手部问题：不要一开始试图完美修手

你说：

> 手部动捕不可靠，有时候手掌卡在一个人体关节不可能达到的位置，旋转角不动，像是跟着人平移。

这是典型的多摄像头/光学识别中手腕、手掌、手指点不稳定问题。

我建议第一版工具里对手采取保守策略：

## 第一阶段只做三件事

1. 检测手腕是否突然跳变；
2. 检测手腕是否超出合理人体范围；
3. 对手腕做平滑和异常帧插值。

暂时不要做：

- 手指修复；
- 掌心朝向修复；
- 复杂 IK；
- 自动自然手势生成。

因为手的问题非常容易越修越假。

对于 MMD 模型，后面可以采用：

```text
源手腕位置可信时：
    用源手腕引导目标手腕 IK/FK

源手腕不可信时：
    退回到上臂/前臂推导的自然手部位置

手指：
    先使用默认半握/放松姿态
```

---

# 7. FreeMoCap npy 置信度：很有价值，但不应该第一步就加

你对 npy 置信度感兴趣是对的。它非常有用，尤其用于判断：

- 哪些帧不要相信；
- 哪些关节需要插值；
- 哪个摄像头视角遮挡严重；
- 手、脚、膝盖是否是低置信度导致的异常。

但我建议**不要第一步就接入置信度**。

原因很简单：  
第一版我们要先把「Blender Action → 数值分析 → JSON 报告 → 修复 → 回滚」这个闭环跑通。

置信度数据涉及：

- FreeMoCap npy 文件路径；
- skeleton 点名；
- Blender bone 名；
- 坐标系转换；
- 时间帧对齐；
- 重定向后的骨骼对应关系。

这些会增加很多复杂度。

所以阶段划分：

## 第 0 版：不用 npy

只分析 Blender 里已有骨骼动画：

- 脚底高度；
- 脚部速度；
- 骨盆高度；
- 手腕跳变；
- 关节角突变；
- 高频抖动。

## 第 1 版：加入 npy 置信度

用于增强判断：

```text
如果手腕跳变 且 confidence 低：
    认为是识别错误，插值/平滑

如果脚尖穿地 但 confidence 高：
    更可能是真实脚部位置 + 地面估计错误

如果脚踝 velocity 高 但 confidence 低：
    不做 foot lock，先插值
```

---

# 8. 我给你选择的最合适工作流

我建议我们现在从这个最小系统开始：

```text
mocap_doctor/
    configs/
        analyze_config.json
    reports/
        report_source.json
    scripts/
        mocap_doctor_blender.py
    actions/
        source_cleaned.blend
```

第一版只做：

1. 自动识别当前场景里的 Armature；
2. 导出骨骼运动统计；
3. 找出最可能的脚骨、手骨、骨盆骨；
4. 检测：
   - 脚尖/脚踝穿地；
   - 脚部浮动；
   - 脚滑；
   - 手腕跳变；
   - 骨盆异常跳变；
5. 输出 JSON 报告；
6. 不自动改动画。

为什么第一版不改？  
因为你现在最大问题不是没有脚本，而是不知道问题叫什么。第一版先让系统帮你把问题命名、定位、量化。

等报告稳定后，再加修复。

---

# 9. 第 0 版 Blender 批处理命令

先采用这种调用方式：

```bat
blender "你的工程.blend" --python "mocap_doctor_blender.py"
```

如果你想后台运行：

```bat
blender --background "你的工程.blend" --python "mocap_doctor_blender.py"
```

后面 Hermes 只需要能执行命令、读取 JSON，就可以参与决策。

---

# 10. 第 0 版脚本目标

我们先不追求智能，只做「验尸报告」。

报告长这样：

```json
{
  "scene": {
    "fps": 30,
    "frame_start": 1,
    "frame_end": 2025
  },
  "armature": "Armature",
  "guessed_bones": {
    "hips": "hips",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_hand": "hand.L",
    "right_hand": "hand.R"
  },
  "issues": [
    {
      "type": "foot_below_floor",
      "bone": "foot.L",
      "frames": [[402, 418], [731, 740]],
      "severity": 0.62
    },
    {
      "type": "foot_slide",
      "bone": "foot.R",
      "frames": [[120, 168]],
      "severity": 0.74
    },
    {
      "type": "hand_jump",
      "bone": "hand.R",
      "frames": [[880, 881]],
      "severity": 0.91
    }
  ]
}
```

这个报告以后就是 Hermes/DeepSeek 的输入。

---

# 11. 第一轮要检测哪些问题？

结合你描述，我建议第一版只检测这几个。

## A. 脚穿地

检测脚骨世界坐标 Z 值是否低于估计地面。

关键点：

```text
floor_z = 所有脚部骨骼 Z 值的 1% 分位数
```

不要直接用 `min(z)`，因为 min 可能是异常跳变。

然后：

```text
if foot_z < floor_z - tolerance:
    认为穿地
```

## B. 脚浮动

脚部在应该接触地面时，Z 值上下漂。

粗略判断：

```text
脚高度接近地面
且垂直速度小
且一段时间内水平速度不大
但 z 抖动明显
```

## C. 脚滑

接触地面时，脚的水平位置还在移动：

```text
foot_z 接近 floor_z
且 foot vertical speed 小
但 foot xy speed 大
```

## D. 手腕跳变

```text
hand position 当前帧到上一帧距离 > median_speed * 5
```

或者绝对阈值：

```text
单帧移动超过 20 cm
```

## E. 骨盆跳变

同理检测 hips。

---

# 12. 后续修复顺序

等报告跑通后，我建议修复顺序是：

```text
1. 修跳变
2. 平滑高频抖动
3. 粗地面对齐
4. 源骨架脚部接触标记
5. 重定向到 Teto
6. 目标模型脚 IK 锁定
7. 目标模型骨盆高度修正
8. 手腕异常处理
```

不要先做 foot lock。  
因为如果源数据有跳变，foot lock 会把错误位置锁死。

---

# 13. Hermes 应该怎么参与？

因为 Hermes 你还不熟，我建议不要一开始让它直接控制 Blender。

让 Hermes 做这几件事：

## 阶段 1：读报告，生成修复计划

输入：

```json
report_source.json
```

输出：

```json
repair_plan.json
```

例如：

```json
{
  "steps": [
    {
      "tool": "remove_position_outliers",
      "target": ["hand.R", "hand.L"],
      "frames": [[880, 881]],
      "strength": 0.8
    },
    {
      "tool": "smooth_bone_position",
      "target": ["foot.L", "foot.R"],
      "frames": [[1, 2025]],
      "method": "butterworth",
      "cutoff_hz": 6
    }
  ]
}
```

## 阶段 2：Blender 脚本读取 repair_plan.json 执行

这样 Hermes 不需要懂 bpy API，只需要根据报告选工具。

## 阶段 3：重新分析

输出：

```json
report_after.json
```

Hermes 比较前后 severity。

---

# 14. 当前不建议让 DeepSeek 直接做的事

不要让它直接：

- 改骨骼层级；
- 自动重命名骨骼；
- 给 MMD 模型乱加约束；
- 在没有 snapshot 的情况下 bake action；
- 同时修脚、手、骨盆、重定向；
- 写复杂 IK 解算器；
- 大范围改 rest pose。

这些都很容易炸。

---

# 15. 关于「修完再重定向更好」这句话的精确版本

更准确地说应该是：

> **识别错误、跳变、噪声，应该在重定向前修。**  
> **比例差异、脚底接触、IK 锁定，应该在重定向后修。**

所以不是单纯「修完再重定向」，而是两段式：

```text
源动作清理：
    清理数据质量

目标动作清理：
    清理角色适配
```

这点对你以后让很多不同的人参与动捕非常重要。  
不同人的身高、臂长、肩宽都不一样，但 Teto 模型是固定的，所以必须有一层**标准化/归一化**。

---

# 16. 你这类项目最终应该形成的模板

以后每个人的动捕都走同一套：

```text
person_A_freemocap/
    raw_videos/
    freemocap_output/
    source_action.blend
    source_report.json
    source_cleaned.blend
    retarget_to_teto.blend
    target_report.json
    target_cleaned.blend
    final.vmd
```

并记录每个人的参数：

```json
{
  "performer": "person_A",
  "height_cm": 178,
  "source_scale": 1.0,
  "target_model": "Kasane_Teto_Arue",
  "target_height_cm": 160,
  "retarget_scale_mode": "leg_length_normalized",
  "foot_lock": true,
  "hand_confidence_threshold": 0.35
}
```

---

# 17. 我建议我们下一步具体做什么

下一步不要直接修动画。  
我们先写第一个脚本：

> **mocap_doctor_blender.py：分析当前 Blender 文件里的骨骼动画，输出 report.json。**

它先不需要懂 FreeMoCap npy，也不需要懂 MMD。  
只需要能在你当前 `.blend` 文件中：

- 找到 armature；
- 找到可能的 hips/feet/hands；
- 采样每帧世界坐标；
- 检测脚和手的问题；
- 输出 JSON。

这一步跑通后，你把 report 的结构贴出来，我们再决定第一个自动修复工具是：

1. 手腕跳变插值；
2. 脚部平滑；
3. 地面对齐；
4. foot contact 检测。

我建议第一个修复工具做：

> **remove_outlier_jumps：修单帧/少数帧跳变**

因为这是最安全、收益最大、最不容易破坏动作的修复。

---

# 18. 当前路线总结

你现在这个项目不要一开始追求「AI 自动修所有动捕」。

先做：

```text
Blender 动作
    ↓
分析脚本
    ↓
JSON 问题报告
    ↓
Hermes/DeepSeek 读报告
    ↓
生成修复计划
    ↓
Blender 执行固定工具
    ↓
重新分析
    ↓
确认改善
```

通信方式先用：

```text
命令行 + JSON 文件
```

不是 socket，也不是直接 MCP。  
等这个跑通后，如果 Hermes 支持 MCP，我们再升级到 MCP；如果不支持，再考虑 socket bridge。

这套方式最适合你现在的情况：你会编程，但动捕专业知识正在补；你的 agent 逻辑强但 Blender 世界知识不足；你的任务需要长期批处理很多人的动作，而不是只救一条动画。

---
## 🧑‍💻 User

最开始说也就是先别管实时通信，先用：
Bash
blender --background your_scene.blend --python mocap_doctor.py -- config.json
这个意思是后台启动Blender并带着config执行这个doctor脚本，对吧？

对于5.比例问题，第一，我重定向用的是ARP，之前的ai和我说，保持手脚平行就行，arp是按角度来重定向的（真的假的？）arp里面确实有个auto scale，我按了一下，缩小以后，我的腿比她短了不少，感觉这样也会带来问题，我就干脆没有auto scale。另外，我不清楚你在这一点里面说的重定向方式是什么什么的是什么意思。归一化我看懂了，先把不同的人归一了，得到“效果好的源数据”，再重定向，这样我这时候修的就都只有“重定向带来的问题”了，而不用再第二阶段也处理第一阶段带来的问题，是不是。

对于手，我捕的是舞蹈视频，没什么手部动作，这一步我们可以用“敷衍过去”的做法，看上去没问题就行。
我的Hermes在wsl里面，发行版Ubuntu2204LTS。我会linux基本操作，但是没用过wsl，我也没写过Blender插件，只是会python，你在这方面得教的细一点，我现在都不知道怎么把文件从Windows放进wsl。
你的其他建议我全部采纳，让我们开始，注意聊几轮后，还得不能忘了把你自己说的这些建议都考虑进去。我确定现在你有联网搜索工具了，也可以搜索看看要不要根据最新动态改方案，记得把修改告诉我

---
## 🤖 Assistant

对，你理解得对：

```bash
blender --background your_scene.blend --python mocap_doctor.py -- config.json
```

意思就是：

> **不开 Blender 图形界面，后台载入 `your_scene.blend`，执行 `mocap_doctor.py`，并把 `config.json` 作为脚本自己的参数传进去。**

其中：

- `--background` / `-b`：后台模式，不打开 UI。Blender 官方文档说明它用于无界面运行，例如渲染或脚本处理 [1]。
- `--python xxx.py`：运行指定 Python 脚本 [1]。
- 最后的单独 `--`：表示 Blender 自己的参数到此结束，后面的参数原样传给 Python 脚本，可以在脚本里通过 `sys.argv` 读取 [1]。
- 参数顺序很重要，Blender 文档明确说命令行参数是按顺序执行的，所以我们会固定使用比较安全的顺序 [1]。

我刚才也按你要求查了一下：这轮搜索结果对 **Blender 命令行参数** 有有效资料；对 **ARP Auto Scale** 和 **Hermes + Blender** 没搜到足够可靠的新资料。所以我对方案做一个明确修正：

> **当前不升级到 MCP / socket bridge。**  
> **第一阶段采用：WSL/Hermes 调用 Windows Blender → Blender 执行 Python → 输出 JSON 报告。**

这是现在对你最稳的工作流。

---

# 一、我们现在采用的工作流

你的环境是：

```text
Hermes：WSL Ubuntu 22.04
Blender：大概率在 Windows
FreeMoCap / ARP / MMD 模型：Windows 侧工程
```

所以我们先用这个结构：

```text
Windows 磁盘里放工程文件
    ↓
WSL/Hermes 调用 Windows Blender.exe
    ↓
Blender 运行 mocap_doctor_analyze.py
    ↓
输出 report_source.json
    ↓
Hermes / DeepSeek 读 report_source.json
    ↓
下一轮再生成 repair_plan.json
```

也就是说：

```text
第一步只分析，不修复。
```

---

# 二、关于 ARP、Auto Scale、比例归一化

## 1. 「ARP 是按角度重定向」这句话半真半假

更准确地说：

> ARP 重定向主要依赖源骨架和目标骨架的姿态/骨骼映射，把源动作的骨骼旋转关系转移到目标骨架上，但它不是一个完全无视比例的“纯角度系统”。

所以之前 AI 说的：

> “保持手脚平行就行，ARP 是按角度重定向的。”

这句话太简化了。

T-pose / A-pose 对齐、手脚方向平行确实很重要，因为源骨架和目标骨架初始姿势不一致会导致旋转偏移。但是比例问题不会因此自动消失。尤其是：

- 你本人比 Teto 高；
- 你的肩更宽；
- 你的臂更长；
- Teto 腿比例更二次元；
- MMD 模型脚 IK 体系和普通 FK rig 不一样。

这些都会导致重定向后出现：

- 骨盆高度不自然；
- 脚踩不住；
- 手伸太远或太短；
- 膝盖方向怪；
- 肩膀过宽；
- 胳膊看起来拉扯。

## 2. ARP 的 Auto Scale 不一定应该开

你按了 Auto Scale 以后，发现你的腿比她短不少，这个直觉是对的：  
**Auto Scale 可能解决“整体单位/整体高度差”，但不一定解决“人体比例差”。**

我建议你把 Auto Scale 分成两类理解：

### 情况 A：单位不一致

比如源骨架 1 单位 = 1 米，目标骨架 1 单位 = 10 厘米。  
这种情况需要 scale。

### 情况 B：人体比例不一致

比如：

```text
你：真实男性比例
Teto：二次元长腿、小躯干、窄腰、特定肩宽
```

这种情况不能简单整体缩放。整体缩放以后可能出现：

```text
身高看似对了
但腿长、骨盆、手长、肩宽仍然不对
```

所以你不盲目开 Auto Scale 是合理的。

我的建议是：

> **ARP 重定向时不要指望 Auto Scale 自动解决风格化模型比例。**  
> **Auto Scale 只在明显整体尺寸不一致时用。**  
> **Teto 这种 MMD/二次元模型，最终脚底接触和骨盆高度要在目标模型上二次修。**

---

# 三、你对「归一化」的理解基本正确

你问：

> 先把不同的人归一了，得到“效果好的源数据”，再重定向，这样我这时候修的就都只有“重定向带来的问题”了，而不用再第二阶段也处理第一阶段带来的问题，是不是？

是的，方向对。

但我建议精确表述成：

```text
源数据阶段：
    修识别错误、跳变、抖动、明显不可能的人体动作。
    得到一个“干净的表演动作”。

目标模型阶段：
    修比例差、脚 IK、骨盆高度、MMD 模型适配。
    得到一个“适合 Teto 的动画”。
```

也就是说：

> 第一阶段修“数据质量”。  
> 第二阶段修“角色适配”。

这个划分非常重要，因为以后你让很多不同的人来动捕，每个人身高、肩宽、腿长都不一样。  
如果第一阶段不归一，第二阶段会永远混着处理两类问题，难以自动化。

---

# 四、关于手部：我们先敷衍过去

你说是舞蹈视频，没什么手部动作。那我们第一版对手部采用低成本策略：

```text
手腕位置：
    检测明显跳变
    异常帧插值
    轻度平滑

手掌旋转：
    暂时不强修
    可在目标模型上使用默认手腕姿态或继承前臂方向

手指：
    暂时不处理
    后面用固定的自然张开 / 半握姿态
```

也就是：

> 手不要追求物理精确，看起来别抽风就行。

这很适合你现在的舞蹈动捕。

---

# 五、先教你 WSL 怎么访问 Windows 文件

你现在 Hermes 在 WSL 里，Windows 文件会挂载在：

```bash
/mnt/c
/mnt/d
/mnt/e
/mnt/f
```

比如你的 Windows 路径：

```text
F:\mocap\project1
```

在 WSL 里就是：

```bash
/mnt/f/mocap/project1
```

如果是：

```text
C:\Users\你的用户名\Desktop
```

在 WSL 里就是：

```bash
/mnt/c/Users/你的用户名/Desktop
```

## 1. 在 WSL 里查看 Windows 磁盘

打开 Ubuntu 终端：

```bash
ls /mnt
```

你应该能看到：

```text
c  d  e  f
```

进入 F 盘：

```bash
cd /mnt/f
ls
```

## 2. 从 Windows 文件管理器访问 WSL

在 Windows 资源管理器地址栏输入：

```text
\\wsl$
```

然后进入你的 Ubuntu 发行版，例如：

```text
\\wsl$\Ubuntu-22.04
```

不过我们的项目建议放在 Windows 磁盘里，比如：

```text
F:\mocap_ai_doctor
```

原因是 Blender、FreeMoCap、模型文件都在 Windows 侧，少走权限和路径坑。

---

# 六、现在创建项目目录

假设我们用 Windows 的 F 盘。

在 WSL 里执行：

```bash
mkdir -p /mnt/f/mocap_ai_doctor/scripts
mkdir -p /mnt/f/mocap_ai_doctor/configs
mkdir -p /mnt/f/mocap_ai_doctor/reports
mkdir -p /mnt/f/mocap_ai_doctor/blends
```

目录结构：

```text
F:\mocap_ai_doctor
    scripts
        mocap_doctor_analyze.py
    configs
        analyze_source.json
    reports
        report_source.json
    blends
        your_scene.blend
```

你可以把你当前的 `.blend` 文件复制到：

```text
F:\mocap_ai_doctor\blends\
```

比如叫：

```text
source_mocap.blend
```

---

# 七、创建配置文件 analyze_source.json

在 WSL 里执行：

```bash
nano /mnt/f/mocap_ai_doctor/configs/analyze_source.json
```

粘贴：

```json
{
  "mode": "analyze",
  "armature_name": "",
  "frame_start": null,
  "frame_end": null,
  "output_report": "F:/mocap_ai_doctor/reports/report_source.json",

  "bone_hints": {
    "hips": [],
    "left_foot": [],
    "right_foot": [],
    "left_hand": [],
    "right_hand": []
  },

  "thresholds": {
    "floor_tolerance_m": 0.03,
    "foot_contact_height_m": 0.06,
    "foot_slide_speed_m_per_frame": 0.025,
    "hand_jump_m_per_frame": 0.20,
    "hips_jump_m_per_frame": 0.25
  }
}
```

保存：

```text
Ctrl + O
Enter
Ctrl + X
```

先让 bone_hints 为空，脚本会自动猜。  
如果猜错，下一轮我们再手动填骨骼名。

---

# 八、创建第 0 版分析脚本

执行：

```bash
nano /mnt/f/mocap_ai_doctor/scripts/mocap_doctor_analyze.py
```

粘贴下面代码：

```python
import bpy
import sys
import json
import math
import statistics
from pathlib import Path
from mathutils import Vector


def get_args_after_double_dash():
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        return sys.argv[idx + 1:]
    return []


def load_config():
    args = get_args_after_double_dash()
    if not args:
        raise RuntimeError("Missing config path after --")
    config_path = Path(args[0])
    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_armature(config):
    name = config.get("armature_name") or ""
    if name and name in bpy.data.objects:
        obj = bpy.data.objects[name]
        if obj.type == "ARMATURE":
            return obj

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("No armature found in scene")

    # 优先找有 action 的 armature
    with_action = []
    for obj in armatures:
        if obj.animation_data and obj.animation_data.action:
            with_action.append(obj)

    if with_action:
        return with_action[0]

    return armatures[0]


def norm_name(s):
    return s.lower().replace("_", "").replace("-", "").replace(".", "")


def guess_bone(armature, candidates):
    bones = list(armature.pose.bones)
    names = [b.name for b in bones]
    normalized = [(name, norm_name(name)) for name in names]

    # 先完全/包含匹配
    for cand in candidates:
        nc = norm_name(cand)
        for original, nn in normalized:
            if nc == nn or nc in nn:
                return original

    return None


def guess_bones(armature, config):
    hints = config.get("bone_hints", {})

    def use_hint_or_guess(key, candidates):
        for h in hints.get(key, []):
            if h in armature.pose.bones:
                return h
        return guess_bone(armature, candidates)

    guessed = {
        "hips": use_hint_or_guess("hips", [
            "hips", "hip", "pelvis", "root", "センター", "center", "groove"
        ]),
        "left_foot": use_hint_or_guess("left_foot", [
            "foot.L", "l_foot", "leftfoot", "ankle.L", "l ankle",
            "左足首", "左足", "足首.L"
        ]),
        "right_foot": use_hint_or_guess("right_foot", [
            "foot.R", "r_foot", "rightfoot", "ankle.R", "r ankle",
            "右足首", "右足", "足首.R"
        ]),
        "left_hand": use_hint_or_guess("left_hand", [
            "hand.L", "l_hand", "lefthand", "wrist.L", "l wrist",
            "左手首", "左手"
        ]),
        "right_hand": use_hint_or_guess("right_hand", [
            "hand.R", "r_hand", "righthand", "wrist.R", "r wrist",
            "右手首", "右手"
        ])
    }

    return guessed


def get_frame_range(config):
    scene = bpy.context.scene
    fs = config.get("frame_start")
    fe = config.get("frame_end")

    if fs is None:
        fs = scene.frame_start
    if fe is None:
        fe = scene.frame_end

    return int(fs), int(fe)


def pose_bone_world_location(armature, bone_name):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None
    mat = armature.matrix_world @ pb.matrix
    return mat.translation.copy()


def sample_bone_positions(armature, bone_names, frame_start, frame_end):
    result = {name: [] for name in bone_names if name}

    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        depsgraph.update()

        for name in result.keys():
            loc = pose_bone_world_location(armature, name)
            if loc is None:
                result[name].append(None)
            else:
                result[name].append([float(loc.x), float(loc.y), float(loc.z)])

    return result


def vec_dist(a, b, xy_only=False):
    if a is None or b is None:
        return None
    if xy_only:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.sqrt(dx * dx + dy * dy)
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    dz = a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)


def ranges_from_frames(frames):
    if not frames:
        return []
    frames = sorted(set(frames))
    ranges = []
    start = prev = frames[0]
    for f in frames[1:]:
        if f == prev + 1:
            prev = f
        else:
            ranges.append([start, prev])
            start = prev = f
    ranges.append([start, prev])
    return ranges


def detect_below_floor(samples, foot_bones, frame_start, thresholds):
    z_values = []
    for bone in foot_bones:
        if bone and bone in samples:
            for p in samples[bone]:
                if p is not None:
                    z_values.append(p[2])

    floor_z = percentile(z_values, 0.01)
    if floor_z is None:
        floor_z = 0.0

    tol = thresholds.get("floor_tolerance_m", 0.03)

    issues = []
    for bone in foot_bones:
        if not bone or bone not in samples:
            continue
        bad_frames = []
        max_depth = 0.0
        for i, p in enumerate(samples[bone]):
            if p is None:
                continue
            frame = frame_start + i
            depth = floor_z - p[2]
            if depth > tol:
                bad_frames.append(frame)
                max_depth = max(max_depth, depth)

        if bad_frames:
            severity = min(1.0, max_depth / 0.15)
            issues.append({
                "type": "foot_below_floor",
                "bone": bone,
                "frames": ranges_from_frames(bad_frames),
                "severity": round(severity, 4),
                "max_depth_m": round(max_depth, 4),
                "floor_z_estimate": round(floor_z, 4)
            })

    return floor_z, issues


def detect_foot_slide(samples, foot_bones, frame_start, floor_z, thresholds):
    contact_h = thresholds.get("foot_contact_height_m", 0.06)
    slide_speed = thresholds.get("foot_slide_speed_m_per_frame", 0.025)

    issues = []

    for bone in foot_bones:
        if not bone or bone not in samples:
            continue

        arr = samples[bone]
        bad_frames = []
        speeds = []

        for i in range(1, len(arr)):
            prev = arr[i - 1]
            cur = arr[i]
            if prev is None or cur is None:
                continue

            frame = frame_start + i
            z = cur[2]
            dz = abs(cur[2] - prev[2])
            xy_speed = vec_dist(cur, prev, xy_only=True)

            # 接近地面，垂直变化小，但水平还在动：认为疑似脚滑
            if z <= floor_z + contact_h and dz < contact_h * 0.5 and xy_speed > slide_speed:
                bad_frames.append(frame)
                speeds.append(xy_speed)

        if bad_frames:
            max_speed = max(speeds) if speeds else 0.0
            severity = min(1.0, max_speed / 0.12)
            issues.append({
                "type": "foot_slide_suspected",
                "bone": bone,
                "frames": ranges_from_frames(bad_frames),
                "severity": round(severity, 4),
                "max_xy_speed_m_per_frame": round(max_speed, 4)
            })

    return issues


def detect_jump(samples, bone, frame_start, threshold, issue_type):
    if not bone or bone not in samples:
        return []

    arr = samples[bone]
    bad_frames = []
    speeds = []

    for i in range(1, len(arr)):
        d = vec_dist(arr[i], arr[i - 1], xy_only=False)
        if d is None:
            continue
        frame = frame_start + i
        if d > threshold:
            bad_frames.append(frame)
            speeds.append(d)

    if not bad_frames:
        return []

    max_speed = max(speeds)
    severity = min(1.0, max_speed / (threshold * 3.0))

    return [{
        "type": issue_type,
        "bone": bone,
        "frames": ranges_from_frames(bad_frames),
        "severity": round(severity, 4),
        "max_speed_m_per_frame": round(max_speed, 4)
    }]


def main():
    config = load_config()
    scene = bpy.context.scene

    armature = find_armature(config)
    guessed = guess_bones(armature, config)

    frame_start, frame_end = get_frame_range(config)

    bone_names = [
        guessed.get("hips"),
        guessed.get("left_foot"),
        guessed.get("right_foot"),
        guessed.get("left_hand"),
        guessed.get("right_hand"),
    ]
    bone_names = [b for b in bone_names if b]

    samples = sample_bone_positions(armature, bone_names, frame_start, frame_end)

    thresholds = config.get("thresholds", {})

    issues = []

    foot_bones = [guessed.get("left_foot"), guessed.get("right_foot")]
    floor_z, below_floor_issues = detect_below_floor(
        samples, foot_bones, frame_start, thresholds
    )
    issues.extend(below_floor_issues)

    issues.extend(detect_foot_slide(
        samples, foot_bones, frame_start, floor_z, thresholds
    ))

    issues.extend(detect_jump(
        samples,
        guessed.get("left_hand"),
        frame_start,
        thresholds.get("hand_jump_m_per_frame", 0.20),
        "hand_jump"
    ))

    issues.extend(detect_jump(
        samples,
        guessed.get("right_hand"),
        frame_start,
        thresholds.get("hand_jump_m_per_frame", 0.20),
        "hand_jump"
    ))

    issues.extend(detect_jump(
        samples,
        guessed.get("hips"),
        frame_start,
        thresholds.get("hips_jump_m_per_frame", 0.25),
        "hips_jump"
    ))

    report = {
        "schema_version": "mocap_doctor_report_v0",
        "scene": {
            "name": scene.name,
            "fps": scene.render.fps,
            "frame_start": frame_start,
            "frame_end": frame_end
        },
        "armature": {
            "name": armature.name,
            "action": armature.animation_data.action.name if armature.animation_data and armature.animation_data.action else None
        },
        "guessed_bones": guessed,
        "floor": {
            "z_estimate": round(floor_z, 5)
        },
        "issues": issues,
        "notes": [
            "This is analysis-only. No animation data was modified.",
            "If guessed_bones are wrong, fill bone_hints in config and run again."
        ]
    }

    out = Path(config["output_report"])
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[mocap_doctor] Report written to: {out}")


if __name__ == "__main__":
    main()
```

保存退出。

---

# 九、从 WSL 调用 Windows Blender

你需要先知道 Blender 安装路径。常见路径是：

```text
C:\Program Files\Blender Foundation\Blender 4.2\blender.exe
```

或：

```text
C:\Program Files\Blender Foundation\Blender 4.3\blender.exe
```

在 WSL 里对应路径是：

```bash
/mnt/c/Program\ Files/Blender\ Foundation/Blender\ 4.2/blender.exe
```

你可以试：

```bash
ls "/mnt/c/Program Files/Blender Foundation"
```

看看里面有什么版本。

假设你的 Blender 是 4.2，运行：

```bash
"/mnt/c/Program Files/Blender Foundation/Blender 4.2/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_mocap.blend" \
  --python "F:/mocap_ai_doctor/scripts/mocap_doctor_analyze.py" \
  --python-exit-code 1 \
  -- "F:/mocap_ai_doctor/configs/analyze_source.json"
```

注意这里我给 Windows Blender 传的是：

```text
F:/mocap_ai_doctor/...
```

而不是：

```text
/mnt/f/mocap_ai_doctor/...
```

因为实际运行的是 Windows 的 `blender.exe`，它更稳定地识别 Windows 路径。

---

# 十、推荐做一个 WSL 启动脚本

创建：

```bash
nano /mnt/f/mocap_ai_doctor/run_analyze_source.sh
```

粘贴：

```bash
#!/usr/bin/env bash
set -e

BLENDER="/mnt/c/Program Files/Blender Foundation/Blender 4.2/blender.exe"

BLEND="F:/mocap_ai_doctor/blends/source_mocap.blend"
SCRIPT="F:/mocap_ai_doctor/scripts/mocap_doctor_analyze.py"
CONFIG="F:/mocap_ai_doctor/configs/analyze_source.json"

"$BLENDER" \
  --background "$BLEND" \
  --python "$SCRIPT" \
  --python-exit-code 1 \
  -- "$CONFIG"
```

保存后：

```bash
chmod +x /mnt/f/mocap_ai_doctor/run_analyze_source.sh
```

运行：

```bash
/mnt/f/mocap_ai_doctor/run_analyze_source.sh
```

如果 Blender 版本不是 4.2，把这一行改成你的实际路径：

```bash
BLENDER="/mnt/c/Program Files/Blender Foundation/Blender 4.2/blender.exe"
```

---

# 十一、运行成功后看报告

执行：

```bash
cat /mnt/f/mocap_ai_doctor/reports/report_source.json
```

或者用 Windows 打开：

```text
F:\mocap_ai_doctor\reports\report_source.json
```

你会看到类似：

```json
{
  "schema_version": "mocap_doctor_report_v0",
  "scene": {
    "fps": 30,
    "frame_start": 1,
    "frame_end": 2025
  },
  "armature": {
    "name": "Armature",
    "action": "freemocap_action"
  },
  "guessed_bones": {
    "hips": "hips",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_hand": "hand.L",
    "right_hand": "hand.R"
  },
  "issues": [
    {
      "type": "foot_below_floor",
      "bone": "foot.L",
      "frames": [[120, 135]],
      "severity": 0.4
    }
  ]
}
```

---

# 十二、如果骨骼名猜错怎么办

这是很可能发生的，尤其是：

- FreeMoCap 骨架；
- ARP 骨架；
- MMD 日文骨骼；
- Rigify / 自定义 rig。

如果报告里：

```json
"guessed_bones": {
  "left_foot": null
}
```

或者猜到了错误骨骼，你就打开 Blender 查看真实骨骼名，然后填到 config：

```json
"bone_hints": {
  "hips": ["真实骨盆骨名"],
  "left_foot": ["真实左脚骨名"],
  "right_foot": ["真实右脚骨名"],
  "left_hand": ["真实左手骨名"],
  "right_hand": ["真实右手骨名"]
}
```

然后重新运行：

```bash
/mnt/f/mocap_ai_doctor/run_analyze_source.sh
```

---

# 十三、下一步我们不立刻修，先确认报告质量

你这轮先做三件事：

1. 把 `.blend` 放到：

```text
F:\mocap_ai_doctor\blends\source_mocap.blend
```

2. 跑：

```bash
/mnt/f/mocap_ai_doctor/run_analyze_source.sh
```

3. 把生成的：

```text
F:\mocap_ai_doctor\reports\report_source.json
```

里面的内容贴给我。

我会根据报告判断：

- 骨骼猜得对不对；
- 脚滑检测阈值是否太敏感；
- 地面估计是否靠谱；
- 手部跳变是否符合你肉眼看到的问题；
- 下一步先做哪个修复工具。

---

# 十四、我们暂定的长期方案，我会继续按这个记

为了防止后面聊几轮忘掉，这里把项目决策固定下来：

```text
通信方式：
    先不用 socket，不用 MCP。
    使用 WSL/Hermes 调用 Windows Blender 命令行。
    Blender 输出 JSON，Hermes/DeepSeek 读 JSON。

阶段 0：
    只分析，不修改动画。

阶段 1：
    修源数据：
        - 跳变
        - 抖动
        - 手腕异常
        - 粗略脚部异常
    暂时不接 FreeMoCap npy 置信度。

阶段 2：
    加入 FreeMoCap npy 置信度。
    用 confidence 判断哪些帧可信。

阶段 3：
    ARP 重定向到 Teto。
    Auto Scale 不盲目开，只在整体尺度明显错时用。

阶段 4：
    修目标模型：
        - MMD 脚 IK 锁定
        - 地面对齐
        - 骨盆高度
        - 膝盖方向
        - 手部视觉敷衍修复

原则：
    源数据阶段修数据质量。
    目标模型阶段修角色适配。
```

你先跑第 0 版分析。报告贴出来后，我们再写第一个真正修改动画的工具：  
**remove_outlier_jumps：修手/脚/骨盆的突然跳变。**
[1] [Command Line Arguments - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)

[2] [Help needed with 2.93 cmd = [ ] arguments in script function](https://blenderartists.org/t/help-needed-with-2-93-cmd-arguments-in-script-function/1321496)

[1] [Command Line Arguments - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)

[2] [Help needed with 2.93 cmd = [ ] arguments in script function](https://blenderartists.org/t/help-needed-with-2-93-cmd-arguments-in-script-function/1321496)

[1] [Command Line Arguments - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)

[2] [Help needed with 2.93 cmd = [ ] arguments in script function](https://blenderartists.org/t/help-needed-with-2-93-cmd-arguments-in-script-function/1321496)

[1] [Command Line Arguments - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)

[2] [Help needed with 2.93 cmd = [ ] arguments in script function](https://blenderartists.org/t/help-needed-with-2-93-cmd-arguments-in-script-function/1321496)
---
## 🧑‍💻 User

freemocap的骨骼是固定的，我要用的mmd模型也就那一个，其实你不用猜，如果需要，可以教我怎么导出这两个模型的骨骼列表，不过我看着感觉你都猜对了。

---
## 🤖 Assistant

对，这份报告很有用，说明第 0 版分析已经跑通了。先解释结果，然后我们开始做第一个**安全修复工具**。

另外先澄清一句：你说“我确定现在你有联网搜索工具了”，但我当前这个对话环境里**没有暴露网页搜索工具**，只有图像生成工具，所以我不能实际联网查资料。后面如果环境给我搜索工具，我会明确告诉你“我查了什么、改了什么方案”。现在继续按我们已经确定的稳妥路线走。

---

# 1. 你的 report 说明了什么

你的报告：

```json
"armature": {
  "name": "import_synchronized_videos_rig",
  "action": null
}
```

这里有个重要点：  
`action: null` 说明这个 armature 本身没有直接挂一个普通 Action，或者动画不是以我们最希望的方式存储在 armature action 上。

但脚本仍然采样到了骨骼位置，说明 Blender 当前帧下骨骼确实在动，可能来自：

- 约束；
- 驱动；
- 子对象；
- NLA；
- FreeMoCap 插件生成的特殊结构；
- 或者动画在别的对象上间接控制这个 rig。

所以接下来修复前，我们要做一个关键动作：

> **先把当前看到的运动“视觉烘焙”为一个普通 Action。**

也就是把每一帧当前骨骼实际姿态 bake 成关键帧。之后我们再修这个 baked action。

这很重要，否则我们后面改 fcurve 时可能没东西可改。

---

# 2. 当前检测结果怎么看

## 骨骼猜测基本正确

```json
"hips": "pelvis",
"left_foot": "foot.L",
"right_foot": "foot.R",
"left_hand": "hand.L",
"right_hand": "hand.R"
```

这看起来就是 FreeMoCap rig 的典型命名。

你说 FreeMoCap 骨骼固定、MMD 模型也固定，那之后我们可以不猜，直接写死配置。

---

## 脚部问题：现在只是“疑似脚滑”

例如：

```json
{
  "type": "foot_slide_suspected",
  "bone": "foot.R",
  "severity": 0.5975
}
```

这个 severity 不低，但还不能立刻修。

原因是现在我们只看了：

```text
foot.L
foot.R
```

这两个通常更接近“脚/脚踝”骨，而你肉眼看到的是：

> 脚尖时不时插进地里

那就应该额外分析：

```text
toe.L
toe.R
```

或者 FreeMoCap 中对应的脚尖骨。

所以脚部先不动。  
下一轮我们会扩展 analyzer，加入 toe bones。

---

## 手部问题：非常适合第一个修复工具

报告里手部跳变是：

```json
hand.L: 1711
hand.R: 1832, 1834
```

这正好符合我们之前说的“第一步修单帧/少数帧跳变”。

这类修复：

- 风险低；
- 容易回滚；
- 对舞蹈视频视觉改善明显；
- 不涉及复杂 IK；
- 不会先把脚修坏。

所以第一修复目标确定：

> **烘焙当前可见动画 → 修 hand.L / hand.R 单帧跳变 → 保存为新 blend。**

---

# 3. 固定骨骼配置

先把你的 config 改成显式骨骼名。

打开：

```bash
nano /mnt/f/mocap_ai_doctor/configs/analyze_source.json
```

把 `bone_hints` 改成：

```json
"bone_hints": {
  "hips": ["pelvis"],
  "left_foot": ["foot.L"],
  "right_foot": ["foot.R"],
  "left_hand": ["hand.L"],
  "right_hand": ["hand.R"]
}
```

完整可以是：

```json
{
  "mode": "analyze",
  "armature_name": "import_synchronized_videos_rig",
  "frame_start": null,
  "frame_end": null,
  "output_report": "F:/mocap_ai_doctor/reports/report_source.json",

  "bone_hints": {
    "hips": ["pelvis"],
    "left_foot": ["foot.L"],
    "right_foot": ["foot.R"],
    "left_hand": ["hand.L"],
    "right_hand": ["hand.R"]
  },

  "thresholds": {
    "floor_tolerance_m": 0.03,
    "foot_contact_height_m": 0.06,
    "foot_slide_speed_m_per_frame": 0.025,
    "hand_jump_m_per_frame": 0.20,
    "hips_jump_m_per_frame": 0.25
  }
}
```

---

# 4. 先做一个骨骼列表导出脚本

你说可以教你导出骨骼列表。我们现在加一个小工具，后面用于确认 toe 骨骼名、MMD 骨骼名。

创建：

```bash
nano /mnt/f/mocap_ai_doctor/scripts/export_bone_list.py
```

粘贴：

```python
import bpy
import sys
import json
from pathlib import Path


def args_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def main():
    args = args_after_dash()
    if len(args) < 1:
        raise RuntimeError("Usage: blender file.blend --python export_bone_list.py -- output.json [armature_name]")

    output_path = Path(args[0])
    armature_name = args[1] if len(args) >= 2 else ""

    if armature_name:
        arm = bpy.data.objects.get(armature_name)
        if not arm or arm.type != "ARMATURE":
            raise RuntimeError(f"Armature not found: {armature_name}")
    else:
        arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
        if not arms:
            raise RuntimeError("No armature found")
        arm = arms[0]

    bones = []
    for pb in arm.pose.bones:
        parent = pb.parent.name if pb.parent else None
        bones.append({
            "name": pb.name,
            "parent": parent,
            "children": [c.name for c in pb.children]
        })

    data = {
        "armature": arm.name,
        "bone_count": len(bones),
        "bones": bones
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[export_bone_list] written: {output_path}")


if __name__ == "__main__":
    main()
```

运行：

```bash
"/mnt/c/Program Files/Blender Foundation/Blender 4.2/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_mocap.blend" \
  --python "F:/mocap_ai_doctor/scripts/export_bone_list.py" \
  --python-exit-code 1 \
  -- "F:/mocap_ai_doctor/reports/source_bones.json" "import_synchronized_videos_rig"
```

如果你的 Blender 不是 4.2，路径照旧改一下。

然后查看：

```bash
cat /mnt/f/mocap_ai_doctor/reports/source_bones.json
```

你可以把里面疑似脚尖的骨名发我。  
通常我们要找名字里包含：

```text
toe
ball
foot_index
脚趾
つま先
```

的骨骼。

---

# 5. 现在写第一个修复脚本：烘焙 + 修手部跳变

这个脚本会做几件事：

1. 打开当前 blend；
2. 选中 armature；
3. 把可见姿态 bake 成普通 Action；
4. 读取 `report_source.json`；
5. 找到 `hand_jump` 问题；
6. 对跳变帧做插值修复；
7. 保存成新文件：

```text
F:\mocap_ai_doctor\blends\source_mocap_handjump_fixed.blend
```

不会覆盖原文件。

---

## 创建脚本

```bash
nano /mnt/f/mocap_ai_doctor/scripts/repair_hand_jumps.py
```

粘贴：

```python
import bpy
import sys
import json
import math
from pathlib import Path


def args_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def load_json(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_armature(name):
    if name:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "ARMATURE":
            return obj
        raise RuntimeError(f"Armature not found: {name}")

    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if not arms:
        raise RuntimeError("No armature found")

    return arms[0]


def ensure_visual_baked_action(armature, frame_start, frame_end):
    """
    把当前看到的骨骼运动烘焙成普通 Action。
    这样后面可以直接改 fcurves。
    """
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.ops.object.mode_set.poll() else None

    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # 进入 pose mode
    bpy.ops.object.mode_set(mode='POSE')

    # 全选 pose bones
    bpy.ops.pose.select_all(action='SELECT')

    # bake 当前可见姿态
    bpy.ops.nla.bake(
        frame_start=frame_start,
        frame_end=frame_end,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=False,
        clean_curves=False,
        bake_types={'POSE'}
    )

    bpy.ops.object.mode_set(mode='OBJECT')

    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("Bake failed: armature still has no action")

    action = armature.animation_data.action
    action.name = action.name + "_visual_baked"

    print(f"[repair] baked action: {action.name}")
    return action


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def get_value_at_frame(fcurve, frame):
    return fcurve.evaluate(frame)


def set_key_value_at_frame(fcurve, frame, value):
    """
    因为我们 bake 后每帧都有 key，所以通常能找到对应 key。
    找不到就插入一个。
    """
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            kp.co.y = value
            kp.interpolation = 'LINEAR'
            return

    fcurve.keyframe_points.insert(frame, value, options={'FAST'})


def normalize_quaternion(vals):
    length = math.sqrt(sum(v * v for v in vals))
    if length < 1e-8:
        return vals
    return [v / length for v in vals]


def repair_bone_frame_range(action, bone_name, frame_a, frame_b, frame_start, frame_end):
    """
    对一个坏区间 [frame_a, frame_b] 进行插值。
    使用前一帧和后一帧作为参考。
    """
    prev_frame = max(frame_start, frame_a - 1)
    next_frame = min(frame_end, frame_b + 1)

    if prev_frame == frame_a or next_frame == frame_b:
        print(f"[repair] skip boundary range {bone_name} {frame_a}-{frame_b}")
        return

    paths = [
        (f'pose.bones["{bone_name}"].location', 3, False),
        (f'pose.bones["{bone_name}"].rotation_euler', 3, False),
        (f'pose.bones["{bone_name}"].rotation_quaternion', 4, True),
        (f'pose.bones["{bone_name}"].scale', 3, False),
    ]

    for data_path, count, is_quat in paths:
        fcurves = [get_fcurve(action, data_path, i) for i in range(count)]

        # 这类旋转模式不一定存在，缺了就跳过
        if any(fc is None for fc in fcurves):
            continue

        prev_vals = [get_value_at_frame(fc, prev_frame) for fc in fcurves]
        next_vals = [get_value_at_frame(fc, next_frame) for fc in fcurves]

        for frame in range(frame_a, frame_b + 1):
            t = (frame - prev_frame) / (next_frame - prev_frame)
            vals = [
                prev_vals[i] * (1.0 - t) + next_vals[i] * t
                for i in range(count)
            ]

            if is_quat:
                vals = normalize_quaternion(vals)

            for i, fc in enumerate(fcurves):
                set_key_value_at_frame(fc, frame, vals[i])

    print(f"[repair] interpolated {bone_name}: {frame_a}-{frame_b}")


def collect_hand_jump_ranges(report):
    ranges = []
    for issue in report.get("issues", []):
        if issue.get("type") != "hand_jump":
            continue

        bone = issue.get("bone")
        for r in issue.get("frames", []):
            if len(r) == 2:
                ranges.append({
                    "bone": bone,
                    "start": int(r[0]),
                    "end": int(r[1]),
                    "severity": issue.get("severity", 0)
                })
    return ranges


def main():
    args = args_after_dash()

    if len(args) < 4:
        raise RuntimeError(
            "Usage: blender input.blend --python repair_hand_jumps.py -- report.json output.blend armature_name max_gap"
        )

    report_path = args[0]
    output_blend = args[1]
    armature_name = args[2]
    max_gap = int(args[3])

    report = load_json(report_path)

    frame_start = int(report["scene"]["frame_start"])
    frame_end = int(report["scene"]["frame_end"])

    armature = find_armature(armature_name)

    action = ensure_visual_baked_action(
        armature=armature,
        frame_start=frame_start,
        frame_end=frame_end
    )

    ranges = collect_hand_jump_ranges(report)

    print(f"[repair] hand jump ranges: {ranges}")

    for item in ranges:
        bone = item["bone"]
        a = item["start"]
        b = item["end"]

        if not bone:
            continue

        gap_len = b - a + 1
        if gap_len > max_gap:
            print(f"[repair] skip {bone} {a}-{b}: gap too long")
            continue

        repair_bone_frame_range(
            action=action,
            bone_name=bone,
            frame_a=a,
            frame_b=b,
            frame_start=frame_start,
            frame_end=frame_end
        )

    # 更新曲线
    for fc in action.fcurves:
        fc.update()

    out = Path(output_blend)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print(f"[repair] saved: {out}")


if __name__ == "__main__":
    main()
```

---

# 6. 运行修复脚本

运行：

```bash
"/mnt/c/Program Files/Blender Foundation/Blender 4.2/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_mocap.blend" \
  --python "F:/mocap_ai_doctor/scripts/repair_hand_jumps.py" \
  --python-exit-code 1 \
  -- "F:/mocap_ai_doctor/reports/report_source.json" \
     "F:/mocap_ai_doctor/blends/source_mocap_handjump_fixed.blend" \
     "import_synchronized_videos_rig" \
     2
```

最后那个 `2` 的意思是：

```text
最多修连续 2 帧的跳变
```

你的报告里：

```text
hand.L 1711
hand.R 1832
hand.R 1834
```

都是单帧，所以会修。

---

# 7. 再分析修复后的文件

现在用之前的 analyzer 分析新 blend。

你可以临时改 `run_analyze_source.sh` 里面的：

```bash
BLEND="F:/mocap_ai_doctor/blends/source_mocap.blend"
```

改成：

```bash
BLEND="F:/mocap_ai_doctor/blends/source_mocap_handjump_fixed.blend"
```

并且把 config 里的输出报告改一下：

```json
"output_report": "F:/mocap_ai_doctor/reports/report_handjump_fixed.json"
```

然后运行：

```bash
/mnt/f/mocap_ai_doctor/run_analyze_source.sh
```

查看：

```bash
cat /mnt/f/mocap_ai_doctor/reports/report_handjump_fixed.json
```

我们希望看到：

```json
"hand_jump"
```

消失，或者 severity 明显下降。

---

# 8. 如果运行中报错，最可能是这几类

## A. Blender 路径错

比如：

```text
No such file or directory: Blender 4.2
```

你运行：

```bash
ls "/mnt/c/Program Files/Blender Foundation"
```

看实际版本。

---

## B. Bake 失败

如果报：

```text
Bake failed: armature still has no action
```

说明当前 rig 可能不允许直接 bake pose，或者 armature 不是实际受控对象。  
这种情况我们再写一个 inspect 脚本查约束和对象层级。

---

## C. 骨骼名不对

如果报：

```text
pose.bones["hand.L"] not found
```

说明当前 blend 中修复脚本拿到的 armature 和报告中的 armature 不一致。  
需要先跑骨骼列表导出确认。

---

# 9. 这一步之后我们做什么

你现在按顺序做：

1. 导出骨骼列表；
2. 跑 hand jump 修复；
3. 对修复后的 blend 再跑分析；
4. 把 `report_handjump_fixed.json` 发我。

然后下一步我们做：

## 下一步 A：扩展脚部检测

加入：

```text
toe.L
toe.R
```

或者你骨骼列表里的真实脚尖骨。

检测：

- 脚尖穿地；
- 脚尖浮动；
- foot/toe 接触段；
- 左右脚分别的地面高度。

## 下一步 B：目标模型阶段先记着不做

MMD/Teto、ARP、IK 的目标模型修复先不急。  
我们先把源数据阶段稳定下来：

```text
手部跳变 → 脚尖检测 → 脚部接触标记 → 轻度平滑
```

现在第一刀只修手部跳变。不要同时修脚。

---
## 🧑‍💻 User

1.我确定联网搜索打开了，但是刚才没开对应的网络服务，工具应该一直都在，只是无法访问，现在应该好了，我这边是有个下拉菜单，里面有个Google选项，我选中了它。2.我的Blender地址：“/mnt/d/blender-3.2.1-windows-x64/blender.exe” 注意，这个是4.3.2版本的，文件夹名字没改而已。3.烘焙这事还挺麻烦，之前是ai告诉我这样烘焙：起始帧 / 结束帧：填入你的视频长度（看你截图应该是 1047 到 1945）。
帧步长 (Frame Step)：1
仅选定骨骼 (Only Selected Bones)：取消勾选（不打勾）。
可视关键帧 (Visual Keying)：必须勾选！（这是把小球的拉扯力转换成真正旋转角度的魔法）。
清除约束 (Clear Constraints)：必须勾选！（烘焙完就和小球解绑）。
清除父级 (Clear Parents)：不打勾。
覆盖当前动作 (Overwrite Current Action)：勾选。
烘焙数据 (Bake Data)：选择 姿态 (Pose)。
我已经按这个操作好了，以后的烘焙也让我手动来，不知道这个参数对不对。
3.只修从我在Blender时间线里面设置的起始到结束帧这些部分，这之外都是我挥舞标定板的动作，别修了。
你上次会话给我的脚本我都还没执行。我没用你的方法获取骨骼，但我想起导出过骨骼重定向映射表，utf8编码文本文件，有很多空着没填的，还有类似hand_fk这样名字的那一边是mmd骨骼，也就是说这里面骨骼数量多的那一边是freemocap原始骨骼

---
## 🤖 Assistant

我先查一下 Blender 4.x 的烘焙参数/命令行细节和 FreeMoCap 骨骼相关资料，然后把工作流改成“你手动烘焙、脚本只处理时间线范围”。

确认：联网搜索这次能用了。我查到的 Blender NLA Bake API 和你之前 AI 给的参数基本一致，尤其是 `visual_keying` 是“用最终变换/约束后的结果打关键帧”，`clear_constraints` 会移除约束，而且文档也提醒清约束时应开启 Visual Keying；`use_current_action` 就是“覆盖当前动作” [1][3]。

## 烘焙参数结论

你手动烘焙的参数可以继续用：

- `Frame Step = 1`：对动捕正确。
- `Only Selected Bones = 取消`：正确，避免漏骨骼。
- `Visual Keying = 勾选`：必须，才能把小球/约束结果烘成真实姿态 [1][3]。
- `Clear Constraints = 勾选`：正确，烘完和 FreeMoCap 小球解绑 [1][3]。
- `Clear Parents = 不勾`：正确，骨架别乱清父级。
- `Overwrite Current Action = 勾选`：可以；但以后建议烘焙前先另存 `.blend`，因为它会写进当前 action [1][3]。
- `Bake Data = Pose`：正确，文档里 `POSE` 就是烘焙骨骼姿态 [1][3]。

所以我们调整工作流：**以后烘焙你手动做，脚本绝不自动 bake。** 这能少很多不可控风险。

## 时间线范围

你说“只修 Blender 时间线起始到结束帧”，这个也采纳。脚本里继续让：

```json
"frame_start": null,
"frame_end": null
```

含义就是读取当前 `.blend` 的 `scene.frame_start` / `scene.frame_end`。你只要在 Blender 时间线里把起止帧设好，脚本就只分析和修这一段，标定板动作不会碰。

## Blender 路径

以后命令统一用你的路径：

```bash
BLENDER="/mnt/d/blender-3.2.1-windows-x64/blender.exe"
```

虽然文件夹叫 3.2.1，但 exe 是 4.3.2 没问题。

## 关于 `remap_preset.bmap`

你这个映射里已经确认了几个关键点：

```text
MMD / ARP 目标侧        FreeMoCap 源侧
foot_ik.L              foot.L
foot_ik.R              foot.R
hand_fk.L              hand.L
hand_fk.R              hand.R
torso_root             pelvis
```

也就是说你上次“腿部重定向到脚 IK、其他基本 FK”的设置确实存在：`foot_ik.L <- foot.L`，`foot_ik.R <- foot.R`。这一步最终仍建议保留，因为目标 Teto 模型的脚底接触要在目标 IK 上二次稳定。

另外你贴出来的源骨骼里有：

```text
heel.02.L
heel.02.R
```

但它们在映射里是空目标。下一版脚部分析应该把它们也纳入采样。即使名字叫 heel，它很可能对判断脚底/脚尖附近接触有帮助。我们先不假设它一定是脚尖，下一轮脚本报告里把 `foot.L/R` 和 `heel.02.L/R` 的高度、速度都列出来，再判断哪个更适合作为“脚底接触点”。

## 现在不要执行我上次的修复脚本

上次那个 `repair_hand_jumps.py` 会自动烘焙，不符合你现在的新要求。废弃它。

我们下一版应该改成：

```text
输入：你已经手动烘焙、保存好的 blend
脚本：只读取当前 action / 当前时间线范围
修复：只改 hand.L / hand.R 跳变帧
输出：另存新 blend
绝不：自动 bake、清约束、改时间线范围外关键帧
```

下一步我建议你先做一件事：把手动烘焙后的文件另存为：

```text
F:\mocap_ai_doctor\blends\source_baked.blend
```

然后我们用这个作为“源数据清理起点”。下一轮我给你一版新的 `repair_hand_jumps_no_bake.py` 和更新版 analyzer，加入 `heel.02.L/R`，并统一使用你的 Blender 路径。
[1] [Nla Operators — Blender 2.75.4](https://docs.blender.org/api/blender_python_api_2_75_4/bpy.ops.nla.html)

[2] [Blender 2.8: NLA Editor and Baking Multiple Actions](https://blenderartists.org/t/blender-2-8-nla-editor-and-baking-multiple-actions/1176253)

[3] [Nla Operators - Blender Python API](https://docs.blender.org/api/current/bpy.ops.nla.html)

[1] [Nla Operators — Blender 2.75.4](https://docs.blender.org/api/blender_python_api_2_75_4/bpy.ops.nla.html)

[2] [Blender 2.8: NLA Editor and Baking Multiple Actions](https://blenderartists.org/t/blender-2-8-nla-editor-and-baking-multiple-actions/1176253)

[3] [Nla Operators - Blender Python API](https://docs.blender.org/api/current/bpy.ops.nla.html)

[1] [Nla Operators — Blender 2.75.4](https://docs.blender.org/api/blender_python_api_2_75_4/bpy.ops.nla.html)

[2] [Blender 2.8: NLA Editor and Baking Multiple Actions](https://blenderartists.org/t/blender-2-8-nla-editor-and-baking-multiple-actions/1176253)

[3] [Nla Operators - Blender Python API](https://docs.blender.org/api/current/bpy.ops.nla.html)
---
## 🧑‍💻 User

按你说的做了。另外，我在之前的工程文件里面帮你看了一下，heel.02.L是脚后跟

---
## 🤖 Assistant

很好，这个确认很关键：`heel.02.L` / `heel.02.R` 明确是**脚后跟**，那它们比 `foot.L` / `foot.R` 更适合作为“落地接触”的重要参考点。  

这会带来一个小调整：

- `foot.L / foot.R`：更像脚踝/脚整体的运动参考，适合看脚滑、抖动、整体位移。
- `heel.02.L / heel.02.R`：更适合看**脚跟是否接地、是否插地、接触时机**。
- 如果后面还有 `toe` 类骨骼，再把它们加入，就能更准确判断“脚尖插地”。

你这套 `bmap` 信息也说明一件事：  
`foot_ik.L <- foot.L`、`foot_ik.R <- foot.R` 这个目标 IK 映射是对的，后面**重定向后还要做一次目标脚部稳定**，但源数据阶段可以先只修清晰可见的问题。

我建议现在固定成这条工作流：

1. **只分析你手动烘焙后的 `source_baked.blend`**
2. **时间范围只用 Blender 时间线的有效动作段**
3. **脚部分析加入 `heel.02.L/R`**
4. **先做“无 bake 的手部跳变修复”**
5. **再做脚部接触和脚滑分析**
6. **最后才碰 ARP / MMD 的目标 IK 修复**

关于你说的手动烘焙参数：你现在那套是合理的，我后面会按“你手动烘焙、脚本不再自动烘焙”这个前提来设计。

下一步最合适的是我直接给你两份更新版脚本的设计：
- `analyze_source.py`：把 `heel.02.L/R` 加进脚部分析
- `repair_hand_jumps_no_bake.py`：不烘焙，直接修你已经烘好的 action

如果你愿意，我下一条就直接把这两份脚本按你的环境路径和命名写出来。

---
## 🧑‍💻 User

好，写脚本并告诉我怎么操作。不过，4.先做“无 bake 的手部跳变修复”是什么意思？不是第一步就已经把各种小球的运动烘焙到freemocap原骨骼了吗。
第二，我之前在网上找到了个脚本，试了以后有一些改善，给你看看，说不定有帮助。原作者在评论区的问答：
原来是通过移动根骨来反向抵消偏移[支持]
 是的，以前想在骨头上搞操作，但发现完全实现不了，它那个世界、骨架自身的坐标系切换起来特别复杂混乱，后来思路一打开，干脆额外添加外置的空物体，让它的运动路径保持一致，以此来代理运算


---
## 🤖 Assistant

对，你现在这一步的“无 bake 手部跳变修复”，意思是：

- **第一步手动 bake 还是要做**，把 FreeMoCap 的约束/小球运动烘成可编辑 Action；
- **“无 bake”指修复脚本本身不再重新 bake**，它只在你已经烘好的 Action 上直接改关键帧。

也就是：  
**先手动烘焙一次，后面修复不再自动烘焙。**

你给的那个 `K + 6 个接触点` 脚本思路是对的，它属于**后期目标模型的 root compensation / anti-slide layer**，很适合后面处理 Teto/MMD 的脚滑；但现在我们先把**源动作清理**做好，别混在一起。

---

## 先做这两个文件

### 1) `mocap_doctor_analyze.py`
放到例如：

`D:\mocap_ai_doctor\scripts\mocap_doctor_analyze.py`

```python
import bpy
import sys
import json
import math
from pathlib import Path


ARMATURE_NAME = "import_synchronized_videos_rig"

BONES = {
    "hips": "pelvis",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_heel": "heel.02.L",
    "right_heel": "heel.02.R",
    "left_hand": "hand.L",
    "right_hand": "hand.R",
}

THRESHOLDS = {
    "floor_tolerance_m": 0.03,
    "foot_contact_height_m": 0.05,
    "foot_slide_speed_m_per_frame": 0.02,
    "heel_slide_speed_m_per_frame": 0.018,
    "hand_jump_m_per_frame": 0.20,
    "hips_jump_m_per_frame": 0.25,
}


def get_args_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def load_config():
    args = get_args_after_dash()
    if not args:
        raise RuntimeError("Missing config path after --")
    path = Path(args[0])
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_armature(name):
    obj = bpy.data.objects.get(name)
    if obj and obj.type == "ARMATURE":
        return obj
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if not arms:
        raise RuntimeError("No armature found")
    return arms[0]


def bone_world_loc(armature, bone_name):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None
    return (armature.matrix_world @ pb.matrix).translation.copy()


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)


def frame_ranges(frames):
    if not frames:
        return []
    frames = sorted(set(frames))
    ranges = []
    start = prev = frames[0]
    for frame in frames[1:]:
        if frame == prev + 1:
            prev = frame
        else:
            ranges.append([start, prev])
            start = prev = frame
    ranges.append([start, prev])
    return ranges


def vec_dist(a, b, xy_only=False):
    if a is None or b is None:
        return None
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    if xy_only:
        return math.sqrt(dx * dx + dy * dy)
    dz = a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def sample_bones(armature, bone_names, frame_start, frame_end):
    out = {name: [] for name in bone_names}
    scene = bpy.context.scene
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        for name in bone_names:
            loc = bone_world_loc(armature, name)
            if loc is None:
                out[name].append(None)
            else:
                out[name].append([float(loc.x), float(loc.y), float(loc.z)])
    return out


def detect_floor(samples, floor_bones):
    zs = []
    for bone in floor_bones:
        for p in samples.get(bone, []):
            if p is not None:
                zs.append(p[2])
    return percentile(zs, 0.01) if zs else 0.0


def detect_slide(samples, bone, frame_start, floor_z, contact_h, slide_speed, issue_type):
    arr = samples.get(bone, [])
    bad = []
    speeds = []
    for i in range(1, len(arr)):
        prev = arr[i - 1]
        cur = arr[i]
        if prev is None or cur is None:
            continue
        z = cur[2]
        dz = abs(cur[2] - prev[2])
        xy = vec_dist(cur, prev, xy_only=True)
        if z <= floor_z + contact_h and dz < contact_h * 0.5 and xy > slide_speed:
            frame = frame_start + i
            bad.append(frame)
            speeds.append(xy)
    if not bad:
        return None
    return {
        "type": issue_type,
        "bone": bone,
        "frames": frame_ranges(bad),
        "severity": round(min(1.0, max(speeds) / 0.12), 4),
        "max_xy_speed_m_per_frame": round(max(speeds), 4),
    }


def detect_jump(samples, bone, frame_start, threshold, issue_type):
    arr = samples.get(bone, [])
    bad = []
    mags = []
    for i in range(1, len(arr)):
        d = vec_dist(arr[i], arr[i - 1], xy_only=False)
        if d is None:
            continue
        if d > threshold:
            frame = frame_start + i
            bad.append(frame)
            mags.append(d)
    if not bad:
        return None
    return {
        "type": issue_type,
        "bone": bone,
        "frames": frame_ranges(bad),
        "severity": round(min(1.0, max(mags) / (threshold * 3.0)), 4),
        "max_speed_m_per_frame": round(max(mags), 4),
    }


def main():
    config = load_config()
    scene = bpy.context.scene
    armature = find_armature(config.get("armature_name", ARMATURE_NAME))

    frame_start = int(config.get("frame_start") or scene.frame_start)
    frame_end = int(config.get("frame_end") or scene.frame_end)

    bone_names = [b for b in BONES.values() if b in armature.pose.bones]
    samples = sample_bones(armature, bone_names, frame_start, frame_end)

    floor_bones = [b for b in [BONES["left_foot"], BONES["right_foot"], BONES["left_heel"], BONES["right_heel"]] if b in samples]
    floor_z = detect_floor(samples, floor_bones)

    issues = []
    th = {**THRESHOLDS, **config.get("thresholds", {})}

    for bone in [BONES["left_foot"], BONES["right_foot"]]:
        if bone in samples:
            item = detect_slide(
                samples, bone, frame_start, floor_z,
                th["foot_contact_height_m"],
                th["foot_slide_speed_m_per_frame"],
                "foot_slide_suspected",
            )
            if item:
                issues.append(item)

    for bone in [BONES["left_heel"], BONES["right_heel"]]:
        if bone in samples:
            item = detect_slide(
                samples, bone, frame_start, floor_z,
                th["foot_contact_height_m"],
                th["heel_slide_speed_m_per_frame"],
                "heel_slide_suspected",
            )
            if item:
                issues.append(item)

    for bone in [BONES["left_hand"], BONES["right_hand"]]:
        if bone in samples:
            item = detect_jump(samples, bone, frame_start, th["hand_jump_m_per_frame"], "hand_jump")
            if item:
                issues.append(item)

    if BONES["hips"] in samples:
        item = detect_jump(samples, BONES["hips"], frame_start, th["hips_jump_m_per_frame"], "hips_jump")
        if item:
            issues.append(item)

    report = {
        "schema_version": "mocap_doctor_report_v1",
        "scene": {
            "name": scene.name,
            "fps": scene.render.fps,
            "frame_start": frame_start,
            "frame_end": frame_end,
        },
        "armature": {
            "name": armature.name,
            "action": armature.animation_data.action.name if armature.animation_data and armature.animation_data.action else None,
        },
        "bones": BONES,
        "floor": {
            "z_estimate": round(floor_z, 5),
        },
        "issues": issues,
        "notes": [
            "Analysis only. No animation was modified.",
            "Manual bake first. This script reads the baked action or evaluated pose.",
        ],
    }

    out = Path(config["output_report"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[mocap_doctor] wrote {out}")


if __name__ == "__main__":
    main()
```

---

### 2) `repair_hand_jumps_no_bake.py`
放到：

`D:\mocap_ai_doctor\scripts\repair_hand_jumps_no_bake.py`

```python
import bpy
import sys
import json
import math
from pathlib import Path


def get_args_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def key_at_frame(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def value_at_frame(fcurve, frame):
    return fcurve.evaluate(frame)


def set_key_value(fcurve, frame, value):
    kp = key_at_frame(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"
    return kp


def normalize_quaternion(values):
    length = math.sqrt(sum(v * v for v in values))
    if length < 1e-8:
        return values
    return [v / length for v in values]


def repair_channel_group(action, bone_name, frame_a, frame_b, frame_start, frame_end):
    prev_frame = max(frame_start, frame_a - 1)
    next_frame = min(frame_end, frame_b + 1)

    if prev_frame == frame_a or next_frame == frame_b:
        print(f"[repair] skip boundary range {bone_name} {frame_a}-{frame_b}")
        return

    groups = [
        (f'pose.bones["{bone_name}"].location', 3, False),
        (f'pose.bones["{bone_name}"].rotation_euler', 3, False),
        (f'pose.bones["{bone_name}"].rotation_quaternion', 4, True),
        (f'pose.bones["{bone_name}"].scale', 3, False),
    ]

    for data_path, count, is_quat in groups:
        fcurves = [get_fcurve(action, data_path, i) for i in range(count)]
        if any(fc is None for fc in fcurves):
            continue

        prev_vals = [value_at_frame(fc, prev_frame) for fc in fcurves]
        next_vals = [value_at_frame(fc, next_frame) for fc in fcurves]

        if is_quat:
            dot = sum(prev_vals[i] * next_vals[i] for i in range(4))
            if dot < 0:
                next_vals = [-v for v in next_vals]

        for frame in range(frame_a, frame_b + 1):
            t = (frame - prev_frame) / (next_frame - prev_frame)
            vals = [(1.0 - t) * prev_vals[i] + t * next_vals[i] for i in range(count)]
            if is_quat:
                vals = normalize_quaternion(vals)
            for i, fc in enumerate(fcurves):
                set_key_value(fc, frame, vals[i])

    print(f"[repair] fixed {bone_name} {frame_a}-{frame_b}")


def collect_hand_issues(report):
    out = []
    for issue in report.get("issues", []):
        if issue.get("type") != "hand_jump":
            continue
        bone = issue.get("bone")
        for r in issue.get("frames", []):
            if len(r) == 2:
                out.append((bone, int(r[0]), int(r[1])))
    return out


def main():
    args = get_args_after_dash()
    if len(args) < 4:
        raise RuntimeError(
            "Usage: blender --background file.blend --python repair_hand_jumps_no_bake.py -- report.json output.blend armature_name max_gap"
        )

    report_path, output_blend, armature_name, max_gap = args[0], args[1], args[2], int(args[3])
    report = load_json(report_path)

    armature = find_armature(armature_name)
    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("No action found. Please manual-bake first, then run this script.")

    action = armature.animation_data.action
    frame_start = int(report["scene"]["frame_start"])
    frame_end = int(report["scene"]["frame_end"])

    for bone, a, b in collect_hand_issues(report):
        if not bone:
            continue
        if (b - a + 1) > max_gap:
            print(f"[repair] skip {bone} {a}-{b}: gap too long")
            continue
        repair_channel_group(action, bone, a, b, frame_start, frame_end)

    for fc in action.fcurves:
        fc.update()

    out = Path(output_blend)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print(f"[repair] saved {out}")


if __name__ == "__main__":
    main()
```

---

## 你现在怎么操作

### 第 1 步：手动烘焙后保存
你已经做了，这一步就是：

- 只烘焙 Blender 时间线里真正的动作段
- 保存为：

`D:\mocap_ai_doctor\blends\source_baked.blend`

---

### 第 2 步：写配置文件
创建：

`D:\mocap_ai_doctor\configs\analyze_source.json`

内容：

```json
{
  "armature_name": "import_synchronized_videos_rig",
  "frame_start": null,
  "frame_end": null,
  "output_report": "D:/mocap_ai_doctor/reports/report_source.json",
  "thresholds": {
    "floor_tolerance_m": 0.03,
    "foot_contact_height_m": 0.05,
    "foot_slide_speed_m_per_frame": 0.02,
    "heel_slide_speed_m_per_frame": 0.018,
    "hand_jump_m_per_frame": 0.20,
    "hips_jump_m_per_frame": 0.25
  }
}
```

---

### 第 3 步：先跑分析
在 WSL 里执行：

```bash
"/mnt/d/blender-3.2.1-windows-x64/blender.exe" \
  --background "D:/mocap_ai_doctor/blends/source_baked.blend" \
  --python "D:/mocap_ai_doctor/scripts/mocap_doctor_analyze.py" \
  --python-exit-code 1 \
  -- "D:/mocap_ai_doctor/configs/analyze_source.json"
```

然后看：

```bash
cat /mnt/d/mocap_ai_doctor/reports/report_source.json
```

---

### 第 4 步：只修手部跳变
如果 report 里还是主要是 `hand_jump`，跑：

```bash
"/mnt/d/blender-3.2.1-windows-x64/blender.exe" \
  --background "D:/mocap_ai_doctor/blends/source_baked.blend" \
  --python "D:/mocap_ai_doctor/scripts/repair_hand_jumps_no_bake.py" \
  --python-exit-code 1 \
  -- "D:/mocap_ai_doctor/reports/report_source.json" \
     "D:/mocap_ai_doctor/blends/source_baked_hands_fixed.blend" \
     "import_synchronized_videos_rig" \
     2
```

`2` 的意思是：只修连续 2 帧以内的小跳变。

---

### 第 5 步：再分析一次
把分析输入换成：

`D:/mocap_ai_doctor/blends/source_baked_hands_fixed.blend`

再跑一遍分析，确认 `hand_jump` 明显减少或消失。

---

## 你提到的那个 `04位置空间脚滑优化脚本`

这个脚本我看懂了，它的核心是：

- 新建一个空物体 `K`
- 用脚后跟/脚尖接触点代理脚底运动
- 通过反向移动 `K` 抵消脚滑
- 再把中心骨/根骨绑定到 `K`

这思路本质上是**root compensation + contact proxy**，很有价值。  
但它更适合**后面目标模型阶段**，尤其是你已经重定向到 MMD/Teto 之后。现在先别急着上它，先把源动作清理稳定。

如果你愿意，我下一条可以继续给你补两个东西：

1. **脚部分析增强版**：把 `heel.02.L/R` 的接触和插地也单独报出来  
2. **目标模型阶段的脚滑修复流程**：怎么把你那个 `K` 思路用到 Teto 上

你先按上面跑一遍，把第一次 `report_source.json` 和修复后的第二次报告贴我。

---
## 🧑‍💻 User

F:\mocap_ai_doctor\才对，Blender在D，我们的脚本和cfg在F。
第三步跑完了，“主要是hand_jump”是怎么个判断标准呢？这时我看到的结果，滑步一大串，hand jump两只手加起来三个。
{
  "schema_version": "mocap_doctor_report_v1",
  "scene": {
    "name": "Scene",
    "fps": 24,
    "frame_start": 1525,
    "frame_end": 2836
  },
  "armature": {
    "name": "import_synchronized_videos_rig",
    "action": "Action"
  },
  "bones": {
    "hips": "pelvis",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_heel": "heel.02.L",
    "right_heel": "heel.02.R",
    "left_hand": "hand.L",
    "right_hand": "hand.R"
  },
  "floor": {
    "z_estimate": 0.02419
  },
  "issues": [
    {
      "type": "foot_slide_suspected",
      "bone": "foot.L",
      "frames": [
        [
          1620,
          1621
        ],
        [
          1686,
          1690
        ],
        [
          1735,
          1736
        ],
        [
          1806,
          1807
        ],
        [
          2055,
          2060
        ],
        [
          2085,
          2086
        ],
        [
          2144,
          2145
        ],
        [
          2705,
          2708
        ],
        [
          2754,
          2756
        ]
      ],
      "severity": 0.4469,
      "max_xy_speed_m_per_frame": 0.0536
    },
    {
      "type": "foot_slide_suspected",
      "bone": "foot.R",
      "frames": [
        [
          1568,
          1570
        ],
        [
          1580,
          1587
        ],
        [
          1661,
          1664
        ],
        [
          1800,
          1801
        ],
        [
          1819,
          1819
        ],
        [
          1893,
          1901
        ],
        [
          1981,
          1982
        ],
        [
          2044,
          2048
        ],
        [
          2072,
          2075
        ],
        [
          2117,
          2118
        ],
        [
          2129,
          2131
        ],
        [
          2152,
          2153
        ],
        [
          2239,
          2239
        ],
        [
          2692,
          2696
        ],
        [
          2767,
          2772
        ]
      ],
      "severity": 0.5975,
      "max_xy_speed_m_per_frame": 0.0717
    },
    {
      "type": "heel_slide_suspected",
      "bone": "heel.02.L",
      "frames": [
        [
          1619,
          1621
        ],
        [
          1686,
          1690
        ],
        [
          1735,
          1737
        ],
        [
          1806,
          1807
        ],
        [
          2055,
          2061
        ],
        [
          2085,
          2086
        ],
        [
          2144,
          2145
        ],
        [
          2704,
          2708
        ],
        [
          2754,
          2756
        ]
      ],
      "severity": 0.4469,
      "max_xy_speed_m_per_frame": 0.0536
    },
    {
      "type": "heel_slide_suspected",
      "bone": "heel.02.R",
      "frames": [
        [
          1568,
          1570
        ],
        [
          1579,
          1587
        ],
        [
          1589,
          1589
        ],
        [
          1661,
          1664
        ],
        [
          1800,
          1801
        ],
        [
          1819,
          1820
        ],
        [
          1893,
          1902
        ],
        [
          1981,
          1983
        ],
        [
          2044,
          2048
        ],
        [
          2072,
          2075
        ],
        [
          2116,
          2118
        ],
        [
          2129,
          2132
        ],
        [
          2152,
          2153
        ],
        [
          2239,
          2239
        ],
        [
          2692,
          2696
        ],
        [
          2767,
          2772
        ]
      ],
      "severity": 0.5975,
      "max_xy_speed_m_per_frame": 0.0717
    },
    {
      "type": "hand_jump",
      "bone": "hand.L",
      "frames": [
        [
          1711,
          1711
        ]
      ],
      "severity": 0.4075,
      "max_speed_m_per_frame": 0.2445
    },
    {
      "type": "hand_jump",
      "bone": "hand.R",
      "frames": [
        [
          1832,
          1832
        ],
        [
          1834,
          1834
        ]
      ],
      "severity": 0.5344,
      "max_speed_m_per_frame": 0.3207
    }
  ],
  "notes": [
    "Analysis only. No animation was modified.",
    "Manual bake first. This script reads the baked action or evaluated pose."
  ]
}
上面这是修之后。我确定我运行了你给的手部修复脚本
这是修之前：
{
  "schema_version": "mocap_doctor_report_v0",
  "scene": {
    "name": "Scene",
    "fps": 24,
    "frame_start": 1525,
    "frame_end": 2836
  },
  "armature": {
    "name": "import_synchronized_videos_rig",
    "action": null
  },
  "guessed_bones": {
    "hips": "pelvis",
    "left_foot": "foot.L",
    "right_foot": "foot.R",
    "left_hand": "hand.L",
    "right_hand": "hand.R"
  },
  "floor": {
    "z_estimate": 0.02428
  },
  "issues": [
    {
      "type": "foot_slide_suspected",
      "bone": "foot.L",
      "frames": [
        [
          1621,
          1622
        ],
        [
          1687,
          1692
        ],
        [
          1732,
          1736
        ],
        [
          1807,
          1808
        ],
        [
          2027,
          2027
        ],
        [
          2055,
          2060
        ],
        [
          2085,
          2087
        ],
        [
          2101,
          2104
        ],
        [
          2159,
          2159
        ],
        [
          2705,
          2707
        ],
        [
          2754,
          2757
        ]
      ],
      "severity": 0.4899,
      "max_xy_speed_m_per_frame": 0.0588
    },
    {
      "type": "foot_slide_suspected",
      "bone": "foot.R",
      "frames": [
        [
          1569,
          1569
        ],
        [
          1580,
          1588
        ],
        [
          1661,
          1664
        ],
        [
          1798,
          1801
        ],
        [
          1894,
          1897
        ],
        [
          2043,
          2048
        ],
        [
          2068,
          2074
        ],
        [
          2117,
          2119
        ],
        [
          2129,
          2131
        ],
        [
          2152,
          2154
        ],
        [
          2693,
          2695
        ],
        [
          2768,
          2771
        ]
      ],
      "severity": 0.5975,
      "max_xy_speed_m_per_frame": 0.0717
    },
    {
      "type": "hand_jump",
      "bone": "hand.L",
      "frames": [
        [
          1711,
          1711
        ]
      ],
      "severity": 0.4075,
      "max_speed_m_per_frame": 0.2445
    },
    {
      "type": "hand_jump",
      "bone": "hand.R",
      "frames": [
        [
          1832,
          1832
        ],
        [
          1834,
          1834
        ]
      ],
      "severity": 0.5344,
      "max_speed_m_per_frame": 0.3207
    }
  ],
  "notes": [
    "This is analysis-only. No animation data was modified.",
    "If guessed_bones are wrong, fill bone_hints in config and run again."
  ]
}
我确定一下，我运行了刚刚这一轮所有的，是只修了手的跳变是吗？我特意手动打开了修前和修后的文件，看了一下，确实没有修复，但是至少你的分析脚本没有问题，分析的那几个地方都确确实实有跳变，而且没有漏检。另外，我发现全程整个骨架都有点朝一侧歪一个较小的角度，不过这个应该是小事，估计是地平面估计歪了，Blender里面整体旋转一下就行了吧？

---
## 🤖 Assistant

报告对比很有价值：分析器确实在抓真实问题，但手部修复脚本没生效的原因也基本清楚了。我先解释原因，然后给你一个改版脚本：修手部跳变时同时插值 `upper_arm/forearm/hand` 这条链。你判断得对：刚刚那版**理论上只修手部跳变**，不碰脚、不碰骨盆、不碰时间线外。  
但它没生效的原因也很明确：我们检测的是 `hand.L/R` 的**世界位置跳变**，而手腕世界位置通常不是由 `hand` 自己的局部位置决定的，而是由上级链条控制：

```text
upper_arm.L → forearm.L → hand.L
upper_arm.R → forearm.R → hand.R
```

所以只插值 `hand.L/R` 自己的 fcurve，可能完全不改变手腕世界位置。下一版要改成：**遇到 hand jump 时，对整条手臂链的旋转/位置做短区间插值**。

另外，“主要是 hand_jump”的意思不是说 foot_slide 少，而是说：  
**我们第一刀只处理最安全的问题：单帧/两帧手部跳变。脚滑虽然多，但要等接触检测更稳后再动。**

---

## 1. 新脚本：`repair_hand_jumps_chain_no_bake.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\repair_hand_jumps_chain_no_bake.py
```

内容：

```python
import bpy
import sys
import json
import math
from pathlib import Path


ARM_CHAINS = {
    "hand.L": ["upper_arm.L", "forearm.L", "hand.L"],
    "hand.R": ["upper_arm.R", "forearm.R", "hand.R"],
}


def args_after_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"


def normalize_quat(values):
    length = math.sqrt(sum(v * v for v in values))
    if length < 1e-8:
        return values
    return [v / length for v in values]


def interpolate_group(action, bone_name, data_path, count, frame_a, frame_b, frame_start, frame_end, is_quat=False):
    fcurves = [get_fcurve(action, data_path, i) for i in range(count)]
    if any(fc is None for fc in fcurves):
        return False

    prev_frame = frame_a - 1
    next_frame = frame_b + 1

    if prev_frame < frame_start or next_frame > frame_end:
        return False

    prev_vals = [fc.evaluate(prev_frame) for fc in fcurves]
    next_vals = [fc.evaluate(next_frame) for fc in fcurves]

    if is_quat:
        dot = sum(prev_vals[i] * next_vals[i] for i in range(4))
        if dot < 0:
            next_vals = [-v for v in next_vals]

    for frame in range(frame_a, frame_b + 1):
        t = (frame - prev_frame) / (next_frame - prev_frame)
        vals = [(1.0 - t) * prev_vals[i] + t * next_vals[i] for i in range(count)]
        if is_quat:
            vals = normalize_quat(vals)

        for i, fc in enumerate(fcurves):
            set_value(fc, frame, vals[i])

    return True


def repair_bone(action, bone_name, frame_a, frame_b, frame_start, frame_end):
    repaired_any = False

    groups = [
        (f'pose.bones["{bone_name}"].rotation_quaternion', 4, True),
        (f'pose.bones["{bone_name}"].rotation_euler', 3, False),
        (f'pose.bones["{bone_name}"].location', 3, False),
    ]

    for data_path, count, is_quat in groups:
        changed = interpolate_group(
            action=action,
            bone_name=bone_name,
            data_path=data_path,
            count=count,
            frame_a=frame_a,
            frame_b=frame_b,
            frame_start=frame_start,
            frame_end=frame_end,
            is_quat=is_quat,
        )
        repaired_any = repaired_any or changed

    return repaired_any


def collect_hand_jumps(report):
    out = []
    for issue in report.get("issues", []):
        if issue.get("type") != "hand_jump":
            continue
        bone = issue.get("bone")
        for r in issue.get("frames", []):
            if len(r) == 2:
                out.append((bone, int(r[0]), int(r[1])))
    return out


def main():
    args = args_after_dash()
    if len(args) < 4:
        raise RuntimeError(
            "Usage: blender --background file.blend --python repair_hand_jumps_chain_no_bake.py -- report.json output.blend armature_name max_gap"
        )

    report_path = args[0]
    output_blend = args[1]
    armature_name = args[2]
    max_gap = int(args[3])

    report = load_json(report_path)
    armature = find_armature(armature_name)

    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("No action found. Manual bake first.")

    action = armature.animation_data.action
    frame_start = int(report["scene"]["frame_start"])
    frame_end = int(report["scene"]["frame_end"])

    print(f"[repair] action: {action.name}")
    print(f"[repair] frame range: {frame_start}-{frame_end}")

    for hand_bone, frame_a, frame_b in collect_hand_jumps(report):
        gap = frame_b - frame_a + 1
        if gap > max_gap:
            print(f"[repair] skip {hand_bone} {frame_a}-{frame_b}: gap too long")
            continue

        chain = ARM_CHAINS.get(hand_bone)
        if not chain:
            print(f"[repair] skip {hand_bone}: no chain configured")
            continue

        print(f"[repair] hand jump {hand_bone} {frame_a}-{frame_b}, chain={chain}")

        for bone_name in chain:
            if bone_name not in armature.pose.bones:
                print(f"[repair] missing bone: {bone_name}")
                continue

            changed = repair_bone(
                action=action,
                bone_name=bone_name,
                frame_a=frame_a,
                frame_b=frame_b,
                frame_start=frame_start,
                frame_end=frame_end,
            )

            if changed:
                print(f"[repair] fixed {bone_name} {frame_a}-{frame_b}")
            else:
                print(f"[repair] no editable fcurves for {bone_name}")

    for fc in action.fcurves:
        fc.update()

    out = Path(output_blend)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print(f"[repair] saved: {out}")


if __name__ == "__main__":
    main()
```

---

## 2. 运行命令

你现在路径是：

- Blender：`/mnt/d/blender-3.2.1-windows-x64/blender.exe`
- 工程：`F:\mocap_ai_doctor`

所以运行：

```bash
"/mnt/d/blender-3.2.1-windows-x64/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_baked.blend" \
  --python "F:/mocap_ai_doctor/scripts/repair_hand_jumps_chain_no_bake.py" \
  --python-exit-code 1 \
  -- "F:/mocap_ai_doctor/reports/report_source.json" \
     "F:/mocap_ai_doctor/blends/source_baked_hands_chain_fixed.blend" \
     "import_synchronized_videos_rig" \
     2
```

然后重新分析：

```bash
"/mnt/d/blender-3.2.1-windows-x64/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_baked_hands_chain_fixed.blend" \
  --python "F:/mocap_ai_doctor/scripts/mocap_doctor_analyze.py" \
  --python-exit-code 1 \
  -- "F:/mocap_ai_doctor/configs/analyze_source.json"
```

注意把 `analyze_source.json` 里的输出报告改成：

```json
"output_report": "F:/mocap_ai_doctor/reports/report_hands_chain_fixed.json"
```

---

## 3. 关于脚滑报告

现在 `foot_slide_suspected` 和 `heel_slide_suspected` 很多是正常的，因为我们的检测还比较粗：

- `heel.02` 是 `foot` 的子骨骼，所以它和 `foot` 的滑动高度重合是合理的。
- 现在只是“疑似滑步”，不是最终修复依据。
- 下一步要做的是**接触段识别**，区分“真的踩地滑”与“脚在移动/抬脚”。

所以暂时不要用这个报告直接修脚。

---

## 4. 关于整体骨架轻微歪斜

这个先别急着在 Blender 里随手整体旋转。可以后面单独做一个“全局校正层”：

```text
源数据阶段：
    不轻易改全局朝向/倾斜，避免影响重定向基准

目标模型阶段：
    根据地面、脚底和角色朝向做统一校正
```

如果只是小角度倾斜，确实最后整体旋转/root 校正即可；但现在先不要混进手部跳变修复里。

你先跑这个链式修复版。如果 `hand_jump` 还没消失，把 `report_hands_chain_fixed.json` 和脚本输出日志贴出来，我再判断是不是跳变来源在 `pelvis/spine/shoulder` 更上游。

---
## 🧑‍💻 User

每次从命令行启动都比我直接点启动慢好多啊。我看确实如你说的，输出长了好多。"type": "hand_jump",
      "bone": "hand.L",
      "frames": [
        [
          1711,
          1711
        ]
      ],
      "severity": 0.4075,
      "max_speed_m_per_frame": 0.2445
    },
    {
      "type": "hand_jump",
      "bone": "hand.R",
      "frames": [
        [
          1832,
          1832
        ],
        [
          1834,
          1834
        ]
      ],
      "severity": 0.5344,
      "max_speed_m_per_frame": 0.3207
    }这是之前。
{
      "type": "hand_jump",
      "bone": "hand.L",
      "frames": [
        [
          1712,
          1712
        ]
      ],
      "severity": 0.3556,
      "max_speed_m_per_frame": 0.2133
    },
    {
      "type": "hand_jump",
      "bone": "hand.R",
      "frames": [
        [
          1834,
          1835
        ]
      ],
      "severity": 0.4181,
      "max_speed_m_per_frame": 0.2509
    }这是之后。
看似修了一个，但是看动画没有区别。我描述一下修之前的：第一处1711帧开始手突然卷进肚子里，1715帧才完全拔出来，修完没变。右手第二处和第三处在一块，1831帧右手开始突然外翻，但是1830-1831帧的这个幅度比较小，1832相比前一帧动作其实也不大，但是和1830比就明显有问题了。1833，外翻到极限，1834回正了一点，1835以后恢复正常。修之后的：肉眼看完全没区别，除了有且仅有第1834帧手外翻的角度减小，1711的那个就真的完全一样了。另外，我每次跑命令行，启动Blender都要好久，明显比我直接Windows里面点快捷方式慢。

---
## 🤖 Assistant

对，你现在看到的结果说明：

1. **分析脚本是有效的**：它抓到的帧，肉眼也确实有问题。
2. **上一版手部修复脚本只产生了很小改善**：因为它按“单帧跳变”插值，但你的实际问题不是单帧尖峰，而是**一小段连续错误姿态**。
3. **你描述的 1711–1715、1831–1835 才是真正该修的区间**，而不是 analyzer 目前只报出来的 1711、1832、1834。
4. **下一步应该做“人工指定坏区间的手臂链插值修复”**，不要继续让 analyzer 自动猜范围。

---

# 1. 为什么上一版肉眼没变化？

你说得很清楚：

> 1711 帧开始手突然卷进肚子里，1715 帧才完全拔出来。  
> 1831 开始右手外翻，1833 到极限，1835 以后恢复。

这说明坏动作是：

```text
hand.L: 1711–1715
hand.R: 1831–1835
```

但 analyzer 只报了：

```text
hand.L: 1711
hand.R: 1832, 1834
```

原因是 analyzer 目前检测的是：

```text
相邻两帧世界位置差 > 阈值
```

它只能抓“速度突变”，抓不到“已经歪了但速度不大”的持续坏姿态。

比如：

```text
1711 突然卷进去  → 被抓到
1712 还在肚子里  → 位置变化不大，可能抓不到
1713 还在肚子里  → 抓不到
1714 还在肚子里  → 抓不到
1715 拔出来      → 可能抓到或抓不到
```

所以我们现在要改策略：

> **由你肉眼指定坏区间，脚本把整段坏区间用前后正常帧插值替换。**

---

# 2. 命令行启动 Blender 慢的问题

你感觉“命令行启动比 Windows 快捷方式慢很多”，这个很正常，原因可能有几个：

## A. 你命令行是从 WSL 启动 Windows Blender

路径是：

```bash
/mnt/d/blender-3.2.1-windows-x64/blender.exe
```

这是 WSL 调 Windows exe，会经过 WSL interop，启动成本会比直接双击高。

## B. 你命令行每次都打开完整 `.blend`

快捷方式可能只是打开空 Blender，或者打开最近文件时缓存状态不同。  
而命令行是：

```bash
blender.exe --background source_baked.blend --python ...
```

它每次都要：

- 启动 Blender；
- 加载工程；
- 加载视频平面；
- 加载模型；
- 加载 action；
- 执行 Python；
- 保存新 blend。

所以慢是预期的。

## C. 你的场景里有视频对象

你截图里有 `VID_2` 这类对象。视频素材、多摄像头背景、贴图、缓存都可能拖慢打开。

## D. 后台模式不等于“秒开”

`--background` 只是不开 UI，它仍然要初始化 Blender、读取文件、构建依赖图、加载数据。Blender 文档中命令行参数确实是按启动流程执行，`--background` 和 `--python` 都是正常启动流程的一部分，不是热加载脚本 [1]。

---

## 建议你现在改成 GUI 里跑脚本

为了迭代快，接下来你可以不用每次命令行启动。推荐：

1. Windows 直接双击打开 Blender；
2. 打开：

```text
F:\mocap_ai_doctor\blends\source_baked.blend
```

3. 在 Blender 里切到 `Scripting`；
4. 新建 Text；
5. 粘贴脚本；
6. 修改脚本顶部几个路径；
7. 点 `Run Script`。

这样不用反复重启 Blender，会快很多。

命令行适合以后批处理；现在调试阶段，GUI 运行更舒服。

---

# 3. 现在写一个“人工指定坏区间”的修复脚本

这版脚本不读 analyzer 的 hand_jump 范围，而是你自己指定：

```python
MANUAL_REPAIR_RANGES = [
    ("hand.L", 1711, 1715),
    ("hand.R", 1831, 1835),
]
```

它会用：

```text
1710 和 1716
1830 和 1836
```

作为正常参考帧，把中间坏区间的手臂链插值替换。

修的骨骼链是：

```text
shoulder.L / upper_arm.L / forearm.L / hand.L
shoulder.R / upper_arm.R / forearm.R / hand.R
```

这比上一版多了 `shoulder`，因为你截图里手臂整体姿态可能来自肩/上臂上游。

---

# 4. 脚本：`repair_manual_hand_ranges.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\repair_manual_hand_ranges.py
```

内容：

```python
import bpy
import math
from pathlib import Path


# ===== 你主要改这里 =====

ARMATURE_NAME = "import_synchronized_videos_rig"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/source_baked_hands_manual_fixed.blend"

# 手动指定坏区间：bone, start, end
# 含义：用 start-1 和 end+1 插值替换 start 到 end
MANUAL_REPAIR_RANGES = [
    ("hand.L", 1711, 1715),
    ("hand.R", 1831, 1835),
]

# 是否把插值后关键帧设为线性
SET_LINEAR = True

# ===== 一般不用改 =====

ARM_CHAINS = {
    "hand.L": ["shoulder.L", "upper_arm.L", "forearm.L", "hand.L"],
    "hand.R": ["shoulder.R", "upper_arm.R", "forearm.R", "hand.R"],
}


def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_action(armature):
    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("No action found. Please manual bake first.")
    return armature.animation_data.action


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value

    if SET_LINEAR:
        kp.interpolation = "LINEAR"

    return kp


def normalize_quat(values):
    length = math.sqrt(sum(v * v for v in values))
    if length < 1e-8:
        return values
    return [v / length for v in values]


def interpolate_fcurve_group(action, data_path, count, start, end, is_quat=False):
    """
    用 start-1 和 end+1 的值，替换 start..end。
    """
    prev_frame = start - 1
    next_frame = end + 1

    fcurves = [get_fcurve(action, data_path, i) for i in range(count)]

    if any(fc is None for fc in fcurves):
        return False

    prev_vals = [fc.evaluate(prev_frame) for fc in fcurves]
    next_vals = [fc.evaluate(next_frame) for fc in fcurves]

    if is_quat:
        # 防止四元数符号翻转导致走远路
        dot = sum(prev_vals[i] * next_vals[i] for i in range(4))
        if dot < 0:
            next_vals = [-v for v in next_vals]

    for frame in range(start, end + 1):
        t = (frame - prev_frame) / (next_frame - prev_frame)
        vals = [
            prev_vals[i] * (1.0 - t) + next_vals[i] * t
            for i in range(count)
        ]

        if is_quat:
            vals = normalize_quat(vals)

        for i, fc in enumerate(fcurves):
            set_value(fc, frame, vals[i])

    return True


def repair_bone(action, bone_name, start, end):
    """
    尝试修一个骨骼的旋转和位置。
    FreeMoCap bake 后通常主要是 rotation，也可能有 location。
    """
    changed = []

    groups = [
        (f'pose.bones["{bone_name}"].rotation_quaternion', 4, True),
        (f'pose.bones["{bone_name}"].rotation_euler', 3, False),
        (f'pose.bones["{bone_name}"].location', 3, False),
    ]

    for data_path, count, is_quat in groups:
        ok = interpolate_fcurve_group(
            action=action,
            data_path=data_path,
            count=count,
            start=start,
            end=end,
            is_quat=is_quat,
        )
        if ok:
            changed.append(data_path)

    return changed


def main():
    scene = bpy.context.scene

    armature = find_armature(ARMATURE_NAME)
    action = get_action(armature)

    print("========================================")
    print("[manual hand repair]")
    print(f"Armature: {armature.name}")
    print(f"Action:   {action.name}")
    print(f"Scene range: {scene.frame_start}-{scene.frame_end}")
    print("========================================")

    for hand_bone, start, end in MANUAL_REPAIR_RANGES:
        if start < scene.frame_start or end > scene.frame_end:
            print(f"[skip] {hand_bone} {start}-{end}: outside scene frame range")
            continue

        chain = ARM_CHAINS.get(hand_bone)
        if not chain:
            print(f"[skip] no chain for {hand_bone}")
            continue

        print(f"\n[repair range] {hand_bone}: {start}-{end}")
        print(f"reference frames: {start - 1}, {end + 1}")
        print(f"chain: {chain}")

        for bone in chain:
            if bone not in armature.pose.bones:
                print(f"  [missing bone] {bone}")
                continue

            changed = repair_bone(action, bone, start, end)

            if changed:
                print(f"  [fixed] {bone}")
                for ch in changed:
                    print(f"      {ch}")
            else:
                print(f"  [no editable fcurves] {bone}")

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("\n========================================")
    print(f"[saved] {out}")
    print("========================================")


if __name__ == "__main__":
    main()
```

---

# 5. 推荐你在 GUI 里运行这个脚本

## 操作方法

1. 直接打开 Blender。
2. 打开：

```text
F:\mocap_ai_doctor\blends\source_baked.blend
```

3. 切到顶部：

```text
Scripting
```

4. 点 `New` 新建文本。
5. 把上面的脚本粘进去。
6. 确认顶部这些值正确：

```python
ARMATURE_NAME = "import_synchronized_videos_rig"
OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/source_baked_hands_manual_fixed.blend"

MANUAL_REPAIR_RANGES = [
    ("hand.L", 1711, 1715),
    ("hand.R", 1831, 1835),
]
```

7. 点 `Run Script`。

它会另存为：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed.blend
```

不会覆盖原文件。

---

# 6. 如果你还是想命令行运行

也可以：

```bash
"/mnt/d/blender-3.2.1-windows-x64/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_baked.blend" \
  --python "F:/mocap_ai_doctor/scripts/repair_manual_hand_ranges.py" \
  --python-exit-code 1
```

但现在我更建议 GUI 里跑，方便你马上看结果。

---

# 7. 跑完后如何判断？

打开：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed.blend
```

重点看：

```text
1710–1716
1830–1836
```

预期效果：

- 1711–1715 左手不再卷进肚子；
- 1831–1835 右手外翻明显减轻；
- 如果动作变得稍微“直线过渡”，这是正常的；
- 舞蹈里这几帧一般肉眼更能接受。

然后再跑 analyzer 看 hand_jump：

```bash
"/mnt/d/blender-3.2.1-windows-x64/blender.exe" \
  --background "F:/mocap_ai_doctor/blends/source_baked_hands_manual_fixed.blend" \
  --python "F:/mocap_ai_doctor/scripts/mocap_doctor_analyze.py" \
  --python-exit-code 1 \
  -- "F:/mocap_ai_doctor/configs/analyze_source.json"
```

注意把 config 里的输出改成：

```json
"output_report": "F:/mocap_ai_doctor/reports/report_hands_manual_fixed.json"
```

---

# 8. 如果这版仍然肉眼没修好，最可能原因

## 原因 A：坏姿态来源在更上游

比如来自：

```text
spine
spine.001
neck
pelvis
```

这种情况下只修肩/臂不够。

但你描述的是“手卷进肚子、手外翻”，更像手臂链问题，不像骨盆/脊柱。

## 原因 B：动作不是由这些 fcurve 决定

虽然你已经手动 bake 了，但有可能某些约束/驱动还在影响。  
不过你的 action 现在是 `"Action"`，说明已经比之前 `null` 好很多。

## 原因 C：坏区间选短了

比如左手其实是：

```text
1710–1717
```

那修：

```text
1711–1715
```

效果会有限。  
可以扩大成：

```python
("hand.L", 1710, 1717)
```

右手也可以扩大：

```python
("hand.R", 1830, 1836)
```

这是现在最实用的调参方式。

---

# 9. 关于整体骨架轻微歪

你说：

> 全程整个骨架都有点朝一侧歪一个较小的角度，估计是地平面估计歪了，Blender 里面整体旋转一下就行了吧？

可以，但我建议**不要现在直接转骨架骨骼本身**。

更稳的做法是后面加一层：

```text
Empty / root correction
```

或者改：

```text
import_mocap2_origin
```

这类外层对象的旋转，而不是直接改每根骨骼。

如果只是整个动作统一歪一点，后面可以用：

```text
全局校正层
```

一次解决，不要现在混到 hand repair 里。

---

# 10. 下一步路线

你现在先跑这版人工区间修复。

如果好了，我们继续：

1. 做脚部“接触段识别”，不是粗糙 foot_slide_suspected；
2. 结合 `foot.L/R` 和 `heel.02.L/R` 找真实落地段；
3. 暂时不直接修源脚；
4. 重定向到 Teto 后，用类似你给的 `K + 接触点 + root compensation` 思路修目标模型脚滑。

这条线比直接在源骨架上强行 foot lock 更稳。
[1] [Blender, slow start-up](https://blenderartists.org/t/blender-slow-start-up/684833)

[2] [New Command Line Arguments](https://devtalk.blender.org/t/new-command-line-arguments/3074)
---
## 🧑‍💻 User

这一点就算搞定！效果不错，只是这样一个个填关键帧区间很麻烦，以后看能不能写个gui，在开始和结束各按一下键盘上的键标记会方便很多。现在整体动作还有点颤颤巍巍的，脚插进地板和整个人会时不时稍微飞起来一点，手严重骨折，按你的计划下一步吧。关于整体骨架轻微歪，你给的方法我没看懂，先不管了

---
## 🤖 Assistant

太好了，手部这条链路跑通就算第一阶段成功了一半。你现在遇到的几个问题，我建议按这个顺序处理：

```text
1. 手部严重骨折：
   继续用“人工区间 + 手臂链插值”修。
   以后再做快捷标记 GUI。

2. 整体颤颤巍巍：
   先做轻度旋转平滑，不动 pelvis 位移，不动 root 大位移。
   目标：去掉高频抖动，但不把舞蹈动作抹平。

3. 脚插地：
   做一个保守的“只抬不压”的地板穿透修复。
   目标：脚/脚跟插进地板时，整体 pelvis 稍微抬起来。

4. 整个人偶尔飞起来：
   这个先不强修。
   因为可能是真实跳动，也可能是接触识别问题。
   之后要结合 foot contact 判断，不能简单往下压。
```

你说“整体骨架轻微歪”先不管，这个没问题，后面统一处理。

---

# 一、关于以后做 GUI 标记

你的想法很好：

> 在开始帧按一下键，结束帧按一下键，自动记录坏区间。

这个完全可以做。Blender 里有几种方式：

1. 用 Timeline Marker；
2. 写一个小面板；
3. 写快捷键 operator；
4. 用 `Text Editor` 脚本临时记录当前帧。

以后可以做成这样：

```text
当前帧 1711，按 Alt+1：标记 hand.L start
当前帧 1715，按 Alt+2：标记 hand.L end
当前帧 1831，按 Alt+3：标记 hand.R start
当前帧 1835，按 Alt+4：标记 hand.R end
点击 Run Repair
```

但现在先别做 UI，先把修复算法跑稳。

---

# 二、下一步先做：整体轻度平滑

你说动作“颤颤巍巍”，这通常是 FreeMoCap / 光学动捕里比较常见的高频噪声。

我们先做一个**保守平滑脚本**：

- 只平滑旋转；
- 不平滑 pelvis 的位置；
- 不直接改 root 位移；
- 不动时间线外；
- 保存新文件；
- 可以反复调强度。

---

## 1. 新建脚本：`repair_mild_rotation_smooth.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\repair_mild_rotation_smooth.py
```

内容：

```python
import bpy
import math
from pathlib import Path


# =========================
# 配置区
# =========================

ARMATURE_NAME = "import_synchronized_videos_rig"

INPUT_NOTE = "Run this script inside Blender after opening the blend you want to smooth."

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/source_baked_hands_manual_fixed_smooth.blend"

# 平滑半径：2 表示用前后 2 帧，总共 5 帧窗口
RADIUS = 2

# 平滑强度：
# 0.0 = 不改
# 1.0 = 完全替换为平滑值
# 建议先 0.35 ~ 0.55
STRENGTH = 0.45

# 是否只处理当前时间线范围
USE_SCENE_FRAME_RANGE = True

# 需要平滑的骨骼
# 先排除 pelvis 的 location，只平滑旋转。
# heel.02 可以先不平滑，避免接触点被抹。
SMOOTH_BONES = [
    "pelvis",

    "spine",
    "spine.001",
    "neck",

    "shoulder.L",
    "upper_arm.L",
    "forearm.L",
    "hand.L",

    "shoulder.R",
    "upper_arm.R",
    "forearm.R",
    "hand.R",

    "pelvis.L",
    "thigh.L",
    "shin.L",
    "foot.L",

    "pelvis.R",
    "thigh.R",
    "shin.R",
    "foot.R",
]

# 是否平滑手部。你现在手部有严重坏帧，建议：
# 已经手动修过之后，可以 True。
# 如果还有很多没修的骨折段，先 False。
INCLUDE_HANDS = True


# =========================
# 工具函数
# =========================

def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_action(armature):
    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("No action found. Please manual bake first.")
    return armature.animation_data.action


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"


def normalize_quat(vals):
    length = math.sqrt(sum(v * v for v in vals))
    if length < 1e-8:
        return vals
    return [v / length for v in vals]


def gaussian_weights(radius):
    if radius <= 0:
        return [1.0]

    sigma = max(1.0, radius / 1.5)
    weights = []
    for i in range(-radius, radius + 1):
        w = math.exp(-(i * i) / (2.0 * sigma * sigma))
        weights.append(w)

    s = sum(weights)
    return [w / s for w in weights]


def smooth_fcurve_values(fcurve, frame_start, frame_end, radius, strength):
    frames = list(range(frame_start, frame_end + 1))
    original = {f: fcurve.evaluate(f) for f in frames}

    weights = gaussian_weights(radius)
    offsets = list(range(-radius, radius + 1))

    result = {}

    for frame in frames:
        weighted = 0.0
        total = 0.0

        for off, w in zip(offsets, weights):
            ff = frame + off
            if ff < frame_start or ff > frame_end:
                continue
            weighted += original[ff] * w
            total += w

        if total <= 1e-8:
            smoothed = original[frame]
        else:
            smoothed = weighted / total

        result[frame] = original[frame] * (1.0 - strength) + smoothed * strength

    return result


def smooth_rotation_group(action, bone_name, frame_start, frame_end):
    changed = False

    # 优先处理 quaternion，如果没有，再处理 euler
    quat_path = f'pose.bones["{bone_name}"].rotation_quaternion'
    quat_curves = [get_fcurve(action, quat_path, i) for i in range(4)]

    if all(fc is not None for fc in quat_curves):
        channel_results = [
            smooth_fcurve_values(fc, frame_start, frame_end, RADIUS, STRENGTH)
            for fc in quat_curves
        ]

        for frame in range(frame_start, frame_end + 1):
            vals = [channel_results[i][frame] for i in range(4)]
            vals = normalize_quat(vals)
            for i, fc in enumerate(quat_curves):
                set_value(fc, frame, vals[i])

        return True

    euler_path = f'pose.bones["{bone_name}"].rotation_euler'
    euler_curves = [get_fcurve(action, euler_path, i) for i in range(3)]

    if all(fc is not None for fc in euler_curves):
        channel_results = [
            smooth_fcurve_values(fc, frame_start, frame_end, RADIUS, STRENGTH)
            for fc in euler_curves
        ]

        for frame in range(frame_start, frame_end + 1):
            for i, fc in enumerate(euler_curves):
                set_value(fc, frame, channel_results[i][frame])

        changed = True

    return changed


def main():
    scene = bpy.context.scene
    armature = find_armature(ARMATURE_NAME)
    action = get_action(armature)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    print("====================================")
    print("[mild rotation smooth]")
    print(f"Armature: {armature.name}")
    print(f"Action:   {action.name}")
    print(f"Frames:   {frame_start}-{frame_end}")
    print(f"Radius:   {RADIUS}")
    print(f"Strength: {STRENGTH}")
    print("====================================")

    for bone in SMOOTH_BONES:
        if not INCLUDE_HANDS and bone in ["hand.L", "hand.R", "forearm.L", "forearm.R"]:
            continue

        if bone not in armature.pose.bones:
            print(f"[missing] {bone}")
            continue

        ok = smooth_rotation_group(action, bone, frame_start, frame_end)

        if ok:
            print(f"[smoothed] {bone}")
        else:
            print(f"[no rotation fcurves] {bone}")

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("====================================")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

## 2. 怎么运行

你现在为了速度，建议在 GUI 里运行：

1. 打开 Blender。
2. 打开你刚刚手部修好的文件：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed.blend
```

3. 切到 `Scripting`。
4. 新建 Text。
5. 粘贴 `repair_mild_rotation_smooth.py`。
6. 运行。

输出文件会是：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed_smooth.blend
```

---

## 3. 平滑结果怎么判断？

重点看：

```text
动作是否不再颤；
舞蹈节奏是否还在；
手臂是否不再抽；
脚是否没有明显被抹糊。
```

如果动作还是抖，把：

```python
STRENGTH = 0.45
```

改成：

```python
STRENGTH = 0.6
```

如果动作变软、变糊，把它改成：

```python
STRENGTH = 0.3
```

建议范围：

```text
0.30 ~ 0.60
```

不要一上来 0.9。

---

# 三、下一步：修脚插地，但只做保守修复

你现在说的“脚插进地板”和“整个人飞起来”其实是两个相反问题：

```text
脚插地：最低脚点低于地板，需要抬人。
人飞起来：最低脚点高于地板，可能需要压人。
```

但“人飞起来”不一定是错误，因为舞蹈可能有踮脚、跳、抬脚、重心起伏。  
所以我们下一刀只修：

> **脚/脚跟低于地板时，整体 pelvis 往上抬一点。**

暂时不做往下压，避免把真实跳跃、踮脚、抬腿压坏。

---

## 1. 新建脚本：`repair_floor_penetration_pelvis_z.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\repair_floor_penetration_pelvis_z.py
```

内容：

```python
import bpy
import math
from pathlib import Path


# =========================
# 配置区
# =========================

ARMATURE_NAME = "import_synchronized_videos_rig"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/source_baked_hands_manual_fixed_smooth_floor.blend"

ROOT_BONE = "pelvis"

CONTACT_BONES = [
    "foot.L",
    "foot.R",
    "heel.02.L",
    "heel.02.R",
]

# 地板高度。
# 如果为 None，则自动估计。
# 你之前 report 约为 0.02419。
# 如果你确定地板是 0，可以改成 0.0。
FLOOR_Z = None

# 自动估计地面时使用最低点分位数
FLOOR_PERCENTILE = 0.01

# 允许轻微插地，单位米
TOLERANCE = 0.015

# 希望脚底最终略高于地板多少
TARGET_CLEARANCE = 0.005

# 单帧最大抬升，避免异常帧把人抬飞
MAX_LIFT_PER_FRAME = 0.12

# 对抬升量做平滑，避免一帧一帧抖
CORRECTION_SMOOTH_RADIUS = 3

# 修复强度
# 1.0 = 完全抬到目标高度
# 0.5 = 只修一半
STRENGTH = 0.85


# =========================
# 工具函数
# =========================

def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_action(armature):
    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("No action found. Please manual bake first.")
    return armature.animation_data.action


def bone_world_loc(armature, bone_name):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None
    return (armature.matrix_world @ pb.matrix).translation.copy()


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def ensure_fcurve(action, data_path, index):
    fc = get_fcurve(action, data_path, index)
    if fc is not None:
        return fc
    return action.fcurves.new(data_path=data_path, index=index)


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"


def gaussian_weights(radius):
    if radius <= 0:
        return [1.0], [0]

    sigma = max(1.0, radius / 1.5)
    offsets = list(range(-radius, radius + 1))
    weights = []

    for i in offsets:
        w = math.exp(-(i * i) / (2.0 * sigma * sigma))
        weights.append(w)

    s = sum(weights)
    weights = [w / s for w in weights]

    return weights, offsets


def smooth_dict_values(values_by_frame, frame_start, frame_end, radius):
    weights, offsets = gaussian_weights(radius)
    out = {}

    for frame in range(frame_start, frame_end + 1):
        total = 0.0
        acc = 0.0

        for w, off in zip(weights, offsets):
            ff = frame + off
            if ff < frame_start or ff > frame_end:
                continue
            acc += values_by_frame.get(ff, 0.0) * w
            total += w

        out[frame] = acc / total if total > 1e-8 else values_by_frame.get(frame, 0.0)

    return out


def main():
    scene = bpy.context.scene
    armature = find_armature(ARMATURE_NAME)
    action = get_action(armature)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    print("====================================")
    print("[floor penetration repair]")
    print(f"Armature: {armature.name}")
    print(f"Action:   {action.name}")
    print(f"Frames:   {frame_start}-{frame_end}")
    print("====================================")

    valid_contact_bones = [b for b in CONTACT_BONES if b in armature.pose.bones]

    if not valid_contact_bones:
        raise RuntimeError("No contact bones found.")

    # 1. 采样最低脚点
    min_z_by_frame = {}
    all_z = []

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)

        zs = []
        for bone in valid_contact_bones:
            loc = bone_world_loc(armature, bone)
            if loc is not None:
                zs.append(float(loc.z))
                all_z.append(float(loc.z))

        if zs:
            min_z_by_frame[frame] = min(zs)
        else:
            min_z_by_frame[frame] = None

    # 2. 地板估计
    if FLOOR_Z is None:
        floor_z = percentile(all_z, FLOOR_PERCENTILE)
    else:
        floor_z = float(FLOOR_Z)

    print(f"[floor_z] {floor_z:.5f}")

    # 3. 计算每帧需要抬升量
    raw_correction = {}

    for frame in range(frame_start, frame_end + 1):
        min_z = min_z_by_frame.get(frame)

        if min_z is None:
            raw_correction[frame] = 0.0
            continue

        target_z = floor_z + TARGET_CLEARANCE
        penetration = target_z - min_z

        if penetration > TOLERANCE:
            lift = min(penetration, MAX_LIFT_PER_FRAME)
            raw_correction[frame] = lift * STRENGTH
        else:
            raw_correction[frame] = 0.0

    # 4. 平滑抬升量
    correction = smooth_dict_values(
        raw_correction,
        frame_start,
        frame_end,
        CORRECTION_SMOOTH_RADIUS
    )

    # 5. 写入 pelvis location.z
    data_path = f'pose.bones["{ROOT_BONE}"].location'
    z_curve = ensure_fcurve(action, data_path, 2)

    changed_frames = 0
    max_lift = 0.0

    for frame in range(frame_start, frame_end + 1):
        lift = correction.get(frame, 0.0)

        if abs(lift) < 1e-8:
            continue

        original_z = z_curve.evaluate(frame)
        new_z = original_z + lift

        set_value(z_curve, frame, new_z)

        changed_frames += 1
        max_lift = max(max_lift, lift)

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[changed_frames] {changed_frames}")
    print(f"[max_lift] {max_lift:.5f} m")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

## 2. 怎么运行

先打开平滑后的文件：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed_smooth.blend
```

在 Blender 的 `Scripting` 里运行上面脚本。

输出：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed_smooth_floor.blend
```

---

## 3. 如果修完人被抬得太多

改这几个参数：

```python
STRENGTH = 0.85
```

改低一点：

```python
STRENGTH = 0.5
```

或者：

```python
MAX_LIFT_PER_FRAME = 0.12
```

改成：

```python
MAX_LIFT_PER_FRAME = 0.06
```

---

# 四、手严重骨折怎么办？

你现在先继续用之前成功的手动区间脚本。

如果看到新的坏区间，比如：

```text
hand.L 2100–2108
hand.R 2302–2307
```

就加入：

```python
MANUAL_REPAIR_RANGES = [
    ("hand.L", 1711, 1715),
    ("hand.R", 1831, 1835),
    ("hand.L", 2100, 2108),
    ("hand.R", 2302, 2307),
]
```

你说这样麻烦，这是对的。  
等我们把脚和平滑流程跑通，我建议马上做一个小工具：

```text
current frame → add bad range start
current frame → add bad range end
auto repair all marked ranges
```

这个会很实用。

---

# 五、你现在按这个顺序来

建议文件链路：

```text
source_baked.blend
    ↓ 手动区间修手
source_baked_hands_manual_fixed.blend
    ↓ 轻度旋转平滑
source_baked_hands_manual_fixed_smooth.blend
    ↓ 脚插地保守修复
source_baked_hands_manual_fixed_smooth_floor.blend
```

现在你先做：

1. 运行 `repair_mild_rotation_smooth.py`
2. 看动作是否少抖
3. 如果可以，再运行 `repair_floor_penetration_pelvis_z.py`
4. 看脚插地有没有改善
5. 不要急着修“飞起来”，那个下一步要用接触段判断

如果这两步效果不错，下一步我们再做：

> **脚部接触段识别 + 目标 MMD/Teto 上的脚 IK 稳定方案。**

---
## 🧑‍💻 User

我压根不会修手，平滑脚本里面包括手这个值给你改成False了，平滑结果不错。修脚插地，地板高度默认的自动计算有点不够，我改成了report 里面的0.02，虽然每次弯膝盖还是会像是踩在棉花糖上面，但有改善，现在脚跟只会在弯膝盖的时候有轻微上下浮动了，但是脚前面部分经常插进地里。继续吧。

---
## 🤖 Assistant

很好，现在阶段进度是：

```text
✅ 手部单段骨折：人工区间插值可用
✅ 整体颤抖：轻度旋转平滑有效
✅ 脚跟插地：pelvis Z 保守抬升有改善
❌ 脚前部经常插地：当前脚本没真正监测“脚尖/脚掌前端”
⚠ 弯膝盖像踩棉花糖：pelvis Z 修正有点跟着脚部噪声起伏
```

你现在这个结果很合理。原因是上一版地板修复脚本只看了这些点：

```python
"foot.L",
"foot.R",
"heel.02.L",
"heel.02.R"
```

但我们采样的是骨骼的 `matrix.translation`，通常更接近骨骼头部/关节位置，不一定是脚掌前端。你看到“脚前面部分经常插进地里”，说明我们还缺一个关键采样点：

> **foot.L / foot.R 的 tail，也就是脚骨末端，往往更接近脚前掌/脚尖方向。**

所以下一步要做：

> **地板修复 v2：同时检查 foot 骨骼的 head 和 tail，尤其是 foot tail。**

---

# 一、为什么脚跟好了，脚前掌还插地？

你的 FreeMoCap 源骨架大概是这样：

```text
shin.L
  ↓
foot.L       可能从脚踝指向脚掌/脚尖方向
  ↓
heel.02.L    脚后跟辅助骨
```

上一版我们采样：

```python
pose_bone.matrix.translation
```

这个位置大概率是骨骼头部，也就是接近：

```text
foot.L 的脚踝端
heel.02.L 的脚后跟端
```

但“脚前掌插地”对应的是：

```text
foot.L 的骨骼末端 / tail
```

所以这次我们要把接触点改成：

```text
foot.L:head
foot.L:tail
foot.R:head
foot.R:tail
heel.02.L:head
heel.02.L:tail
heel.02.R:head
heel.02.R:tail
```

这样脚前部插地就能被检测到。

---

# 二、关于“踩棉花糖”的原因

你说：

> 每次弯膝盖还是会像是踩在棉花糖上面。

这个一般来自两种情况：

## 情况 A：pelvis Z 跟着脚部噪声上下修正

我们用 pelvis 抬升来防止脚穿地，本质是：

```text
脚低于地板 → 抬 pelvis
```

如果脚部检测点本身抖，就会变成：

```text
脚抖 → pelvis 跟着抖 → 人像踩棉花糖
```

## 情况 B：弯膝盖时真实骨架比例和地板估计不完全一致

尤其是 FreeMoCap 光学数据，膝盖、脚踝、脚跟在弯曲时可能有小幅估计误差。

所以这次 v2 脚本会做两件事：

1. 加入脚前掌检测；
2. 对 pelvis Z 修正做“缓入缓出”，避免一帧一帧弹。

但仍然要记住：  
**源阶段只做保守修，不追求最终脚底锁死。最终脚部稳定要在 Teto/MMD 目标 IK 上做。**

---

# 三、新脚本：脚前掌/脚跟地板穿透修复 v2

保存为：

```text
F:\mocap_ai_doctor\scripts\repair_floor_penetration_pelvis_z_v2.py
```

内容如下。

---

```python
import bpy
import math
from pathlib import Path
from mathutils import Vector


# =========================
# 配置区
# =========================

ARMATURE_NAME = "import_synchronized_videos_rig"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/source_baked_hands_manual_fixed_smooth_floor_v2.blend"

ROOT_BONE = "pelvis"

# 地板高度。
# 你现在觉得 0.02 比自动好，就直接用 0.02。
FLOOR_Z = 0.02

# 采样点：
# head = 骨骼头部
# tail = 骨骼尾部
# foot tail 通常更接近脚前掌/脚尖方向
CONTACT_POINTS = [
    ("foot.L", "head"),
    ("foot.L", "tail"),
    ("foot.R", "head"),
    ("foot.R", "tail"),

    ("heel.02.L", "head"),
    ("heel.02.L", "tail"),
    ("heel.02.R", "head"),
    ("heel.02.R", "tail"),
]

# 允许轻微穿地，单位米
# 如果设太小，会导致 pelvis 很敏感，像踩棉花糖。
TOLERANCE = 0.012

# 修完后希望最低点离地板多高
TARGET_CLEARANCE = 0.004

# 每帧最大抬升，避免异常点把人抬飞
MAX_LIFT_PER_FRAME = 0.08

# 修复强度
# 1.0 完全抬到目标高度
# 0.6 更保守
STRENGTH = 0.75

# 对修正曲线做平滑
# 半径越大越不抖，但可能更“棉花糖”
# 建议 2~4
CORRECTION_SMOOTH_RADIUS = 2

# 限制修正量每帧变化，防止 pelvis Z 颤抖
# 单位：米/帧
MAX_CORRECTION_DELTA_PER_FRAME = 0.018

# 是否输出每帧最低点来自哪个 contact point
PRINT_WORST_POINTS = True
PRINT_LIMIT = 80


# =========================
# 工具函数
# =========================

def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_action(armature):
    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("No action found. Please manual bake first.")
    return armature.animation_data.action


def get_pose_bone_point_world(armature, bone_name, point_type):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None

    # pb.head / pb.tail 是 armature object space 下的 pose 位置
    if point_type == "head":
        p = pb.head.copy()
    elif point_type == "tail":
        p = pb.tail.copy()
    else:
        raise ValueError(f"Unknown point type: {point_type}")

    return armature.matrix_world @ p


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def ensure_fcurve(action, data_path, index):
    fc = get_fcurve(action, data_path, index)
    if fc:
        return fc
    return action.fcurves.new(data_path=data_path, index=index)


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"


def gaussian_weights(radius):
    if radius <= 0:
        return [1.0], [0]

    sigma = max(1.0, radius / 1.5)
    offsets = list(range(-radius, radius + 1))
    weights = []

    for off in offsets:
        w = math.exp(-(off * off) / (2.0 * sigma * sigma))
        weights.append(w)

    s = sum(weights)
    weights = [w / s for w in weights]
    return weights, offsets


def smooth_values(values_by_frame, frame_start, frame_end, radius):
    weights, offsets = gaussian_weights(radius)
    out = {}

    for frame in range(frame_start, frame_end + 1):
        acc = 0.0
        total = 0.0

        for w, off in zip(weights, offsets):
            ff = frame + off
            if ff < frame_start or ff > frame_end:
                continue
            acc += values_by_frame.get(ff, 0.0) * w
            total += w

        if total <= 1e-8:
            out[frame] = values_by_frame.get(frame, 0.0)
        else:
            out[frame] = acc / total

    return out


def limit_delta(values_by_frame, frame_start, frame_end, max_delta):
    """
    限制修正量每帧变化，避免突然弹。
    前向一次，后向一次。
    """
    out = dict(values_by_frame)

    # forward
    prev = out.get(frame_start, 0.0)
    for frame in range(frame_start + 1, frame_end + 1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    # backward
    prev = out.get(frame_end, 0.0)
    for frame in range(frame_end - 1, frame_start - 1, -1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    return out


def main():
    scene = bpy.context.scene
    armature = find_armature(ARMATURE_NAME)
    action = get_action(armature)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    print("====================================")
    print("[floor penetration repair v2]")
    print(f"Armature: {armature.name}")
    print(f"Action:   {action.name}")
    print(f"Frames:   {frame_start}-{frame_end}")
    print(f"Floor Z:  {FLOOR_Z}")
    print("====================================")

    valid_points = []
    for bone_name, point_type in CONTACT_POINTS:
        if bone_name in armature.pose.bones:
            valid_points.append((bone_name, point_type))
        else:
            print(f"[missing contact bone] {bone_name}")

    if not valid_points:
        raise RuntimeError("No valid contact points found.")

    # 1. 每帧找最低接触点
    min_z_by_frame = {}
    source_by_frame = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)

        lowest_z = None
        lowest_source = None

        for bone_name, point_type in valid_points:
            loc = get_pose_bone_point_world(armature, bone_name, point_type)
            if loc is None:
                continue

            z = float(loc.z)
            if lowest_z is None or z < lowest_z:
                lowest_z = z
                lowest_source = f"{bone_name}:{point_type}"

        min_z_by_frame[frame] = lowest_z
        source_by_frame[frame] = lowest_source

    # 2. 计算 raw correction
    raw = {}
    worst = []

    target_z = FLOOR_Z + TARGET_CLEARANCE

    for frame in range(frame_start, frame_end + 1):
        min_z = min_z_by_frame.get(frame)

        if min_z is None:
            raw[frame] = 0.0
            continue

        penetration = target_z - min_z

        if penetration > TOLERANCE:
            lift = min(penetration, MAX_LIFT_PER_FRAME)
            lift *= STRENGTH
            raw[frame] = lift

            worst.append((frame, min_z, penetration, lift, source_by_frame.get(frame)))
        else:
            raw[frame] = 0.0

    # 3. 平滑修正量
    smoothed = smooth_values(raw, frame_start, frame_end, CORRECTION_SMOOTH_RADIUS)

    # 4. 限制每帧变化
    corrected = limit_delta(
        smoothed,
        frame_start,
        frame_end,
        MAX_CORRECTION_DELTA_PER_FRAME
    )

    # 5. 写入 pelvis location.z
    data_path = f'pose.bones["{ROOT_BONE}"].location'
    z_curve = ensure_fcurve(action, data_path, 2)

    changed_frames = 0
    max_lift = 0.0

    for frame in range(frame_start, frame_end + 1):
        lift = corrected.get(frame, 0.0)
        if abs(lift) < 1e-8:
            continue

        original_z = z_curve.evaluate(frame)
        new_z = original_z + lift

        set_value(z_curve, frame, new_z)

        changed_frames += 1
        max_lift = max(max_lift, lift)

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[changed_frames] {changed_frames}")
    print(f"[max_lift] {max_lift:.5f} m")

    if PRINT_WORST_POINTS:
        print("------------------------------------")
        print("[worst penetration samples]")
        for item in worst[:PRINT_LIMIT]:
            frame, min_z, penetration, lift, source = item
            print(
                f"frame={frame}, min_z={min_z:.4f}, "
                f"penetration={penetration:.4f}, lift={lift:.4f}, source={source}"
            )

        if len(worst) > PRINT_LIMIT:
            print(f"... {len(worst) - PRINT_LIMIT} more")

    print("------------------------------------")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 四、怎么运行

你现在应该从这个文件继续：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed_smooth.blend
```

也就是：

```text
手动修手 → 平滑
```

然后运行这个 v2 地板修复脚本。

## 推荐 GUI 运行

1. 打开：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed_smooth.blend
```

2. 切到 `Scripting`
3. 新建 Text
4. 粘贴脚本
5. Run Script

输出：

```text
F:\mocap_ai_doctor\blends\source_baked_hands_manual_fixed_smooth_floor_v2.blend
```

---

# 五、跑完以后看什么

重点看三件事：

## 1. 脚前掌插地是否减少

尤其是弯膝盖的时候：

```text
foot.L tail
foot.R tail
```

应该比之前更少插地。

## 2. 踩棉花糖是否加重

如果加重，说明 pelvis Z 修正太敏感。

优先改：

```python
STRENGTH = 0.75
```

改成：

```python
STRENGTH = 0.55
```

其次改：

```python
MAX_LIFT_PER_FRAME = 0.08
```

改成：

```python
MAX_LIFT_PER_FRAME = 0.05
```

## 3. 人有没有被抬飞

如果部分帧突然整个人往上弹，说明某个接触点异常低。

改：

```python
MAX_LIFT_PER_FRAME = 0.08
```

为：

```python
MAX_LIFT_PER_FRAME = 0.04
```

---

# 六、如果脚前掌还是插地

那说明不是 pelvis 高度问题，而是：

> **脚掌旋转/脚骨 pitch 有问题。**

也就是：

```text
脚跟高度差不多对
但脚尖/前掌向下扎进地板
```

这时继续抬 pelvis 会导致：

```text
脚跟浮起来
人像踩棉花糖
但脚尖仍可能扎
```

如果 v2 后仍然是这种情况，下一步就不要再用 pelvis 抬升了，而要做：

> **foot pitch 修复：当 foot tail 低于 floor，而 foot head/heel 正常时，轻微旋转 foot.L/R，把脚前掌抬起来。**

不过这个在源骨架上修风险比 pelvis Z 高一点，因为它会直接改变脚姿态。  
我们先跑 v2，看看情况再决定。

---

# 七、为什么现在还不做“人飞起来往下压”

你现在说“整个人会时不时稍微飞起来一点”，但这个不能马上压，因为舞蹈里有：

- 踮脚；
- 跳步；
- 重心抬升；
- 换脚；
- 弯膝盖反弹。

如果我们简单写：

```text
最低脚点高于地板 → pelvis 往下压
```

就会破坏真实动作。

所以“下压”必须等我们能判断：

```text
哪只脚处于 contact state
```

之后再做。  
这就是下一阶段的脚部接触段识别。

---

# 八、接下来的分支

你跑完 v2 后告诉我一句：

```text
A. 前掌插地明显好了，但棉花糖略有
B. 前掌插地没好，脚跟反而浮了
C. 人被抬得太多
D. 整体效果可接受
```

根据结果决定下一步：

## 如果是 A / D

下一步做：

```text
脚部接触段识别 report
```

用于后面 MMD/Teto IK 脚锁。

## 如果是 B

下一步做：

```text
foot pitch 修复
```

只抬脚前掌，不再抬 pelvis。

## 如果是 C

下一步降低 pelvis 修正，改成更保守的 correction curve。

现在先跑 `repair_floor_penetration_pelvis_z_v2.py`。

---
## 🧑‍💻 User

跑完了，你真牛逼，一遍过，效果很好。继续吧

---
## 🤖 Assistant

牛，这说明我们现在这条“源数据清理链路”是成立的：

```text
手动烘焙
  ↓
人工区间修明显手部骨折
  ↓
轻度旋转平滑
  ↓
脚前掌/脚跟地板穿透修复 v2
```

现在不要继续猛修源骨架了。源骨架阶段修太狠，后面重定向到 Teto 反而可能出新问题。

下一步按计划做：

> **脚部接触段识别 report。**

它暂时不改动画，只判断：

- 左脚哪些帧大概率踩地；
- 右脚哪些帧大概率踩地；
- 哪些帧是“近地但移动”，也就是可能滑步或换步；
- 哪些接触点最低：脚跟、脚尖/前掌、脚踝；
- 生成 JSON，后面重定向到 MMD/Teto 后用来指导脚 IK 锁定。

---

# 一、为什么现在要做“脚部接触段识别”

你现在源数据已经比较顺了，但最终 Teto 上仍可能脚滑。原因还是之前说过的：

```text
源数据脚不滑 ≠ Teto 脚不滑
```

因为：

- Teto 腿长不同；
- Teto 脚掌比例不同；
- ARP 重定向后骨盆高度会变；
- MMD 脚 IK 会改变最终落地点；
- 你本人和角色比例不同。

所以现在我们要先从干净源动作中提取一个信息：

> **什么时候应该锁左脚，什么时候应该锁右脚。**

这个信息比直接在源骨架上 foot lock 更有价值。

后面目标模型阶段可以用它做：

```text
左脚接触段 → 锁 Teto 左脚 IK
右脚接触段 → 锁 Teto 右脚 IK
双脚接触段 → 稳定 center / pelvis
无脚接触段 → 保留跳跃或腾空
```

---

# 二、当前文件先冻结一个版本

你现在这个效果好的文件建议复制/另存为：

```text
F:\mocap_ai_doctor\blends\source_clean_v1.blend
```

也就是把现在这个：

```text
source_baked_hands_manual_fixed_smooth_floor_v2.blend
```

另存一份叫：

```text
source_clean_v1.blend
```

以后如果后面修坏了，就回到这个版本。

---

# 三、新脚本：脚部接触段分析

保存为：

```text
F:\mocap_ai_doctor\scripts\analyze_foot_contacts.py
```

内容如下。

这个脚本只分析，不修改动画。  
它会输出：

```text
F:\mocap_ai_doctor\reports\foot_contacts_source_clean_v1.json
```

并且可选在 Blender 时间线里添加 marker，方便你肉眼检查。

---

```python
import bpy
import json
import math
from pathlib import Path


# =========================
# 配置区
# =========================

ARMATURE_NAME = "import_synchronized_videos_rig"

OUTPUT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v1.json"

# 你现在地板高度用 0.02 效果好，所以这里固定
FLOOR_Z = 0.02

# 是否在时间线添加 marker
ADD_TIMELINE_MARKERS = True

# 接触点定义
FOOT_POINTS = {
    "L": [
        ("foot.L", "head"),
        ("foot.L", "tail"),
        ("heel.02.L", "head"),
        ("heel.02.L", "tail"),
    ],
    "R": [
        ("foot.R", "head"),
        ("foot.R", "tail"),
        ("heel.02.R", "head"),
        ("heel.02.R", "tail"),
    ],
}

# 判定参数
# 接触高度：最低脚点离地多少以内，认为“接近地面”
CONTACT_HEIGHT = 0.045

# planted 判定：接近地面且水平速度较小
PLANTED_XY_SPEED = 0.018

# moving near floor 判定：接近地面但水平速度较大
MOVING_XY_SPEED = 0.018

# 垂直速度太大时，不认为是稳定接触
MAX_VERTICAL_SPEED_FOR_PLANTED = 0.018

# 最短接触段，太短的段认为是噪声
MIN_SEGMENT_LEN = 3

# 相隔几帧以内的接触段合并
MERGE_GAP = 2

# 如果脚最低点低于地板这个值，记录为 penetration sample
PENETRATION_TOLERANCE = 0.008


# =========================
# 工具函数
# =========================

def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_pose_bone_point_world(armature, bone_name, point_type):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None

    if point_type == "head":
        p = pb.head.copy()
    elif point_type == "tail":
        p = pb.tail.copy()
    else:
        raise ValueError(point_type)

    return armature.matrix_world @ p


def dist_xy(a, b):
    if a is None or b is None:
        return None
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)


def ranges_from_frames(frames, min_len=1, merge_gap=0):
    if not frames:
        return []

    frames = sorted(set(frames))
    raw = []

    start = prev = frames[0]
    for f in frames[1:]:
        if f == prev + 1:
            prev = f
        else:
            raw.append([start, prev])
            start = prev = f
    raw.append([start, prev])

    # merge close ranges
    merged = []
    for r in raw:
        if not merged:
            merged.append(r)
            continue

        last = merged[-1]
        if r[0] - last[1] <= merge_gap + 1:
            last[1] = r[1]
        else:
            merged.append(r)

    # filter short
    out = []
    for a, b in merged:
        if b - a + 1 >= min_len:
            out.append([a, b])

    return out


def sample_foot_side(armature, side, frame_start, frame_end):
    """
    返回每帧：
    - lowest_z
    - lowest_source
    - avg_xy_center
    - avg_z
    """
    scene = bpy.context.scene
    points = FOOT_POINTS[side]

    samples = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)

        locs = []
        sources = []

        for bone, point_type in points:
            if bone not in armature.pose.bones:
                continue

            loc = get_pose_bone_point_world(armature, bone, point_type)
            if loc is None:
                continue

            locs.append([float(loc.x), float(loc.y), float(loc.z)])
            sources.append(f"{bone}:{point_type}")

        if not locs:
            samples[frame] = None
            continue

        lowest_i = min(range(len(locs)), key=lambda i: locs[i][2])
        lowest = locs[lowest_i]

        avg_x = sum(p[0] for p in locs) / len(locs)
        avg_y = sum(p[1] for p in locs) / len(locs)
        avg_z = sum(p[2] for p in locs) / len(locs)

        samples[frame] = {
            "lowest_z": lowest[2],
            "lowest_source": sources[lowest_i],
            "avg_center": [avg_x, avg_y, avg_z],
            "point_count": len(locs),
        }

    return samples


def analyze_side(samples, frame_start, frame_end, side):
    planted_frames = []
    moving_near_floor_frames = []
    airborne_frames = []
    penetration_samples = []

    per_frame = {}

    prev_sample = None
    prev_frame = None

    for frame in range(frame_start, frame_end + 1):
        s = samples.get(frame)
        if s is None:
            continue

        lowest_z = s["lowest_z"]
        height_above_floor = lowest_z - FLOOR_Z

        xy_speed = 0.0
        vertical_speed = 0.0

        if prev_sample is not None:
            xy_speed = dist_xy(s["avg_center"], prev_sample["avg_center"])
            vertical_speed = abs(s["avg_center"][2] - prev_sample["avg_center"][2])

        near_floor = height_above_floor <= CONTACT_HEIGHT

        if near_floor and xy_speed <= PLANTED_XY_SPEED and vertical_speed <= MAX_VERTICAL_SPEED_FOR_PLANTED:
            state = "planted"
            planted_frames.append(frame)
        elif near_floor and xy_speed > MOVING_XY_SPEED:
            state = "near_floor_moving"
            moving_near_floor_frames.append(frame)
        else:
            state = "airborne_or_lifted"
            airborne_frames.append(frame)

        if lowest_z < FLOOR_Z - PENETRATION_TOLERANCE:
            penetration_samples.append({
                "frame": frame,
                "lowest_z": round(lowest_z, 5),
                "depth": round(FLOOR_Z - lowest_z, 5),
                "source": s["lowest_source"],
            })

        per_frame[frame] = {
            "state": state,
            "height_above_floor": round(height_above_floor, 5),
            "xy_speed": round(xy_speed, 5),
            "vertical_speed": round(vertical_speed, 5),
            "lowest_source": s["lowest_source"],
        }

        prev_sample = s
        prev_frame = frame

    planted_segments = ranges_from_frames(
        planted_frames,
        min_len=MIN_SEGMENT_LEN,
        merge_gap=MERGE_GAP,
    )

    moving_near_floor_segments = ranges_from_frames(
        moving_near_floor_frames,
        min_len=MIN_SEGMENT_LEN,
        merge_gap=MERGE_GAP,
    )

    airborne_segments = ranges_from_frames(
        airborne_frames,
        min_len=MIN_SEGMENT_LEN,
        merge_gap=MERGE_GAP,
    )

    return {
        "side": side,
        "planted_segments": planted_segments,
        "near_floor_moving_segments": moving_near_floor_segments,
        "airborne_or_lifted_segments": airborne_segments,
        "penetration_samples": penetration_samples[:100],
        "penetration_sample_count": len(penetration_samples),
        "per_frame": per_frame,
    }


def add_markers(report):
    scene = bpy.context.scene

    # 清理旧 marker
    old = [m for m in scene.timeline_markers if m.name.startswith("CONTACT_")]
    for m in old:
        scene.timeline_markers.remove(m)

    for side in ["L", "R"]:
        side_data = report["feet"][side]

        for i, (a, b) in enumerate(side_data["planted_segments"]):
            m1 = scene.timeline_markers.new(f"CONTACT_{side}_START_{i}", frame=a)
            m2 = scene.timeline_markers.new(f"CONTACT_{side}_END_{i}", frame=b)

        for i, (a, b) in enumerate(side_data["near_floor_moving_segments"]):
            scene.timeline_markers.new(f"CONTACT_{side}_MOVING_{i}", frame=a)


def main():
    scene = bpy.context.scene
    armature = find_armature(ARMATURE_NAME)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    print("======================================")
    print("[analyze foot contacts]")
    print(f"Armature: {armature.name}")
    print(f"Frames:   {frame_start}-{frame_end}")
    print(f"Floor Z:  {FLOOR_Z}")
    print("======================================")

    feet_report = {}

    for side in ["L", "R"]:
        samples = sample_foot_side(armature, side, frame_start, frame_end)
        feet_report[side] = analyze_side(samples, frame_start, frame_end, side)

        print(f"[{side}] planted segments: {len(feet_report[side]['planted_segments'])}")
        print(f"[{side}] moving near floor: {len(feet_report[side]['near_floor_moving_segments'])}")
        print(f"[{side}] penetration samples: {feet_report[side]['penetration_sample_count']}")

    report = {
        "schema_version": "foot_contact_report_v1",
        "scene": {
            "name": scene.name,
            "fps": scene.render.fps,
            "frame_start": frame_start,
            "frame_end": frame_end,
        },
        "armature": armature.name,
        "floor_z": FLOOR_Z,
        "params": {
            "contact_height": CONTACT_HEIGHT,
            "planted_xy_speed": PLANTED_XY_SPEED,
            "moving_xy_speed": MOVING_XY_SPEED,
            "max_vertical_speed_for_planted": MAX_VERTICAL_SPEED_FOR_PLANTED,
            "min_segment_len": MIN_SEGMENT_LEN,
            "merge_gap": MERGE_GAP,
        },
        "feet": feet_report,
        "notes": [
            "planted_segments are candidate foot-lock intervals.",
            "near_floor_moving_segments may be true sliding, stepping, or transition frames.",
            "Use this report later on the target MMD/Teto IK stage."
        ],
    }

    out = Path(OUTPUT_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if ADD_TIMELINE_MARKERS:
        add_markers(report)

    print("--------------------------------------")
    print(f"[saved report] {out}")

    if ADD_TIMELINE_MARKERS:
        print("[markers] CONTACT_* markers added to timeline")
        # 保存 marker 到当前 blend 的话需要另存
        # 这里不自动保存，避免覆盖你的文件

    print("======================================")


if __name__ == "__main__":
    main()
```

---

# 四、怎么运行

建议 GUI 运行，快。

1. 打开：

```text
F:\mocap_ai_doctor\blends\source_clean_v1.blend
```

2. 切到 `Scripting`
3. 新建 Text
4. 粘贴 `analyze_foot_contacts.py`
5. Run Script

输出：

```text
F:\mocap_ai_doctor\reports\foot_contacts_source_clean_v1.json
```

如果你开了 `ADD_TIMELINE_MARKERS = True`，时间线上会出现一些 marker：

```text
CONTACT_L_START_0
CONTACT_L_END_0
CONTACT_R_START_0
CONTACT_R_END_0
CONTACT_L_MOVING_0
...
```

这些 marker 只是帮你检查，不会改动作。

---

# 五、跑完后你看什么

打开 JSON，主要看这几段：

```json
"feet": {
  "L": {
    "planted_segments": [...],
    "near_floor_moving_segments": [...],
    "penetration_sample_count": ...
  },
  "R": {
    "planted_segments": [...],
    "near_floor_moving_segments": [...],
    "penetration_sample_count": ...
  }
}
```

我们希望看到：

## 1. `planted_segments` 不为空

比如：

```json
"planted_segments": [
  [1568, 1582],
  [1661, 1670],
  [1800, 1810]
]
```

这些就是后面脚 IK 锁定候选段。

## 2. `near_floor_moving_segments` 不要全部覆盖

如果几乎整段动作都被判成 `near_floor_moving`，说明阈值太敏感，需要调大速度阈值或降低接触高度。

## 3. `penetration_sample_count` 应该比修复前少很多

如果 v2 地板修复效果很好，穿地样本应该不多。  
不过少量可以接受，尤其是脚尖/前掌瞬间插地。

---

# 六、如果 contact report 看起来不合理，怎么调参数

## 情况 A：planted 太少

说明判定太严格。改：

```python
PLANTED_XY_SPEED = 0.018
```

到：

```python
PLANTED_XY_SPEED = 0.025
```

或者：

```python
CONTACT_HEIGHT = 0.045
```

到：

```python
CONTACT_HEIGHT = 0.06
```

## 情况 B：planted 太多，连抬脚也算接触

改严格一点：

```python
CONTACT_HEIGHT = 0.035
PLANTED_XY_SPEED = 0.012
```

## 情况 C：moving near floor 太多

如果是舞蹈步伐多，这是正常的。  
如果明显误判，把：

```python
MOVING_XY_SPEED = 0.018
```

改到：

```python
MOVING_XY_SPEED = 0.025
```

---

# 七、接触段分析之后做什么？

如果 report 看起来靠谱，我们源阶段就可以先停了。接下来进入：

```text
ARP 重定向到 Teto
```

建议使用这个源文件：

```text
source_clean_v1.blend
```

重定向原则：

```text
身体主干 / 手臂：
    正常 FK 映射

脚：
    仍然映射到 Teto / MMD 的 foot_ik.L 和 foot_ik.R
```

也就是你之前 bmap 里这两条继续保留：

```text
foot_ik.L <- foot.L
foot_ik.R <- foot.R
```

因为我们现在修好了源动作的地面穿透，但目标模型上仍然要靠 MMD 脚 IK 最终锁脚。

---

# 八、下一阶段的目标模型修复计划

等你重定向到 Teto 后，下一阶段我们会做：

```text
target_teto_retargeted.blend
    ↓
分析 Teto 脚 IK / 足首 / センター
    ↓
根据 source contact report 或目标脚高度识别接触段
    ↓
锁 foot_ik.L / foot_ik.R
    ↓
微调 センター / torso_root 高度
    ↓
导出最终动作
```

你之前给我的那个 `K + 6 个接触点` 脚滑脚本，后面就会派上用场。  
它的思路适合在目标模型阶段用，不适合现在源骨架阶段强行套。

---

# 九、你现在执行这一轮

现在请你做：

1. 另存当前好效果为：

```text
F:\mocap_ai_doctor\blends\source_clean_v1.blend
```

2. 运行 `analyze_foot_contacts.py`
3. 把 JSON 里这几块贴给我即可，不用贴完整 `per_frame`，太长：

```json
"scene": ...
"params": ...
"feet": {
  "L": {
    "planted_segments": ...,
    "near_floor_moving_segments": ...,
    "penetration_sample_count": ...
  },
  "R": {
    "planted_segments": ...,
    "near_floor_moving_segments": ...,
    "penetration_sample_count": ...
  }
}
```

然后我判断 contact 阈值是否靠谱。  
如果靠谱，我们就进入 ARP/Teto 重定向后的修复阶段。

---
## 🧑‍💻 User

 "penetration_sample_count": 197, "penetration_sample_count": 623,   near_floor_moving_segments是很多一小块一小块的，感觉没问题。
{
  "schema_version": "foot_contact_report_v1",
  "scene": {
    "name": "Scene",
    "fps": 24,
    "frame_start": 1525,
    "frame_end": 2836
  },
  "armature": "import_synchronized_videos_rig",
  "floor_z": 0.02,
  "params": {
    "contact_height": 0.045,
    "planted_xy_speed": 0.018,
    "moving_xy_speed": 0.018,
    "max_vertical_speed_for_planted": 0.018,
    "min_segment_len": 3,
    "merge_gap": 2
  },
  "feet": {
    "L": {
      "side": "L",
      "planted_segments": [
        [
          1525,
          1591
        ],
        [
          1601,
          1618
        ],
        [
 "near_floor_moving_segments": [
        [
          1592,
          1600
        ],
        [
          1619,
          1622
        ],
        [
          1628,
          1631
        ],

  "airborne_or_lifted_segments": [
        [
          1623,
          1627
        ],
        [
          1669,
          1673
        ],
        [
          1694,
          1698
        ],
        [
          2189,
          2191
        ],
        [
          2235,
          2242
      "penetration_samples": [
        {
          "frame": 1555,
          "lowest_z": 0.0108,
          "depth": 0.0092,
          "source": "foot.L:tail"
        },
        {
          "frame": 1556,
          "lowest_z": 0.01186,
          "depth": 0.00814,
          "source": "foot.L:tail"
        },
        {
          "frame": 1580,
          "lowest_z": 0.01074,
          "depth": 0.00926,
          "source": "foot.L:tail"
        },
          "source": "foot.L:tail"
        }
      ],
      "penetration_sample_count": 197,
      "per_frame": {
        "1525": {
          "state": "planted",
          "height_above_floor": 0.0019,
          "xy_speed": 0.0,
          "vertical_speed": 0.0,
          "lowest_source": "foot.L:tail"
        },
        "1526": {
          "state": "planted",
          "height_above_floor": 0.00199,
          "xy_speed": 8e-05,
          "vertical_speed": 0.00015,
          "lowest_source": "foot.L:tail"
        },
       "1597": {
          "state": "near_floor_moving",
          "height_above_floor": 0.03993,
          "xy_speed": 0.04439,
          "vertical_speed": 0.00823,
          "lowest_source": "foot.L:tail"
        },
        "1598": {
          "state": "near_floor_moving",
          "height_above_floor": 0.04181,
          "xy_speed": 0.03639,
          "vertical_speed": 0.00852,
          "lowest_source": "foot.L:tail"
        },
        "1599": {
          "state": "near_floor_moving",
          "height_above_floor": 0.04247,
          "xy_speed": 0.02877,
          "vertical_speed": 0.00691,
          "lowest_source": "foot.L:tail"
        },
        "2836": {
          "state": "planted",
          "height_above_floor": -0.00838,
          "xy_speed": 0.00236,
          "vertical_speed": 0.0009,
          "lowest_source": "foot.L:tail"
        }
      }
    },
    "R": {
      "side": "R",
      "planted_segments": [
        [
          1525,
          1567
        ],
       }
      ],
      "penetration_sample_count": 623,
      "per_frame": {
        "1525": {
          "state": "planted",
          "height_above_floor": -0.00142,
          "xy_speed": 0.0,
          "vertical_speed": 0.0,
          "lowest_source": "heel.02.R:tail"
        },        "2836": {
          "state": "planted",
          "height_above_floor": 0.0132,
          "xy_speed": 0.00248,
          "vertical_speed": 0.00142,
          "lowest_source": "foot.R:tail"
        }
      }
    }
  },
  "notes": [
    "planted_segments are candidate foot-lock intervals.",
    "near_floor_moving_segments may be true sliding, stepping, or transition frames.",
    "Use this report later on the target MMD/Teto IK stage."
  ]
}
给你一样拿了一点上来，还满意吗？另外，你的标记名字太长，时间线里面挤在一起，字显示不全，你用LS LE RS RE这样很简短的表示一下，不然我分不清哪些是间隙哪些是区间了

---
## 🤖 Assistant

满意。这个 contact report 对我们现在的目的来说**够用了**。

你的结果说明：

```text
1. planted_segments 能正常识别出来；
2. near_floor_moving_segments 是一小段一小段，符合舞蹈换步/滑动/过渡；
3. penetration_sample_count 虽然数字看起来大，但很多是 8~9mm 级别；
4. 你肉眼已经觉得地面效果很好，所以源数据阶段不用再强修。
```

尤其你贴的例子：

```json
"height_above_floor": -0.00838
```

这种是 8.38mm 插地。对源骨架阶段来说可以接受。最终到 Teto 上还会再做一次目标脚 IK 稳定，不需要现在把 FreeMoCap 源骨架修到“医学级完美”。

---

# 1. 关于 marker 名太长

对，`CONTACT_L_START_0` 这种太长，在时间线里确实很难看。

我们改成：

```text
LS00 = Left Start
LE00 = Left End
RS00 = Right Start
RE00 = Right End

LM00 = Left Moving near floor
RM00 = Right Moving near floor

LA00 = Left Airborne/Lifted
RA00 = Right Airborne/Lifted
```

其中最重要的是：

```text
LS / LE / RS / RE
```

也就是锁脚候选区间。

---

# 2. 新建短 marker 脚本

保存为：

```text
F:\mocap_ai_doctor\scripts\mark_foot_contacts_short.py
```

内容：

```python
import bpy
import json
from pathlib import Path


# =========================
# 配置区
# =========================

REPORT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v1.json"

# 是否标记 planted 段
MARK_PLANTED = True

# 是否标记 near_floor_moving 段
# 如果嫌时间线太乱，可以改 False
MARK_MOVING = True

# 是否标记 airborne_or_lifted 段
# 一般先 False，不然太挤
MARK_AIRBORNE = False

# 清理这些前缀的旧 marker
CLEAR_PREFIXES = [
    "CONTACT_",
    "LS", "LE",
    "RS", "RE",
    "LM", "RM",
    "LA", "RA",
]


def load_report(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def clear_old_markers(scene):
    to_remove = []
    for m in scene.timeline_markers:
        if any(m.name.startswith(prefix) for prefix in CLEAR_PREFIXES):
            to_remove.append(m)

    for m in to_remove:
        scene.timeline_markers.remove(m)

    print(f"[markers] removed old markers: {len(to_remove)}")


def add_marker(scene, name, frame):
    scene.timeline_markers.new(name, frame=int(frame))


def mark_segments(scene, side, prefix_start, prefix_end, segments):
    for i, seg in enumerate(segments):
        if len(seg) != 2:
            continue
        a, b = int(seg[0]), int(seg[1])
        add_marker(scene, f"{prefix_start}{i:02d}", a)
        add_marker(scene, f"{prefix_end}{i:02d}", b)


def mark_single_start(scene, prefix, segments):
    for i, seg in enumerate(segments):
        if len(seg) != 2:
            continue
        a = int(seg[0])
        add_marker(scene, f"{prefix}{i:02d}", a)


def main():
    scene = bpy.context.scene
    report = load_report(REPORT_JSON)

    clear_old_markers(scene)

    feet = report["feet"]

    if MARK_PLANTED:
        mark_segments(
            scene,
            "L",
            "LS",
            "LE",
            feet["L"].get("planted_segments", [])
        )
        mark_segments(
            scene,
            "R",
            "RS",
            "RE",
            feet["R"].get("planted_segments", [])
        )

    if MARK_MOVING:
        mark_single_start(
            scene,
            "LM",
            feet["L"].get("near_floor_moving_segments", [])
        )
        mark_single_start(
            scene,
            "RM",
            feet["R"].get("near_floor_moving_segments", [])
        )

    if MARK_AIRBORNE:
        mark_single_start(
            scene,
            "LA",
            feet["L"].get("airborne_or_lifted_segments", [])
        )
        mark_single_start(
            scene,
            "RA",
            feet["R"].get("airborne_or_lifted_segments", [])
        )

    print("[markers] short markers added")
    print("Legend:")
    print("  LS/LE = Left planted start/end")
    print("  RS/RE = Right planted start/end")
    print("  LM/RM = near-floor moving start")
    print("  LA/RA = airborne/lifted start")


if __name__ == "__main__":
    main()
```

---

# 3. 怎么运行

在 Blender GUI 里运行即可。

1. 打开：

```text
F:\mocap_ai_doctor\blends\source_clean_v1.blend
```

2. 切到 `Scripting`
3. 新建 Text
4. 粘贴 `mark_foot_contacts_short.py`
5. Run Script

时间线上会变成类似：

```text
LS00  LE00  RS00  RE00  LM00  RM00
```

如果你觉得 `LM/RM` 也太多，把脚本里：

```python
MARK_MOVING = True
```

改成：

```python
MARK_MOVING = False
```

这样时间线只显示真正的 planted 区间：

```text
LS00/LE00
RS00/RE00
```

---

# 4. 当前源数据阶段是否可以收工？

我建议：**可以。**

现在源动作文件冻结为：

```text
F:\mocap_ai_doctor\blends\source_clean_v1.blend
```

这个文件的状态是：

```text
✅ 手动烘焙完成
✅ 严重手部区间可人工修复
✅ 全身高频抖动已平滑
✅ 脚跟和前掌插地明显改善
✅ 脚部接触段 report 已生成
```

不要继续在源骨架上大幅 foot lock。  
源数据再修下去，容易把动作变假。

---

# 5. 下一阶段：重定向到 Teto

现在进入目标模型阶段。

你下一步做 ARP 重定向，使用：

```text
source_clean_v1.blend
```

作为源动作。

## ARP 重定向建议

根据你之前的 `bmap`，继续保留：

```text
foot_ik.L  <- foot.L
foot_ik.R  <- foot.R
torso_root <- pelvis
hand_fk.L  <- hand.L
hand_fk.R  <- hand.R
forearm_fk.L <- forearm.L
forearm_fk.R <- forearm.R
upper_arm_fk.L <- upper_arm.L
upper_arm_fk.R <- upper_arm.R
```

也就是：

```text
腿部目标仍然走 MMD/ARP 的 foot_ik
其他身体部分基本按 FK 映射
```

## Auto Scale

还是之前结论：

```text
不要盲目开 Auto Scale。
```

如果开了之后你觉得：

```text
腿明显比 Teto 短
骨盆高度更怪
脚更难贴地
```

那就不开。  
Teto 这种二次元比例模型，最终脚部还是靠目标阶段修。

---

# 6. 重定向后保存这个文件

重定向完成后，保存为：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1.blend
```

然后我们马上做目标模型阶段分析。

---

# 7. 目标模型阶段我们要分析什么？

重定向到 Teto 后，我们重点看这些骨骼：

从你之前贴的 bmap 和截图看，目标侧大概有：

```text
torso_root
foot_ik.L
foot_ik.R
hand_fk.L
hand_fk.R
forearm_fk.L
forearm_fk.R
upper_arm_fk.L
upper_arm_fk.R
spine_fk
spine_fk.001
```

目标阶段第一版 analyzer 会检查：

```text
1. foot_ik.L / foot_ik.R 是否在 planted 段滑动
2. foot_ik.L / foot_ik.R 是否上下浮动
3. torso_root / センター 是否跟脚接触矛盾
4. Teto 脚底是否插地或浮空
5. 源 contact report 的 LS/LE/RS/RE 是否还能对应目标 IK
```

目标阶段才是真正该使用：

```text
K + 接触点 + root compensation
```

这种脚滑修复思路的时候。

---

# 8. 你现在要做的事

现在按这个顺序来：

## 第一步

运行短 marker 脚本，把时间线 marker 改短。

## 第二步

确认并冻结：

```text
source_clean_v1.blend
```

## 第三步

用 ARP 把 `source_clean_v1` 重定向到 Teto。

## 第四步

保存为：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1.blend
```

## 第五步

打开 Teto 重定向结果，肉眼检查三件事：

```text
1. 脚滑严重吗？
2. 脚是浮多，还是插地多？
3. 骨盆/センター 是否上下乱弹？
```

然后告诉我。  
最好再告诉我 Teto 目标 armature 的名字。如果不确定，我下一步给你一个目标骨骼列表导出脚本，直接导出：

```text
F:\mocap_ai_doctor\reports\teto_bones.json
```

然后我们进入目标模型脚 IK 稳定。

---
## 🧑‍💻 User

脚滑和重定向前差不多，属于轻微，但是远远比修之前好的水平，脚这个我不好说，因为现在人是歪的，脚的落点大体上都在在一个离z=0平面上面高一点点倾斜一点点的平面上，就是不好说脚是浮多，还是插地多，稍微有点全程都踮着脚尖的感觉，但是总体问题不大，骨盆没问题，总体上都挺好。你先教我怎么扶正她（已经重定向完了），然后我可以再看看浮和插地哪个多。你要的名字：arue式重音テトver 2.01_arm        RIG-arue式重音テトver 2.01_arm，截图是项目层级。注意，我用了mikumikurig插件，动作也是重定向到了这个上面，我不懂具体什么意思，只是觉得好用就用了，好像是rigfy什么的，反正重定向的时候不是重定向到了原生的mmd骨骼

---
## 🤖 Assistant

对，你现在这个情况已经进入**目标模型全局校正**阶段了。

你截图里这个歪，不像是某一根骨骼姿势错，更像是：

```text
整个 Teto 动作所在的“局部地面”相对 Blender 世界地面有一点倾斜
```

所以正确处理方式不是去拧腿、拧骨盆，也不是改每帧关键帧，而是加一层**全局校正层**：

```text
teto_global_correction Empty
    ├── arue式重音テトver 2.01
    └── RIG-arue式重音テトver 2.01_arm
```

然后旋转这个 Empty，把角色整体扶正。

这样有几个好处：

- 不破坏 ARP / MikuMikuRig / Rigify 的动画数据；
- 不改内部骨骼；
- 不影响你之后继续修 IK；
- 如果角度不对，直接改 Empty 的旋转即可；
- 后面导出前可以选择 bake 或不 bake。

---

# 1. 你这个模型结构我怎么理解

从截图看，和你描述一致：

```text
arue式重音テトver 2.01
    ├── arue式重音テトver 2.01_arm
    ├── joints
    └── rigidbodies

RIG-arue式重音テトver 2.01_arm
```

大概率是：

```text
arue式重音テトver 2.01
```

是 MMD 模型本体/容器，里面有原始 MMD armature、mesh、刚体、关节等。

```text
RIG-arue式重音テトver 2.01_arm
```

是 MikuMikuRig 生成的控制 Rig，类似 Rigify 控制骨架。

你现在动作应该主要在：

```text
RIG-arue式重音テトver 2.01_arm
```

上，但模型显示依赖原始 MMD armature 和 mesh。所以**扶正时要把模型本体和 RIG 一起转**，不能只转其中一个。

---

# 2. 先用手动方式快速验证

在写脚本之前，你可以先做一次手动验证。

## 操作

1. 在 Object Mode。
2. 选中这两个对象：

```text
arue式重音テトver 2.01
RIG-arue式重音テトver 2.01_arm
```

3. `Shift + A` 添加 Empty：

```text
Empty > Plain Axes
```

4. 把 Empty 改名：

```text
teto_global_correction
```

5. Empty 的位置设为：

```text
X = 0
Y = 0
Z = 0
```

6. 先选中：

```text
arue式重音テトver 2.01
RIG-arue式重音テトver 2.01_arm
```

最后选中 Empty，使 Empty 成为 active object。

7. 按：

```text
Ctrl + P
```

选择：

```text
Object (Keep Transform)
```

8. 然后旋转 Empty。

你截图是在 Front Orthographic，角色左右倾斜通常是绕 Blender 的 **Y 轴** 转：

```text
Empty Rotation Y
```

可以先试：

```text
Y = 1°
Y = -1°
Y = 2°
Y = -2°
```

直到脚底那条斜平面大致水平。

---

# 3. 更推荐：用脚本创建全局校正 Empty

下面这个脚本会自动：

1. 找到 Teto 模型对象；
2. 找到 MikuMikuRig / Rigify 控制 rig；
3. 创建 `teto_global_correction`；
4. 把这两个对象 parent 到 Empty；
5. 让你通过参数调整旋转角度；
6. 保存新文件。

---

## 脚本：`create_teto_global_correction.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\create_teto_global_correction.py
```

内容：

```python
import bpy
from math import radians
from mathutils import Matrix
from pathlib import Path


# =========================
# 配置区
# =========================

# 你的目标模型本体
MODEL_ROOT_NAME = "arue式重音テトver 2.01"

# MikuMikuRig / Rigify 控制骨架
RIG_NAME = "RIG-arue式重音テトver 2.01_arm"

# 全局校正 Empty 名字
CORRECTION_EMPTY_NAME = "teto_global_correction"

# 输出文件
OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_retarget_v1_global_corrected.blend"

# =========================
# 最重要：扶正角度
# =========================
#
# Front Orthographic 里左右歪，通常改 Y。
# 如果方向反了，把正负号反过来。
#
# 先试 0，不保存或只创建 Empty；
# 然后试 1.0 / -1.0 / 2.0 / -2.0。
#

ROT_X_DEG = 0.0
ROT_Y_DEG = 0.0
ROT_Z_DEG = 0.0

# 例如如果角色右低左高，可能需要：
# ROT_Y_DEG = 1.5
#
# 如果反了：
# ROT_Y_DEG = -1.5


# =========================
# 工具函数
# =========================

def get_object(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object not found: {name}")
    return obj


def get_or_create_empty(name):
    obj = bpy.data.objects.get(name)
    if obj:
        return obj

    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.25
    bpy.context.collection.objects.link(empty)
    return empty


def parent_keep_world(child, parent):
    """
    把 child parent 到 parent，但保持 child 当前世界变换不变。
    """
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = world


def main():
    model_root = get_object(MODEL_ROOT_NAME)
    rig = get_object(RIG_NAME)

    empty = get_or_create_empty(CORRECTION_EMPTY_NAME)

    # Empty 放世界原点
    empty.location = (0.0, 0.0, 0.0)
    empty.rotation_euler = (
        radians(ROT_X_DEG),
        radians(ROT_Y_DEG),
        radians(ROT_Z_DEG),
    )
    empty.scale = (1.0, 1.0, 1.0)

    # 先记录当前世界矩阵
    model_world = model_root.matrix_world.copy()
    rig_world = rig.matrix_world.copy()

    # 如果它们还不是这个 Empty 的子级，就 parent
    if model_root.parent != empty:
        parent_keep_world(model_root, empty)

    if rig.parent != empty:
        parent_keep_world(rig, empty)

    # parent 后恢复世界矩阵，避免第一次运行时跳动
    # 注意：Empty 的旋转会作为全局校正层参与显示。
    model_root.matrix_world = model_world
    rig.matrix_world = rig_world

    # 现在再设置 Empty 旋转，让全局校正真正生效
    empty.rotation_euler = (
        radians(ROT_X_DEG),
        radians(ROT_Y_DEG),
        radians(ROT_Z_DEG),
    )

    print("======================================")
    print("[teto global correction]")
    print(f"Empty: {empty.name}")
    print(f"Model: {model_root.name}")
    print(f"Rig:   {rig.name}")
    print(f"Rotation degrees: X={ROT_X_DEG}, Y={ROT_Y_DEG}, Z={ROT_Z_DEG}")
    print("======================================")

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
```

---

# 4. 怎么用这个脚本

## 第一次运行

先把角度保持 0：

```python
ROT_X_DEG = 0.0
ROT_Y_DEG = 0.0
ROT_Z_DEG = 0.0
```

在 Blender GUI 里打开：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1.blend
```

然后 Scripting 运行脚本。

它会保存：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_global_corrected.blend
```

这一步主要确认它没有报错、没有把模型搞飞。

---

## 第二次调角度

重新打开：

```text
teto_retarget_v1.blend
```

或者打开刚生成的也可以。

改：

```python
ROT_Y_DEG = 1.0
```

运行，看看是否扶正。

如果歪得更厉害，改：

```python
ROT_Y_DEG = -1.0
```

通常你的这种轻微倾斜，大概在：

```text
-3° 到 3°
```

之间。

---

# 5. 更快的调法：直接在界面改 Empty

其实脚本主要是帮你建立结构。  
建立好以后，你可以不用每次跑脚本。

打开：

```text
teto_retarget_v1_global_corrected.blend
```

然后：

1. 选中：

```text
teto_global_correction
```

2. 在右侧 Transform 面板里改：

```text
Rotation Y
```

3. 试几个值：

```text
0.5°
1.0°
1.5°
2.0°
-0.5°
-1.0°
-1.5°
-2.0°
```

直到视觉上脚底平面水平。

这个最快。

---

# 6. 如果绕 Y 不对怎么办？

看你截图是在 Front Orthographic：

```text
横轴 = X
纵轴 = Z
视线方向 = Y
```

角色在这个视图里左右歪，一般是绕：

```text
Y 轴
```

如果你发现绕 Y 只是前后倒，不是左右扶正，那就试：

```text
Rotation X
```

如果是整个角色朝向不对，比如面向偏了，则是：

```text
Rotation Z
```

但从截图看，优先试：

```text
Rotation Y
```

---

# 7. 这个扶正会不会影响后面脚 IK？

会影响，但这是我们想要的影响。

因为现在的问题是：

```text
目标角色整体所在的地面是斜的
```

先用全局校正层把它扶正，后面我们才能判断：

```text
脚是浮还是插
```

否则你现在判断脚底高度会混乱。

---

# 8. 扶正后不要立刻 Apply

不要按：

```text
Ctrl + A > Apply Rotation
```

先别应用变换。

原因：

- MMD 模型、刚体、约束、MikuMikuRig 结构复杂；
- Apply 可能改变父子空间；
- 后面如果要导出 VMD/FBX，我们再决定是否 bake。

现在只保留这个 Empty correction layer。

---

# 9. 扶正后你再检查脚

扶正以后，你重新看：

```text
脚底相对 Z=0 平面
```

然后告诉我：

```text
A. 主要是全程浮一点
B. 主要是经常插地
C. 有时浮有时插
D. 基本可以接受，只剩轻微脚滑
```

如果是 A：

```text
整体下移 target correction Empty 或 torso_root/center
```

如果是 B：

```text
整体上移或脚 IK 抬高
```

如果是 C：

```text
需要目标脚 IK 接触段修复
```

如果是 D：

```text
目标动作基本可用，后面只做脚滑/手部视觉修
```

---

# 10. 目前不要动这些

在扶正阶段先不要动：

```text
torso_root
センター
foot_ik.L
foot_ik.R
足首
つま先
```

也不要进 Pose Mode 拧骨骼。

先只动：

```text
teto_global_correction
```

这就是我们现在的“最小侵入式修正”。

你先按这个创建 Empty，然后手动调 `Rotation Y`。调好以后告诉我大概角度，以及脚现在是浮还是插。
[1] [Major deformation on retarget with both Rokoko and ReTarget?](https://blenderartists.org/t/major-deformation-on-retarget-with-both-rokoko-and-retarget/1633409)
---
## 🧑‍💻 User

模型默认离z=0有点距离，我按你说的不敢动teto，新建了一个平面，高度z=0.0257 m，此时第一帧和没有动作时脚会微微插进这个平面（不进正交视图就看不出来），有动作的时候会轻微插入，膝盖弯曲比较猛的时候会插的深一些，半个脚掌都进去了，但绝大多数时候都只是鞋底插进去一点。倾斜角：ROT_X_DEG = -4.2
ROT_Y_DEG = 3.7
ROT_Z_DEG = 0.0

---
## 🤖 Assistant

很好。你现在的信息非常关键：

```python
ROT_X_DEG = -4.2
ROT_Y_DEG = 3.7
ROT_Z_DEG = 0.0
```

这说明之前确实不是单纯绕一个轴歪，而是有一个小的复合倾斜。你用全局校正 Empty 扶正是对的。

另外：

```text
地面高度：Z = 0.0257 m
```

这个也没问题。**目标模型默认脚底不一定正好在 Z=0**，所以我们后面都用你这个 `0.0257` 当 Teto 的目标地面高度，不强行回到世界 0。

现在的问题是：

```text
绝大多数时候只是鞋底轻微插地；
膝盖弯曲猛的时候，半个脚掌插进去；
总体脚滑轻微，骨盆没问题。
```

这非常适合做一个**目标模型阶段的“网格最低点地板修复”**。

---

# 下一步策略

之前源骨架阶段我们用的是骨骼点：

```text
foot.L tail / heel.02 tail
```

但现在目标阶段你看到的是**鞋子网格**插进地板。

所以这次不要只看 `foot_ik` 骨骼，而是直接看 Teto 模型的**实际 mesh 顶点最低点**：

```text
每一帧扫描 Teto 的网格最低顶点
如果最低点低于 floor_z
就把 teto_global_correction 的 Z 抬高一点
```

这样优点是：

- 直接修你肉眼看到的鞋底/脚掌插地；
- 不需要先知道 MikuMikuRig 具体脚骨命名；
- 不破坏内部 rig、MMD 骨骼、IK；
- 只动外层 `teto_global_correction`；
- 非常适合你现在这个“总体挺好，只是脚掌插地”的阶段。

---

# 脚本：目标模型 mesh 地板穿透修复

保存为：

```text
F:\mocap_ai_doctor\scripts\repair_teto_mesh_floor_lift.py
```

内容：

```python
import bpy
import math
from pathlib import Path


# =========================
# 配置区
# =========================

MODEL_ROOT_NAME = "arue式重音テトver 2.01"

CORRECTION_EMPTY_NAME = "teto_global_correction"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_retarget_v1_global_floor_fixed.blend"

# 你实测的目标地面高度
FLOOR_Z = 0.0257

# 希望鞋底略高于地面多少
TARGET_CLEARANCE = 0.0025

# 允许轻微插地，单位米
# 0.003 = 3mm，肉眼基本看不出
TOLERANCE = 0.003

# 单帧最大抬升，避免异常顶点把人抬飞
MAX_LIFT_PER_FRAME = 0.08

# 修复强度
# 1.0 = 完全抬到目标高度
# 0.75 = 稍微保守
STRENGTH = 0.85

# 修正曲线平滑半径
# 越大越平滑，但可能棉花糖
SMOOTH_RADIUS = 3

# 限制每帧 correction Z 的变化
MAX_DELTA_PER_FRAME = 0.012

# 是否只使用可见 mesh
VISIBLE_ONLY = True

# 排除这些名字的对象或祖先
EXCLUDE_NAME_KEYWORDS = [
    "ground",
    "plane",
    "video",
    "VID",
    "rigid",
    "joints",
    "Joint",
]

# 为了加速，每隔几个顶点采样一次。
# 1 = 全部顶点，最准确但慢
# 2/3/4 = 更快
VERTEX_SAMPLE_STEP = 2

# 打印最差穿地样本
PRINT_WORST = True
PRINT_LIMIT = 80


# =========================
# 工具函数
# =========================

def find_object(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object not found: {name}")
    return obj


def name_has_excluded_keyword(obj):
    current = obj
    while current is not None:
        for kw in EXCLUDE_NAME_KEYWORDS:
            if kw in current.name:
                return True
        current = current.parent
    return False


def collect_meshes_under(root):
    objects = [root] + list(root.children_recursive)

    meshes = []

    for obj in objects:
        if obj.type != "MESH":
            continue

        if name_has_excluded_keyword(obj):
            continue

        if VISIBLE_ONLY and not obj.visible_get():
            continue

        if not obj.data or len(obj.data.vertices) == 0:
            continue

        meshes.append(obj)

    return meshes


def get_scene_frame_range():
    scene = bpy.context.scene
    return int(scene.frame_start), int(scene.frame_end)


def gaussian_weights(radius):
    if radius <= 0:
        return [1.0], [0]

    sigma = max(1.0, radius / 1.5)
    offsets = list(range(-radius, radius + 1))
    weights = []

    for off in offsets:
        w = math.exp(-(off * off) / (2.0 * sigma * sigma))
        weights.append(w)

    s = sum(weights)
    weights = [w / s for w in weights]

    return weights, offsets


def smooth_values(values_by_frame, frame_start, frame_end, radius):
    weights, offsets = gaussian_weights(radius)
    out = {}

    for frame in range(frame_start, frame_end + 1):
        acc = 0.0
        total = 0.0

        for w, off in zip(weights, offsets):
            ff = frame + off
            if ff < frame_start or ff > frame_end:
                continue
            acc += values_by_frame.get(ff, 0.0) * w
            total += w

        out[frame] = acc / total if total > 1e-8 else values_by_frame.get(frame, 0.0)

    return out


def limit_delta(values_by_frame, frame_start, frame_end, max_delta):
    out = dict(values_by_frame)

    prev = out.get(frame_start, 0.0)
    for frame in range(frame_start + 1, frame_end + 1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    prev = out.get(frame_end, 0.0)
    for frame in range(frame_end - 1, frame_start - 1, -1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    return out


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def ensure_object_location_z_fcurve(obj):
    obj.animation_data_create()

    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_floor_lift")

    action = obj.animation_data.action

    fc = get_fcurve(action, "location", 2)
    if fc is None:
        fc = action.fcurves.new(data_path="location", index=2)

    return action, fc


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_key_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"


def evaluated_mesh_min_z(obj, depsgraph):
    """
    返回该 mesh 当前帧 evaluated 后的世界最低 z。
    """
    eval_obj = obj.evaluated_get(depsgraph)

    try:
        mesh = eval_obj.to_mesh()
    except Exception:
        return None

    if mesh is None or len(mesh.vertices) == 0:
        return None

    mw = eval_obj.matrix_world
    min_z = None

    verts = mesh.vertices
    step = max(1, int(VERTEX_SAMPLE_STEP))

    for i in range(0, len(verts), step):
        z = (mw @ verts[i].co).z
        if min_z is None or z < min_z:
            min_z = float(z)

    eval_obj.to_mesh_clear()

    return min_z


def main():
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    root = find_object(MODEL_ROOT_NAME)
    correction = find_object(CORRECTION_EMPTY_NAME)

    frame_start, frame_end = get_scene_frame_range()

    meshes = collect_meshes_under(root)

    if not meshes:
        raise RuntimeError("No target meshes found under model root.")

    print("====================================")
    print("[Teto mesh floor lift]")
    print(f"Root:       {root.name}")
    print(f"Correction: {correction.name}")
    print(f"Frames:     {frame_start}-{frame_end}")
    print(f"Floor Z:    {FLOOR_Z}")
    print(f"Meshes:     {len(meshes)}")
    for m in meshes:
        print(f"  mesh: {m.name}, verts={len(m.data.vertices)}")
    print("====================================")

    min_z_by_frame = {}
    worst_mesh_by_frame = {}

    # 1. 采样每帧模型网格最低点
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        depsgraph.update()

        global_min_z = None
        global_min_mesh = None

        for obj in meshes:
            mz = evaluated_mesh_min_z(obj, depsgraph)
            if mz is None:
                continue

            if global_min_z is None or mz < global_min_z:
                global_min_z = mz
                global_min_mesh = obj.name

        min_z_by_frame[frame] = global_min_z
        worst_mesh_by_frame[frame] = global_min_mesh

    # 2. 计算需要抬升量
    raw_lift = {}
    worst_samples = []

    target_z = FLOOR_Z + TARGET_CLEARANCE

    for frame in range(frame_start, frame_end + 1):
        min_z = min_z_by_frame.get(frame)

        if min_z is None:
            raw_lift[frame] = 0.0
            continue

        penetration = target_z - min_z

        if penetration > TOLERANCE:
            lift = min(penetration, MAX_LIFT_PER_FRAME)
            lift *= STRENGTH
            raw_lift[frame] = lift

            worst_samples.append({
                "frame": frame,
                "min_z": min_z,
                "penetration": penetration,
                "lift": lift,
                "mesh": worst_mesh_by_frame.get(frame),
            })
        else:
            raw_lift[frame] = 0.0

    # 3. 平滑和限制变化
    smoothed = smooth_values(raw_lift, frame_start, frame_end, SMOOTH_RADIUS)
    corrected = limit_delta(smoothed, frame_start, frame_end, MAX_DELTA_PER_FRAME)

    # 4. 写入 correction Empty 的 location.z
    action, z_curve = ensure_object_location_z_fcurve(correction)

    changed_frames = 0
    max_lift = 0.0

    for frame in range(frame_start, frame_end + 1):
        lift = corrected.get(frame, 0.0)
        if abs(lift) < 1e-8:
            continue

        original_z = z_curve.evaluate(frame)
        new_z = original_z + lift

        set_key_value(z_curve, frame, new_z)

        changed_frames += 1
        max_lift = max(max_lift, lift)

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[changed_frames] {changed_frames}")
    print(f"[max_lift] {max_lift:.5f} m")

    if PRINT_WORST:
        print("------------------------------------")
        print("[worst penetration samples]")
        for s in worst_samples[:PRINT_LIMIT]:
            print(
                f"frame={s['frame']}, "
                f"min_z={s['min_z']:.5f}, "
                f"penetration={s['penetration']:.5f}, "
                f"lift={s['lift']:.5f}, "
                f"mesh={s['mesh']}"
            )
        if len(worst_samples) > PRINT_LIMIT:
            print(f"... {len(worst_samples) - PRINT_LIMIT} more")

    print("------------------------------------")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 怎么运行

你现在打开已经扶正后的文件，例如：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_global_corrected.blend
```

确保里面有：

```text
teto_global_correction
```

并且它的旋转是：

```python
X = -4.2
Y = 3.7
Z = 0
```

然后在 Blender `Scripting` 里运行上面脚本。

输出：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_global_floor_fixed.blend
```

---

# 跑完以后看什么

重点看这几个地方：

## 1. 弯膝盖时半个脚掌插地有没有明显改善

这是本脚本主要目标。

## 2. 是否出现“整个人上下弹”

如果变成踩棉花糖，说明修正太激进。

优先改：

```python
STRENGTH = 0.85
```

为：

```python
STRENGTH = 0.6
```

或者改：

```python
MAX_DELTA_PER_FRAME = 0.012
```

为：

```python
MAX_DELTA_PER_FRAME = 0.006
```

## 3. 是否全程浮太高

如果修完后整体有点浮，把：

```python
TARGET_CLEARANCE = 0.0025
```

改成：

```python
TARGET_CLEARANCE = 0.001
```

或者：

```python
TOLERANCE = 0.003
```

改成：

```python
TOLERANCE = 0.005
```

---

# 关于你“不敢动 Teto”

你现在做得很对。当前阶段只应该动：

```text
teto_global_correction
```

不要动：

```text
arue式重音テトver 2.01
RIG-arue式重音テトver 2.01_arm
foot_ik
センター
torso_root
```

因为 MikuMikuRig / MMD / Rigify 混在一起，直接改内部骨骼容易破坏约束关系。  
我们现在用外层 Empty 修整体地面，是最安全的。

---

# 这一步之后

如果这个 mesh floor lift 效果好，我们就进入最后一类目标修复：

```text
轻微脚滑 / 脚 IK 锁定
```

但你已经说脚滑轻微，所以可能不需要上复杂的 `K + 6 接触点`。  
下一步我们可以只做一个**目标脚 IK 诊断报告**，判断：

```text
foot_ik.L / foot_ik.R 在接触段到底滑了多少
```

如果滑动量小，就不修，避免过度处理。

---
## 🧑‍💻 User

忘了告诉你，现在很多时候脚是这样歪着放着的，偶尔还出现第二张图这样的比较大的扭曲，扭的网格都有点变形了（这种极端情况很少），你要不要改什么？

---
## 🤖 Assistant

要改。你这个不是“脚底高度”的问题了，而是**目标模型脚部 IK/脚控旋转过度**的问题。

你现在先**不要运行我上一条的 mesh floor lift 脚本**。  
原因是：如果脚已经扭成第二张图那样，mesh 最低点会乱跳，地板修复脚本会错误地抬整个人，反而可能加重“踩棉花糖”。

现在优先顺序改成：

```text
1. 先修 Teto 目标 rig 的 foot_ik 旋转扭曲
2. 再检查脚底浮/插
3. 最后才做 mesh floor lift
```

---

# 一、这个问题大概率是什么

你现在重定向后用的是 MikuMikuRig / Rigify 风格控制 rig：

```text
RIG-arue式重音テトver 2.01_arm
```

而你的映射里有：

```text
foot_ik.L <- foot.L
foot_ik.R <- foot.R
```

这个映射本身没错，但问题是：

> 源 FreeMoCap 的 `foot.L / foot.R` 旋转被直接传给了目标 `foot_ik.L / foot_ik.R`，目标模型脚 IK 控制器承受了不适合它的旋转。

结果就是：

- 脚底经常歪着放；
- 脚掌 pitch/roll/twist 过大；
- 极端帧脚部 mesh 被扭变形；
- 看起来像脚踝/鞋子被拧麻花。

对于 MMD/MikuMikuRig 目标模型，通常更稳的是：

```text
foot_ik 主要负责位置；
foot_ik 的旋转要么弱化，要么保持接近默认姿态；
脚底细节后面再单独处理。
```

所以我们现在做一个安全修复：

> **保留 foot_ik 的位置动画，但把 foot_ik 的旋转向参考帧姿态拉回。**

---

# 二、先做 foot_ik 旋转弱化脚本

这个脚本不会动：

```text
teto_global_correction
模型 mesh
pelvis
torso_root
手臂
脚 IK 位置
```

只动目标控制 rig 的：

```text
foot_ik.L rotation
foot_ik.R rotation
```

位置不动，所以脚落点大体不变。

---

# 三、脚本：`repair_teto_foot_ik_rotation_dampen.py`

保存为：

```text
F:\mocap_ai_doctor\scripts\repair_teto_foot_ik_rotation_dampen.py
```

内容：

```python
import bpy
from pathlib import Path


# =========================
# 配置区
# =========================

RIG_NAME = "RIG-arue式重音テトver 2.01_arm"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_retarget_v1_footik_rot_fixed.blend"

FOOT_IK_BONES = [
    "foot_ik.L",
    "foot_ik.R",
]

# 参考帧：
# 你的动作起始帧是 1525，通常第一帧双脚站稳，适合作为脚 IK 默认姿态。
REFERENCE_FRAME = 1525

# 旋转修复强度：
# 0.0 = 不修
# 1.0 = 每帧 foot_ik 旋转完全改成参考帧旋转
# 0.75 = 保留 25% 原始脚部旋转
#
# 你第二张图已经有明显扭曲，建议先 0.85。
# 如果脚还是扭，改 1.0。
# 如果脚太死板，改 0.6。
STRENGTH = 0.85

# 是否只处理当前时间线范围
USE_SCENE_FRAME_RANGE = True

# 是否每帧插关键帧
KEY_EVERY_FRAME = True


# =========================
# 工具函数
# =========================

def find_rig(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Rig armature not found: {name}")
    return obj


def get_rotation_quat(pb):
    """
    获取 pose bone 当前局部旋转，统一转成 quaternion。
    """
    mode = pb.rotation_mode

    if mode == "QUATERNION":
        q = pb.rotation_quaternion.copy()
    elif mode == "AXIS_ANGLE":
        q = pb.rotation_axis_angle.to_quaternion()
    else:
        q = pb.rotation_euler.to_quaternion()

    q.normalize()
    return q


def set_rotation_from_quat(pb, q):
    """
    按骨骼当前 rotation_mode 写回旋转。
    """
    q = q.copy()
    q.normalize()

    mode = pb.rotation_mode

    if mode == "QUATERNION":
        pb.rotation_quaternion = q
    elif mode == "AXIS_ANGLE":
        axis, angle = q.to_axis_angle()
        pb.rotation_axis_angle[0] = angle
        pb.rotation_axis_angle[1] = axis.x
        pb.rotation_axis_angle[2] = axis.y
        pb.rotation_axis_angle[3] = axis.z
    else:
        pb.rotation_euler = q.to_euler(mode)


def insert_rotation_key(pb, frame):
    mode = pb.rotation_mode

    if mode == "QUATERNION":
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    elif mode == "AXIS_ANGLE":
        pb.keyframe_insert(data_path="rotation_axis_angle", frame=frame)
    else:
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_linear_interpolation_for_bone(action, bone_name):
    if action is None:
        return

    paths = [
        f'pose.bones["{bone_name}"].rotation_quaternion',
        f'pose.bones["{bone_name}"].rotation_euler',
        f'pose.bones["{bone_name}"].rotation_axis_angle',
    ]

    for fc in action.fcurves:
        if fc.data_path in paths:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.update()


def main():
    scene = bpy.context.scene
    rig = find_rig(RIG_NAME)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    print("======================================")
    print("[Teto foot IK rotation dampen]")
    print(f"Rig:       {rig.name}")
    print(f"Frames:    {frame_start}-{frame_end}")
    print(f"Ref frame: {REFERENCE_FRAME}")
    print(f"Strength:  {STRENGTH}")
    print("======================================")

    # 确保 pose mode 相关数据可用
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)

    # 1. 在参考帧记录 foot_ik 参考旋转
    scene.frame_set(REFERENCE_FRAME)
    bpy.context.view_layer.update()

    ref_rotations = {}

    for bone_name in FOOT_IK_BONES:
        pb = rig.pose.bones.get(bone_name)
        if pb is None:
            print(f"[missing] {bone_name}")
            continue

        ref_rotations[bone_name] = get_rotation_quat(pb)
        print(f"[ref] {bone_name}: {ref_rotations[bone_name]}")

    if not ref_rotations:
        raise RuntimeError("No valid foot IK bones found.")

    # 2. 逐帧把 foot_ik 旋转向参考姿态拉回
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        for bone_name, ref_q in ref_rotations.items():
            pb = rig.pose.bones.get(bone_name)
            if pb is None:
                continue

            cur_q = get_rotation_quat(pb)

            # 防止四元数走远路
            if cur_q.dot(ref_q) < 0:
                ref_q_use = -ref_q
            else:
                ref_q_use = ref_q

            new_q = cur_q.slerp(ref_q_use, STRENGTH)
            set_rotation_from_quat(pb, new_q)

            if KEY_EVERY_FRAME:
                insert_rotation_key(pb, frame)

    # 3. 线性插值，避免贝塞尔过冲
    action = rig.animation_data.action if rig.animation_data else None

    for bone_name in ref_rotations.keys():
        set_linear_interpolation_for_bone(action, bone_name)

    # 4. 保存
    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("--------------------------------------")
    print(f"[saved] {out}")
    print("======================================")


if __name__ == "__main__":
    main()
```

---

# 四、怎么运行

你现在打开已经扶正的文件，比如：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_global_corrected.blend
```

注意：**先不要用 mesh floor lift 之后的文件**。  
从“扶正但还没地板 mesh 修复”的文件开始。

然后：

1. Blender 顶部切到 `Scripting`
2. 新建 Text
3. 粘贴脚本
4. Run Script

输出：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_rot_fixed.blend
```

---

# 五、跑完后你看什么

重点看脚：

## 情况 A：脚不再极端扭曲，脚掌也没那么歪

很好，继续下一步地板修复。

## 情况 B：脚还是扭，但少了一些

把脚本里：

```python
STRENGTH = 0.85
```

改成：

```python
STRENGTH = 1.0
```

再跑一次。

## 情况 C：脚完全不扭了，但动作看起来脚太死

把：

```python
STRENGTH = 0.85
```

改成：

```python
STRENGTH = 0.6
```

这会保留更多原本脚部旋转。

---

# 六、为什么这一步可能比地板修复更重要

你第二张图这种情况属于：

```text
脚 IK 旋转异常 → 网格变形 → 脚底最低点异常
```

如果直接跑 mesh floor lift，脚底最低点会因为扭曲不断变化，脚本可能误以为：

```text
人该往上抬
```

于是造成：

```text
脚更怪
人上下弹
踩棉花糖
```

所以必须先把 foot IK 旋转收住。

---

# 七、如果 foot_ik 旋转弱化后仍有极端扭曲

那说明扭曲可能不是来自：

```text
foot_ik.L / foot_ik.R
```

而是来自更下游或旁路骨骼，比如：

```text
toe / toe_ik
足首
つま先
ORG-foot
MCH-foot
```

这种情况下下一步要导出目标 rig 的骨骼列表。

我给你一个快速导出脚本。

---

## 可选：导出目标 rig 骨骼列表

保存为：

```text
F:\mocap_ai_doctor\scripts\export_target_rig_bones.py
```

内容：

```python
import bpy
import json
from pathlib import Path


RIG_NAME = "RIG-arue式重音テトver 2.01_arm"
OUTPUT_JSON = "F:/mocap_ai_doctor/reports/teto_rig_bones.json"


def main():
    rig = bpy.data.objects.get(RIG_NAME)

    if not rig or rig.type != "ARMATURE":
        raise RuntimeError(f"Rig not found: {RIG_NAME}")

    bones = []

    for pb in rig.pose.bones:
        bones.append({
            "name": pb.name,
            "parent": pb.parent.name if pb.parent else None,
            "children": [c.name for c in pb.children],
            "rotation_mode": pb.rotation_mode,
        })

    out = Path(OUTPUT_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump({
            "rig": rig.name,
            "bone_count": len(bones),
            "bones": bones
        }, f, ensure_ascii=False, indent=2)

    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
```

如果 `foot_ik` 修完仍有问题，你把 `teto_rig_bones.json` 里包含这些关键词的骨骼名贴我：

```text
foot
toe
heel
足
つま
IK
ORG
MCH
```

---

# 八、修完 foot_ik 之后再做什么

如果 foot_ik 旋转修复成功，下一步才回到：

```text
repair_teto_mesh_floor_lift.py
```

但参数建议更保守一点：

```python
FLOOR_Z = 0.0257
TARGET_CLEARANCE = 0.0015
TOLERANCE = 0.004
STRENGTH = 0.65
MAX_DELTA_PER_FRAME = 0.006
```

因为现在脚本不是主要修大穿地，只是处理鞋底轻微插地。

---

# 九、当前更新后的目标阶段顺序

现在我们改成：

```text
teto_retarget_v1_global_corrected.blend
    ↓
foot_ik 旋转弱化 / 防脚扭曲
    ↓
teto_retarget_v1_footik_rot_fixed.blend
    ↓
检查脚是否还歪/扭
    ↓
mesh 地板轻微抬升
    ↓
最终检查脚滑
```

你先跑 `repair_teto_foot_ik_rotation_dampen.py`。  
如果 `STRENGTH = 0.85` 后脚明显变正常，就继续；如果还扭，直接试 `1.0`。

---
## 🧑‍💻 User

你这脚本有问题，我运行完脚完全不转了，strength从0.1到0.95都试了，没区别，看了系统控制台，也没报错
[Teto foot IK rotation dampen]
Rig:       RIG-arue式重音テトver 2.01_arm
Frames:    1525-2836
Ref frame: 1525
Strength:  0.1
======================================
[ref] foot_ik.L: <Quaternion (w=0.9659, x=0.0379, y=-0.0921, z=0.2389)>
[ref] foot_ik.R: <Quaternion (w=0.9850, x=-0.0120, y=0.0018, z=-0.1721)>
MeasureIt: Cleaning data
Info: Saved "teto_retarget_v1_footik_rot_fixed.blend"
--------------------------------------
[saved] F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_rot_fixed.blend
======================================
======================================
[Teto foot IK rotation dampen]
Rig:       RIG-arue式重音テトver 2.01_arm
Frames:    1525-2836
Ref frame: 1525
Strength:  0.95
======================================
[ref] foot_ik.L: <Quaternion (w=0.9659, x=0.0379, y=-0.0921, z=0.2389)>
[ref] foot_ik.R: <Quaternion (w=0.9850, x=-0.0120, y=0.0018, z=-0.1721)>
MeasureIt: Cleaning data
Info: Saved "teto_retarget_v1_footik_rot_fixed.blend"
--------------------------------------
[saved] F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_rot_fixed.blend

---
## 🤖 Assistant

对，这版脚本确实设计错了。问题不在你操作。

我上一版做的是：

```text
把 foot_ik.L / foot_ik.R 的完整旋转，包括脚尖朝向 yaw、脚掌 roll、脚掌 pitch，全都往参考帧拉回
```

这太粗暴了。  
`foot_ik` 的旋转里有一部分是**正常的脚朝向变化**，不能全部压掉。你看到“脚完全不转了”，就是因为脚尖朝向也被一起锁死了。

而且你说 `STRENGTH = 0.1` 到 `0.95` 看起来都差不多，这说明在 MikuMikuRig 这个 rig 里，`foot_ik` 的旋转可能被控制器/约束/插值方式放大或接管了。总之，上一版不要用了。

---

# 现在先回退

请从这个文件继续：

```text
teto_retarget_v1_global_corrected.blend
```

也就是：

```text
已经扶正，但还没跑 foot_ik rotation dampen 的版本
```

不要从：

```text
teto_retarget_v1_footik_rot_fixed.blend
```

继续。

---

# 正确修法：只压脚掌倾斜，不压脚尖朝向

你现在的问题主要是：

```text
脚掌歪、脚踝扭、鞋底侧翻、脚掌扎地
```

而不是：

```text
脚尖方向完全不该变
```

所以应该：

```text
保留脚的水平朝向 yaw
只减弱脚掌 pitch / roll
```

用简单理解就是：

```text
脚可以朝左朝右转
但不要翻船、不要脚底侧翻、不要脚尖过度扎地
```

---

# 新脚本：只弱化 foot_ik 的倾斜轴

保存为：

```text
F:\mocap_ai_doctor\scripts\repair_teto_foot_ik_tilt_only.py
```

内容：

```python
import bpy
from mathutils import Euler
from pathlib import Path
import math


# =========================
# 配置区
# =========================

RIG_NAME = "RIG-arue式重音テトver 2.01_arm"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_retarget_v1_footik_tilt_fixed.blend"

FOOT_IK_BONES = [
    "foot_ik.L",
    "foot_ik.R",
]

REFERENCE_FRAME = 1525

# 只修倾斜，不修水平转向。
# 默认认为：
#   X/Y = 脚掌前后俯仰、左右侧翻
#   Z   = 脚尖水平朝向
#
# 如果结果不对，我们再换轴。
DAMP_X = True
DAMP_Y = True
DAMP_Z = False

# 倾斜修复强度
# 建议先 0.45 或 0.6
# 0.0 = 不改
# 1.0 = 倾斜完全拉回参考帧
STRENGTH = 0.55

# 是否每帧插关键帧
KEY_EVERY_FRAME = True

# 输出调试信息
PRINT_SAMPLES = True
SAMPLE_FRAMES = [1525, 1711, 1834, 2000, 2400, 2836]


# =========================
# 工具函数
# =========================

def find_rig(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Rig armature not found: {name}")
    return obj


def quat_to_euler_xyz(q):
    q = q.copy()
    q.normalize()
    return q.to_euler("XYZ")


def get_current_quat(pb):
    mode = pb.rotation_mode

    if mode == "QUATERNION":
        q = pb.rotation_quaternion.copy()
    elif mode == "AXIS_ANGLE":
        q = pb.rotation_axis_angle.to_quaternion()
    else:
        q = pb.rotation_euler.to_quaternion()

    q.normalize()
    return q


def set_quat_to_bone(pb, q):
    q = q.copy()
    q.normalize()

    mode = pb.rotation_mode

    if mode == "QUATERNION":
        pb.rotation_quaternion = q
    elif mode == "AXIS_ANGLE":
        axis, angle = q.to_axis_angle()
        pb.rotation_axis_angle[0] = angle
        pb.rotation_axis_angle[1] = axis.x
        pb.rotation_axis_angle[2] = axis.y
        pb.rotation_axis_angle[3] = axis.z
    else:
        pb.rotation_euler = q.to_euler(mode)


def insert_rotation_key(pb, frame):
    mode = pb.rotation_mode

    if mode == "QUATERNION":
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    elif mode == "AXIS_ANGLE":
        pb.keyframe_insert(data_path="rotation_axis_angle", frame=frame)
    else:
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)


def lerp_angle(a, b, t):
    """
    角度插值，处理 -pi/pi 环绕。
    返回从 a 向 b 走 t 的结果。
    """
    diff = (b - a + math.pi) % (2.0 * math.pi) - math.pi
    return a + diff * t


def damp_tilt_euler(cur_e, ref_e):
    x = cur_e.x
    y = cur_e.y
    z = cur_e.z

    if DAMP_X:
        x = lerp_angle(cur_e.x, ref_e.x, STRENGTH)
    if DAMP_Y:
        y = lerp_angle(cur_e.y, ref_e.y, STRENGTH)
    if DAMP_Z:
        z = lerp_angle(cur_e.z, ref_e.z, STRENGTH)

    return Euler((x, y, z), "XYZ")


def set_linear_for_bone(action, bone_name):
    if action is None:
        return

    paths = [
        f'pose.bones["{bone_name}"].rotation_quaternion',
        f'pose.bones["{bone_name}"].rotation_euler',
        f'pose.bones["{bone_name}"].rotation_axis_angle',
    ]

    for fc in action.fcurves:
        if fc.data_path in paths:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.update()


def deg_tuple(e):
    return (
        round(math.degrees(e.x), 2),
        round(math.degrees(e.y), 2),
        round(math.degrees(e.z), 2),
    )


def main():
    scene = bpy.context.scene
    rig = find_rig(RIG_NAME)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)

    print("======================================")
    print("[Teto foot IK tilt-only dampen]")
    print(f"Rig:       {rig.name}")
    print(f"Frames:    {frame_start}-{frame_end}")
    print(f"Ref frame: {REFERENCE_FRAME}")
    print(f"Strength:  {STRENGTH}")
    print(f"Damp axes: X={DAMP_X}, Y={DAMP_Y}, Z={DAMP_Z}")
    print("======================================")

    # 1. 读取参考帧旋转
    scene.frame_set(REFERENCE_FRAME)
    bpy.context.view_layer.update()

    ref_eulers = {}

    for bone_name in FOOT_IK_BONES:
        pb = rig.pose.bones.get(bone_name)
        if pb is None:
            print(f"[missing] {bone_name}")
            continue

        q = get_current_quat(pb)
        ref_e = quat_to_euler_xyz(q)
        ref_eulers[bone_name] = ref_e

        print(f"[ref] {bone_name}: XYZ deg {deg_tuple(ref_e)}")

    if not ref_eulers:
        raise RuntimeError("No valid foot IK bones found.")

    # 2. 逐帧只弱化倾斜轴
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        for bone_name, ref_e in ref_eulers.items():
            pb = rig.pose.bones.get(bone_name)
            if pb is None:
                continue

            cur_q = get_current_quat(pb)
            cur_e = quat_to_euler_xyz(cur_q)

            new_e = damp_tilt_euler(cur_e, ref_e)
            new_q = new_e.to_quaternion()

            set_quat_to_bone(pb, new_q)

            if KEY_EVERY_FRAME:
                insert_rotation_key(pb, frame)

    # 3. 线性插值
    action = rig.animation_data.action if rig.animation_data else None

    for bone_name in ref_eulers.keys():
        set_linear_for_bone(action, bone_name)

    # 4. 打印几个采样帧，方便确认 Z 有没有被保留
    if PRINT_SAMPLES:
        print("--------------------------------------")
        print("[samples after repair]")
        for frame in SAMPLE_FRAMES:
            if frame < frame_start or frame > frame_end:
                continue

            scene.frame_set(frame)
            bpy.context.view_layer.update()

            for bone_name in FOOT_IK_BONES:
                pb = rig.pose.bones.get(bone_name)
                if pb is None:
                    continue

                e = quat_to_euler_xyz(get_current_quat(pb))
                print(f"frame {frame} {bone_name}: XYZ deg {deg_tuple(e)}")

    # 5. 保存
    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("--------------------------------------")
    print(f"[saved] {out}")
    print("======================================")


if __name__ == "__main__":
    main()
```

---

# 怎么运行

打开：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_global_corrected.blend
```

不要打开上次 footik 修坏的文件。

然后在 Blender 里运行：

```text
repair_teto_foot_ik_tilt_only.py
```

输出：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_fixed.blend
```

---

# 先用这个参数

先保持：

```python
DAMP_X = True
DAMP_Y = True
DAMP_Z = False
STRENGTH = 0.55
```

看效果。

---

# 判断结果

## 情况 A：脚可以转向了，但不再严重侧翻

这就是我们要的。继续下一步。

## 情况 B：脚还是侧翻/扎地明显

把：

```python
STRENGTH = 0.55
```

改成：

```python
STRENGTH = 0.75
```

再跑。

## 情况 C：脚又几乎不转了

说明 `Z` 不是脚尖水平朝向轴，或者 MikuMikuRig 的 foot_ik 轴和我们假设不一样。

这时不要继续猜，我们导出/观察轴数据。

---

# 如果情况 C 出现，跑诊断脚本

保存为：

```text
F:\mocap_ai_doctor\scripts\inspect_teto_foot_ik_rotation.py
```

内容：

```python
import bpy
import math
import json
from pathlib import Path


RIG_NAME = "RIG-arue式重音テトver 2.01_arm"

BONES = [
    "foot_ik.L",
    "foot_ik.R",
]

OUTPUT_JSON = "F:/mocap_ai_doctor/reports/teto_foot_ik_rotation_inspect.json"

SAMPLE_EVERY_N_FRAMES = 10


def find_rig(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Rig not found: {name}")
    return obj


def get_quat(pb):
    if pb.rotation_mode == "QUATERNION":
        q = pb.rotation_quaternion.copy()
    elif pb.rotation_mode == "AXIS_ANGLE":
        q = pb.rotation_axis_angle.to_quaternion()
    else:
        q = pb.rotation_euler.to_quaternion()

    q.normalize()
    return q


def deg_tuple(e):
    return [
        round(math.degrees(e.x), 3),
        round(math.degrees(e.y), 3),
        round(math.degrees(e.z), 3),
    ]


def main():
    scene = bpy.context.scene
    rig = find_rig(RIG_NAME)

    frame_start = scene.frame_start
    frame_end = scene.frame_end

    report = {
        "rig": rig.name,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "bones": {},
    }

    for bone_name in BONES:
        pb = rig.pose.bones.get(bone_name)
        if pb is None:
            report["bones"][bone_name] = {"missing": True}
            continue

        samples = []
        xs, ys, zs = [], [], []

        for frame in range(frame_start, frame_end + 1, SAMPLE_EVERY_N_FRAMES):
            scene.frame_set(frame)
            bpy.context.view_layer.update()

            pb = rig.pose.bones.get(bone_name)
            q = get_quat(pb)
            e = q.to_euler("XYZ")
            d = deg_tuple(e)

            samples.append({
                "frame": frame,
                "xyz_deg": d,
                "rotation_mode": pb.rotation_mode,
            })

            xs.append(d[0])
            ys.append(d[1])
            zs.append(d[2])

        report["bones"][bone_name] = {
            "rotation_mode": pb.rotation_mode,
            "x_deg_minmax": [min(xs), max(xs)] if xs else None,
            "y_deg_minmax": [min(ys), max(ys)] if ys else None,
            "z_deg_minmax": [min(zs), max(zs)] if zs else None,
            "samples": samples[:50],
        }

    out = Path(OUTPUT_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
```

跑完把这个文件里这几项发我：

```json
"x_deg_minmax"
"y_deg_minmax"
"z_deg_minmax"
```

我就能判断哪个轴是脚尖朝向，哪个轴是侧翻/俯仰。

---

# 当前顺序更新

现在目标阶段修复顺序改成：

```text
teto_retarget_v1_global_corrected.blend
    ↓
只弱化 foot_ik 倾斜轴，不弱化脚尖朝向
    ↓
teto_retarget_v1_footik_tilt_fixed.blend
    ↓
确认脚不再严重歪/扭
    ↓
再做 mesh floor lift
```

先跑 `repair_teto_foot_ik_tilt_only.py`。  
如果这次脚能正常转向、但不再严重翻船，我们就继续地面轻修。

---
## 🧑‍💻 User

改成了0.65，效果很好，那些极端情况修完以后还是剩了一点点z轴偏移，到时候手动修一下吧，顺便看了一下，之前对foot planting的标注还挺准，范围大小可能略有问题，但是踩点都踩对了。继续。

---
## 🤖 Assistant

很好，`STRENGTH = 0.65` 说明这条路线对了：

```text
保留脚尖转向
压掉脚掌侧翻/俯仰过度
```

你说“极端情况还剩一点点 z 轴偏移，到时候手动修”，这也合理。那种少量残留不要继续用自动脚本硬压，否则又会把正常脚朝向变死。

现在继续下一步：

> **在 foot_ik 倾斜修复后的文件上，做目标模型 mesh 地板轻修。**

也就是处理你前面说的：

```text
绝大多数时候鞋底轻微插地；
弯膝盖猛的时候脚掌插得深一些。
```

这次参数要比我上一版更保守，因为脚部大扭曲已经修掉了，剩下只是地面微调。

---

# 当前文件链路

你现在应该有这个文件：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_fixed.blend
```

接下来从它继续。

输出文件：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_floor_fixed.blend
```

---

# 脚本：`repair_teto_mesh_floor_lift_v2.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\repair_teto_mesh_floor_lift_v2.py
```

内容：

```python
import bpy
import math
from pathlib import Path


# =========================
# 配置区
# =========================

MODEL_ROOT_NAME = "arue式重音テトver 2.01"
CORRECTION_EMPTY_NAME = "teto_global_correction"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_retarget_v1_footik_tilt_floor_fixed.blend"

# 你实测出来的目标地面高度
FLOOR_Z = 0.0257

# 这次只做轻修
TARGET_CLEARANCE = 0.0015

# 允许 4mm 内轻微插地，不修
TOLERANCE = 0.004

# 单帧最大抬升，避免异常网格点把人抬飞
MAX_LIFT_PER_FRAME = 0.045

# 修复强度，保守
STRENGTH = 0.60

# 修正曲线平滑半径
SMOOTH_RADIUS = 3

# 限制每帧抬升变化，防止踩棉花糖
MAX_DELTA_PER_FRAME = 0.006

# 只扫描可见 mesh
VISIBLE_ONLY = True

# 顶点采样步长
# 1 最准但慢；2 通常够用
VERTEX_SAMPLE_STEP = 2

# 排除地面、视频、刚体、关节等
EXCLUDE_NAME_KEYWORDS = [
    "ground",
    "plane",
    "video",
    "VID",
    "rigid",
    "Rigid",
    "joints",
    "Joint",
    "Camera",
    "Light",
]

PRINT_WORST = True
PRINT_LIMIT = 80


# =========================
# 工具函数
# =========================

def find_object(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object not found: {name}")
    return obj


def has_excluded_keyword(obj):
    cur = obj
    while cur:
        for kw in EXCLUDE_NAME_KEYWORDS:
            if kw in cur.name:
                return True
        cur = cur.parent
    return False


def collect_meshes_under(root):
    objects = [root] + list(root.children_recursive)
    meshes = []

    for obj in objects:
        if obj.type != "MESH":
            continue

        if VISIBLE_ONLY and not obj.visible_get():
            continue

        if has_excluded_keyword(obj):
            continue

        if not obj.data or len(obj.data.vertices) == 0:
            continue

        meshes.append(obj)

    return meshes


def gaussian_weights(radius):
    if radius <= 0:
        return [1.0], [0]

    sigma = max(1.0, radius / 1.5)
    offsets = list(range(-radius, radius + 1))
    weights = []

    for off in offsets:
        w = math.exp(-(off * off) / (2.0 * sigma * sigma))
        weights.append(w)

    total = sum(weights)
    weights = [w / total for w in weights]

    return weights, offsets


def smooth_values(values_by_frame, frame_start, frame_end, radius):
    weights, offsets = gaussian_weights(radius)
    out = {}

    for frame in range(frame_start, frame_end + 1):
        acc = 0.0
        total = 0.0

        for w, off in zip(weights, offsets):
            ff = frame + off
            if ff < frame_start or ff > frame_end:
                continue
            acc += values_by_frame.get(ff, 0.0) * w
            total += w

        out[frame] = acc / total if total > 1e-8 else values_by_frame.get(frame, 0.0)

    return out


def limit_delta(values_by_frame, frame_start, frame_end, max_delta):
    out = dict(values_by_frame)

    # forward pass
    prev = out.get(frame_start, 0.0)
    for frame in range(frame_start + 1, frame_end + 1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    # backward pass
    prev = out.get(frame_end, 0.0)
    for frame in range(frame_end - 1, frame_start - 1, -1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    return out


def evaluated_mesh_min_z(obj, depsgraph):
    eval_obj = obj.evaluated_get(depsgraph)

    try:
        mesh = eval_obj.to_mesh()
    except Exception:
        return None

    if mesh is None or len(mesh.vertices) == 0:
        return None

    mw = eval_obj.matrix_world
    min_z = None

    step = max(1, int(VERTEX_SAMPLE_STEP))

    for i in range(0, len(mesh.vertices), step):
        z = (mw @ mesh.vertices[i].co).z
        if min_z is None or z < min_z:
            min_z = float(z)

    eval_obj.to_mesh_clear()
    return min_z


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def ensure_location_z_fcurve(obj):
    obj.animation_data_create()

    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_floor_lift")

    action = obj.animation_data.action
    fc = get_fcurve(action, "location", 2)

    if fc is None:
        fc = action.fcurves.new(data_path="location", index=2)

    return action, fc


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_key_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)

    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value

    kp.interpolation = "LINEAR"


def fcurve_has_keys(fcurve):
    return fcurve is not None and len(fcurve.keyframe_points) > 0


def main():
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    root = find_object(MODEL_ROOT_NAME)
    correction = find_object(CORRECTION_EMPTY_NAME)

    frame_start = int(scene.frame_start)
    frame_end = int(scene.frame_end)

    meshes = collect_meshes_under(root)

    if not meshes:
        raise RuntimeError("No target meshes found under model root.")

    print("====================================")
    print("[Teto mesh floor lift v2]")
    print(f"Root:       {root.name}")
    print(f"Correction: {correction.name}")
    print(f"Frames:     {frame_start}-{frame_end}")
    print(f"Floor Z:    {FLOOR_Z}")
    print(f"Meshes:     {len(meshes)}")
    for m in meshes:
        print(f"  mesh: {m.name}, verts={len(m.data.vertices)}")
    print("====================================")

    # 1. 采样每帧 mesh 最低点
    min_z_by_frame = {}
    worst_mesh_by_frame = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        depsgraph.update()

        global_min_z = None
        global_min_mesh = None

        for obj in meshes:
            mz = evaluated_mesh_min_z(obj, depsgraph)
            if mz is None:
                continue

            if global_min_z is None or mz < global_min_z:
                global_min_z = mz
                global_min_mesh = obj.name

        min_z_by_frame[frame] = global_min_z
        worst_mesh_by_frame[frame] = global_min_mesh

    # 2. 计算每帧 raw lift
    raw_lift = {}
    worst_samples = []

    target_z = FLOOR_Z + TARGET_CLEARANCE

    for frame in range(frame_start, frame_end + 1):
        min_z = min_z_by_frame.get(frame)

        if min_z is None:
            raw_lift[frame] = 0.0
            continue

        penetration = target_z - min_z

        if penetration > TOLERANCE:
            lift = min(penetration, MAX_LIFT_PER_FRAME) * STRENGTH
            raw_lift[frame] = lift

            worst_samples.append({
                "frame": frame,
                "min_z": min_z,
                "penetration": penetration,
                "lift": lift,
                "mesh": worst_mesh_by_frame.get(frame),
            })
        else:
            raw_lift[frame] = 0.0

    # 3. 平滑 + 限制变化
    smoothed = smooth_values(raw_lift, frame_start, frame_end, SMOOTH_RADIUS)
    corrected = limit_delta(smoothed, frame_start, frame_end, MAX_DELTA_PER_FRAME)

    # 4. 写入 correction empty 的 location.z
    action, z_curve = ensure_location_z_fcurve(correction)

    base_z = correction.location.z

    changed_frames = 0
    max_lift = 0.0

    for frame in range(frame_start, frame_end + 1):
        lift = corrected.get(frame, 0.0)

        if abs(lift) < 1e-8:
            continue

        if fcurve_has_keys(z_curve):
            original_z = z_curve.evaluate(frame)
        else:
            original_z = base_z

        new_z = original_z + lift
        set_key_value(z_curve, frame, new_z)

        changed_frames += 1
        max_lift = max(max_lift, lift)

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[changed_frames] {changed_frames}")
    print(f"[max_lift] {max_lift:.5f} m")

    if PRINT_WORST:
        print("------------------------------------")
        print("[worst penetration samples]")
        for s in worst_samples[:PRINT_LIMIT]:
            print(
                f"frame={s['frame']}, "
                f"min_z={s['min_z']:.5f}, "
                f"penetration={s['penetration']:.5f}, "
                f"lift={s['lift']:.5f}, "
                f"mesh={s['mesh']}"
            )
        if len(worst_samples) > PRINT_LIMIT:
            print(f"... {len(worst_samples) - PRINT_LIMIT} more")

    print("------------------------------------")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 怎么运行

打开：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_fixed.blend
```

在 Blender 的 `Scripting` 里运行脚本。

输出：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_floor_fixed.blend
```

---

# 跑完后看什么

重点检查：

```text
1. 弯膝盖时脚掌插地是否减少；
2. 脚是否又开始踩棉花糖；
3. 人是否整体上下弹；
4. foot_ik 倾斜修好的效果有没有被破坏。
```

这版只动：

```text
teto_global_correction.location.z
```

不会再改脚 IK 旋转，所以不会破坏你刚刚修好的 foot tilt。

---

# 如果结果有问题怎么调

## A. 仍然有明显脚掌插地

把：

```python
STRENGTH = 0.60
```

改为：

```python
STRENGTH = 0.75
```

或者把：

```python
TOLERANCE = 0.004
```

改为：

```python
TOLERANCE = 0.0025
```

---

## B. 踩棉花糖变明显

把：

```python
STRENGTH = 0.60
```

改为：

```python
STRENGTH = 0.45
```

或者把：

```python
MAX_DELTA_PER_FRAME = 0.006
```

改为：

```python
MAX_DELTA_PER_FRAME = 0.0035
```

---

## C. 整个人被抬得太多

把：

```python
MAX_LIFT_PER_FRAME = 0.045
```

改为：

```python
MAX_LIFT_PER_FRAME = 0.025
```

---

# 这一步之后

如果地板轻修效果也好，我们就进入最后检查：

```text
目标脚 IK 滑动诊断
```

你已经说脚滑轻微，而且 source foot planting 标注还挺准，所以我不建议立刻上复杂的 `K + 6 接触点` 根骨抵消法。

下一步只做一个报告：

```text
在 LS/LE、RS/RE 接触段内，
foot_ik.L / foot_ik.R 到底滑了多少？
```

如果滑动量很小，就不修；  
如果某几段明显滑，再只修那些段。这样不会过度处理。

---
## 🧑‍💻 User

肯定出问题了，teto在平静时z轴不怎么变，一动起来就整个人往上飞，没有任何往下飞的部分，一直越飞越高

---
## 🤖 Assistant

是的，这个是我脚本的 bug，不是你操作问题。  
**立刻丢弃这个会飞的文件，不要从它继续。**

你现在应该回到这个文件：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_fixed.blend
```

也就是：

```text
已经扶正
已经修 foot_ik 倾斜
但还没跑 mesh floor lift 的版本
```

---

# 1. 为什么会越飞越高？

上一版 `repair_teto_mesh_floor_lift_v2.py` 的问题在这里：

```python
original_z = z_curve.evaluate(frame)
new_z = original_z + lift
set_key_value(z_curve, frame, new_z)
```

看起来没问题，但实际运行时它是一边写关键帧，一边继续 evaluate 后面的帧。

由于前面帧已经插入了更高的 Z，后面帧 `evaluate(frame)` 会受到前面新增关键帧插值影响，于是变成：

```text
第 1 帧：原始 Z + lift
第 2 帧：已经被第 1 帧影响过的 Z + lift
第 3 帧：已经被前面影响过的 Z + lift
...
```

结果就是你看到的：

```text
只往上修，不往下回；
一动起来越飞越高。
```

正确做法应该是：

```text
先完整记录原始 correction_empty.location.z 曲线；
再计算每帧 lift；
最后一次性写入 original_z_by_frame[frame] + lift[frame]
```

不能边写边读同一条曲线。

---

# 2. 不要用坏文件

不要继续用：

```text
teto_retarget_v1_footik_tilt_floor_fixed.blend
```

或者任何你看到“越飞越高”的文件。

请重新打开：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_fixed.blend
```

---

# 3. 修正版脚本：`repair_teto_mesh_floor_lift_v3_safe.py`

这个版本修了两个关键问题：

1. **先缓存原始 Z，再写入，不会累计飞高。**
2. **如果发现 `teto_global_correction` 已经有 location.z 关键帧，可以选择清掉重新写。**

保存为：

```text
F:\mocap_ai_doctor\scripts\repair_teto_mesh_floor_lift_v3_safe.py
```

内容：

```python
import bpy
import math
from pathlib import Path


# =========================
# 配置区
# =========================

MODEL_ROOT_NAME = "arue式重音テトver 2.01"
CORRECTION_EMPTY_NAME = "teto_global_correction"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_retarget_v1_footik_tilt_floor_fixed_v3.blend"

# 你实测的 Teto 地面高度
FLOOR_Z = 0.0257

# 轻修参数
TARGET_CLEARANCE = 0.0015
TOLERANCE = 0.004

MAX_LIFT_PER_FRAME = 0.035
STRENGTH = 0.55

SMOOTH_RADIUS = 3
MAX_DELTA_PER_FRAME = 0.0045

VISIBLE_ONLY = True
VERTEX_SAMPLE_STEP = 2

# 重要：
# 如果你是从干净的 footik_tilt_fixed.blend 开始，可以 False。
# 如果你不确定这个 Empty 有没有被上一版坏脚本写过 Z key，可以 True。
#
# 我建议这次设 True。
RESET_EXISTING_LOCATION_Z_KEYS = True

EXCLUDE_NAME_KEYWORDS = [
    "ground",
    "plane",
    "video",
    "VID",
    "rigid",
    "Rigid",
    "joints",
    "Joint",
    "Camera",
    "Light",
]

PRINT_WORST = True
PRINT_LIMIT = 80


# =========================
# 工具函数
# =========================

def find_object(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object not found: {name}")
    return obj


def has_excluded_keyword(obj):
    cur = obj
    while cur:
        for kw in EXCLUDE_NAME_KEYWORDS:
            if kw in cur.name:
                return True
        cur = cur.parent
    return False


def collect_meshes_under(root):
    objs = [root] + list(root.children_recursive)
    meshes = []

    for obj in objs:
        if obj.type != "MESH":
            continue

        if VISIBLE_ONLY and not obj.visible_get():
            continue

        if has_excluded_keyword(obj):
            continue

        if not obj.data or len(obj.data.vertices) == 0:
            continue

        meshes.append(obj)

    return meshes


def gaussian_weights(radius):
    if radius <= 0:
        return [1.0], [0]

    sigma = max(1.0, radius / 1.5)
    offsets = list(range(-radius, radius + 1))
    weights = []

    for off in offsets:
        w = math.exp(-(off * off) / (2.0 * sigma * sigma))
        weights.append(w)

    s = sum(weights)
    weights = [w / s for w in weights]
    return weights, offsets


def smooth_values(values_by_frame, frame_start, frame_end, radius):
    weights, offsets = gaussian_weights(radius)
    out = {}

    for frame in range(frame_start, frame_end + 1):
        acc = 0.0
        total = 0.0

        for w, off in zip(weights, offsets):
            ff = frame + off
            if ff < frame_start or ff > frame_end:
                continue

            acc += values_by_frame.get(ff, 0.0) * w
            total += w

        out[frame] = acc / total if total > 1e-8 else values_by_frame.get(frame, 0.0)

    return out


def limit_delta(values_by_frame, frame_start, frame_end, max_delta):
    out = dict(values_by_frame)

    # forward
    prev = out.get(frame_start, 0.0)
    for frame in range(frame_start + 1, frame_end + 1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    # backward
    prev = out.get(frame_end, 0.0)
    for frame in range(frame_end - 1, frame_start - 1, -1):
        cur = out.get(frame, 0.0)
        if cur > prev + max_delta:
            cur = prev + max_delta
        elif cur < prev - max_delta:
            cur = prev - max_delta
        out[frame] = cur
        prev = cur

    return out


def evaluated_mesh_min_z(obj, depsgraph):
    eval_obj = obj.evaluated_get(depsgraph)

    try:
        mesh = eval_obj.to_mesh()
    except Exception:
        return None

    if mesh is None or len(mesh.vertices) == 0:
        return None

    mw = eval_obj.matrix_world
    min_z = None

    step = max(1, int(VERTEX_SAMPLE_STEP))

    for i in range(0, len(mesh.vertices), step):
        z = (mw @ mesh.vertices[i].co).z
        if min_z is None or z < min_z:
            min_z = float(z)

    eval_obj.to_mesh_clear()
    return min_z


def get_fcurve(action, data_path, index):
    if action is None:
        return None

    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc

    return None


def remove_location_z_fcurve(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return 0

    action = obj.animation_data.action
    removed = 0

    for fc in list(action.fcurves):
        if fc.data_path == "location" and fc.array_index == 2:
            action.fcurves.remove(fc)
            removed += 1

    return removed


def ensure_location_z_fcurve(obj):
    obj.animation_data_create()

    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_floor_lift_v3")

    action = obj.animation_data.action

    fc = get_fcurve(action, "location", 2)
    if fc is None:
        fc = action.fcurves.new(data_path="location", index=2)

    return action, fc


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_key_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)

    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value

    kp.interpolation = "LINEAR"


def cache_original_z_values(obj, frame_start, frame_end):
    """
    关键修复点：
    先完整缓存原始 Z，后面写关键帧时绝不再 evaluate 同一条 fcurve。
    """
    scene = bpy.context.scene

    original = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        original[frame] = float(obj.location.z)

    return original


def main():
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    root = find_object(MODEL_ROOT_NAME)
    correction = find_object(CORRECTION_EMPTY_NAME)

    frame_start = int(scene.frame_start)
    frame_end = int(scene.frame_end)

    print("====================================")
    print("[Teto mesh floor lift v3 SAFE]")
    print(f"Root:       {root.name}")
    print(f"Correction: {correction.name}")
    print(f"Frames:     {frame_start}-{frame_end}")
    print(f"Floor Z:    {FLOOR_Z}")
    print("====================================")

    # 0. 缓存原始 correction Z
    # 如果从干净文件开始，基本就是常数。
    # 如果已有正确的 Z 动画，也会尊重原动画。
    original_z_by_frame = cache_original_z_values(correction, frame_start, frame_end)

    print(f"[original z] first={original_z_by_frame[frame_start]:.5f}, last={original_z_by_frame[frame_end]:.5f}")

    # 如果要重置已有 location.z key，必须在缓存后进行。
    if RESET_EXISTING_LOCATION_Z_KEYS:
        removed = remove_location_z_fcurve(correction)
        print(f"[reset] removed existing location.z fcurves: {removed}")

    meshes = collect_meshes_under(root)

    if not meshes:
        raise RuntimeError("No target meshes found under model root.")

    print(f"[meshes] {len(meshes)}")
    for m in meshes:
        print(f"  mesh: {m.name}, verts={len(m.data.vertices)}")

    # 1. 采样每帧 mesh 最低点
    min_z_by_frame = {}
    worst_mesh_by_frame = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        depsgraph.update()

        global_min_z = None
        global_min_mesh = None

        for obj in meshes:
            mz = evaluated_mesh_min_z(obj, depsgraph)
            if mz is None:
                continue

            if global_min_z is None or mz < global_min_z:
                global_min_z = mz
                global_min_mesh = obj.name

        min_z_by_frame[frame] = global_min_z
        worst_mesh_by_frame[frame] = global_min_mesh

    # 2. 计算 raw lift
    raw_lift = {}
    worst_samples = []

    target_z = FLOOR_Z + TARGET_CLEARANCE

    for frame in range(frame_start, frame_end + 1):
        min_z = min_z_by_frame.get(frame)

        if min_z is None:
            raw_lift[frame] = 0.0
            continue

        penetration = target_z - min_z

        if penetration > TOLERANCE:
            lift = min(penetration, MAX_LIFT_PER_FRAME) * STRENGTH
            raw_lift[frame] = lift

            worst_samples.append({
                "frame": frame,
                "min_z": min_z,
                "penetration": penetration,
                "lift": lift,
                "mesh": worst_mesh_by_frame.get(frame),
            })
        else:
            raw_lift[frame] = 0.0

    # 3. 平滑和限速
    smoothed = smooth_values(raw_lift, frame_start, frame_end, SMOOTH_RADIUS)
    corrected_lift = limit_delta(smoothed, frame_start, frame_end, MAX_DELTA_PER_FRAME)

    # 4. 写入 correction.location.z
    # 注意：这里使用缓存的 original_z_by_frame，绝不再次 evaluate 已写入的曲线。
    action, z_curve = ensure_location_z_fcurve(correction)

    changed_frames = 0
    max_lift = 0.0

    for frame in range(frame_start, frame_end + 1):
        lift = corrected_lift.get(frame, 0.0)
        original_z = original_z_by_frame.get(frame, correction.location.z)

        new_z = original_z + lift

        # 即使 lift 为 0，也可以插入原始值，保证曲线不会被前后插值污染。
        set_key_value(z_curve, frame, new_z)

        if abs(lift) > 1e-8:
            changed_frames += 1
            max_lift = max(max_lift, lift)

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[changed_frames] {changed_frames}")
    print(f"[max_lift] {max_lift:.5f} m")
    print(f"[final z] first={z_curve.evaluate(frame_start):.5f}, last={z_curve.evaluate(frame_end):.5f}")

    if PRINT_WORST:
        print("------------------------------------")
        print("[worst penetration samples]")
        for s in worst_samples[:PRINT_LIMIT]:
            print(
                f"frame={s['frame']}, "
                f"min_z={s['min_z']:.5f}, "
                f"penetration={s['penetration']:.5f}, "
                f"lift={s['lift']:.5f}, "
                f"mesh={s['mesh']}"
            )

        if len(worst_samples) > PRINT_LIMIT:
            print(f"... {len(worst_samples) - PRINT_LIMIT} more")

    print("------------------------------------")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 4. 运行方式

请打开这个文件：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_fixed.blend
```

然后在 Blender `Scripting` 里运行：

```text
repair_teto_mesh_floor_lift_v3_safe.py
```

输出：

```text
F:\mocap_ai_doctor\blends\teto_retarget_v1_footik_tilt_floor_fixed_v3.blend
```

---

# 5. 运行后你先看控制台这两行

正常情况下应该类似：

```text
[original z] first=0.00000, last=0.00000
[final z] first=0.00000, last=0.00000
```

或者：

```text
[final z] first=0.00120, last=0.00080
```

允许小变化。

但绝对不应该是：

```text
first=0.00000, last=1.50000
```

如果 `last` 明显比 `first` 高几十厘米甚至几米，那就是仍然有累积问题，立刻停。

---

# 6. 如果这次还是有“踩棉花糖”

把参数再保守一点：

```python
STRENGTH = 0.35
MAX_LIFT_PER_FRAME = 0.02
MAX_DELTA_PER_FRAME = 0.0025
```

但先用我给你的 v3 默认值试一次。

---

# 7. 当前正确文件链路

现在文件链路应该是：

```text
teto_retarget_v1_global_corrected.blend
    ↓ foot_ik tilt-only, strength 0.65
teto_retarget_v1_footik_tilt_fixed.blend
    ↓ mesh floor lift v3 safe
teto_retarget_v1_footik_tilt_floor_fixed_v3.blend
```

不要从旧的：

```text
teto_retarget_v1_footik_tilt_floor_fixed.blend
```

继续。这个就是会越飞越高的坏版本。

---
## 🧑‍💻 User

总体不错普遍的轻微插地解决，偶尔有个例有问题，我觉得已经完全可以算作偶然事件，而且我加大strength对这些个例没有用，反而只会加重漂浮，默认0.55挺不错，感觉手动修就行。中间有一段是我脚不动，人躯干在扭动，这一段脚还是会动，但我相信这个应该是我们接下来要做的内容，和现在这步没关系

---
## 🤖 Assistant

很好，你现在判断是对的：

```text
普遍轻微插地解决了；
少数个例继续自动修反而会漂浮；
这些个例适合手动修；
“脚不动，躯干扭动，但脚还在动”属于 foot planting / foot lock 问题。
```

所以现在进入最后一个核心目标：

> **目标模型阶段的脚部 planted 段锁定。**

这一步不是修“脚底高度”，而是修：

```text
应该踩住的时候，foot_ik 在平面内轻微漂移。
```

---

# 一、当前状态冻结

先把现在这个不错的文件保存/另存为：

```text
F:\mocap_ai_doctor\blends\teto_clean_floor_v1.blend
```

也就是你现在这版：

```text
扶正
foot_ik tilt 修复 0.65
mesh floor lift v3 safe 0.55
```

这个版本已经是一个可靠基线。

---

# 二、接下来怎么修脚滑

你说：

> 中间有一段我脚不动，人躯干在扭动，这一段脚还是会动。

这正是 foot lock 的典型场景。

我们之前生成的 source contact report：

```text
foot_contacts_source_clean_v1.json
```

里面的：

```json
planted_segments
```

可以直接作为目标 Teto 脚 IK 的候选锁定区间。

不过你也说：

> 范围大小可能略有问题，但是踩点都踩对了。

所以脚本要保守一点：

```text
每个 planted segment 去掉头尾几帧；
只锁 XY，不锁 Z；
不改 foot_ik 旋转；
不改 torso_root；
不改 mesh；
不改全局 correction；
```

也就是：

```text
脚仍然可以上下有一点自然变化；
脚尖方向也保留；
只是让踩住那一段的水平位置别漂。
```

---

# 三、先做诊断：目标 foot_ik 在 planted 段滑了多少

先不要直接锁，先测。

## 脚本：`analyze_teto_foot_ik_drift.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\analyze_teto_foot_ik_drift.py
```

内容：

```python
import bpy
import json
import math
from pathlib import Path


# =========================
# 配置区
# =========================

RIG_NAME = "RIG-arue式重音テトver 2.01_arm"

SOURCE_CONTACT_REPORT = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v1.json"

OUTPUT_REPORT = "F:/mocap_ai_doctor/reports/teto_foot_ik_drift_report.json"

FOOT_IK = {
    "L": "foot_ik.L",
    "R": "foot_ik.R",
}

# planted 段头尾去掉几帧，避免换步过渡误判
TRIM_SEGMENT_ENDS = 2

# 小于这个长度的段不分析
MIN_SEGMENT_LEN = 4


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def find_rig(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Rig not found: {name}")
    return obj


def bone_world_loc(armature, bone_name):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None
    return (armature.matrix_world @ pb.matrix).translation.copy()


def dist_xy(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


def analyze_segment(scene, rig, bone_name, a, b):
    positions = []

    for frame in range(a, b + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        loc = bone_world_loc(rig, bone_name)
        if loc is not None:
            positions.append((frame, loc.copy()))

    if not positions:
        return None

    anchor = positions[0][1]

    max_drift = 0.0
    end_drift = dist_xy(positions[0][1], positions[-1][1])

    total_step = 0.0
    prev = positions[0][1]

    for _, loc in positions[1:]:
        d = dist_xy(anchor, loc)
        max_drift = max(max_drift, d)

        total_step += dist_xy(prev, loc)
        prev = loc

    return {
        "frames": [a, b],
        "length": b - a + 1,
        "max_drift_xy_m": round(max_drift, 5),
        "end_drift_xy_m": round(end_drift, 5),
        "total_xy_motion_m": round(total_step, 5),
    }


def main():
    scene = bpy.context.scene
    rig = find_rig(RIG_NAME)
    contact = load_json(SOURCE_CONTACT_REPORT)

    result = {
        "schema_version": "teto_foot_ik_drift_v1",
        "rig": rig.name,
        "source_contact_report": SOURCE_CONTACT_REPORT,
        "params": {
            "trim_segment_ends": TRIM_SEGMENT_ENDS,
            "min_segment_len": MIN_SEGMENT_LEN,
        },
        "feet": {
            "L": [],
            "R": [],
        },
    }

    for side in ["L", "R"]:
        bone_name = FOOT_IK[side]

        if bone_name not in rig.pose.bones:
            print(f"[missing] {bone_name}")
            continue

        segments = contact["feet"][side]["planted_segments"]

        for seg in segments:
            if len(seg) != 2:
                continue

            a, b = int(seg[0]), int(seg[1])
            aa = a + TRIM_SEGMENT_ENDS
            bb = b - TRIM_SEGMENT_ENDS

            if bb - aa + 1 < MIN_SEGMENT_LEN:
                continue

            item = analyze_segment(scene, rig, bone_name, aa, bb)
            if item:
                result["feet"][side].append(item)

    # 排序：最大滑动大的排前面，方便看
    for side in ["L", "R"]:
        result["feet"][side].sort(
            key=lambda x: x["max_drift_xy_m"],
            reverse=True
        )

    out = Path(OUTPUT_REPORT)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("====================================")
    print("[Teto foot IK drift analysis]")
    print(f"Saved: {out}")

    for side in ["L", "R"]:
        arr = result["feet"][side]
        print(f"{side}: {len(arr)} planted segments")
        for item in arr[:10]:
            print(
                f"  {item['frames']} "
                f"max={item['max_drift_xy_m']}m "
                f"end={item['end_drift_xy_m']}m "
                f"total={item['total_xy_motion_m']}m"
            )

    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 四、运行诊断

打开：

```text
F:\mocap_ai_doctor\blends\teto_clean_floor_v1.blend
```

在 Blender `Scripting` 里运行：

```text
analyze_teto_foot_ik_drift.py
```

输出：

```text
F:\mocap_ai_doctor\reports\teto_foot_ik_drift_report.json
```

重点看控制台打印的前几段，比如：

```text
L [1800, 1840] max=0.032m
R [1900, 1930] max=0.018m
```

判断标准大概是：

```text
< 0.01m：基本不用修
0.01m ~ 0.03m：轻微脚滑，可选修
> 0.03m：建议修
> 0.05m：明显脚滑
```

你提到“中间那段脚不动但还动”，一般会在这个报告里排到前面。

---

# 五、如果诊断确认有脚滑：锁定 foot_ik XY

下面这个脚本会：

```text
读取 source planted_segments；
对 Teto 的 foot_ik.L/R；
每个 planted segment 去掉头尾；
把 foot_ik 的 local location X/Y 固定到该段中位数；
Z 不动；
旋转不动；
段头段尾做 2 帧过渡。
```

这比直接 world-space 反推更简单，且对 MikuMikuRig 控制骨通常有效。

---

## 脚本：`repair_teto_foot_ik_xy_lock.py`

保存到：

```text
F:\mocap_ai_doctor\scripts\repair_teto_foot_ik_xy_lock.py
```

内容：

```python
import bpy
import json
import statistics
from pathlib import Path


# =========================
# 配置区
# =========================

RIG_NAME = "RIG-arue式重音テトver 2.01_arm"

SOURCE_CONTACT_REPORT = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v1.json"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_clean_floor_v1_footlock_xy.blend"

FOOT_IK = {
    "L": "foot_ik.L",
    "R": "foot_ik.R",
}

# 去掉 planted 段头尾，避免过渡帧锁错
TRIM_SEGMENT_ENDS = 2

# 太短不锁
MIN_SEGMENT_LEN = 5

# 锁定前后缓入缓出帧数
BLEND_FRAMES = 2

# 只锁 XY，不锁 Z
LOCK_X = True
LOCK_Y = True
LOCK_Z = False

# 使用哪种 anchor
# "median"：取区间内 local location 中位数，更稳
# "first"：取区间第一帧
# "middle"：取区间中间帧
ANCHOR_MODE = "median"

# 只修滑动超过这个值的段
# 0.0 = 所有 planted 段都修
# 建议先 0.008，避免过度修
MIN_LOCAL_XY_RANGE_TO_REPAIR = 0.006

# 是否打印每段
PRINT_SEGMENTS = True


# =========================
# 工具函数
# =========================

def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def find_rig(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Rig not found: {name}")
    return obj


def get_action(rig):
    if not rig.animation_data or not rig.animation_data.action:
        raise RuntimeError("Rig has no action.")
    return rig.animation_data.action


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def ensure_fcurve(action, data_path, index):
    fc = get_fcurve(action, data_path, index)
    if fc is None:
        fc = action.fcurves.new(data_path=data_path, index=index)
    return fc


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value
    kp.interpolation = "LINEAR"


def cache_curve_values(fcurve, frame_start, frame_end):
    return {
        frame: fcurve.evaluate(frame)
        for frame in range(frame_start, frame_end + 1)
    }


def local_xy_range(x_values, y_values):
    if not x_values or not y_values:
        return 0.0
    rx = max(x_values) - min(x_values)
    ry = max(y_values) - min(y_values)
    return (rx * rx + ry * ry) ** 0.5


def choose_anchor(values, a, b, mode):
    frames = list(range(a, b + 1))

    if mode == "first":
        return values[a]

    if mode == "middle":
        mid = frames[len(frames) // 2]
        return values[mid]

    if mode == "median":
        return statistics.median([values[f] for f in frames])

    raise ValueError(f"Unknown anchor mode: {mode}")


def apply_lock_to_channel(values, a, b, anchor, blend_frames):
    """
    返回修复后的 values 副本。
    核心锁定区间 a..b 设为 anchor。
    在 a-blend..a-1 和 b+1..b+blend 做过渡。
    """
    out = dict(values)

    # 核心锁定
    for frame in range(a, b + 1):
        out[frame] = anchor

    # blend in
    for i in range(1, blend_frames + 1):
        frame = a - i
        if frame not in out:
            continue

        t = i / (blend_frames + 1)
        # frame 越靠近 a，越接近 anchor
        out[frame] = values[frame] * t + anchor * (1.0 - t)

    # blend out
    for i in range(1, blend_frames + 1):
        frame = b + i
        if frame not in out:
            continue

        t = i / (blend_frames + 1)
        out[frame] = anchor * (1.0 - t) + values[frame] * t

    return out


def repair_segment(action, bone_name, a, b, frame_start, frame_end):
    data_path = f'pose.bones["{bone_name}"].location'

    fcx = ensure_fcurve(action, data_path, 0)
    fcy = ensure_fcurve(action, data_path, 1)
    fcz = ensure_fcurve(action, data_path, 2)

    vx = cache_curve_values(fcx, frame_start, frame_end)
    vy = cache_curve_values(fcy, frame_start, frame_end)
    vz = cache_curve_values(fcz, frame_start, frame_end)

    xs = [vx[f] for f in range(a, b + 1)]
    ys = [vy[f] for f in range(a, b + 1)]

    xy_range = local_xy_range(xs, ys)

    if xy_range < MIN_LOCAL_XY_RANGE_TO_REPAIR:
        return {
            "repaired": False,
            "reason": "below_threshold",
            "xy_range": xy_range,
        }

    ax = choose_anchor(vx, a, b, ANCHOR_MODE)
    ay = choose_anchor(vy, a, b, ANCHOR_MODE)
    az = choose_anchor(vz, a, b, ANCHOR_MODE)

    new_vx = vx
    new_vy = vy
    new_vz = vz

    if LOCK_X:
        new_vx = apply_lock_to_channel(vx, a, b, ax, BLEND_FRAMES)

    if LOCK_Y:
        new_vy = apply_lock_to_channel(vy, a, b, ay, BLEND_FRAMES)

    if LOCK_Z:
        new_vz = apply_lock_to_channel(vz, a, b, az, BLEND_FRAMES)

    write_start = max(frame_start, a - BLEND_FRAMES)
    write_end = min(frame_end, b + BLEND_FRAMES)

    for frame in range(write_start, write_end + 1):
        if LOCK_X:
            set_value(fcx, frame, new_vx[frame])
        if LOCK_Y:
            set_value(fcy, frame, new_vy[frame])
        if LOCK_Z:
            set_value(fcz, frame, new_vz[frame])

    return {
        "repaired": True,
        "xy_range": xy_range,
        "anchor": [ax, ay, az],
    }


def main():
    scene = bpy.context.scene
    rig = find_rig(RIG_NAME)
    action = get_action(rig)

    contact = load_json(SOURCE_CONTACT_REPORT)

    frame_start = int(scene.frame_start)
    frame_end = int(scene.frame_end)

    print("====================================")
    print("[Teto foot IK XY lock]")
    print(f"Rig: {rig.name}")
    print(f"Action: {action.name}")
    print(f"Frames: {frame_start}-{frame_end}")
    print(f"Trim: {TRIM_SEGMENT_ENDS}")
    print(f"Blend: {BLEND_FRAMES}")
    print("====================================")

    repaired_count = 0
    skipped_count = 0

    for side in ["L", "R"]:
        bone_name = FOOT_IK[side]

        if bone_name not in rig.pose.bones:
            print(f"[missing] {bone_name}")
            continue

        segments = contact["feet"][side]["planted_segments"]

        for seg in segments:
            if len(seg) != 2:
                continue

            a, b = int(seg[0]), int(seg[1])
            aa = a + TRIM_SEGMENT_ENDS
            bb = b - TRIM_SEGMENT_ENDS

            if bb - aa + 1 < MIN_SEGMENT_LEN:
                skipped_count += 1
                continue

            result = repair_segment(
                action=action,
                bone_name=bone_name,
                a=aa,
                b=bb,
                frame_start=frame_start,
                frame_end=frame_end,
            )

            if result["repaired"]:
                repaired_count += 1
                if PRINT_SEGMENTS:
                    print(
                        f"[fixed] {side} {aa}-{bb} "
                        f"xy_range={result['xy_range']:.5f}"
                    )
            else:
                skipped_count += 1
                if PRINT_SEGMENTS:
                    print(
                        f"[skip] {side} {aa}-{bb} "
                        f"{result['reason']} "
                        f"xy_range={result['xy_range']:.5f}"
                    )

    for fc in action.fcurves:
        fc.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[repaired_count] {repaired_count}")
    print(f"[skipped_count] {skipped_count}")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 六、运行脚锁

从这个文件开始：

```text
F:\mocap_ai_doctor\blends\teto_clean_floor_v1.blend
```

运行：

```text
repair_teto_foot_ik_xy_lock.py
```

输出：

```text
F:\mocap_ai_doctor\blends\teto_clean_floor_v1_footlock_xy.blend
```

---

# 七、效果判断

重点看你说的那一段：

```text
脚不动，躯干扭动
```

预期：

```text
脚掌水平位置明显更稳；
躯干可以继续扭；
脚不会再跟着身体轻微漂；
脚尖方向仍然能变化；
脚不会被强行压到地板。
```

---

# 八、如果结果有问题怎么调

## 1. 锁得不够，脚还是滑

改：

```python
MIN_LOCAL_XY_RANGE_TO_REPAIR = 0.006
```

为：

```python
MIN_LOCAL_XY_RANGE_TO_REPAIR = 0.002
```

或者：

```python
TRIM_SEGMENT_ENDS = 2
```

改成：

```python
TRIM_SEGMENT_ENDS = 1
```

---

## 2. 锁得太死，换步不自然

改：

```python
TRIM_SEGMENT_ENDS = 2
```

为：

```python
TRIM_SEGMENT_ENDS = 4
```

或者：

```python
BLEND_FRAMES = 2
```

为：

```python
BLEND_FRAMES = 4
```

---

## 3. 脚高度开始怪

确认：

```python
LOCK_Z = False
```

不要开 `LOCK_Z`。  
你现在已经用 mesh floor 修过高度，不要再锁 foot_ik 的 Z。

---

## 4. 锁了以后没有变化

那说明 `foot_ik.L/R` 的 visible world motion 不是由它自己的 `location` fcurve 决定，而是上游控制器在动。

这种情况下我们需要导出 `RIG` 的脚部骨骼列表，找真正控制器。  
但从你之前 bmap 看，`foot_ik.L/R` 大概率就是正确控制骨。

---

# 九、当前最终流程更新

目前目标阶段流程变成：

```text
teto_retarget_v1.blend
    ↓
teto_global_correction 扶正
    ↓
foot_ik tilt-only 修复，STRENGTH = 0.65
    ↓
mesh floor lift v3 safe，STRENGTH = 0.55
    ↓
teto_clean_floor_v1.blend
    ↓
foot_ik XY lock planted 段
    ↓
teto_clean_floor_v1_footlock_xy.blend
```

你先跑诊断脚本，看最大 drift；  
如果确实如你肉眼看到的那段有明显 drift，再跑 XY lock。

---
## 🧑‍💻 User

我暂时只执行了分析脚本，planted检测阈值有点太低了，排前三位的吞了我一整个脚略微抬起后位移大概十几厘米的动作，这个时间窗口过长的程度不是掐掉头尾几帧可以解决的，要不干脆改一下参数重新检测

---
## 🤖 Assistant

对，应该**重新检测 planted**，不要用现在这个 report 继续脚锁。

你这个判断很重要：

> planted 检测把“脚略微抬起后位移十几厘米”的动作吞进去了。  
> 这不是 trim 头尾几帧能解决的。

这说明当前 planted 判断太宽松，尤其是：

```python
CONTACT_HEIGHT = 0.045
PLANTED_XY_SPEED = 0.018
MERGE_GAP = 2
```

对于舞蹈动作来说有点大。更关键的是，当前检测只看**相邻帧速度**，如果脚慢慢移动十几厘米，每帧速度可能仍然低，于是会被误判为 planted。

所以 v2 要加一个判断：

> **一个 planted 段内，脚相对该段起点/锚点的累计水平漂移不能太大。**

也就是：

```text
脚在地面附近 + 每帧速度小 + 段内总漂移也小
```

才算真正 planted。

---

# 1. 这次修改目标

我们要解决：

```text
慢速挪脚十几厘米，但每帧速度不大 → 被误判为 planted
```

新增参数：

```python
MAX_PLANTED_ANCHOR_DRIFT = 0.025
```

意思是：

> 如果一个 planted 段内，脚的平均接触中心相对段起点漂移超过 2.5cm，就切断这个 planted 段。

你这个“十几厘米位移”会被直接切掉。

---

# 2. 建议参数

这次先用更严格的参数：

```python
CONTACT_HEIGHT = 0.030
PLANTED_XY_SPEED = 0.012
MOVING_XY_SPEED = 0.012
MAX_VERTICAL_SPEED_FOR_PLANTED = 0.010
MIN_SEGMENT_LEN = 4
MERGE_GAP = 1
MAX_PLANTED_ANCHOR_DRIFT = 0.025
```

如果 planted 太碎，再稍微放宽：

```python
CONTACT_HEIGHT = 0.035
MAX_PLANTED_ANCHOR_DRIFT = 0.035
```

但先别放宽。

---

# 3. 新脚本：`analyze_foot_contacts_v2.py`

保存为：

```text
F:\mocap_ai_doctor\scripts\analyze_foot_contacts_v2.py
```

内容如下。

```python
import bpy
import json
import math
from pathlib import Path


# =========================
# 配置区
# =========================

ARMATURE_NAME = "import_synchronized_videos_rig"

OUTPUT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"

FLOOR_Z = 0.02

ADD_TIMELINE_MARKERS = True

FOOT_POINTS = {
    "L": [
        ("foot.L", "head"),
        ("foot.L", "tail"),
        ("heel.02.L", "head"),
        ("heel.02.L", "tail"),
    ],
    "R": [
        ("foot.R", "head"),
        ("foot.R", "tail"),
        ("heel.02.R", "head"),
        ("heel.02.R", "tail"),
    ],
}

# 更严格的 planted 参数
CONTACT_HEIGHT = 0.030
PLANTED_XY_SPEED = 0.012
MOVING_XY_SPEED = 0.012
MAX_VERTICAL_SPEED_FOR_PLANTED = 0.010

MIN_SEGMENT_LEN = 4
MERGE_GAP = 1

# 新增：一个 planted 段内，相对锚点最大允许漂移
# 超过这个值，就认为脚不是“钉住”的，而是在慢慢挪。
MAX_PLANTED_ANCHOR_DRIFT = 0.025

# 如果一段 planted 太长，也容易误吞动作。超过这个长度会做二次检查。
# 不是直接切，而是配合 anchor drift 切。
MAX_REASONABLE_PLANTED_LEN = 80

PENETRATION_TOLERANCE = 0.008


# =========================
# 工具函数
# =========================

def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_pose_bone_point_world(armature, bone_name, point_type):
    pb = armature.pose.bones.get(bone_name)
    if pb is None:
        return None

    if point_type == "head":
        p = pb.head.copy()
    elif point_type == "tail":
        p = pb.tail.copy()
    else:
        raise ValueError(point_type)

    return armature.matrix_world @ p


def dist_xy_vec(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)


def ranges_from_frames(frames, min_len=1, merge_gap=0):
    if not frames:
        return []

    frames = sorted(set(frames))
    raw = []

    start = prev = frames[0]
    for f in frames[1:]:
        if f == prev + 1:
            prev = f
        else:
            raw.append([start, prev])
            start = prev = f
    raw.append([start, prev])

    merged = []
    for r in raw:
        if not merged:
            merged.append(r)
            continue

        last = merged[-1]
        if r[0] - last[1] <= merge_gap + 1:
            last[1] = r[1]
        else:
            merged.append(r)

    out = []
    for a, b in merged:
        if b - a + 1 >= min_len:
            out.append([a, b])

    return out


def sample_foot_side(armature, side, frame_start, frame_end):
    scene = bpy.context.scene
    points = FOOT_POINTS[side]

    samples = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)

        locs = []
        sources = []

        for bone, point_type in points:
            if bone not in armature.pose.bones:
                continue

            loc = get_pose_bone_point_world(armature, bone, point_type)
            if loc is None:
                continue

            locs.append([float(loc.x), float(loc.y), float(loc.z)])
            sources.append(f"{bone}:{point_type}")

        if not locs:
            samples[frame] = None
            continue

        lowest_i = min(range(len(locs)), key=lambda i: locs[i][2])
        lowest = locs[lowest_i]

        avg_x = sum(p[0] for p in locs) / len(locs)
        avg_y = sum(p[1] for p in locs) / len(locs)
        avg_z = sum(p[2] for p in locs) / len(locs)

        samples[frame] = {
            "lowest_z": lowest[2],
            "lowest_source": sources[lowest_i],
            "avg_center": [avg_x, avg_y, avg_z],
            "point_count": len(locs),
        }

    return samples


def split_planted_by_anchor_drift(planted_frames, per_frame):
    """
    关键新增逻辑：
    初步 planted 后，再按段内相对锚点的水平漂移切段。
    """
    initial_segments = ranges_from_frames(
        planted_frames,
        min_len=1,
        merge_gap=0
    )

    final_frames = []
    rejected_frames = []

    for a, b in initial_segments:
        current_start = None
        anchor_xy = None

        for frame in range(a, b + 1):
            pf = per_frame.get(frame)
            if pf is None:
                if current_start is not None:
                    current_start = None
                    anchor_xy = None
                continue

            xy = pf["avg_xy"]

            if current_start is None:
                current_start = frame
                anchor_xy = xy
                final_frames.append(frame)
                continue

            drift = dist_xy_vec(xy, anchor_xy)

            if drift <= MAX_PLANTED_ANCHOR_DRIFT:
                final_frames.append(frame)
            else:
                # 当前帧已经离锚点太远，认为这是挪脚/过渡，不再算 planted。
                rejected_frames.append(frame)

                # 重新开一个潜在 planted 小段
                # 这样如果脚移动后又重新稳定，会形成新 planted 段。
                current_start = frame
                anchor_xy = xy

    final_segments = ranges_from_frames(
        final_frames,
        min_len=MIN_SEGMENT_LEN,
        merge_gap=MERGE_GAP,
    )

    rejected_segments = ranges_from_frames(
        rejected_frames,
        min_len=1,
        merge_gap=1,
    )

    return final_segments, rejected_segments


def analyze_side(samples, frame_start, frame_end, side):
    initial_planted_frames = []
    moving_near_floor_frames = []
    airborne_frames = []
    penetration_samples = []

    per_frame = {}

    prev_sample = None

    for frame in range(frame_start, frame_end + 1):
        s = samples.get(frame)
        if s is None:
            continue

        lowest_z = s["lowest_z"]
        height_above_floor = lowest_z - FLOOR_Z

        xy_speed = 0.0
        vertical_speed = 0.0

        if prev_sample is not None:
            xy_speed = dist_xy_vec(s["avg_center"], prev_sample["avg_center"])
            vertical_speed = abs(s["avg_center"][2] - prev_sample["avg_center"][2])

        near_floor = height_above_floor <= CONTACT_HEIGHT

        # 初步状态
        if near_floor and xy_speed <= PLANTED_XY_SPEED and vertical_speed <= MAX_VERTICAL_SPEED_FOR_PLANTED:
            state = "planted_candidate"
            initial_planted_frames.append(frame)
        elif near_floor and xy_speed > MOVING_XY_SPEED:
            state = "near_floor_moving"
            moving_near_floor_frames.append(frame)
        else:
            state = "airborne_or_lifted"
            airborne_frames.append(frame)

        if lowest_z < FLOOR_Z - PENETRATION_TOLERANCE:
            penetration_samples.append({
                "frame": frame,
                "lowest_z": round(lowest_z, 5),
                "depth": round(FLOOR_Z - lowest_z, 5),
                "source": s["lowest_source"],
            })

        per_frame[frame] = {
            "state_initial": state,
            "height_above_floor": round(height_above_floor, 5),
            "xy_speed": round(xy_speed, 5),
            "vertical_speed": round(vertical_speed, 5),
            "lowest_source": s["lowest_source"],
            "avg_xy": [s["avg_center"][0], s["avg_center"][1]],
        }

        prev_sample = s

    # 二次切分：防止慢速挪脚被吞进 planted
    planted_segments, drift_rejected_segments = split_planted_by_anchor_drift(
        initial_planted_frames,
        per_frame,
    )

    # 把二次剔除的帧，也作为 moving/transition 参考
    for a, b in drift_rejected_segments:
        for f in range(a, b + 1):
            moving_near_floor_frames.append(f)
            if f in per_frame:
                per_frame[f]["state_initial"] = "rejected_by_anchor_drift"

    moving_near_floor_segments = ranges_from_frames(
        moving_near_floor_frames,
        min_len=MIN_SEGMENT_LEN,
        merge_gap=MERGE_GAP,
    )

    airborne_segments = ranges_from_frames(
        airborne_frames,
        min_len=MIN_SEGMENT_LEN,
        merge_gap=MERGE_GAP,
    )

    # 给最终 planted 帧标注 final state
    planted_frame_set = set()
    for a, b in planted_segments:
        for f in range(a, b + 1):
            planted_frame_set.add(f)

    for frame, pf in per_frame.items():
        if frame in planted_frame_set:
            pf["state"] = "planted"
        elif pf["state_initial"] == "rejected_by_anchor_drift":
            pf["state"] = "near_floor_moving_or_reposition"
        elif pf["state_initial"] == "near_floor_moving":
            pf["state"] = "near_floor_moving"
        else:
            pf["state"] = "airborne_or_lifted"

    return {
        "side": side,
        "planted_segments": planted_segments,
        "near_floor_moving_segments": moving_near_floor_segments,
        "airborne_or_lifted_segments": airborne_segments,
        "drift_rejected_segments": drift_rejected_segments,
        "penetration_samples": penetration_samples[:100],
        "penetration_sample_count": len(penetration_samples),
        "per_frame": per_frame,
    }


def clear_contact_markers(scene):
    prefixes = [
        "CONTACT_",
        "LS", "LE", "RS", "RE",
        "LM", "RM",
        "LA", "RA",
        "LD", "RD",
    ]

    old = []
    for m in scene.timeline_markers:
        if any(m.name.startswith(p) for p in prefixes):
            old.append(m)

    for m in old:
        scene.timeline_markers.remove(m)


def add_marker(scene, name, frame):
    scene.timeline_markers.new(name, frame=int(frame))


def add_short_markers(report):
    scene = bpy.context.scene
    clear_contact_markers(scene)

    feet = report["feet"]

    for side in ["L", "R"]:
        prefix_s = "LS" if side == "L" else "RS"
        prefix_e = "LE" if side == "L" else "RE"
        prefix_m = "LM" if side == "L" else "RM"
        prefix_d = "LD" if side == "L" else "RD"

        for i, (a, b) in enumerate(feet[side]["planted_segments"]):
            add_marker(scene, f"{prefix_s}{i:02d}", a)
            add_marker(scene, f"{prefix_e}{i:02d}", b)

        # near moving 只标起点，避免太挤
        for i, (a, b) in enumerate(feet[side]["near_floor_moving_segments"]):
            add_marker(scene, f"{prefix_m}{i:02d}", a)

        # drift rejected 也只标起点，用 D 表示“被漂移剔除”
        for i, (a, b) in enumerate(feet[side]["drift_rejected_segments"]):
            add_marker(scene, f"{prefix_d}{i:02d}", a)


def main():
    scene = bpy.context.scene
    armature = find_armature(ARMATURE_NAME)

    frame_start = int(scene.frame_start)
    frame_end = int(scene.frame_end)

    print("======================================")
    print("[analyze foot contacts v2]")
    print(f"Armature: {armature.name}")
    print(f"Frames:   {frame_start}-{frame_end}")
    print(f"Floor Z:  {FLOOR_Z}")
    print("======================================")

    feet_report = {}

    for side in ["L", "R"]:
        samples = sample_foot_side(armature, side, frame_start, frame_end)
        feet_report[side] = analyze_side(samples, frame_start, frame_end, side)

        print(f"[{side}] planted: {len(feet_report[side]['planted_segments'])}")
        print(f"[{side}] moving:  {len(feet_report[side]['near_floor_moving_segments'])}")
        print(f"[{side}] drift rejected: {len(feet_report[side]['drift_rejected_segments'])}")
        print(f"[{side}] penetration: {feet_report[side]['penetration_sample_count']}")

    report = {
        "schema_version": "foot_contact_report_v2",
        "scene": {
            "name": scene.name,
            "fps": scene.render.fps,
            "frame_start": frame_start,
            "frame_end": frame_end,
        },
        "armature": armature.name,
        "floor_z": FLOOR_Z,
        "params": {
            "contact_height": CONTACT_HEIGHT,
            "planted_xy_speed": PLANTED_XY_SPEED,
            "moving_xy_speed": MOVING_XY_SPEED,
            "max_vertical_speed_for_planted": MAX_VERTICAL_SPEED_FOR_PLANTED,
            "min_segment_len": MIN_SEGMENT_LEN,
            "merge_gap": MERGE_GAP,
            "max_planted_anchor_drift": MAX_PLANTED_ANCHOR_DRIFT,
            "max_reasonable_planted_len": MAX_REASONABLE_PLANTED_LEN,
        },
        "feet": feet_report,
        "notes": [
            "v2 adds anchor-drift rejection to avoid slow foot reposition being swallowed as planted.",
            "LS/LE and RS/RE markers are final planted candidates.",
            "LD/RD markers are planted candidates rejected by anchor drift."
        ],
    }

    out = Path(OUTPUT_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if ADD_TIMELINE_MARKERS:
        add_short_markers(report)

    print("--------------------------------------")
    print(f"[saved report] {out}")
    if ADD_TIMELINE_MARKERS:
        print("[markers] short markers added:")
        print("  LS/LE = left planted start/end")
        print("  RS/RE = right planted start/end")
        print("  LM/RM = near-floor moving start")
        print("  LD/RD = rejected by anchor drift")
    print("======================================")


if __name__ == "__main__":
    main()
```

---

# 4. 怎么运行

打开源动作干净版：

```text
F:\mocap_ai_doctor\blends\source_clean_v1.blend
```

在 Blender 的 `Scripting` 里运行：

```text
analyze_foot_contacts_v2.py
```

输出：

```text
F:\mocap_ai_doctor\reports\foot_contacts_source_clean_v2.json
```

时间线 marker 会变成：

```text
LS / LE / RS / RE = 最终 planted
LM / RM = 近地移动
LD / RD = 原本像 planted，但因为段内漂移太大被剔除
```

你重点看那段“脚略微抬起后位移十几厘米”的动作，应该会出现：

```text
LD 或 RD
```

而不是被包在：

```text
LS...LE / RS...RE
```

里面。

---

# 5. 如果 v2 还是吞动作

优先调这个：

```python
MAX_PLANTED_ANCHOR_DRIFT = 0.025
```

改成更严格：

```python
MAX_PLANTED_ANCHOR_DRIFT = 0.015
```

意思是 planted 段内最多允许 1.5cm 漂移。

也可以把：

```python
CONTACT_HEIGHT = 0.030
```

改成：

```python
CONTACT_HEIGHT = 0.025
```

但我建议优先调 `MAX_PLANTED_ANCHOR_DRIFT`，因为你这次的问题本质是“慢速挪脚”，不是纯高度问题。

---

# 6. 如果 v2 太碎

如果脚明明是踩住，但 marker 被切得很碎，调宽一点：

```python
MAX_PLANTED_ANCHOR_DRIFT = 0.035
```

或者：

```python
PLANTED_XY_SPEED = 0.014
```

不要一下回到 0.018。

---

# 7. 后续脚锁脚本要改路径

等 v2 report 看起来合理后，脚锁脚本里这个路径：

```python
SOURCE_CONTACT_REPORT = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v1.json"
```

改成：

```python
SOURCE_CONTACT_REPORT = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

也就是后面全部使用 v2 的 planted 段。

---

# 8. 你现在先做什么

你现在先别跑 foot lock。

先：

1. 运行 `analyze_foot_contacts_v2.py`
2. 看那段“脚略微抬起移动十几厘米”的区间是否被切掉
3. 如果还没切掉，把：

```python
MAX_PLANTED_ANCHOR_DRIFT = 0.015
```

再跑一次

4. 确认 planted marker 基本合理后，再继续脚锁。

---
## 🧑‍💻 User

改好路径了，有一个速度比较慢的脚步移动被算作了planted，踩实的部分又略微提前结束planted了。这次别文件名还改成v3了，我改来改去还要新建文件好累。

---
## 🤖 Assistant

对，这种情况就别继续靠自动阈值硬调了。

你现在遇到的是典型矛盾：

```text
慢速挪脚被误判 planted
    → 需要更严格

踩实段提前结束 planted
    → 需要更宽松
```

这两个靠一组全局参数很难同时解决。继续调只会变成：

```text
修好 A，弄坏 B
修好 B，弄坏 A
```

所以现在更合理的做法是：

> **自动检测给 90% 基础结果，剩下 10% 用手动 override 修 contact report。**

而且你说得对，文件名改来改去很累。后面我们固定：

```text
F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json
```

不再改 v3/v4。  
脚本可以覆盖这个文件，但会自动备份一份 `.bak`。

---

# 现在这样做

你只需要手动填两类区间：

```python
DELETE_PLANTED_RANGES
```

用于删除“误判 planted”的慢速脚步移动。

```python
ADD_PLANTED_RANGES
```

用于补上“踩实但提前结束”的 planted 段。

---

# 新脚本：`edit_contact_report_overrides.py`

保存为：

```text
F:\mocap_ai_doctor\scripts\edit_contact_report_overrides.py
```

以后你只需要反复改这个脚本顶部的区间，不用改文件名。

```python
import json
import shutil
from pathlib import Path


# =========================
# 配置区：以后主要改这里
# =========================

REPORT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"

# 删除误判 planted 的区间
# 例如：左脚 1800-1835 被误判为 planted，就写 ("L", 1800, 1835)
DELETE_PLANTED_RANGES = [
    # ("L", 1800, 1835),
    # ("R", 2100, 2130),
]

# 补回漏掉的 planted 区间
# 例如：左脚 1900-1915 明明踩住，但被提前结束，就写 ("L", 1900, 1915)
ADD_PLANTED_RANGES = [
    # ("L", 1900, 1915),
    # ("R", 2200, 2220),
]

# 区间合并间隙
MERGE_GAP = 1

# 最短 planted 段
MIN_LEN = 3


# =========================
# 工具函数
# =========================

def load_json(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ranges_to_frames(ranges):
    frames = set()
    for a, b in ranges:
        a = int(a)
        b = int(b)
        if b < a:
            a, b = b, a
        for f in range(a, b + 1):
            frames.add(f)
    return frames


def frames_to_ranges(frames, merge_gap=0, min_len=1):
    if not frames:
        return []

    frames = sorted(set(frames))
    raw = []

    start = prev = frames[0]

    for f in frames[1:]:
        if f == prev + 1:
            prev = f
        else:
            raw.append([start, prev])
            start = prev = f

    raw.append([start, prev])

    merged = []

    for r in raw:
        if not merged:
            merged.append(r)
            continue

        last = merged[-1]

        if r[0] - last[1] <= merge_gap + 1:
            last[1] = r[1]
        else:
            merged.append(r)

    out = []

    for a, b in merged:
        if b - a + 1 >= min_len:
            out.append([a, b])

    return out


def split_ops_by_side(ops):
    out = {
        "L": [],
        "R": []
    }

    for item in ops:
        if len(item) != 3:
            raise ValueError(f"Bad override item: {item}")

        side, a, b = item

        if side not in ["L", "R"]:
            raise ValueError(f"Bad side: {side}")

        out[side].append([int(a), int(b)])

    return out


def apply_overrides(report):
    deletes = split_ops_by_side(DELETE_PLANTED_RANGES)
    adds = split_ops_by_side(ADD_PLANTED_RANGES)

    if "manual_overrides" not in report:
        report["manual_overrides"] = []

    for side in ["L", "R"]:
        foot = report["feet"][side]

        old_ranges = foot.get("planted_segments", [])
        planted_frames = ranges_to_frames(old_ranges)

        delete_frames = ranges_to_frames(deletes[side])
        add_frames = ranges_to_frames(adds[side])

        before_count = len(planted_frames)

        planted_frames -= delete_frames
        planted_frames |= add_frames

        new_ranges = frames_to_ranges(
            planted_frames,
            merge_gap=MERGE_GAP,
            min_len=MIN_LEN
        )

        foot["planted_segments_before_manual_override"] = old_ranges
        foot["planted_segments"] = new_ranges

        after_count = len(planted_frames)

        print(f"[{side}] planted frame count: {before_count} -> {after_count}")
        print(f"[{side}] ranges: {len(old_ranges)} -> {len(new_ranges)}")

    report["manual_overrides"].append({
        "delete_planted_ranges": DELETE_PLANTED_RANGES,
        "add_planted_ranges": ADD_PLANTED_RANGES,
        "merge_gap": MERGE_GAP,
        "min_len": MIN_LEN
    })

    report["notes"].append(
        "Manual planted overrides applied by edit_contact_report_overrides.py"
    )

    return report


def main():
    path = Path(REPORT_JSON)

    if not path.exists():
        raise RuntimeError(f"Report not found: {path}")

    backup = path.with_suffix(path.suffix + ".bak")

    shutil.copy2(path, backup)
    print(f"[backup] {backup}")

    report = load_json(path)
    report = apply_overrides(report)
    save_json(path, report)

    print(f"[saved overwritten] {path}")
    print("Done.")


if __name__ == "__main__":
    main()
```

---

# 怎么用

比如你发现：

```text
左脚 2010-2045 是慢速移动，不该 planted
右脚 2300-2312 明明踩实，但漏了
```

就改成：

```python
DELETE_PLANTED_RANGES = [
    ("L", 2010, 2045),
]

ADD_PLANTED_RANGES = [
    ("R", 2300, 2312),
]
```

然后在 Blender 里或者命令行里运行这个脚本都行。它不依赖 Blender API，普通 Python 也能跑。

WSL 里可以直接：

```bash
python3 /mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py
```

它会：

1. 备份：

```text
foot_contacts_source_clean_v2.json.bak
```

2. 覆盖更新：

```text
foot_contacts_source_clean_v2.json
```

后面脚锁脚本继续读取这个同名文件就行，不用改路径。

---

# 重新生成短 marker

因为你手动改了 report，时间线 marker 也要刷新。

你之前的 marker 脚本如果路径还是 v1，改成：

```python
REPORT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

然后重新运行 marker 脚本。

如果你懒得跑 marker 也没事，脚锁脚本读的是 JSON，不读 marker。

---

# 接下来建议

现在别再调自动检测参数了。你已经确认：

```text
踩点基本对
只是少数区间范围不对
```

所以最快路线是：

1. 用 `DELETE_PLANTED_RANGES` 删掉那个慢速脚步移动。
2. 用 `ADD_PLANTED_RANGES` 补上提前结束的踩实部分。
3. 继续跑 foot IK XY lock。

这比再调 v3/v4 检测器更省时间，也更可控。

---
## 🧑‍💻 User

跑了你的脚锁，效果很不错，但是我发现我漏了一段应该add的区间，我就改了edit_contact_report_overrides.py，再运行报这个Traceback (most recent call last):
  File "/mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py", line 193, in <module>
    main()
  File "/mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py", line 177, in main
    raise RuntimeError(f"Report not found: {path}")
RuntimeError: Report not found: F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json
我看了，这个cfg明明白白的就在那，文件名也对。vsc打开了这个文件，我特意关了vsc，还是这样

---
## 🤖 Assistant

这是 **WSL 路径问题**，不是文件不存在，也不是 VSCode 占用。

你现在是这样运行的：

```bash
python3 /mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py
```

这说明脚本是在 **WSL/Linux 的 Python** 里运行。

但脚本里写的是 Windows 路径：

```python
REPORT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

在 WSL 里，`F:/xxx` 不会自动等价于 Windows 的 F 盘。  
WSL 里 F 盘路径应该是：

```text
/mnt/f/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json
```

所以 Python 报：

```text
Report not found: F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json
```

是正常的。

---

# 立刻修复方法

打开：

```bash
nano /mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py
```

把：

```python
REPORT_JSON = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

改成：

```python
REPORT_JSON = "/mnt/f/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

然后再跑：

```bash
python3 /mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py
```

就行。

---

# 为什么之前其他脚本可以用 `F:/...`

因为之前很多脚本是在 **Windows Blender** 里面运行的：

```text
D:\blender-3.2.1-windows-x64\blender.exe
```

虽然你从 WSL 启动它，但真正执行 Python 的是 **Windows 版 Blender 的 Python**。

所以在 Blender 脚本里：

```python
F:/mocap_ai_doctor/...
```

是能识别的。

但这次你运行的是：

```bash
python3 ...
```

这是 WSL 自己的 Linux Python，所以只能识别：

```python
/mnt/f/mocap_ai_doctor/...
```

---

# 以后记住这个规则

## 在 Windows Blender 里跑脚本

用：

```python
F:/mocap_ai_doctor/...
```

## 在 WSL 的 python3 里跑脚本

用：

```python
/mnt/f/mocap_ai_doctor/...
```

---

# 更稳的改法：让脚本自动兼容 WSL 和 Windows

如果你想以后少踩坑，可以把脚本开头的路径部分改成这样：

```python
from pathlib import Path
import platform

def smart_path(win_path):
    """
    支持：
    - Windows Blender Python: F:/xxx
    - WSL Python: /mnt/f/xxx
    """
    p = str(win_path)

    if platform.system().lower() == "linux":
        if len(p) >= 3 and p[1:3] == ":/":
            drive = p[0].lower()
            rest = p[3:]
            return Path(f"/mnt/{drive}/{rest}")

    return Path(p)


REPORT_JSON = smart_path("F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json")
```

但是你现在最简单就是直接改成：

```python
REPORT_JSON = "/mnt/f/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

---

# 注意备份问题

你现在的脚本会生成：

```text
foot_contacts_source_clean_v2.json.bak
```

如果你多次运行，它会覆盖 `.bak`。

这没问题，但如果你想更安全，后面可以改成带时间戳备份。现在先不用。

---

# 你接下来做

1. 把路径改成：

```python
REPORT_JSON = "/mnt/f/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

2. 运行：

```bash
python3 /mnt/f/mocap_ai_doctor/scripts/edit_contact_report_overrides.py
```

3. 再重新跑脚锁脚本。

注意脚锁脚本如果是在 **Blender 里跑**，它里面的路径仍然应该保持：

```python
SOURCE_CONTACT_REPORT = "F:/mocap_ai_doctor/reports/foot_contacts_source_clean_v2.json"
```

不要把 Blender 脚本里的路径也改成 `/mnt/f/...`。

---
## 🧑‍💻 User

效果非常好。在细化之前，现在我要导出成vmd给别人用mmd软件本体看看，我们现在数据都在mmr控制器上面，告诉我怎么正确导出

---
## 🤖 Assistant

对，现在要导出给 MMD 本体测试，关键点是：

> **不要直接把 MMR / Rigify 控制器当 VMD 导出。**  
> **要先把 MMR 控制器上的最终视觉动作烘焙回“原生 MMD 骨骼”，再从原生 MMD 骨骼导出 VMD。**

你现在项目里大概是：

```text
RIG-arue式重音テトver 2.01_arm
    ↑ 这是 MMR / Rigify 控制器，动作主要在这里

arue式重音テトver 2.01_arm
    ↑ 这是原始 MMD armature / PMX 骨骼
```

VMD 要给 MMD 本体用，所以最终必须导出：

```text
arue式重音テトver 2.01_arm
```

而不是：

```text
RIG-arue式重音テトver 2.01_arm
```

MMR 本身就是“给骨架生成 Rigify 控制器”的插件，并且有导入/导出动画相关功能，这和我们现在的结构是吻合的 [3]。网上也确实有专门讲 MMR 控制器动作导出、Rigify 导入/导出 VMD 的教程内容 [2]。

---

# 0. 先复制一个导出专用工程

不要在当前修复工程上直接操作。

把现在效果好的文件另存为：

```text
F:\mocap_ai_doctor\blends\teto_export_vmd_test.blend
```

后面所有烘焙、清约束、删控制器都在这个副本里做。

---

# 1. 确认时间范围

你的动作范围现在是：

```text
Start = 1525
End   = 2836
```

如果你想给别人一个从第 0 帧或第 1 帧开始的 VMD，最好先说清楚：

- 临时测试可以保持 `1525-2836`；
- 正式分发建议整体平移到 `0` 或 `1` 帧；
- 但现在先别做复杂处理，先导出测试。

---

# 2. 重要：MMD 帧率问题

你 Blender 里之前显示：

```text
fps = 24
```

MMD / VMD 通常按 **30fps 的帧数逻辑**播放。VMD 本身不真正保存“24fps/30fps”这个概念，它主要保存关键帧编号。

所以如果你直接把 24fps 的 1312 帧动作导出给 MMD，MMD 里可能会**播放得偏快**。

现在先测试动作姿态、脚、手、IK 没问题的话，可以先不管。  
但正式导出前，可能需要把帧时间缩放：

```text
30 / 24 = 1.25
```

也就是：

```text
Blender 第 1525 帧到 2836 帧
导到 MMD 时应该拉长 1.25 倍
```

这件事我们可以后面专门处理。现在先导一个“姿态测试版”。

---

# 3. 导出前的正确总体流程

完整逻辑是：

```text
MMR/Rigify 控制器动作
    ↓ 视觉烘焙
原生 MMD 骨骼 action
    ↓ mmd_tools / MMR 导出
VMD
    ↓
MMD 本体加载测试
```

---

# 4. 在副本里烘焙到原生 MMD 骨骼

打开：

```text
F:\mocap_ai_doctor\blends\teto_export_vmd_test.blend
```

## 4.1 选中原生 MMD armature

在 Outliner 里选这个：

```text
arue式重音テトver 2.01_arm
```

不要选：

```text
RIG-arue式重音テトver 2.01_arm
```

也不要选模型根：

```text
arue式重音テトver 2.01
```

要选原始 MMD 骨架对象。

---

## 4.2 进入 Pose Mode

选中 `arue式重音テトver 2.01_arm` 后：

```text
Object Mode → Pose Mode
```

然后：

```text
A 全选所有骨骼
```

如果骨骼很多、隐藏很多，最好在骨骼层里确保 MMD 主要骨骼、IK 骨骼都能被选中。  
如果不确定，就用：

```text
Pose Mode → A 全选
```

---

## 4.3 Bake Action 参数

菜单大概是：

```text
Pose / Object → Animation → Bake Action
```

不同 Blender 版本位置可能略有区别。

参数建议：

```text
Start Frame: 1525
End Frame:   2836
Frame Step:  1

Only Selected Bones: 关闭 或者如果你确认全选了所有骨骼也可以开启
Visual Keying:       开启
Clear Constraints:   开启
Clear Parents:       关闭
Overwrite Current Action: 开启
Bake Data:           Pose
```

这里重点是：

```text
Visual Keying = 开启
```

因为我们要把 MMR 控制器、约束、teto_global_correction、IK 造成的最终视觉结果烘到原生 MMD 骨骼上。

```text
Clear Constraints = 开启
```

是因为这是导出副本。烘焙完以后就不需要 MMR 控制器继续驱动原生 MMD 骨骼了，清掉约束可以避免双重影响。

如果你担心清坏，没关系，因为我们是在：

```text
teto_export_vmd_test.blend
```

副本里操作。

---

# 5. 烘焙后做一个关键检查

烘焙完成后，先不要导出。检查一下：

## 5.1 隐藏 MMR 控制器

在 Outliner 里把这个隐藏：

```text
RIG-arue式重音テトver 2.01_arm
```

只看原生模型和原生 MMD armature。

播放时间线，看动作是否还在。

如果动作仍然正常，说明：

```text
MMR 控制器动作已经成功烘到原生 MMD 骨骼上
```

如果隐藏 RIG 后动作没了，说明你烘焙对象选错了，或者没有烘到原生 MMD 骨骼。

---

## 5.2 检查 global correction 有没有被吃进去

你之前用了：

```python
ROT_X_DEG = -4.2
ROT_Y_DEG = 3.7
```

如果烘焙后隐藏控制器，模型仍然是扶正状态，说明全局校正大概率也被视觉烘焙进去了。

如果烘焙后模型又歪回去了，说明 Empty correction 没被烘进原生骨架。  
这种情况先别继续导出，告诉我，我们再单独处理“把 global correction 烘到 MMD bones / 全ての親”。

---

# 6. 用 mmd_tools 导出 VMD

如果你装了 `mmd_tools`，通常流程是：

1. 选中 MMD 模型根或原生 MMD armature：

```text
arue式重音テトver 2.01
```

或：

```text
arue式重音テトver 2.01_arm
```

不同版本 mmd_tools 要求略有区别。如果选模型根导不出，就选 armature。

2. 菜单：

```text
File → Export → MikuMikuDance Motion (.vmd)
```

3. 导出文件名：

```text
F:\mocap_ai_doctor\exports\teto_mocap_test.vmd
```

如果没有 `exports` 文件夹，先建一个。

4. 导出设置里，尽量选择：

```text
Export Bone Animation: 开启
Export Morph Animation: 关闭/随意
Export Camera Animation: 关闭
Frame Range: 1525 - 2836
```

如果有类似：

```text
Scale
Bone Animation
Morph Animation
Camera Animation
```

保持默认即可，重点是导出骨骼动作。

---

# 7. 如果 MMR 自带“导出动作 / 导出 VMD”按钮

如果 MMR 面板里有类似：

```text
导出动作
Export Motion
Export VMD
控制器动作导出
```

也可以用它。MMR 的定位就是给骨架生成 Rigify 控制器、处理动画导入导出，这类教程里也明确有“控制器动作导出 / Rigify 导出 VMD”内容 [2][3]。

但我建议你第一次还是按上面方式：

```text
先烘到原生 MMD 骨骼
再用 mmd_tools 导出 VMD
```

因为这个流程最透明，出问题容易排查。

---

# 8. 在 MMD 本体里测试

给别人测试时，需要至少给：

```text
PMX 模型
VMD 动作
```

如果对方已经有同一个 Teto 模型，只发 VMD 也可以。

MMD 本体测试：

1. 打开 MMD。
2. 加载：

```text
arue式重音テトver 2.01.pmx
```

3. 加载：

```text
teto_mocap_test.vmd
```

4. 检查：

```text
动作是否加载
脚 IK 是否正常
脚是否严重滑
模型是否仍然歪
播放速度是否偏快
```

---

# 9. 测试时重点看这几个问题

## A. MMD 里模型又歪了

说明：

```text
teto_global_correction 没有被烘进 VMD
```

解决方式：需要把 correction 转进 MMD 的“全ての親 / センター / root”一类骨骼，或者在导出前专门视觉烘焙到原生骨架。

---

## B. MMD 里播放速度太快

这是 24fps → 30fps 问题。

解决方式：正式版导出前把关键帧按：

```text
1.25 倍
```

拉长。

---

## C. MMD 里脚 IK 没动或脚乱飞

说明：

```text
导出的不是原生 MMD 骨骼动作
```

或者：

```text
IK 骨骼没有被正确 bake/export
```

这种情况我们要检查烘焙后的 `arue式重音テトver 2.01_arm` 上有没有：

```text
足ＩＫ / foot IK / センター
```

相关关键帧。

---

## D. Blender 里正常，MMD 里手脚比例怪

可能是：

```text
导出 VMD 的模型和 MMD 里加载的 PMX 不是同一个版本
```

VMD 对骨骼名非常敏感。模型版本不同，骨骼名或 IK 结构不同，就会错。

---

# 10. 我建议你这次导出用的文件名

测试版：

```text
F:\mocap_ai_doctor\exports\teto_mocap_test_24fps_raw.vmd
```

这个名字明确表示：

```text
还没做 24→30 时间缩放
```

如果 MMD 里姿态没问题，但速度快，我们再做：

```text
teto_mocap_test_30fps_timing.vmd
```

---

# 11. 简短版流程

你照这个做：

```text
1. 另存 teto_export_vmd_test.blend
2. 选 arue式重音テトver 2.01_arm
3. Pose Mode，全选骨骼
4. Bake Action：
   - Start 1525
   - End 2836
   - Step 1
   - Visual Keying 开
   - Clear Constraints 开
   - Clear Parents 关
   - Overwrite Current Action 开
   - Bake Data Pose
5. 隐藏 RIG-arue式重音テトver 2.01_arm
6. 播放检查模型是否还正常
7. File → Export → MikuMikuDance Motion (.vmd)
8. MMD 本体加载 PMX + VMD 测试
```

如果你做到第 5 步，隐藏 RIG 后动作还正常，就基本可以导出测试 VMD 了。
[1] [【Blender】想在blender中自由制作MMD二创？新版MMR插件使用教学_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1S9FPepEkV/)

[2] [初识Rigify: MMR插件 控制器 动作导出_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1bj411R7NQ/)

[3] [GitHub - LaoBro/Miku_Miku_Rig: MikuMikuRig是一款集生成控制器，自动导入动画，自动布料为一体的blender插件](https://github.com/LaoBro/Miku_Miku_Rig)

[4] [MMD桥能直接导出VMD给blender用了？！改变传统blender制作流程！_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1EYHNzQEBe/)

[5] [【Blender自制插件】傻瓜式MMD K帧插件 MikuMikuRig (简称MMR）_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1vZ4y1P71a/)
---
## 🧑‍💻 User

我直接把rig删掉，动作看起来都正常。但是，我导出vmd后再导回来，首先是确实人又歪了，然后膝盖每次弯曲的时候，人躯干不动，腿特别夸张地弯曲而离地，转身的时候脚踝会在Z方向剧烈弯曲，人上下浮动。我让朋友用mmd软件本体打开，也是一样的现象，而且他说“足ik的on和off我都试过了”。至少最后一点是肯定会出问题的：我在这边播放这个删掉了rig但是仍然正常的视频的时候，mmd模型最父级的那个空物体一直在上下移动补偿，这个肯定不会被导入进vmd。

---
## 🤖 Assistant

你判断完全正确：**现在 VMD 坏掉的核心原因就是外层 Empty / 全局校正 / floor lift 没进 VMD**。

你在 Blender 里删掉 `RIG-...` 后仍然正常，是因为：

```text
原生 MMD 骨骼 + 外层 teto_global_correction Empty
```

还在一起工作。

但 VMD 只能保存 MMD 骨骼/表情/相机等动作，**不会保存 Blender 外层 Empty 的动画**。mmd_tools 文档也明确提到，VMD 导出主要依赖当前对象的 F-Curve，driver / NLA 不会被导出；如果要导最终动画，需要 bake 到新的 action/fcurves [1][4]。另外 mmd_tools / MMD 工作流本身也不推荐靠 object 坐标移动模型，而应该用 `センター`、`全ての親` 这类 MMD 骨骼移动模型 [2]。

所以现在要做的不是继续修脚，而是：

> **把 `teto_global_correction` 的旋转和上下移动，烘焙到原生 MMD 骨骼里的 `全ての親` 或等效根骨。**

---

# 1. 当前问题总结

你现在 VMD 导出后出现：

```text
人又歪了
膝盖弯曲时躯干不动，腿夸张弯曲离地
转身脚踝 Z 方向剧烈弯曲
人上下浮动
```

这些都符合一个特征：

```text
Blender 里外层 Empty 的全局补偿没有被 VMD 导出
```

尤其你说：

> mmd 模型最父级的那个空物体一直在上下移动补偿，这个肯定不会被导入进 vmd。

对，就是这个。

---

# 2. 正确导出思路

现在要把导出流程改成：

```text
当前 Blender 正常动作
    ↓
把 teto_global_correction 的变换转移到 MMD 的 全ての親 骨骼
    ↓
把 teto_global_correction 清零
    ↓
确认 Blender 里仍然正常
    ↓
从原生 MMD 模型导出 VMD
    ↓
再导回 Blender / MMD 本体测试
```

注意关键词：

```text
先转移到 MMD 骨骼，再清零 Empty。
```

如果清零后 Blender 里仍然正常，那么导出的 VMD 才有希望在 MMD 本体里正常。

---

# 3. 先别用之前导出的 VMD

先丢弃：

```text
已经导出的坏 VMD
已经导回来的坏动作
```

回到你导出前那个正常文件，最好是：

```text
F:\mocap_ai_doctor\blends\teto_clean_floor_v1_footlock_xy.blend
```

或者你现在效果最好的那个 Blender 文件。

另存为导出专用副本：

```text
F:\mocap_ai_doctor\blends\teto_vmd_export_fix_v1.blend
```

后面都在这个副本里操作。

---

# 4. 先确认原生 MMD 骨骼里有没有“全ての親”

我们先用脚本找一下根骨名。

保存为：

```text
F:\mocap_ai_doctor\scripts\find_mmd_root_bones.py
```

内容：

```python
import bpy
import json
from pathlib import Path


ARMATURE_NAME = "arue式重音テトver 2.01_arm"
OUTPUT_JSON = "F:/mocap_ai_doctor/reports/mmd_root_bone_candidates.json"

KEYWORDS = [
    "全て",
    "全ての親",
    "全親",
    "親",
    "root",
    "Root",
    "センター",
    "center",
    "Center",
    "グルーブ",
    "groove",
    "Groove",
]


def main():
    arm = bpy.data.objects.get(ARMATURE_NAME)
    if not arm or arm.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {ARMATURE_NAME}")

    candidates = []

    for pb in arm.pose.bones:
        hit = any(k in pb.name for k in KEYWORDS)

        # mmd_tools 有时把 MMD 名存在自定义属性或 bone data 里
        props = {}
        for k in pb.keys():
            try:
                props[k] = str(pb[k])
            except Exception:
                pass

        if hit or props:
            candidates.append({
                "name": pb.name,
                "parent": pb.parent.name if pb.parent else None,
                "children": [c.name for c in pb.children],
                "rotation_mode": pb.rotation_mode,
                "custom_props": props,
            })

    out = Path(OUTPUT_JSON)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump({
            "armature": arm.name,
            "candidates": candidates,
        }, f, ensure_ascii=False, indent=2)

    print(f"[saved] {out}")

    print("Candidates:")
    for c in candidates:
        print(c["name"])


if __name__ == "__main__":
    main()
```

在 Blender GUI 里打开：

```text
teto_vmd_export_fix_v1.blend
```

运行这个脚本。

然后看控制台或打开：

```text
F:\mocap_ai_doctor\reports\mmd_root_bone_candidates.json
```

我们希望看到类似：

```text
全ての親
センター
グルーブ
```

如果有 `全ての親`，后面就用它。  
如果没有，把 candidates 内容贴我。

---

# 5. 把 `teto_global_correction` 烘到 `全ての親`

下面这个脚本做的事：

1. 读取 `teto_global_correction` 每一帧的：
   - location
   - rotation
2. 写入原生 MMD armature 的：
   - `全ての親` 骨骼 location
   - `全ての親` 骨骼 rotation
3. 然后把 `teto_global_correction` 清零
4. 保存新文件

这一步之后，**Blender 里播放仍应保持和之前差不多**。如果清零后动作又歪/上下错，那就不能导出，要回来调整。

---

## 脚本：`bake_global_correction_to_all_parent.py`

保存为：

```text
F:\mocap_ai_doctor\scripts\bake_global_correction_to_all_parent.py
```

内容：

```python
import bpy
from pathlib import Path
from mathutils import Euler


# =========================
# 配置区
# =========================

ARMATURE_NAME = "arue式重音テトver 2.01_arm"

CORRECTION_EMPTY_NAME = "teto_global_correction"

# 如果你的骨骼名不是这个，改这里
ALL_PARENT_BONE = "全ての親"

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_vmd_export_fix_v1_allparent_baked.blend"

# 是否清零 correction empty
# 第一次建议 True，因为我们就是要验证全局补偿是否已经进骨骼了
RESET_CORRECTION_EMPTY_AFTER_BAKE = True

# 是否每帧插 key
KEY_EVERY_FRAME = True

# 是否设置线性插值
SET_LINEAR = True


# =========================
# 工具函数
# =========================

def find_object(name, expected_type=None):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object not found: {name}")

    if expected_type and obj.type != expected_type:
        raise RuntimeError(f"{name} is not {expected_type}, got {obj.type}")

    return obj


def set_pose_bone_rotation(pb, euler):
    """
    按当前 rotation_mode 写回旋转。
    为了 VMD 导出稳定，建议 root 骨用 XYZ Euler。
    """
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = euler


def insert_root_keys(pb, frame):
    pb.keyframe_insert(data_path="location", frame=frame)
    pb.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_linear_for_bone(action, bone_name):
    if action is None:
        return

    paths = [
        f'pose.bones["{bone_name}"].location',
        f'pose.bones["{bone_name}"].rotation_euler',
        f'pose.bones["{bone_name}"].rotation_quaternion',
    ]

    for fc in action.fcurves:
        if fc.data_path in paths:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.update()


def clear_object_transform_animation(obj):
    """
    清掉 correction empty 自己的 location/rotation/scale 动画。
    """
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        for fc in list(action.fcurves):
            if fc.data_path in ["location", "rotation_euler", "rotation_quaternion", "scale"]:
                action.fcurves.remove(fc)

    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)


def main():
    scene = bpy.context.scene

    arm = find_object(ARMATURE_NAME, "ARMATURE")
    correction = find_object(CORRECTION_EMPTY_NAME)

    pb = arm.pose.bones.get(ALL_PARENT_BONE)
    if pb is None:
        names = [b.name for b in arm.pose.bones]
        raise RuntimeError(
            f"Bone not found: {ALL_PARENT_BONE}\n"
            f"Available root-ish names may need inspection. Total bones={len(names)}"
        )

    arm.animation_data_create()
    if arm.animation_data.action is None:
        arm.animation_data.action = bpy.data.actions.new(name="vmd_export_allparent_baked")

    action = arm.animation_data.action

    frame_start = int(scene.frame_start)
    frame_end = int(scene.frame_end)

    print("======================================")
    print("[Bake global correction to all-parent]")
    print(f"Armature:   {arm.name}")
    print(f"Correction: {correction.name}")
    print(f"Bone:       {pb.name}")
    print(f"Frames:     {frame_start}-{frame_end}")
    print("======================================")

    # 先缓存 correction 的世界变换
    correction_locs = {}
    correction_rots = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        # 用世界变换，因为 correction empty 是外层全局校正
        mw = correction.matrix_world.copy()
        loc, rot, scale = mw.decompose()

        correction_locs[frame] = loc.copy()
        correction_rots[frame] = rot.to_euler("XYZ")

    # 写到 全ての親
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        pb.location = correction_locs[frame]
        set_pose_bone_rotation(pb, correction_rots[frame])

        if KEY_EVERY_FRAME:
            insert_root_keys(pb, frame)

    if SET_LINEAR:
        set_linear_for_bone(action, ALL_PARENT_BONE)

    # 清零 correction empty
    if RESET_CORRECTION_EMPTY_AFTER_BAKE:
        clear_object_transform_animation(correction)

    # 更新
    scene.frame_set(frame_start)
    bpy.context.view_layer.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("--------------------------------------")
    print(f"[saved] {out}")
    print("Now hide/delete rig and test playback.")
    print("If playback still looks correct, export VMD from this file.")
    print("======================================")


if __name__ == "__main__":
    main()
```

---

# 6. 运行后检查

打开：

```text
F:\mocap_ai_doctor\blends\teto_vmd_export_fix_v1_allparent_baked.blend
```

然后检查：

## 6.1 隐藏或删除 MMR rig

隐藏/删除：

```text
RIG-arue式重音テトver 2.01_arm
```

你之前已经确认删 rig 后动作正常，这次也要确认。

## 6.2 确认 `teto_global_correction` 已经不动

选中：

```text
teto_global_correction
```

看 Transform：

```text
Location ≈ 0,0,0
Rotation ≈ 0,0,0
Scale ≈ 1,1,1
```

并播放时间线，确认它不再上下跳。

## 6.3 播放动作

如果现在播放仍然：

```text
不歪
不飞
脚高度正常
脚锁仍正常
```

说明全局补偿已经进入 `全ての親` 骨骼，可以导出 VMD。

如果现在播放又歪了，说明 `全ての親` 的坐标轴/空间和 Empty 不一致，我们再改矩阵版烘焙脚本。

---

# 7. 重新导出 VMD

导出时注意 mmd_tools 的选择对象。

mmd_tools 文档里写得比较明确：导出模型动画，也就是骨骼和表情时，选 root empty；只导骨骼动画时，选 armature；而且只导出 active object 的动画 [1][4]。

你这次建议：

## 方式 A：选 MMD 模型根 Empty 导出

选：

```text
arue式重音テトver 2.01
```

也就是模型根，不是 `RIG-...`。

然后：

```text
File → Export → MikuMikuDance Motion (.vmd)
```

导出：

```text
F:\mocap_ai_doctor\exports\teto_test_allparent_baked.vmd
```

如果选 root empty 导出失败，再用方式 B。

---

## 方式 B：选原生 MMD armature 导出

选：

```text
arue式重音テトver 2.01_arm
```

导出 VMD。

---

# 8. 导出后立刻做回导测试

不要直接发朋友。

在 Blender 里新建一个干净场景，或者重新打开原始 Teto 模型，导入这个 VMD。

重点检查：

```text
1. 人还歪不歪
2. 膝盖弯曲时躯干是否跟着上下补偿
3. 转身脚踝 Z 方向是否还剧烈弯
4. 人是否还上下浮动
```

如果回导正常，再发给朋友 MMD 本体测试。

---

# 9. 如果仍然膝盖/脚踝爆炸，下一步查 IK 双重问题

如果全局补偿烘进去以后：

```text
人不歪了
上下补偿也有了
但脚踝/膝盖仍然在 MMD 里爆炸
```

那下一类问题才是：

```text
MMD IK 和导出的腿 FK / 足 IK keyframe 冲突
```

也就是 VMD 里可能同时有：

```text
足IK key
足首/ひざ/足 FK key
```

MMD 本体又重新 IK 解算，导致脚踝 Z 方向被二次扭。

但现在不要先处理这个。  
你目前最确定的 bug 是：

```text
外层 Empty 动画没有进入 VMD
```

先修这个。

---

# 10. 你现在按这个顺序来

1. 回到正常导出前文件，另存：

```text
teto_vmd_export_fix_v1.blend
```

2. 跑 `find_mmd_root_bones.py`，确认是否有：

```text
全ての親
```

3. 如果有，跑：

```text
bake_global_correction_to_all_parent.py
```

4. 打开输出：

```text
teto_vmd_export_fix_v1_allparent_baked.blend
```

5. 确认：

```text
teto_global_correction 不动
删/隐藏 RIG 后动作仍正常
```

6. 从原生 MMD 模型导出 VMD。
7. 回导测试。

这一步如果成功，你看到的“人又歪、腿弯离地、上下浮动”应该会明显改善。
[1] [MMD Tools/マニュアル for v1](https://mmd-blender.fandom.com/ja/wiki/MMD_Tools/%E3%83%9E%E3%83%8B%E3%83%A5%E3%82%A2%E3%83%AB_for_v1)

[2] [blender_mmd_tools/README_en.md at master · sugiany/blender_mmd_tools](https://github.com/sugiany/blender_mmd_tools/blob/master/README_en.md)

[3] [blenderでMMDモデル作るとき用の備忘録（1.ボーン生成編）](https://note.com/izu_cg/n/n46d003953b0b)

[4] [mmd_toolsの使い方｜blender](https://usausakokoko.hatenablog.com/entry/2018/07/21/212242)
---
## 🧑‍💻 User

我自己搞定了，选中左足 (左大腿)、左ひざ (左膝盖)、左足首 (左脚踝)
右足 (右大腿)、右ひざ (右膝盖)、右足首 (右脚踝)
删除他们的关键帧就行了，导出以后效果和teto_clean_floor_v1_footlock_xy一样是最完美状态。不过，你的这个bake_global_correction_to_all_parent.py依然很有用。猜想的问题根源：我们烘焙到了ik，但它又把ik烘焙到了fk，两个数据叠加了。不深究这个，现在有个问题：我们的模型一直比地平面略高一点点，朋友说mmd本体里面调这个很麻烦。既然我们在Blender里面按一下g就搞定了，告诉我正确的让vmd文件导入后人的脚踩在地板上。我记得之前我们修脚的时候所用的参考平面大概离地0.2m

---
## 🤖 Assistant

你这个判断基本对：

> 烘焙到了 IK，但同时又把腿 FK 也烘了；导出 VMD 后 MMD 本体同时读到 FK 腿骨和 IK 骨，出现双重解算/叠加。  
> 删除 `左足/左ひざ/左足首/右足/右ひざ/右足首` 的关键帧后，只让 IK 控脚，结果恢复正常。

这个结论非常有价值。以后导出 VMD 前就把它作为固定步骤：

```text
导出前删除腿部 FK 关键帧：
左足
左ひざ
左足首
右足
右ひざ
右足首

保留：
センター / 全ての親
左足IK / 右足IK
必要的上半身/手臂/头/表情等
```

现在说你问的地面高度问题。

---

# 结论

**不要在 Object Mode 里直接 G 移动模型对象。**  
那样 Blender 里看起来对，但 VMD 不会记录这个对象位移。

正确做法是：

> **把整个人的垂直偏移写进 MMD 骨骼关键帧里，优先写到 `全ての親`，没有就写到 `センター`。**

也就是说，在 Blender 里相当于你按 `G Z` 移动整个人，但真正导出时要变成：

```text
全ての親.location.z += offset
```

或：

```text
センター.location.z += offset
```

然后再导出 VMD。

你之前说“参考平面大概离地 0.2m”，我这里提醒一下：我们之前精确用过的是：

```text
FLOOR_Z = 0.0257 m
```

也就是 **2.57 cm**，不是 0.2 m。  
如果你现在肉眼看到的偏高也是“略高一点点”，大概率就是几厘米量级。

---

# 推荐做法：给 VMD 导出前整体下移一个固定量

既然你朋友说 MMD 本体里调麻烦，那就在 Blender 里导出前修好。

假设当前导入 MMD 后脚底整体高了：

```text
0.0257 m
```

那我们就在导出前给 `全ての親` 加：

```text
Z offset = -0.0257
```

如果导出后还是高一点，再调成：

```text
-0.030
```

如果插地了，就改成：

```text
-0.020
```

---

# 脚本：给 `全ての親` 或 `センター` 添加整体高度偏移

保存为：

```text
F:\mocap_ai_doctor\scripts\apply_vmd_floor_z_offset.py
```

内容：

```python
import bpy
from pathlib import Path


# =========================
# 配置区
# =========================

ARMATURE_NAME = "arue式重音テトver 2.01_arm"

# 优先用全ての親。如果没有，再改成 センター。
TARGET_BONE = "全ての親"

# 如果你的模型没有全ての親，就用：
# TARGET_BONE = "センター"

# 整体高度偏移，单位是 Blender 米。
# 负数 = 往下移。
#
# 你之前的参考地面高度是 0.0257m，所以先试 -0.0257。
Z_OFFSET = -0.0257

OUTPUT_BLEND = "F:/mocap_ai_doctor/blends/teto_vmd_export_floor_offset.blend"

# 是否每帧都写关键帧。
# 建议 True，因为你的 全ての親 可能已有上下补偿动画。
KEY_EVERY_FRAME = True

# 只处理当前时间线范围
USE_SCENE_RANGE = True


# =========================
# 工具函数
# =========================

def find_armature(name):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "ARMATURE":
        raise RuntimeError(f"Armature not found: {name}")
    return obj


def get_action(arm):
    arm.animation_data_create()
    if arm.animation_data.action is None:
        arm.animation_data.action = bpy.data.actions.new(name="floor_z_offset")
    return arm.animation_data.action


def get_fcurve(action, data_path, index):
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def ensure_fcurve(action, data_path, index):
    fc = get_fcurve(action, data_path, index)
    if fc is None:
        fc = action.fcurves.new(data_path=data_path, index=index)
    return fc


def get_key(fcurve, frame):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.x - frame) < 0.001:
            return kp
    return None


def set_key_value(fcurve, frame, value):
    kp = get_key(fcurve, frame)
    if kp is None:
        kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    else:
        kp.co.y = value

    kp.interpolation = "LINEAR"


def main():
    scene = bpy.context.scene
    arm = find_armature(ARMATURE_NAME)

    pb = arm.pose.bones.get(TARGET_BONE)
    if pb is None:
        available = [b.name for b in arm.pose.bones]
        raise RuntimeError(
            f"Bone not found: {TARGET_BONE}\n"
            f"Please check bone name. Total bones: {len(available)}"
        )

    action = get_action(arm)

    frame_start = int(scene.frame_start)
    frame_end = int(scene.frame_end)

    data_path = f'pose.bones["{TARGET_BONE}"].location'

    # Z 通道
    z_curve = ensure_fcurve(action, data_path, 2)

    # 先缓存原始值，避免边写边读造成累积
    original_z = {}

    for frame in range(frame_start, frame_end + 1):
        original_z[frame] = z_curve.evaluate(frame)

    print("====================================")
    print("[apply VMD floor Z offset]")
    print(f"Armature: {arm.name}")
    print(f"Bone:     {TARGET_BONE}")
    print(f"Frames:   {frame_start}-{frame_end}")
    print(f"Z offset: {Z_OFFSET}")
    print("====================================")

    for frame in range(frame_start, frame_end + 1):
        new_z = original_z[frame] + Z_OFFSET
        set_key_value(z_curve, frame, new_z)

    z_curve.update()

    out = Path(OUTPUT_BLEND)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    print("------------------------------------")
    print(f"[saved] {out}")
    print("====================================")


if __name__ == "__main__":
    main()
```

---

# 怎么用

在你**已经确认导出正常的那个 Blender 文件**上操作，例如：

```text
teto_clean_floor_v1_footlock_xy
```

或者你现在导出前的最终工程。

## 操作顺序建议

```text
1. 打开最终导出工程
2. 确认已经 bake_global_correction_to_all_parent
3. 确认删除腿部 FK 关键帧
4. 运行 apply_vmd_floor_z_offset.py
5. 打开输出文件
6. 导出 VMD
7. 在 MMD 本体测试脚底高度
```

输出文件：

```text
F:\mocap_ai_doctor\blends\teto_vmd_export_floor_offset.blend
```

---

# 参数怎么调

先用：

```python
Z_OFFSET = -0.0257
```

如果 MMD 里还是浮：

```python
Z_OFFSET = -0.030
```

如果插地：

```python
Z_OFFSET = -0.020
```

大概以 `0.005m` 为步长调，也就是 5mm：

```text
-0.015
-0.020
-0.025
-0.030
-0.035
```

---

# 如果 `全ての親` 不生效

有些模型导出 VMD 时，`全ての親` 可能不按预期，或者模型没有这个骨骼。那就改：

```python
TARGET_BONE = "センター"
```

再试一次。

一般优先级：

```text
1. 全ての親
2. センター
3. グルーブ
```

如果只是整体脚底高度，`全ての親` 最干净；  
如果导出后 MMD 不认 `全ての親`，就用 `センター`。

---

# 注意：不要再移动这些东西

不要为了调地面直接移动：

```text
arue式重音テトver 2.01
arue式重音テトver 2.01_arm
teto_global_correction
mesh 对象
```

因为这些对象位移不一定进入 VMD。

要动就动：

```text
全ての親
```

或者：

```text
センター
```

---

# 当前推荐最终 VMD 导出流程

你现在已经摸清了问题，所以导出流程可以定成这样：

```text
1. 使用最终修好的 Blender 文件
2. bake_global_correction_to_all_parent.py
3. 删除腿部 FK 关键帧：
   左足
   左ひざ
   左足首
   右足
   右ひざ
   右足首
4. apply_vmd_floor_z_offset.py
   先试 Z_OFFSET = -0.0257
5. 导出 VMD
6. 回导 Blender 或 MMD 本体测试
7. 如果脚浮/插，微调 Z_OFFSET
```

这样朋友在 MMD 本体里加载后，角色应该直接踩在地面附近，不需要他再手动调模型高度。

---
## 🧑‍💻 User

全部正常。现在就已经有人想看看我的半成品方案了，我们一路上这些脚本哪些有用，哪些没用，总结一下，再概括一下总体思路，注意对方没有动画相关知识，只是懂编程。

---
## 🤖 Assistant

下面给你一份可以直接发给懂编程但不懂动画/动捕的人看的总结。  
我按“**最终有用 / 试验性 / 废弃**”分类，并把总体思路讲成人话。

---

# 0. 项目目标

目标是把 FreeMoCap 多手机光学动捕结果，修干净后重定向到 MMD/MikuMikuRig 控制的 Teto 模型，并最终导出成 MMD 本体可用的 `.vmd` 动作文件。

数据链路大概是：

```text
FreeMoCap 原始动捕
    ↓
Blender 中手动 bake 成可编辑骨骼动画
    ↓
源骨架清理
    ↓
ARP / MikuMikuRig 重定向到 Teto
    ↓
目标模型脚部、地面、IK 修正
    ↓
烘焙/清理成 MMD 原生骨骼动作
    ↓
导出 VMD
```

---

# 1. 总体方法论

我们没有让 AI 直接“一键修动画”，而是把问题拆成很多个**小而可控的数值修复步骤**：

```text
分析 → 输出报告 → 人确认 → 脚本小范围修改 → 另存新文件 → 再分析/肉眼检查
```

核心原则：

1. **不要让 AI 直接乱改骨骼系统。**
2. **每个脚本只解决一个问题。**
3. **每一步都另存文件，方便回滚。**
4. **源数据阶段只修数据质量。**
5. **目标模型阶段再修 MMD/Teto 比例、IK、地面问题。**
6. **最终 VMD 必须只依赖 MMD 原生骨骼，不能依赖 Blender 的外层 Empty 或 MMR 控制器。**

---

# 2. 最终有效的主流程

最终跑通的流程是：

```text
A. 源 FreeMoCap 骨架阶段
    1. 手动 Bake FreeMoCap 小球/约束到源骨架
    2. 人工区间修手部严重骨折
    3. 轻度旋转平滑
    4. 修脚/脚掌穿地
    5. 生成 foot planting 接触段报告
    6. 手动修正接触段报告

B. 重定向阶段
    1. ARP 重定向到 Teto / MikuMikuRig
    2. 脚仍然重定向到 foot_ik
    3. 不盲目使用 Auto Scale

C. Teto 目标模型阶段
    1. 创建全局校正 Empty，扶正模型
    2. 修 foot_ik 倾斜过度
    3. mesh 地面穿透轻修
    4. foot_ik XY 锁脚，修轻微脚滑

D. VMD 导出阶段
    1. 把全局校正烘到 MMD 的 全ての親
    2. 删除腿部 FK 关键帧，只保留 IK 关键帧
    3. 给 全ての親 添加整体 Z 偏移，让脚落到 MMD 地面
    4. 导出 VMD
```

---

# 3. 最终“有用”的脚本

下面这些是这次真正进入有效流程的脚本。

---

## 3.1 `mocap_doctor_analyze.py`

用途：

```text
分析 FreeMoCap 源骨架的基本问题。
```

检查：

- 脚滑疑似区间；
- 手部跳变；
- 骨盆跳变；
- 脚跟/脚部高度。

地位：

```text
早期诊断工具，有用。
```

现在它主要用于快速确认：

```text
这个动作哪里有明显异常。
```

---

## 3.2 `export_bone_list.py`

用途：

```text
导出骨骼列表。
```

用于确认：

- FreeMoCap 骨骼名；
- MMD / MikuMikuRig 骨骼名；
- foot、heel、hand、pelvis 等关键骨骼。

地位：

```text
工具型脚本，有用。
```

---

## 3.3 `repair_manual_hand_ranges.py`

用途：

```text
人工指定坏区间，修手部严重骨折。
```

这次非常有效。

手部动捕在 FreeMoCap 里不可靠，有些帧手会突然卷进肚子、外翻、折断。  
自动检测只能抓到“跳变点”，但真实坏动作往往持续好几帧。

所以最终采用：

```python
MANUAL_REPAIR_RANGES = [
    ("hand.L", 1711, 1715),
    ("hand.R", 1831, 1835),
]
```

然后脚本对：

```text
shoulder → upper_arm → forearm → hand
```

整条链做插值修复。

地位：

```text
非常有用。
```

缺点：

```text
需要人工填帧段。
```

后续可改成 Blender UI：按键标记 start/end。

---

## 3.4 `repair_mild_rotation_smooth.py`

用途：

```text
轻度平滑整体动作的高频抖动。
```

只平滑旋转，不平滑骨盆大位移，避免把舞蹈动作抹掉。

效果：

```text
整体“颤颤巍巍”明显改善。
```

注意：

这次实际使用时：

```python
INCLUDE_HANDS = False
```

因为手部本身问题多，不适合自动平滑。

地位：

```text
非常有用。
```

---

## 3.5 `repair_floor_penetration_pelvis_z_v2.py`

用途：

```text
源 FreeMoCap 阶段修脚掌/脚跟穿地。
```

它比 v1 更好，因为同时采样：

```text
foot.L head/tail
foot.R head/tail
heel.02.L head/tail
heel.02.R head/tail
```

这样能看到脚前掌，不只是脚踝/脚跟。

修复方式：

```text
当脚部最低点低于地面时，略微抬 pelvis。
```

效果：

```text
脚跟和脚前掌插地显著改善。
```

地位：

```text
非常有用。
```

---

## 3.6 `analyze_foot_contacts.py` / `analyze_foot_contacts_v2.py`

用途：

```text
识别哪些帧是左脚/右脚 planted，也就是应该踩住地面的区间。
```

生成：

```text
foot_contacts_source_clean_v2.json
```

里面有：

```json
planted_segments
near_floor_moving_segments
airborne_or_lifted_segments
```

v2 增加了：

```text
anchor drift 检测
```

用于避免“脚慢慢移动十几厘米但每帧速度不大”被误判为 planted。

地位：

```text
有用，但需要人工修正。
```

---

## 3.7 `mark_foot_contacts_short.py`

用途：

```text
把 foot contact report 标到 Blender 时间线。
```

使用短 marker：

```text
LS / LE = Left planted start/end
RS / RE = Right planted start/end
LM / RM = moving
LD / RD = drift rejected
```

比长名字更可读。

地位：

```text
有用，辅助人工检查。
```

---

## 3.8 `edit_contact_report_overrides.py`

用途：

```text
手动修正 foot contact report。
```

因为纯自动 planted 检测有矛盾：

```text
严格了会漏踩实段
宽松了会把慢速挪脚吞进去
```

所以最终采用：

```python
DELETE_PLANTED_RANGES = [
    ("L", 2010, 2045),
]

ADD_PLANTED_RANGES = [
    ("R", 2300, 2312),
]
```

然后覆盖更新：

```text
foot_contacts_source_clean_v2.json
```

地位：

```text
非常有用。
```

这是把自动化和人工校正结合起来的关键脚本。

---

## 3.9 `create_teto_global_correction.py`

用途：

```text
给 Teto 整体加一个全局校正 Empty。
```

用于修正目标模型整体倾斜。

这次使用的角度大概是：

```python
ROT_X_DEG = -4.2
ROT_Y_DEG = 3.7
ROT_Z_DEG = 0.0
```

修法：

```text
teto_global_correction Empty
    ├── Teto 模型本体
    └── MikuMikuRig 控制器
```

地位：

```text
非常有用。
```

注意：

这个 Empty 在 Blender 里有效，但**不能直接导出到 VMD**，后面必须烘到 `全ての親`。

---

## 3.10 `repair_teto_foot_ik_tilt_only.py`

用途：

```text
修 Teto 的 foot_ik 旋转过度。
```

问题现象：

- 脚掌歪着放；
- 脚底侧翻；
- 极端帧脚网格扭曲；
- 鞋子变形。

错误修法是把 foot_ik 全部旋转拉回参考帧。  
这样脚完全不转了。

正确修法是：

```text
保留脚尖水平转向
只压制脚掌 pitch/roll 倾斜
```

这次有效参数：

```python
STRENGTH = 0.65
```

地位：

```text
非常有用。
```

---

## 3.11 `repair_teto_mesh_floor_lift_v3_safe.py`

用途：

```text
目标 Teto 阶段直接扫描 mesh 最低点，轻微修鞋底插地。
```

之前 v2 有 bug，会让角色越飞越高。  
v3 修复了问题：

```text
先缓存原始 Z
再写入 lift
避免边写边读导致累积漂移
```

效果：

```text
普遍轻微插地解决。
```

这次有效参数大概：

```python
STRENGTH = 0.55
```

地位：

```text
非常有用。
```

注意：

个别异常帧不建议继续加大 strength，手动修更好。  
加大 strength 会导致整体漂浮。

---

## 3.12 `analyze_teto_foot_ik_drift.py`

用途：

```text
分析 Teto foot_ik 在 planted 段内滑动多少。
```

它不修，只输出报告，帮助判断是否需要 foot lock。

地位：

```text
有用。
```

---

## 3.13 `repair_teto_foot_ik_xy_lock.py`

用途：

```text
根据 planted report 锁 foot_ik 的 XY 位置，修轻微脚滑。
```

它只锁：

```text
foot_ik.location X/Y
```

不锁：

```text
Z
rotation
```

所以不会破坏脚高度和脚尖方向。

这一步对“脚不动、躯干扭动，但脚还在漂”的问题非常有效。

地位：

```text
非常有用。
```

---

## 3.14 `find_mmd_root_bones.py`

用途：

```text
查 MMD 原生骨架里有没有 全ての親 / センター / グルーブ。
```

导出 VMD 前用来确认应该把全局补偿烘到哪个骨骼。

地位：

```text
工具型脚本，有用。
```

---

## 3.15 `bake_global_correction_to_all_parent.py`

用途：

```text
把 Blender 外层 teto_global_correction Empty 的旋转/位移烘到 MMD 的 全ての親 骨骼。
```

这是导出 VMD 的关键。

原因：

```text
VMD 不会保存 Blender 里的 Empty 动画。
```

所以如果不烘进去，导出后会出现：

- 人又歪了；
- 上下补偿消失；
- 腿/脚在 MMD 里表现异常；
- Blender 正常，MMD 本体坏。

地位：

```text
非常有用，导出 VMD 前必须考虑。
```

---

## 3.16 `apply_vmd_floor_z_offset.py`

用途：

```text
导出 VMD 前，让角色脚底正好踩到 MMD 地面。
```

不要移动 Blender 对象本身，而是给：

```text
全ての親
```

或：

```text
センター
```

添加 Z 偏移。

这次解决的问题：

```text
朋友在 MMD 本体里打开时，模型整体略微浮在地面上。
```

地位：

```text
非常有用。
```

---

# 4. 试验过但不推荐继续用的脚本

---

## 4.1 `repair_hand_jumps_no_bake.py`

用途：

```text
只修 hand.L / hand.R 单帧跳变。
```

问题：

手的世界位置跳变通常不是 `hand` 自己局部 key 导致的，而是上游链条：

```text
shoulder → upper_arm → forearm → hand
```

导致。

所以只修 hand bone 没明显效果。

结论：

```text
废弃，改用 repair_manual_hand_ranges.py。
```

---

## 4.2 `repair_hand_jumps_chain_no_bake.py`

用途：

```text
自动根据 analyzer 报告，修整条手臂链。
```

问题：

自动检测只抓到单帧跳变，但真实坏手姿态持续好几帧。

例如真实是：

```text
1711–1715
```

检测可能只报：

```text
1711
```

所以修得不彻底。

结论：

```text
思路有用，但最终被人工区间版替代。
```

---

## 4.3 `repair_floor_penetration_pelvis_z.py`

用途：

```text
早期地板穿透修复。
```

问题：

只看 foot/heel 的位置，不看 foot tail，漏掉脚前掌。

结论：

```text
被 repair_floor_penetration_pelvis_z_v2.py 替代。
```

---

## 4.4 `repair_teto_foot_ik_rotation_dampen.py`

用途：

```text
把 foot_ik 完整旋转向参考帧拉回。
```

问题：

太粗暴。  
它把脚尖朝向也一起锁死，导致：

```text
脚完全不转了。
```

结论：

```text
废弃。
```

被：

```text
repair_teto_foot_ik_tilt_only.py
```

替代。

---

## 4.5 `repair_teto_mesh_floor_lift_v2.py`

用途：

```text
早期 Teto mesh 地面修复。
```

问题：

边写关键帧边 evaluate 同一条 Z 曲线，导致累计误差：

```text
角色越飞越高。
```

结论：

```text
废弃。
```

被：

```text
repair_teto_mesh_floor_lift_v3_safe.py
```

替代。

---

# 5. 截图里这些脚本大概怎么归类

你截图里的文件大概可以这样分类：

## 最终主流程核心脚本

```text
mocap_doctor_analyze.py
export_bone_list.py
repair_manual_hand_ranges.py
repair_mild_rotation_smooth.py
repair_floor_penetration_pelvis_z_v2.py
analyze_foot_contacts_v2.py
mark_foot_contacts_short.py
edit_contact_report_overrides.py
create_teto_global_correction.py
repair_teto_foot_ik_tilt_only.py
repair_teto_mesh_floor_lift_v3_safe.py
analyze_teto_foot_ik_drift.py
repair_teto_foot_ik_xy_lock.py
find_mmd_root_bones.py
bake_global_correction_to_all_parent.py
apply_vmd_floor_z_offset.py
```

## 有参考价值但已被替代

```text
analyze_foot_contacts.py
repair_floor_penetration_pelvis_z.py
repair_hand_jumps_chain_no_bake.py
repair_hand_jumps_no_bake.py
```

## 废弃/不要再用

```text
repair_teto_foot_ik_rotation_dampen.py
repair_teto_mesh_floor_lift_v2.py
```

## 你后来可能自己加的导出辅助脚本

截图里还有这些：

```text
prepare_vmd_transfer_body_loc_to_c...
inspect_mmd_location_fcurves.py
prepare_mmd_vmd_export_clean_l...
prepare_mmd_vmd_ik_leg_export.py
```

这些应该是你后面围绕 VMD 导出、清理 FK/IK 冲突写的。  
从结果来看，这类脚本的核心思想是对的：

```text
导出 VMD 前：
    保留 IK 腿部控制
    删除腿部 FK 关键帧
```

---

# 6. 最关键的经验总结

## 6.1 FreeMoCap 源骨架不是最终目标

源骨架阶段只修：

```text
明显跳变
抖动
手部严重异常
脚底穿地
```

不要在源骨架阶段过度 foot lock。  
因为重定向到二次元 MMD 模型后，比例会变，脚还会产生新问题。

---

## 6.2 目标模型阶段必须重新修脚

Teto 的比例和真人不同：

```text
腿长比例不同
脚掌形状不同
骨盆高度不同
MMD IK 结构不同
```

所以即使源动作干净，重定向后仍然要修：

```text
foot_ik 倾斜
mesh 穿地
planted 段脚滑
```

---

## 6.3 foot_ik 最好“锁位置，不乱锁旋转”

这次最有效策略是：

```text
foot_ik 旋转：
    只压 pitch/roll 过度，不压 yaw

foot_ik 位置：
    planted 段锁 XY，不锁 Z
```

这样既能减少脚滑，又不会让脚变死。

---

## 6.4 VMD 导出最容易踩坑

Blender 里正常，不代表 VMD 正常。

原因是 VMD 不会导出：

```text
Blender Object / Empty 变换
MMR 控制器
约束
部分 driver
Blender 外层补偿
```

VMD 只关心 MMD 骨骼和表情等数据。

所以导出前必须：

```text
把全局校正烘到 全ての親
把地面高度偏移写进 全ての親/センター
删除腿部 FK 关键帧，避免和 IK 双重叠加
```

---

# 7. 最终 VMD 导出规则

这次最终稳定导出的关键规则：

```text
1. 不导出 MMR 控制器动作。
2. 动作必须落到 MMD 原生骨骼。
3. 全局 Empty 修正必须转移到 全ての親。
4. 腿部 FK 关键帧要删除：
   左足
   左ひざ
   左足首
   右足
   右ひざ
   右足首
5. 保留足 IK 相关关键帧。
6. 用 全ての親 或 センター 做最终地面高度偏移。
```

---

# 8. 对方如果只懂编程，可以这样理解

这套流程本质上不是“动画魔法”，而是一个数据清洗 pipeline：

```text
输入：骨骼时间序列
输出：目标模型可用的骨骼时间序列
```

我们做了几类操作：

```text
1. Outlier repair
   修手部/脚部异常帧。

2. Low-pass smoothing
   平滑高频噪声。

3. Constraint projection
   把脚底约束到地面附近。

4. Contact segmentation
   找出脚应该踩住的时间段。

5. Retarget cleanup
   修目标模型比例和 IK 引入的新错误。

6. Export baking
   把 Blender 内部控制器/Empty/约束转成 MMD VMD 能理解的骨骼关键帧。
```

核心思想和软件工程里的 ETL 很像：

```text
Extract 动捕数据
Transform 清洗和重定向
Load 导出到 MMD/VMD
```

---

# 9. 现在半成品方案的状态

当前已经做到：

```text
✅ FreeMoCap 源动作可清理
✅ 重定向到 Teto 后脚部效果可接受
✅ 脚滑可通过 planted report + foot_ik XY lock 修复
✅ VMD 导出后在 MMD 本体里可正常播放
✅ 地面高度可以在导出前统一修正
```

还没有完全自动化的是：

```text
1. 手部坏区间仍需要人工标记
2. planted 段仍需要少量人工 override
3. 个别极端脚部异常帧仍适合手动修
4. 24fps → MMD 30fps 的时间缩放还没系统化
5. 还没有做完整 GUI
```

---

# 10. 后续最值得做的改进

如果要继续开发，优先级建议：

## 第一优先级：Blender 小 UI

做一个面板：

```text
Mark hand bad start
Mark hand bad end
Add planted
Delete planted
Run repair
Export VMD
```

这样就不用手动改 Python 列表。

---

## 第二优先级：统一 config

现在很多脚本路径写死。  
应该变成：

```text
project_config.json
```

统一管理：

```json
{
  "source_armature": "...",
  "target_rig": "...",
  "mmd_armature": "...",
  "floor_z": 0.0257,
  "frame_start": 1525,
  "frame_end": 2836
}
```

---

## 第三优先级：导出一键化

把这些步骤合成一个 export pipeline：

```text
bake_global_correction_to_all_parent
delete leg FK keys
apply_vmd_floor_z_offset
export VMD
```

---

## 第四优先级：加入 FreeMoCap npy confidence

目前我们主要靠 Blender 骨骼运动检测。  
后面可以用 FreeMoCap 原始 npy 置信度，自动判断：

```text
哪些手部/脚部帧不可信
哪些帧应该插值
哪些接触段可疑
```

---

# 11. 一句话总结

这套半成品方案的核心是：

> **不要让 VMD 直接吃 MMR/Rigify 控制器。先把 FreeMoCap 动作清洗干净，再重定向到 Teto，修目标 IK 和地面，最后把所有 Blender 外部补偿烘进 MMD 原生骨骼，只导出 MMD 能理解的关键帧。**
