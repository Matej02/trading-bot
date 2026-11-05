@echo off
rem Spousti live test FM strategii na MT5 DEMU (run_fm_demo.py --live).
rem Spousti ho zastupce "FM demo live" ve slozce Po spusteni (po prihlaseni); lze spustit i rucne dvojklikem.
rem Konec: Ctrl-C v tomto okne (a potvrdit Y). Druha instance se sama ukonci (ochrana v runneru).
title FM demo live
cd /d "D:\Trading bot"
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
