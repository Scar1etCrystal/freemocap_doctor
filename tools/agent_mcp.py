"""Stdio MCP bridge for the in-Blender agent tool server.

Any MCP-capable host (Claude Code, Cursor, ...) spawns this script as its MCP
server; each tools/call is forwarded over the local socket to the addon's
agent_bridge inside the running GUI Blender session.

    { "mcpServers": { "mocap-doctor": {
        "command": "<python>",
        "args": ["F:\\mocap_ai_doctor\\tools\\agent_mcp.py"] } } }

Protocol: JSON-RPC 2.0 over stdio, newline-delimited messages.
"""

import json
import os
import socket
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HOST = "127.0.0.1"
PORT = int(os.environ.get("MCD_AGENT_PORT", "6211"))

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "mocap-doctor", "version": "1.6.0"}

# name → (description, input schema).  Schemas stay permissive - the bridge
# validates args and returns actionable errors.
TOOL_DEFS = [
    ("ping", "服务存活与数据版本号", {}),
    ("get_overview", "帧范围/fps/信号清单/区间清单总览",
     {"force_refresh": {"type": "boolean"}}),
    ("list_intervals", "按类型列出标注/可靠区间",
     {"kind": {"type": "string"}, "frame_range": {"type": "array"},
      "tag": {"type": "string"}}),
    ("describe", "摘要卡片：某区间/帧段各信号统计+前后对比+事件",
     {"target": {}, "channels": {"type": "array"},
      "context": {"type": "integer"}}),
    ("get_series", "下采样取曲线数据",
     {"channels": {"type": "array"}, "frame_range": {"type": "array"},
      "max_points": {"type": "integer"}, "agg": {"type": "string"}}),
    ("find_events", "声明式条件找帧段（all/any/min_len 白名单）",
     {"cond": {"type": "object"}, "frame_range": {"type": "array"}}),
    ("compare", "同一信号两区间对比（峰值比/均值差/分布距）",
     {"channel": {"type": "string"}, "a": {}, "b": {}}),
    ("snapshot", "某帧关键点世界坐标",
     {"frame": {"type": "integer"}, "roles": {"type": "array"}}),
    ("bake_range", "帧段内指定骨骼的世界位置数组",
     {"frame_range": {"type": "array"}, "roles": {"type": "array"}}),
    ("get_joint_angles", "逐帧每节骨骼屈伸/外展/扭转角（度）",
     {"bones": {"type": "array"}, "frame_range": {"type": "array"},
      "max_points": {"type": "integer"}}),
    ("hold_pose", "通用姿态保持：骨骼在帧段内钉住某姿态（AGENT_PREVIEW 轨）。"
                  "target=values(默认identity伸直)|from_frame(区间内自动挑最标准帧)|world_dir(指向世界向量)；"
                  "mode=replace|clamp(超阈值压回)|outlier(坏帧插值)",
     {"bones": {"type": "array"}, "frame_range": {"type": "array"},
      "target": {"type": "string", "enum": ["values", "from_frame", "world_dir"]},
      "values": {"type": "object"}, "ref_frame": {},
      "world_dir": {"type": "array"}, "world_axis": {"type": "string",
                   "enum": ["X", "Y", "Z", "-X", "-Y", "-Z"]},
      "mode": {"type": "string",
               "enum": ["replace", "clamp", "outlier"]},
      "threshold_deg": {"type": "number"}, "strength": {"type": "number"},
      "blend": {"type": "integer"}}),
    ("set_influence", "按 op 设力度：把该修复 delta 重写成 delta^value（>1 超量）",
     {"value": {"type": "number"}, "op_id": {"type": "string"},
      "track_name": {"type": "string"}}),
    ("effect_check", "A/B 自检：mute/求值对比确认写入真的生效",
     {"op_id": {"type": "string"}, "track_name": {"type": "string"},
      "bones": {"type": "array"}, "frames": {"type": "array"}}),
    ("clean_jitter", "窗口内零相位平滑（每条修复一条轨）",
     {"frame_range": {"type": "array"}, "bone": {"type": "string"},
      "paths": {"type": "array"}, "strength": {"type": "number"},
      "width": {"type": "integer"}, "blend": {"type": "integer"},
      "mode": {"type": "string", "enum": ["preview", "commit"]}}),
    ("fix_ground", "修着地脚的离地/穿地/悬空（AGENT_PREVIEW 轨）",
     {"frame_range": {"type": "array"}, "side": {"type": "string"},
      "loc_path": {"type": "string"},
      "mode": {"type": "string", "enum": ["lift", "pen", "float"]},
      "pin_xy": {"type": "boolean"}, "blend": {"type": "integer"}}),
    ("restore_accent", "力量感：ease_reshape/retime（quaternion/location 通道整骨重塑，index 仅其他通道需要）",
     {"frame_range": {"type": "array"}, "data_path": {"type": "string"},
      "index": {"type": "integer"},
      "method": {"type": "string",
                 "enum": ["ease_reshape", "retime", "hf_reinject", "refilter"]},
      "strength": {"type": "number"}, "impact_frame": {"type": "integer"},
      "retime_speed": {"type": "number"}, "retime_split": {"type": "number"},
      "raw_action": {"type": "string"}, "blend": {"type": "integer"}}),
    ("solve_pelvis", "写骨盆 Z 增量（dz 由调用方算好传入）",
     {"frame_range": {"type": "array"}, "pelvis_path": {"type": "string"},
      "pelvis_dz": {"type": "array"}, "blend": {"type": "integer"}}),
    ("apply_exemplar", "把样例残差迁移到目标区间（AGENT_PREVIEW 轨）",
     {"frame_range": {"type": "array"}, "ex_id": {"type": "string"},
      "loc_path": {"type": "string"}, "quat_path": {"type": "string"},
      "target_pos": {"type": "array"}, "target_quat": {"type": "array"},
      "anchor_yaw_deg": {"type": "number"}, "yaw_scale": {"type": "number"},
      "mirror": {"type": "boolean"}, "blend": {"type": "integer"}}),
    ("validate", "穿地/滑步/悬空/边界跳变检查",
     {"frame_range": {"type": "array"}}),
    ("list_ops", "op 日志 + 实时状态（track/applied_exp/mute/丢失对账）", {}),
    ("commit", "标记某 op 已提交（不搬轨，仍可调力度/静音）",
     {"op_id": {"type": "string"}}),
    ("revert", "撤掉某 op（删 strip + action + 空轨）",
     {"op_id": {"type": "string"}}),
    ("ab_toggle", "全部 agent 轨一起静音/放响（前后对比）", {}),
    ("set_preview", "设预览播放范围", {"frame_range": {"type": "array"}}),
]


