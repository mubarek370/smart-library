@echo off
echo ============================================
echo   Smart Library Management System
echo ============================================
echo.
echo Starting server...
echo Open your browser and go to:
echo   http://127.0.0.1:8080
echo.
echo Press Ctrl+C to stop the server.
echo.

call .venv\Scripts\activate
python manage.py runserver 8080
pause
