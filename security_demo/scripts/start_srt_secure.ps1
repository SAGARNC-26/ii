param()
$ErrorActionPreference = 'Stop'
$envPath = Join-Path $PSScriptRoot '..' '.env'
if (Test-Path $envPath) {
  Get-Content $envPath | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($name, $value)
  }
}

$device = $env:DSHOW_DEVICE; if (-not $device) { $device = 'Integrated Camera' }
$port   = $env:SRT_PORT;     if (-not $port)   { $port   = 9000 }
$pass   = $env:SRT_PASS;     if (-not $pass)   { $pass   = 'secretkey' }

Write-Host "[SRT] Serving encrypted SRT at srt://0.0.0.0:$port?listen=1&passphrase=***"
ffmpeg -f dshow -i "video=$device" -c copy -f mpegts "srt://0.0.0.0:$port?listen=1&passphrase=$pass"
