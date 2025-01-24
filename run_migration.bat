@echo off
SETLOCAL EnableDelayedExpansion

echo Available Migration Checklists:
echo --------------------------------

SET count=0
for %%i in (.checklists\*.json) do (
    set /a count+=1
    echo   !count!. %%~ni
    set "checklist_!count!=%%~ni"
)

if %count%==0 (
    echo No JSON checklists found in .checklists directory.
    exit /b 1
)

echo.
echo Actions:
echo 1. Run checklist
echo 2. Check status
echo.
set /p action="Select action (1-2): "

if "!action!"=="" (
    echo No action selected.
    exit /b 1
)

if !action! gtr 2 (
    echo Invalid action.
    exit /b 1
)

echo.
set /p choice="Select a checklist by number (1-!count!): "

if "!choice!"=="" (
    echo No checklist selected.
    exit /b 1
)

if !choice! gtr !count! (
    echo Invalid selection.
    exit /b 1
)

SET selected_checklist=!checklist_%choice%!

echo.
if "!action!"=="1" (
    echo Running checklist: %selected_checklist%
    echo --------------------------------
    python orchestrator.py --checklist %selected_checklist%
) else (
    echo Checking status of: %selected_checklist%
    echo --------------------------------
    python orchestrator.py --checklist %selected_checklist% --status
)

if errorlevel 1 (
    echo.
    echo ❌ Operation failed.
    exit /b 1
) else (
    if "!action!"=="1" (
        echo.
        echo ✅ Checklist execution completed successfully.
    )
)

ENDLOCAL 