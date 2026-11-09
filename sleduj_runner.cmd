@echo off
rem Okno se zivym logem runneru FM demo (runner bezi na pozadi). Zavrenim okna se runner NEVYPINA.
title FM demo live - log
chcp 65001 >nul
powershell -NoProfile -Command "Get-Content -Path 'D:\Trading bot\fm_demo_log.txt' -Tail 40 -Wait -Encoding UTF8"
