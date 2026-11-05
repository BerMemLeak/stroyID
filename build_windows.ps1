param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'
Set-Location -LiteralPath $PSScriptRoot
$logs = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$transcript = Join-Path $logs ('build-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.txt')
Start-Transcript -Path $transcript -Force | Out-Null
$exitCode = 1
try {
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Требуется Windows x64.' }
    $nativeArch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    if ($nativeArch -ne 'AMD64') { throw 'Этот пакет предназначен для Windows x64 на Intel/AMD.' }
    Write-Host 'СтройИД: проверка Python, тесты, сборка и проверка EXE.'
    $vendorManifest = Join-Path $PSScriptRoot 'vendor\manifest.json'
    if (Test-Path -LiteralPath $vendorManifest) {
        Write-Host 'Проверяются библиотеки, включённые в полный архив.'
        $vendorFiles = Get-Content -LiteralPath $vendorManifest -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($item in $vendorFiles.files) {
            $localFile = Join-Path $PSScriptRoot $item.file
            if (-not (Test-Path -LiteralPath $localFile)) {
                throw ('В полном архиве отсутствует файл: ' + $item.file + '. Распакуйте архив полностью.')
            }
            if ((Get-FileHash -LiteralPath $localFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) {
                throw ('Повреждён файл в архиве: ' + $item.file + '. Распакуйте архив повторно.')
            }
        }
    }
    $python = $null
    $check = "import sys,struct; assert sys.version_info[:2] in [(3,12),(3,13)] and struct.calcsize('P')==8; print(sys.executable)"
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($version in @('-3.13', '-3.12')) {
            try { $found = & $launcher.Source $version -c $check 2>$null } catch { continue }
            if ($LASTEXITCODE -eq 0 -and $found) { $python = [string]($found | Select-Object -Last 1); break }
        }
    }
    $privatePython = Join-Path $env:LOCALAPPDATA 'StroyIDBuild\Python313\python.exe'
    if (-not $python -and (Test-Path -LiteralPath $privatePython)) {
        $found = & $privatePython -c $check
        if ($LASTEXITCODE -eq 0) { $python = $privatePython }
    }
    if (-not $python) {
        Write-Host 'Python не найден. Устанавливается отдельный Python для сборки СтройИД.'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $installer = Join-Path $PSScriptRoot 'vendor\python\python-3.13.16-amd64.exe'
        if (-not (Test-Path -LiteralPath $installer)) {
            $installer = Join-Path $logs 'python-3.13.16-amd64.exe'
            Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe' -OutFile $installer
        }
        $expected = 'fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b'
        if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
            throw 'Контрольная сумма установщика Python не совпала. Установка остановлена.'
        }
        $signature = Get-AuthenticodeSignature -LiteralPath $installer
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
            throw 'Не подтверждена цифровая подпись установщика Python.'
        }
        $target = Split-Path -Parent $privatePython
        $arguments = @('/passive','InstallAllUsers=0','Include_launcher=0','Include_test=0',
                       'Include_doc=0','Include_tcltk=0','Shortcuts=0','PrependPath=0','AssociateFiles=0',
                       ('TargetDir="' + $target + '"'))
        $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
        if ($process.ExitCode -notin @(0,3010) -or -not (Test-Path -LiteralPath $privatePython)) {
            throw ('Установка Python завершилась с кодом ' + $process.ExitCode)
        }
        $python = $privatePython
    }
    Write-Host ('Python: ' + $python)
    $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $python -m venv (Join-Path $PSScriptRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'Не удалось создать окружение сборки.' }
    }
    & $venvPython -c $check
    if ($LASTEXITCODE -ne 0) { throw 'Окружение .venv не подходит. Переименуйте .venv и повторите запуск.' }
    $wheels = Join-Path $PSScriptRoot 'vendor\wheels'
    if (Test-Path -LiteralPath $wheels) {
        Write-Host 'Устанавливаются библиотеки из полного архива.'
        & $venvPython -m pip install --no-index --find-links $wheels -r requirements-build.txt
    } else {
        & $venvPython -m pip install -r requirements-build.txt
    }
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось установить зависимости. Подробности выше в журнале.' }
    $buildOutput = Join-Path $logs 'build-output.txt'
    $buildErrors = Join-Path $logs 'build-errors.txt'
    Write-Host ('Начата сборка. Полный вывод: ' + $buildOutput)
    Write-Host 'Тесты и упаковка могут занять несколько минут. Не закрывайте окно.'
    $process = Start-Process -FilePath $venvPython -ArgumentList @('-u', 'tools\build_release.py') `
        -WorkingDirectory $PSScriptRoot -RedirectStandardOutput $buildOutput `
        -RedirectStandardError $buildErrors -NoNewWindow -Wait -PassThru
    foreach ($path in @($buildOutput, $buildErrors)) {
        if (Test-Path -LiteralPath $path) {
            Get-Content -LiteralPath $path -Encoding UTF8 | ForEach-Object { Write-Host $_ }
        }
    }
    if ($process.ExitCode -ne 0) {
        throw ('Сборка остановлена, код ' + $process.ExitCode + '. См. logs\build-errors.txt, logs\build-output.txt и release\build-report.json.')
    }
    $executable = Join-Path $PSScriptRoot 'release\StroyID.exe'
    Write-Host ('Готовое приложение: ' + $executable) -ForegroundColor Green
    Write-Host 'Для переноса нужен только release\StroyID.exe. Все библиотеки находятся внутри файла.'
    if (-not $NoLaunch) { Start-Process -FilePath $executable }
    $exitCode = 0
} catch {
    Write-Host ('Ошибка: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host ('Журнал: ' + $transcript)
} finally {
    Stop-Transcript | Out-Null
}
exit $exitCode
