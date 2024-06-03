@echo off
setlocal enabledelayedexpansion

REM Read the addresses from the file
set ADDRESSES=
for /f "tokens=1,2" %%i in (src\address.txt) do (
    if not defined ADDRESSES (
        set ADDRESSES=%%i:%%j
    ) else (
        set ADDRESSES=!ADDRESSES!,%%i:%%j
    )
)

REM Check if "membership" argument is provided
if "%1" == "membership" (
    REM Get the first address from the list
    for /f "tokens=1,2" %%i in (src\address.txt) do (
        set FIRST_ADDRESS=%%i %%j
        goto :start_membership
    )
    
    :start_membership
    REM Start the first server without contact address
    echo Starting leader server with address %FIRST_ADDRESS%
    start cmd /k python src\server.py %FIRST_ADDRESS% membership
    
    REM Start the rest of the servers with the first address as the contact address
    for /f "skip=1 tokens=1,2" %%i in (src\address.txt) do (
        echo Starting server with address %%i:%%j and contact %FIRST_ADDRESS%
        start cmd /k python src\server.py %%i %%j %FIRST_ADDRESS% membership
    )
    exit /b
) else (
    REM Default behavior
    REM Start the Raft servers with addresses from the file
    echo Starting servers with addresses from the file
    for /f "tokens=1,2" %%i in (src\address.txt) do (
        @REM echo and run the file
        echo Starting server with address %%i:%%j
        start cmd /k python src\server.py %%i %%j !ADDRESSES!
        @REM goto end
    )
)

:end