def _socket_call(tool: str, args: dict) -> dict:
    req = {"id": 1, "tool": tool, "args": args}
    with socket.create_connection((HOST, PORT), timeout=120.0) as sock:
        sock.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(1 << 20)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))


def _reply(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle(req: dict):
    method = req.get("method", "")
    mid = req.get("id")
    if method == "initialize":
        _reply(mid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })
    elif method == "notifications/initialized":
        return
    elif method == "ping":
        _reply(mid, {})
    elif method == "tools/list":
        _reply(mid, {"tools": [
            {"name": name, "description": desc,
             "inputSchema": {"type": "object", "properties": props,
                             "additionalProperties": True}}
            for name, desc, props in TOOL_DEFS
        ]})
    elif method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name", "")
        args = params.get("arguments") or {}
        if name not in {t[0] for t in TOOL_DEFS}:
            _reply(mid, {"content": [{"type": "text",
                                      "text": f"未知工具 {name}"}],
                         "isError": True})
            return
        try:
            resp = _socket_call(name, args)
            text = json.dumps(resp, ensure_ascii=False)
            _reply(mid, {"content": [{"type": "text", "text": text}],
                         "isError": not resp.get("ok", False)})
        except OSError as exc:
            _reply(mid, {"content": [{"type": "text",
                                      "text": f"连不上 Blender 工具服务器 "
                                              f"({HOST}:{PORT})：{exc}。"
                                              f"先在面板里启动 Agent 服务"}],
                         "isError": True})
    elif mid is not None:
        _reply(mid, error={"code": -32601, "message": f"method {method}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        _handle(req)


if __name__ == "__main__":
    main()
