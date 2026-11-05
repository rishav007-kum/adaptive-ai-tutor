$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.desktop-venv\Scripts\python.exe'
$basePython = @(
    (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python312\python.exe'),
    (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python313\python.exe'),
    (Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python314\python.exe')
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $basePython) { throw 'Python 3.10 or later was not found. Install Python and retry.' }

if (-not (Test-Path $python) -or -not (Test-Path (Join-Path $root '.desktop-venv\pyvenv.cfg'))) {
    Write-Host 'Creating the desktop Python environment...'
    & $basePython -m venv --clear --system-site-packages --without-pip (Join-Path $root '.desktop-venv')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $python)) { throw 'Could not create the desktop Python environment.' }
}

$stamp = Join-Path $root '.desktop-venv\dependencies-installed'
if (-not (Test-Path $stamp)) {
    Write-Host 'Installing the tutor and desktop dependencies...'
    $packages = Join-Path $root '.desktop-venv\Lib\site-packages'
    New-Item -ItemType Directory -Path $packages -Force | Out-Null
    & $basePython -m pip install --target $packages -r (Join-Path $root 'backend\requirements.txt') -r (Join-Path $PSScriptRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    New-Item -ItemType File -Path $stamp -Force | Out-Null
}

if (-not (Test-Path (Join-Path $root 'backend\.env'))) {
    $envFile = Join-Path $root 'backend\.env'
    Copy-Item (Join-Path $root 'backend\.env.example') $envFile
    $secret = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $contents = Get-Content -LiteralPath $envFile -Raw
    $contents = [regex]::Replace($contents, '(?m)^SECRET_KEY=.*$', "SECRET_KEY=$secret")
    Set-Content -LiteralPath $envFile -Value $contents -NoNewline
    Write-Host 'Created backend\.env with a fresh private signing key.' -ForegroundColor Green
}

Write-Host 'Starting Learnwell Adaptive AI Tutor...'
& $python (Join-Path $PSScriptRoot 'run_desktop.py')
exit $LASTEXITCODE
