@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo =============================================
echo  EP 자동 갱신 (1시간마다 ep.txt 갱신)
echo  종료하려면 이 창을 닫으세요.
echo =============================================
python scheduler.py
pause
