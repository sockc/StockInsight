param(
    [string]$Keystore = "stockinsight-release.jks",
    [string]$Alias = "stockinsight"
)

$ErrorActionPreference = "Stop"

if (Test-Path $Keystore) {
    throw "$Keystore already exists. Do NOT overwrite the fixed release keystore."
}

if (-not (Get-Command keytool -ErrorAction SilentlyContinue)) {
    throw "keytool was not found. Install JDK 17+ and reopen PowerShell."
}

Write-Host "Creating the ONE fixed StockInsight release key." -ForegroundColor Cyan
Write-Host "Remember the passwords you enter. Back up the JKS securely." -ForegroundColor Yellow

& keytool -genkeypair -v `
    -keystore $Keystore `
    -alias $Alias `
    -keyalg RSA `
    -keysize 4096 `
    -validity 36500

if ($LASTEXITCODE -ne 0) { throw "keytool failed" }

$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path $Keystore)))
$base64File = "$Keystore.base64.txt"
[IO.File]::WriteAllText((Join-Path (Get-Location) $base64File), $base64)

Write-Host ""
Write-Host "Created: $Keystore" -ForegroundColor Green
Write-Host "Created: $base64File" -ForegroundColor Green
Write-Host ""
Write-Host "GitHub repository Secrets required:" -ForegroundColor Cyan
Write-Host "SIGNING_KEY_BASE64      = contents of $base64File"
Write-Host "SIGNING_STORE_PASSWORD  = the keystore password you entered"
Write-Host "SIGNING_KEY_ALIAS       = $Alias"
Write-Host "SIGNING_KEY_PASSWORD    = the key password you entered (often same as store password)"
Write-Host ""
Write-Host "Never commit the .jks or .base64.txt file to Git." -ForegroundColor Yellow
