param()
$ErrorActionPreference = 'Stop'
$envDir = Join-Path $PSScriptRoot '..'
$envPath = Join-Path $envDir '.env'
if (Test-Path $envPath) {
  Get-Content $envPath | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($name, $value)
  }
}

$proxyPort = $env:RTSP_PROXY_PORT; if (-not $proxyPort) { $proxyPort = 8556 }
$rtspPort  = $env:RTSP_PORT;       if (-not $rtspPort)  { $rtspPort  = 8554 }
$sourceUrl = $env:SOURCE_URL;      if (-not $sourceUrl) { $sourceUrl = "rtsp://127.0.0.1:$rtspPort/live.sdp" }

Write-Host "[RTSP PROXY] Listening at rtsp://0.0.0.0:$proxyPort/live.sdp"
Write-Host "[RTSP PROXY] Forwarding from SOURCE_URL=$sourceUrl"

ffmpeg -rtsp_transport tcp -i "$sourceUrl" -c copy -f rtsp "rtsp://0.0.0.0:$proxyPort/live.sdp?listen=1"
