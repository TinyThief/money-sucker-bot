@echo off
echo 💻 Запускаю торгового бота Money Sucker Bot и мониторинг Watchdog...

:: Активация виртуального окружения (если нужно)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: Запуск бота в отдельном окне
start "Money Sucker Bot" cmd /k "python launcher_async.py"

:: Запуск watchdog в отдельном окне
start "Watchdog" cmd /k "python watchdog.py"

exit
