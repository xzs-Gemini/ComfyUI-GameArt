param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw '请先按 INSTALL.md 创建 .venv 并安装依赖。' }
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot 'ComfyUI\main.py'))) { throw '请先按 INSTALL.md 安装指定版本的 ComfyUI 并应用 Searge 补丁。' }
$logDir = Join-Path $taskRoot 'data'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
try { $null = Invoke-RestMethod 'http://127.0.0.1:8189/system_stats' -TimeoutSec 2 } catch {
    $backendArgs = @('main.py', '--listen', '127.0.0.1', '--port', '8189', '--extra-model-paths-config', ('"' + (Join-Path $taskRoot 'extra_model_paths.yaml') + '"'), '--disable-api-nodes', '--preview-method', 'none')
    Start-Process -FilePath $taskPython -ArgumentList $backendArgs -WorkingDirectory (Join-Path $taskRoot 'ComfyUI') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'comfy.log') -RedirectStandardError (Join-Path $logDir 'comfy-error.log')
}
try { $null = Invoke-RestMethod 'http://127.0.0.1:5213/api/state' -TimeoutSec 2 } catch {
    Start-Process -FilePath $taskPython -ArgumentList '-m','gameart.server' -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'app.log') -RedirectStandardError (Join-Path $logDir 'app-error.log')
}
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:5213' }
