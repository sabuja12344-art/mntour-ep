@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo =============================================
echo  EP 한 번 생성 (ep.txt 파일이 만들어집니다)
echo =============================================
python crawler.py
pause
