@echo off

echo [+] Aktywacja srodowiska wirtualnego (env\Scripts\activate)...
CALL env\Scripts\activate

if "%VIRTUAL_ENV%"=="" (
    echo [!] Blad: Nie udalo sie aktywowac srodowiska wirtualnego.
    echo     Upewnij sie, ze plik run_game.bat jest w tym samym folderze co katalog 'env'.
    pause
    exit /b 1
) else (
    echo [+] Srodowisko wirtualne aktywowane: %VIRTUAL_ENV%
)


echo [+] Zmiana katalogu na VampireGame...
cd VampireGame

if not exist "." (
    echo [!] Blad: Nie mozna przejsc do katalogu 'VampireGame'.
    pause
    exit /b 1
)


echo [+] Zmiana katalogu na drugi VampireGame...
cd VampireGame

if not exist "VampireGame.py" (
    echo [!] Blad: Nie mozna przejsc do drugiego katalogu 'VampireGame' lub nie znaleziono pliku VampireGame.py.
    pause
    exit /b 1
)


echo [+] Uruchamianie gry (python VampireGame.py)...
python VampireGame.py

echo.
echo [+] Gra zakonczona. Nacisnij dowolny klawisz, aby zamknac to okno...
pause