#!/bin/bash

# Enhanced Detection Metrics System Deployment Script
# This script deploys the complete enhanced detection metrics system

set -e  # Exit on any error

echo "[DEPLOY] Deploying Enhanced Detection Metrics System"
echo "================================================"

# Configuration
ELASTICSEARCH_URL=${ELASTICSEARCH_URL:-"http://localhost:9200"}
KIBANA_URL=${KIBANA_URL:-"http://localhost:5601"}
LOGSTASH_CONFIG="logstash/pipeline/logstash.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if a service is running
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    print_status "Checking $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is running"
            return 0
        fi
        
        print_status "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name is not responding after $max_attempts attempts"
    return 1
}

# Function to start ELK stack (if using Docker)
start_elk_stack() {
    print_status "Starting ELK stack with Docker Compose..."
    
    if [ -f "docker-compose.yml" ]; then
        # Check if ELK services are defined in docker-compose
        if grep -q "elasticsearch\|kibana\|logstash" docker-compose.yml; then
            docker-compose up -d elasticsearch kibana logstash
            print_success "ELK stack started with Docker Compose"
        else
            print_warning "ELK services not found in docker-compose.yml"
            print_status "Please start Elasticsearch, Kibana, and Logstash manually"
        fi
    else
        print_warning "docker-compose.yml not found"
        print_status "Please start Elasticsearch, Kibana, and Logstash manually"
    fi
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        python -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate || source .venv/Scripts/activate
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python requirements..."
        pip install -r requirements.txt
        print_success "Python requirements installed"
    fi
}

# Function to run the detection metrics setup
run_setup_script() {
    print_status "Running detection metrics setup..."
    
    if [ -f "scripts/setup_detection_metrics.py" ]; then
        python scripts/setup_detection_metrics.py
        print_success "Detection metrics setup completed"
    else
        print_error "Setup script not found: scripts/setup_detection_metrics.py"
        return 1
    fi
}

# Function to validate Logstash configuration
validate_logstash_config() {
    print_status "Validating Logstash configuration..."
    
    if [ -f "$LOGSTASH_CONFIG" ]; then
        print_success "Logstash configuration file found"
        
        # Basic validation - check for required sections
        if grep -q "input\|filter\|output" "$LOGSTASH_CONFIG"; then
            print_success "Logstash configuration appears valid"
        else
            print_warning "Logstash configuration may be incomplete"
        fi
    else
        print_error "Logstash configuration not found: $LOGSTASH_CONFIG"
        return 1
    fi
}

# Function to check detection system integration
check_detection_integration() {
    print_status "Checking detection system integration..."
    
    # Check if detection metrics module exists
    if [ -f "src/detection_metrics.py" ]; then
        print_success "Detection metrics module found"
    else
        print_error "Detection metrics module not found: src/detection_metrics.py"
        return 1
    fi
    
    # Check if tasks.py has been updated
    if grep -q "detection_metrics" "src/tasks.py" 2>/dev/null; then
        print_success "Celery tasks updated with metrics logging"
    else
        print_warning "Celery tasks may not be integrated with metrics logging"
    fi
    
    # Check if frame processor has been updated
    if grep -q "detection_metrics" "src/frame_processor.py" 2>/dev/null; then
        print_success "Frame processor updated with metrics logging"
    else
        print_warning "Frame processor may not be integrated with metrics logging"
    fi
}

# Function to display post-deployment information
show_post_deployment_info() {
    print_success "Enhanced Detection Metrics System Deployed Successfully!"
    echo ""
    echo "[ACCESS] URLs:"
    echo "   Elasticsearch: $ELASTICSEARCH_URL"
    echo "   Kibana:        $KIBANA_URL"
    echo ""
    echo "[DASHBOARDS] Kibana Dashboards:"
    echo "   • Enhanced Detection System Dashboard"
    echo "   • Camera System Overview (legacy)"
    echo ""
    echo "[METRICS] Key Metrics Being Tracked:"
    echo "   • Detection confidence and accuracy"
    echo "   • System performance (FPS, latency)"
    echo "   • Camera health and connectivity"
    echo "   • Alert triggers and responses"
    echo ""
    echo "[ALERTS] Alerting:"
    echo "   • High detection rate alerts"
    echo "   • System performance degradation"
    echo "   • Camera offline notifications"
    echo "   • Model drift detection"
    echo ""
    echo "[DOCS] Documentation:"
    echo "   • Read docs/DETECTION_METRICS_GUIDE.md for detailed usage"
    echo "   • Check kibana/detection_metrics_alerting.json for alert configs"
    echo ""
    echo "[NEXT] Next Steps:"
    echo "   1. Start your camera detection system"
    echo "   2. Monitor incoming metrics in Kibana"
    echo "   3. Customize alert thresholds as needed"
    echo "   4. Set up email notifications for alerts"
    echo ""
}

# Main deployment flow
main() {
    print_status "Starting Enhanced Detection Metrics System deployment..."
    
    # Setup Python environment
    setup_python_env
    
    # Start ELK stack (if using Docker)
    start_elk_stack
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check Elasticsearch
    if ! check_service "Elasticsearch" "$ELASTICSEARCH_URL"; then
        print_error "Deployment failed: Elasticsearch not available"
        exit 1
    fi
    
    # Check Kibana
    if ! check_service "Kibana" "$KIBANA_URL/api/status"; then
        print_warning "Kibana not available - dashboard import may fail"
    fi
    
    # Validate Logstash configuration
    validate_logstash_config
    
    # Run setup script
    run_setup_script
    
    # Check integration
    check_detection_integration
    
    # Show post-deployment information
    show_post_deployment_info
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@" 