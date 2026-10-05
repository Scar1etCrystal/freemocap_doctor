"""打 Blender 扩展包：dist/mocap_doctor-<version>.zip

目录结构必须是 <pkg>/blender_manifest.toml（顶层带包名目录），
与 1.7.0 包一致。排除 __pycache__/*.pyc（manifest 的 build 规则同款）。
"""
import re
import zipfile
from pathlib import Path

ROOT = Path(r"F:\mocap_ai_doctor")
PKG = ROOT / "mocap_doctor"
DIST = ROOT / "dist"
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIX = {".pyc", ".pyo"}

manifest = (PKG / "blender_manifest.toml").read_text(encoding="utf-8")
version = re.search(r'^version\s*=\s*"([^"]+)"', manifest, re.M).group(1)
out = DIST / f"mocap_doctor-{version}.zip"

files = []
for p in sorted(PKG.rglob("*")):
    if p.is_dir():
        continue
    rel = p.relative_to(PKG)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        continue
    if p.suffix in EXCLUDE_SUFFIX:
        continue
    files.append((p, rel))

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p, rel in files:
        arc = f"mocap_doctor/{rel.as_posix()}"
        z.write(p, arc)

print(f"打包完成: {out}")
print(f"  版本   : {version}")
print(f"  条目数 : {len(files)}")
print(f"  大小   : {out.stat().st_size:,} 字节 ({out.stat().st_size/1024:.0f} KB)")

# 自检
z = zipfile.ZipFile(out)
names = z.namelist()
tops = {n.split("/")[0] for n in names}
assert tops == {"mocap_doctor"}, f"顶层目录不对: {tops}"
assert any(n.endswith("blender_manifest.toml") for n in names), "缺 manifest"
assert not any("__pycache__" in n or n.endswith(".pyc") for n in names), "混入缓存"
bad = z.testzip()
assert bad is None, f"zip 损坏: {bad}"
inner = z.read("mocap_doctor/blender_manifest.toml").decode("utf-8")
inner_v = re.search(r'^version\s*=\s*"([^"]+)"', inner, re.M).group(1)
assert inner_v == version, f"包内版本 {inner_v} != 文件名版本 {version}"

print("\n自检通过:")
print(f"  顶层目录 = {tops}")
print(f"  包内版本 = {inner_v}")
core = sorted(n.split("/")[-1] for n in names if n.startswith("mocap_doctor/core/"))
print(f"  core 模块 ({len(core)}): {', '.join(core)}")
