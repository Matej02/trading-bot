@echo off
rem Spousti live test FM strategii na MT5 DEMU (run_fm_demo.py --live).
rem Spousti ho zastupce "FM demo live" ve slozce Po spusteni (po prihlaseni); lze spustit i rucne dvojklikem.
rem Konec: Ctrl-C v tomto okne (a potvrdit Y). Druha instance se sama ukonci (ochrana v runneru).
title FM demo live
cd /d "D:\Trading bot"
rem --- Prihlaseni MT5 (2026-11-10) ---
rem MT5 spusteny z aplikace Claude (balickova aplikace Windows) uklada prihlaseni do virtualni kopie AppData
rem (AppData\Local\Packages\Claude_...\LocalCache\Roaming). MT5 spusteny Windows ho proto nevidel a chtel "Otevrit ucet".
rem Kopie funkcniho prihlaseni je v scratch\mt5_config_claude; jednou se prenese do skutecneho AppData (puvodni se zalohuji).
set "SRC=D:\Trading bot\scratch\mt5_config_claude"
set "CFG=%APPDATA%\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\config"
if not exist "%SRC%\accounts.dat" goto prihlaseni_konec
if exist "%SRC%\preneseno.txt" goto prihlaseni_konec
tasklist /fi "imagename eq terminal64.exe" 2>nul | find /i "terminal64.exe" >nul
if not errorlevel 1 (
  echo MT5 uz bezi - prihlaseni ted neprenasim. Zavri MT5 a spust znovu.
  goto prihlaseni_konec
)
if not exist "%SRC%\zaloha_puvodni" mkdir "%SRC%\zaloha_puvodni"
for %%F in (accounts.dat servers.dat common.ini) do if exist "%CFG%\%%F" copy /y "%CFG%\%%F" "%SRC%\zaloha_puvodni\" >nul
for %%F in (accounts.dat servers.dat common.ini) do copy /y "%SRC%\%%F" "%CFG%\" >nul
echo Prihlaseni MT5 preneseno do %CFG%
echo preneseno %date% %time% > "%SRC%\preneseno.txt"
:prihlaseni_konec
echo Cekam 60 s na sit a MT5 po prihlaseni...
timeout /t 60 /nobreak >nul
set N=0
:loop
python -u "D:\Trading bot\run_fm_demo.py" --live
set /a N+=1
if %N% GEQ 30 goto konec
echo Runner skoncil (pokus %N%/30), restart za 60 s. Ctrl-C = konec.
timeout /t 60 /nobreak >nul
goto loop
:konec
echo Runner skoncil 30x po sobe, dalsi restart se nedela. Zkontroluj fm_demo_log.txt.
powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [void][System.Windows.MessageBox]::Show('Runner FM demo skoncil 30x po sobe a dal se nespousti. Zkontroluj, ze bezi MT5, a log fm_demo_log.txt v D:\Trading bot. Znovu spustis dvojklikem na start_fm_demo.cmd.', 'FM demo live - POZOR')"
pause
