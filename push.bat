@echo off
setlocal EnableDelayedExpansion
title Git Push - progress-dashboard

echo ========================================================
echo   Pushing Process Dashboard to GitHub (progress-dashboard)
echo ========================================================
echo.

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: 1. Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in PATH!
    echo Please install Git from https://git-scm.com/ and try again.
    echo.
    pause
    exit /b 1
)

:: 2. Check if git repo exists
if not exist ".git" (
    echo [INFO] Initializing new git repository...
    git init -b main
    echo.
)

:: 3. Check for remote origin
git remote get-url origin >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] No remote 'origin' configured yet.
    echo.
    set /p REPO_URL="Enter your GitHub repository URL (e.g. https://github.com/USERNAME/progress-dashboard.git): "
    if "!REPO_URL!"=="" (
        echo [ERROR] No remote URL provided. Aborting push.
        pause
        exit /b 1
    )
    git remote add origin !REPO_URL!
    echo [OK] Remote origin set to: !REPO_URL!
    echo.
) else (
    for /f "delims=" %%u in ('git remote get-url origin') do set CURRENT_REMOTE=%%u
    echo [INFO] Remote origin: !CURRENT_REMOTE!
    echo.
)

:: 4. Show status
echo [INFO] Checking status...
git status -s
echo.

:: 5. Add all files
echo [INFO] Staging files...
git add .

:: 6. Check if anything is staged to commit
git diff --cached --quiet
if %ERRORLEVEL% equ 0 (
    echo [INFO] No new changes to commit.
) else (
    set DEFAULT_MSG=Update progress-dashboard: %DATE% %TIME%
    set /p COMMIT_MSG="Enter commit message [Press Enter for default: '!DEFAULT_MSG!']: "
    if "!COMMIT_MSG!"=="" set COMMIT_MSG=!DEFAULT_MSG!
    
    echo.
    echo [INFO] Committing changes...
    git commit -m "!COMMIT_MSG!"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Commit failed!
        pause
        exit /b 1
    )
)

:: 7. Ensure branch is main
git branch -M main

:: 8. Push to GitHub
echo.
echo ========================================================
echo   Pushing branch 'main' to origin...
echo ========================================================
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Successfully pushed to progress-dashboard!
) else (
    echo.
    echo [WARNING] Git push encountered an issue.
    echo Possible causes:
    echo  1. Remote has changes you don't have locally (try: git pull --rebase origin main)
    echo  2. Authentication required (GitHub Personal Access Token or SSH key)
    echo  3. Repository does not exist on GitHub yet (create 'progress-dashboard' on GitHub first)
)

echo.
pause
