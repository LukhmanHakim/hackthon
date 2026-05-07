@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  run_deployment.bat
REM  Args:  %1 = full project folder path
REM         %2 = project name  (used as DB name for sqlcmd)
REM         %3 = client name
REM ============================================================

set "PROJECT_PATH=%~1"
set "PROJECT_NAME=%~2"
set "CLIENT=%~3"

echo ============================================================
echo  Deployment Start : %DATE% %TIME%
echo  Project          : %PROJECT_NAME%
echo  Client           : %CLIENT%
echo  Path             : %PROJECT_PATH%
echo ============================================================

REM -- Validate path -------------------------------------------
if not exist "%PROJECT_PATH%" (
    echo [ERROR] Project path not found: %PROJECT_PATH%
    exit /b 1
)

cd /d "%PROJECT_PATH%"

REM -- Git pull ------------------------------------------------
echo [GIT] Pulling latest changes from origin/main ...
git pull origin main
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] git pull failed
    exit /b 1
)
echo [GIT] Pull successful

REM -- Execute SQL scripts ------------------------------------
if exist "*.sql" (
    echo [SQL] Executing SQL scripts ...
    for %%F in (*.sql) do (
        echo [SQL] Running: %%F
        sqlcmd -S localhost -E -d "%PROJECT_NAME%" -i "%%F"
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] SQL script failed: %%F
            exit /b 1
        )
        echo [SQL] Done: %%F
    )
    echo [SQL] All scripts executed successfully
) else (
    echo [SQL] No .sql files found — skipping SQL step
)

echo ============================================================
echo  Deployment End : %DATE% %TIME%
echo  Status         : SUCCESS
echo ============================================================
exit /b 0
