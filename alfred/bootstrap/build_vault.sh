#!/bin/bash
# Alfred vault scaffolding. Creates the Karpathy wiki structure and initial config.
# Usage: build_vault.sh [--init-user] <vault_root>
# Examples:
#   build_vault.sh ~/Alfred/vault                    # Create empty vault structure
#   build_vault.sh --init-user ~/Alfred/vault        # Also create user profile + automation_01 (requires alfred.conf)

set -e

INIT_USER=false
VAULT_ROOT=""

# Parse arguments
if [[ "$1" == "--init-user" ]]; then
    INIT_USER=true
    VAULT_ROOT="$2"
else
    VAULT_ROOT="$1"
fi

if [[ -z "$VAULT_ROOT" ]]; then
    echo "Usage: build_vault.sh [--init-user] <vault_root>" >&2
    exit 1
fi

VAULT_ROOT=$(cd "$(dirname "$VAULT_ROOT")" && pwd)/$(basename "$VAULT_ROOT")

# Create directory structure
mkdir -p "$VAULT_ROOT"/{raw,wiki,_templates}

echo "Creating vault structure in $VAULT_ROOT..."

# Create note template
cat > "$VAULT_ROOT/_templates/note.md" << 'EOF'
# [Note Title]

**Summary**: One sentence.
**Tags**: #tag1 #tag2
**Date**: [YYYY-MM-DD]

---

[Content]

## Related Notes
- [[Other Note]]
EOF

# Create ALFRED.md schema file
cat > "$VAULT_ROOT/ALFRED.md" << 'EOF'
# Alfred Operating Schema

## Identity
You are Alfred. You maintain this knowledge base.
Your job is to compile, organize, and update this wiki from everything
you learn about the user and their work. You write and maintain
nearly all content here. The human reads and directs. You do the
bookkeeping.

## Directory Rules
- raw/ is append-only. Never edit files here. Only add.
- wiki/ is your workspace. Create, update, and link articles freely.
- Every wiki article starts with a one-sentence summary and relevant tags.
- When new information contradicts existing wiki content, note the
  contradiction explicitly. Do not silently overwrite.

## Ingest Protocol
When a new file appears in raw/, read it fully, identify concepts,
update or create relevant wiki articles, add backlinks, update index.md.

## Wiki Article Format
# [Article Title]
**Summary**: One sentence.
**Tags**: #tag1 #tag2
**Last Updated**: [date]
**Sources**: [[raw/source_file]]
---
[Content]

## Related Notes
- [[Linked Article]]

## Automation Log
Every automation Alfred runs is logged here with outcome and timestamp.
EOF

# Create empty index
cat > "$VAULT_ROOT/index.md" << 'EOF'
# Alfred's Knowledge Base

Master index of all notes and automations.

## Core Articles
- [[user_profile]]
- [[automation_01]]

## Auto-Generated Sections
(Updated by nightly compilation)
EOF

echo "✓ Vault structure created"

# Initialize user profile and first automation if --init-user flag is set
if [[ "$INIT_USER" == "true" ]]; then
    # Load config helpers
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/lib/conf.sh"

    USER_NAME=$(get_conf_value "user_name" 2>/dev/null || echo "")
    CONTEXT_TYPE=$(get_conf_value "context_type" 2>/dev/null || echo "")
    PAIN_POINT=$(get_conf_value "primary_pain_point" 2>/dev/null || echo "")
    AUTOMATION_TYPE=$(get_conf_value "automation_type" 2>/dev/null || echo "")
    AUTOMATION_DESC=$(get_conf_value "automation_description" 2>/dev/null || echo "")
    FIRST_ACTION=$(get_conf_value "first_action" 2>/dev/null || echo "")
    INSTALL_DATE=$(date +%Y-%m-%d)

    # Create user_profile.md
    cat > "$VAULT_ROOT/wiki/user_profile.md" << PROFILE
# User Profile

**Summary**: Setup information for Alfred's user.
**Tags**: #user #setup
**Created**: $INSTALL_DATE

## User
- **Name**: $USER_NAME
- **Environment**: $CONTEXT_TYPE
- **Primary Pain Point**: $PAIN_POINT

## Automation Setup
- **Type**: $AUTOMATION_TYPE
- **Description**: $AUTOMATION_DESC
- **First Action**: $FIRST_ACTION

## Related Notes
- [[automation_01]]
PROFILE

    # Create automation_01.md
    cat > "$VAULT_ROOT/wiki/automation_01.md" << AUTOMATION
# First Automation: $AUTOMATION_TYPE

**Summary**: $AUTOMATION_DESC
**Tags**: #automation #setup
**Created**: $INSTALL_DATE
**Status**: Configured

## Overview
$AUTOMATION_DESC

## First Action
Tomorrow morning Alfred will: $FIRST_ACTION

## Schedule
Run automatically each morning. Can be adjusted via alfred.conf.

## Related Notes
- [[user_profile]]
AUTOMATION

    # Create onboarding raw entry
    cat > "$VAULT_ROOT/raw/onboarding_$(date +%Y%m%d_%H%M%S).md" << ONBOARDING
# Onboarding - $INSTALL_DATE

User: $USER_NAME
Environment: $CONTEXT_TYPE
Pain point: $PAIN_POINT
Automation selected: $AUTOMATION_TYPE

Description: $AUTOMATION_DESC
First action: $FIRST_ACTION

Installation timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
ONBOARDING

    echo "✓ User profile and first automation initialized"
fi

echo "Done."
