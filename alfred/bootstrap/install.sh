#!/bin/bash
# Alfred installation script for Linux (Ubuntu/Debian/Raspberry Pi OS).
# Installs Ollama, pulls model, installs Obsidian, sets up vault, schedules automations, launches onboarding interface.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALFRED_ROOT="$(dirname "$SCRIPT_DIR")"
ALFRED_HOME="${ALFRED_HOME:-$HOME/Alfred}"
CONFIG_DIR="$ALFRED_HOME/config"
VAULT_DIR="$ALFRED_HOME/vault"
LOGS_DIR="$ALFRED_HOME/logs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Initialize logging
mkdir -p "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/alfred.log"

log_to_file() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if running on supported OS
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    log_error "This installer supports Linux only. For other OS, manual installation required."
    exit 1
fi

log_info "Starting Alfred installation..."
log_to_file "Installation started on $(uname -a)"

# Step 1: Install Ollama
if ! command -v ollama &> /dev/null; then
    log_info "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh >> "$LOG_FILE" 2>&1 || {
        log_error "Failed to install Ollama. Check $LOG_FILE for details."
        exit 1
    }
    log_info "Ollama installed"
else
    log_info "Ollama already installed"
fi

# Step 2: Start Ollama service (if not already running)
if ! pgrep -x "ollama" > /dev/null; then
    log_info "Starting Ollama service..."
    ollama serve >> "$LOG_FILE" 2>&1 &
    OLLAMA_PID=$!
    sleep 3
    log_to_file "Started Ollama with PID $OLLAMA_PID"
else
    log_info "Ollama is already running"
fi

# Step 3: Pull the model
log_info "Pulling SmolLM2 1.7B model (this may take a few minutes)..."
OLLAMA_API="${OLLAMA_API:-http://localhost:11434}"
export OLLAMA_API

timeout 600 ollama pull smollm2:1.7b >> "$LOG_FILE" 2>&1 || {
    log_warn "Model pull may still be in progress. Check $LOG_FILE."
}
log_info "Model ready"
log_to_file "SmolLM2 1.7B model pulled"

# Step 4: Install Obsidian (if not already installed)
if ! command -v obsidian &> /dev/null; then
    log_info "Installing Obsidian..."
    # Download AppImage
    OBSIDIAN_URL="https://github.com/obsidianmd/obsidian-releases/releases/download/latest/Obsidian-latest.AppImage"
    OBSIDIAN_PATH="/opt/Obsidian.AppImage"

    if command -v wget &> /dev/null; then
        sudo wget -q "$OBSIDIAN_URL" -O "$OBSIDIAN_PATH" >> "$LOG_FILE" 2>&1 || {
            log_warn "Failed to download Obsidian AppImage. Manual installation may be required."
        }
    elif command -v curl &> /dev/null; then
        sudo curl -fL "$OBSIDIAN_URL" -o "$OBSIDIAN_PATH" >> "$LOG_FILE" 2>&1 || {
            log_warn "Failed to download Obsidian AppImage. Manual installation may be required."
        }
    fi

    if [[ -f "$OBSIDIAN_PATH" ]]; then
        sudo chmod +x "$OBSIDIAN_PATH"
        log_info "Obsidian AppImage installed"
        log_to_file "Obsidian installed at $OBSIDIAN_PATH"
    fi
else
    log_info "Obsidian already installed"
fi

# Step 5: Copy vault structure
log_info "Setting up vault..."
mkdir -p "$ALFRED_HOME"/{vault,config,logs,automations,briefings}
mkdir -p "$VAULT_DIR"/{raw,wiki,_templates}

# Copy scaffold from repo if available
if [[ -d "$ALFRED_ROOT/vault" ]]; then
    cp -r "$ALFRED_ROOT/vault"/* "$VAULT_DIR/" 2>/dev/null || true
    log_info "Vault scaffolding copied"
fi

log_to_file "Vault initialized at $VAULT_DIR"

# Step 6: Install Python dependencies
log_info "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install flask requests --quiet 2>> "$LOG_FILE" || {
        log_warn "pip3 install had issues. Check $LOG_FILE."
    }
    log_info "Python dependencies installed"
fi

# Step 7: Copy automation scripts
log_info "Installing automations..."
if [[ -d "$ALFRED_ROOT/automations" ]]; then
    cp "$ALFRED_ROOT/automations"/*.py "$ALFRED_HOME/automations/" 2>/dev/null || true
    chmod +x "$ALFRED_HOME/automations"/*.py
    log_info "Automations installed"
fi

# Step 8: Copy interface
log_info "Installing onboarding interface..."
if [[ -d "$ALFRED_ROOT/interface" ]]; then
    cp "$ALFRED_ROOT/interface"/*.py "$ALFRED_HOME/interface/" 2>/dev/null || true
    cp "$ALFRED_ROOT/interface"/*.{html,css} "$ALFRED_HOME/interface/" 2>/dev/null || true
    chmod +x "$ALFRED_HOME/interface"/*.py
    log_info "Interface installed"
fi

# Step 9: Initialize config file
log_info "Initializing configuration..."
mkdir -p "$CONFIG_DIR"
if [[ ! -f "$CONFIG_DIR/alfred.conf" ]]; then
    cat > "$CONFIG_DIR/alfred.conf" << 'EOF'
# Alfred Configuration
user_name=""
context_type=""
primary_pain_point=""
automation_type=""
automation_description=""
first_action=""
model_name="smollm2:1.7b"
briefing_time="06:00"
watch_folder="~/Documents/Alfred/notes"
output_method="file"
install_date=""
last_update_check=""
EOF
    log_info "Configuration file created"
fi

# Step 10: Launch onboarding interface
log_info "Launching onboarding interface..."
log_to_file "Installation completed. Launching Flask interface..."

cd "$ALFRED_HOME/interface" 2>/dev/null || cd "$ALFRED_ROOT/interface" 2>/dev/null || {
    log_error "Could not find interface directory"
    exit 1
}

if command -v python3 &> /dev/null; then
    python3 server.py &
    FLASK_PID=$!
    log_to_file "Flask server started with PID $FLASK_PID"

    # Give Flask time to start
    sleep 2

    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:4242" &
    elif command -v open &> /dev/null; then
        open "http://localhost:4242" &
    fi

    echo ""
    echo "================================================"
    echo "Alfred is ready!"
    echo "Open your browser to: http://localhost:4242"
    echo "================================================"
    echo ""

    # Keep script running
    wait $FLASK_PID 2>/dev/null || true
else
    log_error "Python 3 not found. Cannot start interface."
    exit 1
fi
