#!/usr/bin/env bash
# ==============================================================================
# update.bash - Automatic Update & Deploy Script for PythonAnywhere
# Repository: progress-dashboard
# ==============================================================================

set -e

# Terminal colors for readable output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Updating progress-dashboard on PythonAnywhere      ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""

# 1. Switch to project root directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
echo -e "${BLUE}[1/5] Working Directory:${NC} $PROJECT_DIR"

# 2. Activate Virtual Environment
echo -e "${BLUE}[2/5] Activating virtual environment...${NC}"
VENV_ACTIVATED=false

# Check common virtual environment paths on PythonAnywhere
if [ -f "$HOME/.virtualenvs/process_env/bin/activate" ]; then
    source "$HOME/.virtualenvs/process_env/bin/activate"
    VENV_ACTIVATED=true
    echo -e "${GREEN}✓ Activated:${NC} $HOME/.virtualenvs/process_env"
elif [ -f "$HOME/.virtualenvs/progress-dashboard/bin/activate" ]; then
    source "$HOME/.virtualenvs/progress-dashboard/bin/activate"
    VENV_ACTIVATED=true
    echo -e "${GREEN}✓ Activated:${NC} $HOME/.virtualenvs/progress-dashboard"
elif [ -f "$PROJECT_DIR/env/bin/activate" ]; then
    source "$PROJECT_DIR/env/bin/activate"
    VENV_ACTIVATED=true
    echo -e "${GREEN}✓ Activated:${NC} $PROJECT_DIR/env"
elif [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    VENV_ACTIVATED=true
    echo -e "${GREEN}✓ Activated:${NC} $PROJECT_DIR/venv"
elif [ -n "$VIRTUAL_ENV" ]; then
    VENV_ACTIVATED=true
    echo -e "${GREEN}✓ Already active:${NC} $VIRTUAL_ENV"
else
    echo -e "${YELLOW}! No virtualenv found automatically. Using current Python environment.${NC}"
fi

# 3. Pull latest code from GitHub
echo -e "${BLUE}[3/5] Pulling latest code from GitHub...${NC}"
git pull origin main || git pull
echo -e "${GREEN}✓ Code up to date.${NC}"

# 4. Install dependencies, run migrations & collect static files
echo -e "${BLUE}[4/5] Applying updates (requirements, migrations, static files)...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Requirements verified.${NC}"
fi

python manage.py migrate --noinput
echo -e "${GREEN}✓ Database migrations applied.${NC}"

python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Static files collected.${NC}"

# 5. Reload the PythonAnywhere Web App
echo -e "${BLUE}[5/5] Reloading PythonAnywhere Web App...${NC}"

# PythonAnywhere auto-reloads when the WSGI configuration file is touched
WSGI_TOUCHED=false
for wsgi_path in /var/www/*_wsgi.py /var/www/*_pythonanywhere_com_wsgi.py; do
    if [ -f "$wsgi_path" ]; then
        touch "$wsgi_path"
        WSGI_TOUCHED=true
        echo -e "${GREEN}✓ Reloaded via WSGI touch:${NC} $wsgi_path"
        break
    fi
done

if [ "$WSGI_TOUCHED" = false ]; then
    if command -v pa_reload_webapp.py &> /dev/null; then
        USER_NAME=$(whoami)
        pa_reload_webapp.py "${USER_NAME}.pythonanywhere.com" || true
        echo -e "${GREEN}✓ Reloaded via pa_reload_webapp.py${NC}"
    else
        echo -e "${YELLOW}Notice: Could not locate WSGI file automatically.${NC}"
        echo -e "${YELLOW}Please click the green 'Reload' button in your PythonAnywhere Web tab.${NC}"
    fi
fi

echo ""
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}   Update completed successfully!                     ${NC}"
echo -e "${GREEN}======================================================${NC}"
