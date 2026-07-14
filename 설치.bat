@echo off
chcp 65001 > nul
echo =============================================
echo  필요한 패키지를 설치합니다...
echo =============================================
pip install -r requirements.txt
echo.
echo 설치 완료! 이제 실행.bat 을 더블클릭하세요.
pause
