@echo off
rem Spusti simulator jen na tomhle PC (bez Vercelu a bez prihlasovani): http://localhost:3000
rem Okno nech otevrene - zavrenim se simulator vypne.
cd /d "%~dp0"
title Simulator obchodovani - http://localhost:3000

if not exist node_modules (
  echo Prvni spusteni: instaluji knihovny...
  call npm install || goto chyba
)
echo Pripravuji aplikaci...
call npm run build || goto chyba

rem prohlizec se otevre, az server nabehne
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:3000"
echo.
echo Simulator bezi na http://localhost:3000  (zavrenim okna se vypne)
call npm start
goto :eof

:chyba
echo.
echo Neco se nepovedlo - text chyby je vyse.
pause
