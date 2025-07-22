#!/bin/bash

# =============================================================================
# SHOPLIFTING DETECTION SYSTEM - DEVELOPMENT SETUP SCRIPT
# =============================================================================
# This script sets up a complete development environment
# Usage: ./scripts/setup_dev.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python3 not found"
        return 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv .venv
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    source .venv/bin/activate

    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip

    # Install dependencies
    print_status "Installing requirements..."
    pip install -r requirements.txt

    print_success "Python dependencies installed"
}

# Function to setup configuration files
setup_config() {
    print_status "Setting up configuration files..."

    # Copy environment variables
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Created .env file from example"
        print_warning "Please edit .env file with your specific configuration"
    else
        print_warning ".env file already exists"
    fi

    # Copy main configuration
    if [ ! -f "config/config.yaml" ]; then
        cp config/config.example.yaml config/config.yaml
        print_success "Created config/config.yaml from example"
    else
        print_warning "config/config.yaml already exists"
    fi

    # Copy Alembic configuration
    if [ ! -f "alembic.ini" ] && [ -f "alembic.example.ini" ]; then
        cp alembic.example.ini alembic.ini
        print_success "Created alembic.ini from example"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    directories=(
        "logs"
        "uploads"
        "uploads/videos"
        "temp_frames"
        "output"
        "keys"
        "data"
        "models"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done

    print_success "Directories created"
}

# Function to generate RSA keys
generate_keys() {
    print_status "Generating RSA key pairs for encryption..."

    if [ ! -f "keys/private_key.pem" ] || [ ! -f "keys/public_key.pem" ]; then
        # Generate private key
        openssl genpkey -algorithm RSA -out keys/private_key.pem -pkcs8 -aes-256-cbc -pass pass:development_key_password 2>/dev/null || {
            # Fallback to older OpenSSL syntax
            openssl genrsa -aes256 -passout pass:development_key_password -out keys/private_key.pem 2048
        }

        # Generate public key
        openssl rsa -pubout -in keys/private_key.pem -passin pass:development_key_password -out keys/public_key.pem

        print_success "RSA keys generated"
        print_warning "Development keys created with password: development_key_password"
        print_warning "Change this for production use!"
    else
        print_warning "RSA keys already exist"
    fi
}

# Function to setup database with Docker
setup_database_docker() {
    print_status "Setting up database with Docker..."

    if command_exists docker && command_exists docker-compose; then
        # Start only the database services
        docker-compose -f docker-compose.dev.yml up -d postgres redis

        # Wait for database to be ready
        print_status "Waiting for database to be ready..."
        sleep 10

        # Run database migrations
        print_status "Running database migrations..."
        source .venv/bin/activate
        alembic upgrade head

        print_success "Database setup complete"
    else
        print_error "Docker or docker-compose not found"
        print_status "Please install Docker and Docker Compose, or setup PostgreSQL manually"
        return 1
    fi
}

# Function to setup database manually
setup_database_manual() {
    print_status "Manual database setup instructions:"
    print_status "1. Install PostgreSQL 12+"
    print_status "2. Create database: createdb shoplifting_detection"
    print_status "3. Update DATABASE_URL in .env file"
    print_status "4. Run migrations: alembic upgrade head"
}

# Function to download sample model (placeholder)
setup_model() {
    print_status "Setting up AI model..."

    if [ ! -f "models/lrcn_160S_90_90Q.h5" ]; then
        print_warning "LRCN model file not found"
        print_status "Please place your trained model file at: models/lrcn_160S_90_90Q.h5"
        print_status "Or update the MODEL_PATH in your configuration"

        # Create a placeholder file
        touch models/lrcn_160S_90_90Q.h5
        echo "# This is a placeholder model file" > models/README.md
        echo "# Place your actual LRCN model (lrcn_160S_90_90Q.h5) in this directory" >> models/README.md

        print_status "Created placeholder model file"
    else
        print_success "Model file found"
    fi
}

# Function to install Node.js dependencies (if frontend exists)
setup_frontend() {
    if [ -f "package.json" ]; then
        print_status "Setting up frontend dependencies..."

        if command_exists npm; then
            npm install
            print_success "Frontend dependencies installed"
        elif command_exists yarn; then
            yarn install
            print_success "Frontend dependencies installed"
        else
            print_warning "npm or yarn not found, skipping frontend setup"
        fi
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    source .venv/bin/activate

    if [ -d "tests" ]; then
        python -m pytest tests/ -v
        print_success "Tests completed"
    else
        print_warning "No tests directory found"
    fi
}

# Main setup function
main() {
    echo "======================================================================="
    echo "    SHOPLIFTING DETECTION SYSTEM - DEVELOPMENT SETUP"
    echo "======================================================================="
    echo ""

    print_status "Starting development environment setup..."

    # Check prerequisites
    print_status "Checking prerequisites..."

    if ! check_python_version; then
        print_error "Please install Python 3.8 or higher"
        exit 1
    fi

    if ! command_exists git; then
        print_error "Git not found. Please install Git"
        exit 1
    fi

    # Setup steps
    create_directories
    setup_config
    generate_keys
    install_python_deps
    setup_model
    setup_frontend

    # Database setup
    print_status "Choose database setup method:"
    echo "1) Docker (recommended)"
    echo "2) Manual setup"
    read -p "Enter choice (1 or 2): " db_choice

    case $db_choice in
        1)
            setup_database_docker
            ;;
        2)
            setup_database_manual
            ;;
        *)
            print_warning "Invalid choice, skipping database setup"
            ;;
    esac

    # Optional: Run tests
    read -p "Run tests? (y/N): " run_test_choice
    if [[ $run_test_choice =~ ^[Yy]$ ]]; then
        run_tests
    fi

    # Setup complete
    echo ""
    echo "======================================================================="
    print_success "DEVELOPMENT ENVIRONMENT SETUP COMPLETE!"
    echo "======================================================================="
    echo ""

    print_status "Next steps:"
    echo "1. Edit .env file with your specific configuration"
    echo "2. Place your LRCN model file in models/ directory"
    echo "3. Start the development server:"
    echo "   source .venv/bin/activate"
    echo "   python api_server.py"
    echo ""
    echo "4. Access the application:"
    echo "   - API Documentation: http://localhost:8001/docs"
    echo "   - Database Admin: http://localhost:8080 (if using Docker)"
    echo "   - Kibana Dashboard: http://localhost:5601 (if using Docker)"
    echo ""

    print_status "For Docker users:"
    echo "   docker-compose -f docker-compose.dev.yml up -d    # Start all services"
    echo "   docker-compose -f docker-compose.dev.yml down     # Stop all services"
    echo ""

    print_warning "Remember to:"
    echo "- Change default passwords in production"
    echo "- Update JWT secret keys"
    echo "- Configure proper database credentials"
    echo "- Set up proper SSL certificates for production"
}

# Run main function
main "$@"
