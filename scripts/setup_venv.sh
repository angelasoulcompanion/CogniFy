#!/bin/bash
# =============================================================================
# Python Virtual Environment Setup Script
# Standard for all David's projects
# =============================================================================
#
# Usage:
#   ./scripts/setup_venv.sh              # Setup venv for current project
#   ./scripts/setup_venv.sh --recreate   # Delete and recreate venv
#
# Standard:
#   - Python version: 3.13
#   - Single-module projects: .venv at root
#   - Full-stack projects: .venv in backend/
#
# By: Angela 💜
# Created: 2026-01-17
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.13"
PYTHON_CMD="python${PYTHON_VERSION}"

echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}💜 Python Virtual Environment Setup${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Detect project structure
PROJECT_ROOT=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_ROOT")

if [ -d "backend" ] && [ -d "frontend" ]; then
    # Full-stack project
    VENV_PATH="backend/.venv"
    REQUIREMENTS_PATH="backend/requirements.txt"
    echo -e "${BLUE}📁 Detected: Full-stack project${NC}"
elif [ -d "backend" ]; then
    # Backend-only with backend folder
    VENV_PATH="backend/.venv"
    REQUIREMENTS_PATH="backend/requirements.txt"
    echo -e "${BLUE}📁 Detected: Backend project${NC}"
else
    # Single-module project
    VENV_PATH=".venv"
    REQUIREMENTS_PATH="requirements.txt"
    echo -e "${BLUE}📁 Detected: Single-module project${NC}"
fi

echo -e "${BLUE}📍 Project: ${PROJECT_NAME}${NC}"
echo -e "${BLUE}📍 Venv path: ${VENV_PATH}${NC}"
echo ""

# Check Python version
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}❌ Python ${PYTHON_VERSION} not found!${NC}"
    echo -e "${YELLOW}   Please install Python ${PYTHON_VERSION} first.${NC}"
    exit 1
fi

ACTUAL_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}✅ Found: ${ACTUAL_VERSION}${NC}"

# Handle --recreate flag
if [ "$1" == "--recreate" ]; then
    if [ -d "$VENV_PATH" ]; then
        echo -e "${YELLOW}🗑️  Removing existing venv...${NC}"
        rm -rf "$VENV_PATH"
    fi
fi

# Create venv if not exists
if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}⚠️  Venv already exists at ${VENV_PATH}${NC}"
    echo -e "${YELLOW}   Use --recreate to delete and recreate${NC}"
else
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv "$VENV_PATH"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
"$VENV_PATH/bin/pip" install --upgrade pip --quiet

# Install requirements if exists
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo -e "${BLUE}📦 Installing requirements from ${REQUIREMENTS_PATH}...${NC}"
    "$VENV_PATH/bin/pip" install -r "$REQUIREMENTS_PATH" --quiet
    echo -e "${GREEN}✅ Requirements installed${NC}"
else
    echo -e "${YELLOW}⚠️  No requirements.txt found at ${REQUIREMENTS_PATH}${NC}"
fi

# Show summary
echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "   Venv location: ${BLUE}${VENV_PATH}${NC}"
echo -e "   Python version: ${BLUE}$("$VENV_PATH/bin/python" --version)${NC}"
echo -e "   Packages: ${BLUE}$("$VENV_PATH/bin/pip" list 2>/dev/null | wc -l | tr -d ' ') packages${NC}"
echo ""
echo -e "   ${YELLOW}To activate:${NC}"
echo -e "   ${BLUE}source ${VENV_PATH}/bin/activate${NC}"
echo ""
echo -e "${PURPLE}💜 Made with love by Angela${NC}"
