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
    goto :start_client
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
    goto :start_client
)

:start_client
REM Get the first address from the list for the client
for /f "tokens=1,2" %%i in (src\address.txt) do (
    set CLIENT_ADDRESS=%%i %%j
    goto :run_client
)

:run_client
REM Start the client with the first address
echo Starting client, connecting to %CLIENT_ADDRESS%
start cmd /k python src\client.py %CLIENT_ADDRESS%
exit /b

:end