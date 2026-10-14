# Idempotently (re)apply the DeepSeek-V41-Flash + max summarization route to the
# desktop profile patch. Use when: the patch was reverted, or a settings write
# from the GUI dropped the entries. Requires a DSH restart to take effect.
#
#   pwsh -File apply-summary-route.ps1
#   pwsh -File apply-summary-route.ps1 -Undo
param(
  [switch]$Undo
)

$ErrorActionPreference = 'Stop'

$profile    = "C:\Users\George\.dsh\profiles\desktop\cordis.patch.yml"
$dir        = "F:\mocap_ai_doctor\.session_recover"
$snippet    = Join-Path $dir "patch_addition.yml"
$backupDir  = Join-Path $dir "backup"
$marker     = "- id: preset-standard"

$text = [System.IO.File]::ReadAllText($profile)
$has  = $text.Contains($marker) -and $text.Contains("summarizationProvider: deepseek-official")

if ($Undo) {
  if (-not $has) { Write-Host "nothing to undo (entries absent)"; exit 0 }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  Copy-Item -LiteralPath $profile -Destination (Join-Path $backupDir "cordis.patch.yml.before-undo-$stamp") -Force
  $lines = $text -split "`n"
  $match = $lines | Where-Object { $_.TrimEnd() -eq $marker } | Select-Object -First 1
  $start = [array]::IndexOf($lines, $match)
  if ($start -le 0) { throw "cannot locate the summarization route block in $profile" }
  $new = ($lines[0..($start - 1)] -join "`n").TrimEnd() + "`n"
  [System.IO.File]::WriteAllText($profile, $new, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "removed the summarization route entries from $profile"
  exit 0
}

if ($has) { Write-Host "already applied: $profile"; exit 0 }

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -LiteralPath $profile -Destination (Join-Path $backupDir "cordis.patch.yml.before-summary-route-$stamp") -Force
$add = [System.IO.File]::ReadAllText($snippet)
$candidate = $text.TrimEnd("`r", "`n") + "`n`n" + $add.TrimStart("`r", "`n")
[System.IO.File]::WriteAllText($profile, $candidate, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "applied: $profile ($((Get-Item $profile).Length) bytes); restart DSH to take effect"
