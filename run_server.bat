@echo off
title KSFCTA Portal - Development Server
echo =====================================================================
echo  KERALA SELF FINANCING COLLEGE TEACHERS' ASSOCIATION (KSFCTA)
echo  Membership Campaign 2026 Web Application
echo =====================================================================
echo.
echo  Website URL : http://127.0.0.1:8000/
echo  Admin Login : http://127.0.0.1:8000/login/
echo  Username    : shafi
echo  Password    : shafi@pulpara
echo.
echo  Starting server now...
echo =====================================================================
python manage.py runserver 127.0.0.1:8000
pause
