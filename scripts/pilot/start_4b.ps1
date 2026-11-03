# Start llama-server with Qwen3-4B (4 slots) for the main runs. Stops any running llama-server first.
$server = 'C:\AI\Tools\llama-cpp-b11756-cuda134\llama-server.exe'
$model  = 'C:\AI\Models\Qwen3-4B-Instruct-2507\Qwen3-4B-Instruct-2507-Q4_K_M.gguf'
$logs   = 'C:\AI\Logs'
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Start-Process -FilePath $server -WorkingDirectory (Split-Path $server) -WindowStyle Hidden `
  -RedirectStandardOutput "$logs\q4b-fast.stdout.log" -RedirectStandardError "$logs\q4b-fast.stderr.log" `
  -ArgumentList @('--model',$model,'--alias','qwen3-4b-instruct-2507-q4_k_m','--host','127.0.0.1','--port','8080',
    '--ctx-size','16384','--parallel','4','--device','CUDA0','--fit','on','--fit-target','768',
    '--flash-attn','on','--cache-type-k','q8_0','--cache-type-v','q8_0','--threads','16','--threads-batch','16','--jinja')
for ($i=0; $i -lt 120; $i++) {
  Start-Sleep -Seconds 5
  try { Invoke-RestMethod http://127.0.0.1:8080/health -TimeoutSec 4 | Out-Null; Write-Host '4B ready'; exit 0 } catch {}
}
Write-Host 'not healthy; see C:\AI\Logs\q4b-fast.stderr.log'; exit 1
