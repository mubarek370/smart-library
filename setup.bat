@echo off
echo ============================================
echo   Smart Library Management System - Setup
echo ============================================
echo.

echo [1/3] Creating virtual environment...
python -m venv .venv
echo Done.
echo.

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate
echo Done.
echo.

echo [3/3] Installing dependencies...
pip install -r requirements.txt
echo Done.
echo.

echo ============================================
echo   Setup complete! Starting the server...
echo ============================================
echo.
echo Open your browser and go to:
echo   http://127.0.0.1:8080
echo.
echo Press Ctrl+C to stop the server.
echo.

python manage.py runserver 8080
pause
