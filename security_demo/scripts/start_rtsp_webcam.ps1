param()
$ErrorActionPreference = 'Stop'
$envDir = Join-Path $PSScriptRoot '..'
$envPath = Join-Path $envDir '.env'
if (Test-Path $envPath) {
  Get-Content $envPath | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($name, $value)
  }
}

$port = $env:RTSP_PORT; if (-not $port) { $port = 8554 }
$device = $env:DSHOW_DEVICE; if (-not $device) { $device = 'Integrated Camera' }

# Vulnerable mode: plain RTSP from local webcam (Windows dshow)
# Note: list devices with: ffmpeg -list_devices true -f dshow -i dummy
ffmpeg -f dshow -i "video=$device" -c copy -f rtsp "rtsp://0.0.0.0:$port/live.sdp?listen=1"
