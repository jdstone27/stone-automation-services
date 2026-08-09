#!/bin/bash
# Alfred configuration management for shell scripts.
# Source this file: source alfred/bootstrap/lib/conf.sh

ALFRED_CONF_PATH="${ALFRED_CONF_PATH:-$HOME/Alfred/config/alfred.conf}"

# Initialize config file with defaults if it doesn't exist
_init_conf() {
    local conf_dir=$(dirname "$ALFRED_CONF_PATH")
    mkdir -p "$conf_dir"

    if [[ ! -f "$ALFRED_CONF_PATH" ]]; then
        cat > "$ALFRED_CONF_PATH" << 'EOF'
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
    fi
}

# Get a config value by key
get_conf_value() {
    local key="$1"
    _init_conf

    if grep -q "^$key=" "$ALFRED_CONF_PATH"; then
        grep "^$key=" "$ALFRED_CONF_PATH" | cut -d'=' -f2- | tr -d '"' | tr -d "'"
    else
        return 1
    fi
}

# Set a config value (overwrites existing or appends new)
set_conf_value() {
    local key="$1"
    local value="$2"
    _init_conf

    if grep -q "^$key=" "$ALFRED_CONF_PATH"; then
        # Use sed to replace the line (portable across macOS/Linux)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^$key=.*/$key=\"$value\"/" "$ALFRED_CONF_PATH"
        else
            sed -i "s/^$key=.*/$key=\"$value\"/" "$ALFRED_CONF_PATH"
        fi
    else
        echo "$key=\"$value\"" >> "$ALFRED_CONF_PATH"
    fi
}

# Initialize on source
_init_conf
