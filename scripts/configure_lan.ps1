param([string]$Address)
$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path $PSScriptRoot -Parent
if (-not $Address) {
    $Address = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | ForEach-Object { $_.IPv4Address.IPAddress } | Select-Object -First 1
}
$parsedAddress = $null
if (-not [Net.IPAddress]::TryParse($Address, [ref]$parsedAddress) -or $parsedAddress.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'Supply your Wi-Fi IPv4 address using -Address.'
}
function Set-LanSetting([string]$Path, [string]$Name, [string]$Value) {
    $contents = if (Test-Path -LiteralPath $Path) { [IO.File]::ReadAllText($Path) } else { '' }
    $line = "$Name=$Value"
    if ($contents -match "(?m)^$Name=.*$") {
        $contents = [regex]::Replace($contents, "(?m)^$Name=.*$", $line)
    } else {
        $contents = $contents.TrimEnd() + "`n$line`n"
    }
    [IO.File]::WriteAllText($Path, $contents, (New-Object Text.UTF8Encoding($false)))
}
Set-LanSetting (Join-Path $kitRoot '.env') 'FRONTEND_EXTRA_ORIGINS' "http://${Address}:3000"
Set-LanSetting (Join-Path $kitRoot 'frontend/.env.local') 'NEXT_PUBLIC_API_BASE_URL' ''
Set-LanSetting (Join-Path $kitRoot 'frontend/.env.local') 'LAN_ALLOWED_HOSTS' $Address
Write-Host "LAN configured: http://${Address}:3000"
Write-Host 'Restart the API, then run npm run dev:lan in frontend. Keep the API bound to 127.0.0.1.'
