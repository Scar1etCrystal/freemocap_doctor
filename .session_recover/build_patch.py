"""Build the profile-patch additions for pinning the compaction summarizer.

Reads the shipped `standard` preset declaration extracted from app.asar and emits
a profile-patch snippet that overrides the `preset-standard` row by id, with the
compaction-basic row gaining summarization routing, plus a route-level
reasoningEffort for the DeepSeek adapter.
"""
import io
import re

SRC = r"F:\mocap_ai_doctor\.session_recover\asar_extract\presets_standard.patch.yml"
OUT = r"F:\mocap_ai_doctor\.session_recover\patch_addition.yml"

with io.open(SRC, encoding="utf-8") as fh:
    lines = fh.read().split("\n")

start = next(i for i, line in enumerate(lines) if re.match(r"^\s*- id: persona\s*$", line))
base_indent = len(lines[start]) - len(lines[start].lstrip(" "))
dedent = base_indent - 6  # plugin items belong at 6 spaces under `config: plugins:`
assert dedent > 0, f"unexpected plugin item indent {base_indent}"

items = []
for line in lines[start:]:
    if line.strip() == "":
        items.append("")
        continue
    assert line.startswith(" " * dedent), f"line less indented than expected: {line!r}"
    items.append(line[dedent:])
while items and items[-1] == "":
    items.pop()

out = []
for line in items:
    out.append(line)
    if re.match(r"^\s*name: '@deepseek-ai/dsh-compaction-basic'\s*$", line):
        name_indent = len(line) - len(line.lstrip(" "))
        out.append(" " * name_indent + "config:")
        out.append(" " * (name_indent + 2) + "summarizationProvider: deepseek-official")
        out.append(" " * (name_indent + 2) + "summarizationModel: deepseek-flash")
items = out

header = """# ── 摘要（compaction）路由：钉到 DeepSeek-V41-Flash + max 思考强度 ──────────
# 1) standard preset 的声明整体覆盖（原声明在 app.asar 内
#    @deepseek-ai/dsh-web-app/presets/standard.patch.yml；插件行逐字保持原样，
#    只有 compaction-basic 增加了 summarization* 两项）。preset 声明按 Loader
#    行 id 覆盖，见 app 自带 skill `editing-cordis-compositions`。
# 2) 摘要调用本身不带 reasoning effort，取的是路由默认值（适配器默认 high），
#    所以在 llm-deepseek 行上把默认强度设为 max。
- id: preset-standard
  name: '@deepseek-ai/dsh-agent-preset'
  config:
    id: standard
    order: 1
    plugins:"""

footer = """
- id: llm-deepseek
  name: '@deepseek-ai/dsh-llm-deepseek-api-key'
  config:
    reasoningEffort: max
"""

text = header + "\n" + "\n".join(items) + "\n" + footer
with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)

body = text.split("\n")
print(f"wrote {OUT} ({len(text)} bytes, {len(body)} lines); plugin item indent = 6")
print("---- first 16 lines ----")
print("\n".join(body[:16]))
print("---- compaction rows ----")
for i, line in enumerate(body):
    if "compaction-basic" in line:
        print("\n".join(body[i - 2:i + 6]))
        print("   ...")
print("---- last 10 lines ----")
print("\n".join(body[-10:]))
