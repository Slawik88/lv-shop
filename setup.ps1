# =============================================================================
#  LV Shop — Скрипт полной установки проекта на новом ПК
#  Запуск: правой кнопкой → "Выполнить с помощью PowerShell"
#          ИЛИ в PowerShell: .\setup.ps1
# =============================================================================

$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Цветной вывод ────────────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK    { param($msg) Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "    [!]  $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "`n[ОШИБКА] $msg" -ForegroundColor Red; exit 1 }

Clear-Host
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "         LV Shop — Установка проекта" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 0: Политика выполнения PowerShell
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Проверка политики выполнения PowerShell"
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq 'Restricted' -or $policy -eq 'AllSigned') {
    Write-Warn "Политика '$policy' — меняем на RemoteSigned для текущего пользователя"
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-OK "Политика изменена"
} else {
    Write-OK "Политика '$policy' — подходит"
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 1: Проверка Python
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Проверка Python"

$pythonCmd = $null
foreach ($cmd in @('python', 'python3', 'py')) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match 'Python (\d+)\.(\d+)') {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $pythonCmd = $cmd
                Write-OK "Найден: $ver (команда: $cmd)"
                break
            } else {
                Write-Warn "Найден $ver — нужен 3.10+, продолжаем поиск"
            }
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-Host @"

    Python 3.10+ не найден!
    Скачайте и установите с https://www.python.org/downloads/
    При установке ОБЯЗАТЕЛЬНО отметьте "Add Python to PATH"
    
    После установки Python запустите этот скрипт снова.
"@ -ForegroundColor Red
    Write-Fail "Python не найден"
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 2: Проверка pip
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Проверка pip"
try {
    $pipVer = & $pythonCmd -m pip --version 2>&1
    Write-OK "pip: $pipVer"
} catch {
    Write-Fail "pip не найден. Попробуйте: $pythonCmd -m ensurepip --upgrade"
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 3: Виртуальное окружение
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Создание виртуального окружения (venv)"

$venvDir = Join-Path $ProjectDir 'venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$venvPip    = Join-Path $venvDir 'Scripts\pip.exe'

if (Test-Path $venvPython) {
    Write-OK "venv уже существует, пропускаем создание"
} else {
    & $pythonCmd -m venv $venvDir
    if (-not (Test-Path $venvPython)) {
        Write-Fail "Не удалось создать venv"
    }
    Write-OK "venv создан: $venvDir"
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 4: Обновление pip внутри venv
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Обновление pip в venv"
& $venvPython -m pip install --upgrade pip --quiet
Write-OK "pip обновлён"

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 5: Установка зависимостей
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Установка зависимостей из requirements.txt"

$reqFile = Join-Path $ProjectDir 'requirements.txt'
if (-not (Test-Path $reqFile)) {
    Write-Fail "Файл requirements.txt не найден в $ProjectDir"
}

& $venvPip install -r $reqFile
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Ошибка установки зависимостей"
}
Write-OK "Все зависимости установлены"

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 6: Создание нужных папок
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Создание папок static и media"

foreach ($dir in @('static', 'media')) {
    $path = Join-Path $ProjectDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
        Write-OK "Создана папка: $dir\"
    } else {
        Write-OK "Папка уже есть: $dir\"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 7: Применение миграций
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Применение миграций базы данных"

Set-Location $ProjectDir
& $venvPython manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Ошибка при применении миграций"
}
Write-OK "Миграции применены"

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 8: Создание суперпользователя
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Создание суперпользователя для Admin-панели"

$createAdminCode = @"
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser('admin', 'admin@lvshop.ru', 'admin1234')
    print('CREATED')
else:
    print('EXISTS')
"@

$result = $createAdminCode | & $venvPython manage.py shell 2>&1 | Select-String -Pattern 'CREATED|EXISTS'
if ($result -match 'CREATED') {
    Write-OK "Суперпользователь создан: логин=admin, пароль=admin1234"
    Write-Warn "ВАЖНО: смените пароль после первого входа!"
} elseif ($result -match 'EXISTS') {
    Write-OK "Суперпользователь 'admin' уже существует"
} else {
    Write-Warn "Не удалось проверить суперпользователя — создайте вручную:"
    Write-Warn "  $venvPython manage.py createsuperuser"
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 9: Тестовые данные (опционально)
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Загрузка тестовых данных"

$answer = Read-Host "    Загрузить демо-товары и категории? (y/n)"
if ($answer -match '^[YyДд]') {
    & $venvPython manage.py seed_data
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Тестовые данные загружены"
    } else {
        Write-Warn "Не удалось загрузить тестовые данные (не критично)"
    }
} else {
    Write-OK "Пропускаем тестовые данные"
}

# ─────────────────────────────────────────────────────────────────────────────
# ШАГ 10: Создание ярлыка запуска сервера
# ─────────────────────────────────────────────────────────────────────────────
Write-Step "Создание вспомогательных файлов"

# run.bat — двойной клик для запуска
$runBat = Join-Path $ProjectDir 'run.bat'
@"
@echo off
cd /d "%~dp0"
echo ===================================================
echo  LV Shop - Запуск сервера
echo  Откройте браузер: http://127.0.0.1:8000/
echo  Панель управления: http://127.0.0.1:8000/manager/
echo  Django Admin:      http://127.0.0.1:8000/admin/
echo  Для остановки нажмите Ctrl+C
echo ===================================================
venv\Scripts\python.exe manage.py runserver
pause
"@ | Set-Content -Path $runBat -Encoding UTF8
Write-OK "Создан run.bat (двойной клик для запуска сервера)"

# ─────────────────────────────────────────────────────────────────────────────
# ФИНАЛ
# ─────────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Запуск сервера (2 способа):" -ForegroundColor White
Write-Host ""
Write-Host "  1. Двойной клик на  run.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. В PowerShell:" -ForegroundColor Yellow
Write-Host "       cd $ProjectDir" -ForegroundColor Gray
Write-Host "       .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "       python manage.py runserver" -ForegroundColor Gray
Write-Host ""
Write-Host "  Адреса после запуска:" -ForegroundColor White
Write-Host "    Сайт:               http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "    Панель управления:  http://127.0.0.1:8000/manager/" -ForegroundColor Cyan
Write-Host "    Django Admin:       http://127.0.0.1:8000/admin/" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Данные для входа в Admin:" -ForegroundColor White
Write-Host "    Логин:  admin" -ForegroundColor Yellow
Write-Host "    Пароль: admin1234" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Для открытия в VS Code:" -ForegroundColor White
Write-Host "    code $ProjectDir" -ForegroundColor Gray
Write-Host ""

$openVSCode = Read-Host "Открыть проект в VS Code сейчас? (y/n)"
if ($openVSCode -match '^[YyДд]') {
    try {
        code $ProjectDir
        Write-OK "VS Code открыт"
    } catch {
        Write-Warn "VS Code не найден в PATH — откройте вручную: File → Open Folder"
    }
}

Write-Host ""
Write-Host "  Нажмите Enter для выхода..." -ForegroundColor Gray
Read-Host
