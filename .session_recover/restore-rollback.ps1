# Re-apply (or undo) the session rollback for session-2c3a0cb5.
# Run with DSH fully closed: any live instance holds the pre-rollback state in
# memory and would append a non-contiguous seq, corrupting the log.
param(
  [switch]$Undo
)

$ErrorActionPreference = 'Stop'

$sessionDir = "C:\Users\George\.dsh\sessions\--F-mocap_ai_doctor--\session-2c3a0cb5-3175-4358-a29a-34ccc991b9da"
$log        = Join-Path $sessionDir "session.v4.jsonl.zstd"
$backupDir  = "F:\mocap_ai_doctor\.session_recover\backup"
$restored   = Join-Path $backupDir "restored-session.v4.jsonl.zstd"
$origLog    = Get-ChildItem -Path $backupDir -Filter "session.v4.jsonl.zstd.orig-*" |
              Sort-Object LastWriteTime | Select-Object -Last 1
$origCache  = Get-ChildItem -Path $backupDir -Filter "projcache-*.json" |
              Sort-Object LastWriteTime | Select-Object -Last 1
$cachePath  = "C:\Users\George\.dsh\storages\session_projcache\sessions\session-2c3a0cb5-3175-4358-a29a-34ccc991b9da.json"

if ($Undo) {
  if (-not $origLog) { throw "no original log backup found in $backupDir" }
  Copy-Item -LiteralPath $origLog.FullName -Destination $log -Force
  if ($origCache) { Copy-Item -LiteralPath $origCache.FullName -Destination $cachePath -Force }
  Write-Host "undone: restored original log ($($origLog.Name))"
  exit 0
}

if (-not (Test-Path -LiteralPath $restored)) { throw "missing $restored" }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -LiteralPath $log -Destination (Join-Path $backupDir "session.v4.jsonl.zstd.prereapply-$stamp") -Force
$tmp = Join-Path $sessionDir "session.v4.jsonl.zstd.rollback-tmp"
Copy-Item -LiteralPath $restored -Destination $tmp -Force
Move-Item -LiteralPath $tmp -Destination $log -Force
if (Test-Path -LiteralPath $cachePath) { Remove-Item -LiteralPath $cachePath -Force }
Write-Host "rollback re-applied: $log ($((Get-Item -LiteralPath $log).Length) bytes)"
