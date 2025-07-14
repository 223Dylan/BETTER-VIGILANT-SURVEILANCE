@echo off
REM =============================================================================
REM SHOPLIFTING DETECTION SYSTEM - DEVELOPMENT SETUP SCRIPT (WINDOWS)
REM =============================================================================
REM This script sets up a complete development environment on Windows
REM Usage: scripts\setup_dev.bat

setlocal enabledelayedexpansion

echo =======================================================================
echo     SHOPLIFTING DETECTION SYSTEM - DEVELOPMENT SETUP (WINDOWS)
echo =======================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8 or higher
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Found Python %PYTHON_VERSION%

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Git not found. Please install Git for Windows
    echo Download from: https://git-scm.com/download/win
)

echo [INFO] Starting development environment setup...

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "uploads\videos" mkdir uploads\videos
if not exist "temp_frames" mkdir temp_frames
if not exist "output" mkdir output
if not exist "keys" mkdir keys
if not exist "data" mkdir data
if not exist "models" mkdir models
echo [SUCCESS] Directories created

REM Setup configuration files
echo [INFO] Setting up configuration files...

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [SUCCESS] Created .env file from example
    echo [WARNING] Please edit .env file with your specific configuration
) else (
    echo [WARNING] .env file already exists
)

if not exist "config\config.yaml" (
    copy "config\config.example.yaml" "config\config.yaml" >nul
    echo [SUCCESS] Created config\config.yaml from example
) else (
    echo [WARNING] config\config.yaml already exists
)

REM Create virtual environment
echo [INFO] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo [INFO] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [SUCCESS] Python dependencies installed
) else (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

REM Setup model placeholder
echo [INFO] Setting up AI model...
if not exist "models\lrcn_160S_90_90Q.h5" (
    echo [WARNING] LRCN model file not found
    echo [INFO] Please place your trained model file at: models\lrcn_160S_90_90Q.h5
    
    REM Create placeholder file and README
    type nul > "models\lrcn_160S_90_90Q.h5"
    echo # This is a placeholder model file > "models\README.md"
    echo # Place your actual LRCN model (lrcn_160S_90_90Q.h5) in this directory >> "models\README.md"
    
    echo [INFO] Created placeholder model file
) else (
    echo [SUCCESS] Model file found
)

REM Check for Node.js and install frontend dependencies
where node >nul 2>&1
if %errorlevel% equ 0 (
    if exist "package.json" (
        echo [INFO] Installing frontend dependencies...
        npm install
        echo [SUCCESS] Frontend dependencies installed
    )
) else (
    echo [WARNING] Node.js not found, skipping frontend setup
    echo [INFO] Install Node.js from: https://nodejs.org/
)

REM Database setup options
echo.
echo [INFO] Choose database setup method:
echo 1) Docker Desktop (recommended)
echo 2) Manual PostgreSQL setup
echo 3) Skip database setup
set /p choice="Enter choice (1, 2, or 3): "

if "%choice%"=="1" (
    REM Check for Docker
    docker --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Starting database services with Docker...
        docker-compose -f docker-compose.dev.yml up -d postgres redis
        
        echo [INFO] Waiting for database to be ready...
        timeout /t 15 /nobreak >nul
        
        echo [INFO] Running database migrations...
        alembic upgrade head
        
        echo [SUCCESS] Database setup complete with Docker
    ) else (
        echo [ERROR] Docker not found. Please install Docker Desktop
        echo Download from: https://www.docker.com/products/docker-desktop
        echo [INFO] Falling back to manual setup instructions
        goto manual_db
    )
) else if "%choice%"=="2" (
    :manual_db
    echo [INFO] Manual database setup instructions:
    echo 1. Install PostgreSQL 12+ from: https://www.postgresql.org/download/windows/
    echo 2. Create database: createdb shoplifting_detection
    echo 3. Update DATABASE_URL in .env file
    echo 4. Run migrations: alembic upgrade head
) else (
    echo [INFO] Skipping database setup
)

REM Generate development keys (if OpenSSL is available)
where openssl >nul 2>&1
if %errorlevel% equ 0 (
    if not exist "keys\private_key.pem" (
        echo [INFO] Generating RSA key pairs for encryption...
        openssl genpkey -algorithm RSA -out keys\private_key.pem -pkcs8
        openssl rsa -pubout -in keys\private_key.pem -out keys\public_key.pem
        echo [SUCCESS] RSA keys generated
    ) else (
        echo [WARNING] RSA keys already exist
    )
) else (
    echo [WARNING] OpenSSL not found, skipping key generation
    echo [INFO] You can install OpenSSL or use Windows Subsystem for Linux
)

REM Test setup (optional)
echo.
set /p test_choice="Run tests? (y/N): "
if /i "%test_choice%"=="y" (
    if exist "tests" (
        echo [INFO] Running tests...
        python -m pytest tests\ -v
        echo [SUCCESS] Tests completed
    ) else (
        echo [WARNING] No tests directory found
    )
)

REM Setup complete message
echo.
echo =======================================================================
echo [SUCCESS] DEVELOPMENT ENVIRONMENT SETUP COMPLETE!
echo =======================================================================
echo.

echo [INFO] Next steps:
echo 1. Edit .env file with your specific configuration
echo 2. Place your LRCN model file in models\ directory
echo 3. Start the development server:
echo    .venv\Scripts\activate.bat
echo    python api_server.py
echo.
echo 4. Access the application:
echo    - API Documentation: http://localhost:8001/docs
echo    - Database Admin: http://localhost:8080 (if using Docker)
echo    - Kibana Dashboard: http://localhost:5601 (if using Docker)
echo.

echo [INFO] For Docker users:
echo    docker-compose -f docker-compose.dev.yml up -d    ^(Start all services^)
echo    docker-compose -f docker-compose.dev.yml down     ^(Stop all services^)
echo.

echo [WARNING] Remember to:
echo - Change default passwords in production
echo - Update JWT secret keys
echo - Configure proper database credentials
echo - Set up proper SSL certificates for production
echo.

echo [INFO] Development environment setup completed successfully!
echo Press any key to exit...
pause >nul 