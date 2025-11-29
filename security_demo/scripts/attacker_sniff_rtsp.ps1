param()
$ErrorActionPreference = 'Stop'
$envPath = Join-Path $PSScriptRoot '..' '.env'
$outDir = Join-Path $PSScriptRoot '..' 'output'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
if (Test-Path $envPath) {
  Get-Content $envPath | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($name, $value)
  }
}

$iface = $env:IFACE;      if (-not $iface) { $iface = 'Wi-Fi' }
$port  = $env:RTSP_PORT;  if (-not $port)  { $port  = 8554 }
$outFile = Join-Path $outDir 'sniff_rtsp.txt'

Write-Host "[ATTACKER] Sniffing RTSP on interface: $iface (tcp port $port)"
Write-Host "Saving to: $outFile"
Write-Host "Press Ctrl+C to stop."

# Requires tshark installed
&tshark -i "$iface" -f "tcp port $port" -Y 'rtsp || (tcp contains "DESCRIBE") || (tcp contains "SETUP") || (tcp contains "PLAY")' `
  -T fields `
  -e frame.time -e ip.src -e ip.dst -e rtsp.method -e rtsp.request -e rtsp.response -e rtsp.session `
  2>&1 | Tee-Object -FilePath "$outFile"
