#!/usr/bin/env bash
# ==============================================================================
# update.sh - Automatic Update & Deploy Script for PythonAnywhere
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

# 1. Locate and switch to project repository directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_DIR="$SCRIPT_DIR"

if [ -d "$CURRENT_DIR/.git" ]; then
    PROJECT_DIR="$CURRENT_DIR"
elif [ -d "$CURRENT_DIR/progress-dashboard/.git" ]; then
    PROJECT_DIR="$CURRENT_DIR/progress-dashboard"
elif [ -d "$CURRENT_DIR/process_dashboard/.git" ]; then
    PROJECT_DIR="$CURRENT_DIR/process_dashboard"
elif [ -d "$HOME/progress-dashboard/.git" ]; then
    PROJECT_DIR="$HOME/progress-dashboard"
elif [ -d "$HOME/process_dashboard/.git" ]; then
    PROJECT_DIR="$HOME/process_dashboard"
else
    echo -e "${YELLOW}[!] Current directory is not a git repository: $CURRENT_DIR${NC}"
    echo -e "${BLUE}    Cloning repository from GitHub...${NC}"
    echo ""
    read -p "Enter GitHub repo URL (Press Enter for https://github.com/ppriyank/progress-dashboard.git): " REPO_URL
    if [ -z "$REPO_URL" ]; then
        REPO_URL="https://github.com/ppriyank/progress-dashboard.git"
    fi
    echo -e "${BLUE}Cloning $REPO_URL into progress-dashboard...${NC}"
    git clone "$REPO_URL" progress-dashboard
    PROJECT_DIR="$CURRENT_DIR/progress-dashboard"
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}[1/5] Working Directory:${NC} $PROJECT_DIR"

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
    # Look for any virtualenv in ~/.virtualenvs/
    for venv in "$HOME/.virtualenvs/"*/bin/activate; do
        if [ -f "$venv" ]; then
            source "$venv"
            VENV_ACTIVATED=true
            echo -e "${GREEN}✓ Activated found virtualenv:${NC} $venv"
            break
        fi
    done
fi

if [ "$VENV_ACTIVATED" = false ]; then
    echo -e "${YELLOW}! No active virtualenv found.${NC}"
    echo -e "${YELLOW}  Tip: You can create one via: mkvirtualenv --python=/usr/bin/python3.10 process_env${NC}"
fi

# 3. Pull latest code from GitHub (Protecting Live Databases)
echo -e "${BLUE}[3/5] Pulling latest code from GitHub...${NC}"

# Safety Backup of live databases before any git pull
if [ -f "main_app/app_database.db" ]; then
    cp -p "main_app/app_database.db" "$HOME/app_database.db.live_backup"
    echo -e "${GREEN}✓ Backed up live app_database.db${NC}"
fi
if [ -f "db.sqlite3" ]; then
    cp -p "db.sqlite3" "$HOME/db.sqlite3.live_backup"
    echo -e "${GREEN}✓ Backed up live db.sqlite3${NC}"
fi

# Ensure git skips local database modifications so live data is never overwritten
git update-index --skip-worktree main_app/app_database.db 2>/dev/null || true

# Temporarily disable set -e to handle git conflicts gracefully
set +e

# Auto-resolve uncommitted local changes to avoid merge aborts
git reset HEAD -- update.bash update.sh 2>/dev/null || true
git checkout -- update.bash update.sh 2>/dev/null || true

# Attempt git pull
PULL_OUTPUT=$(git pull origin main 2>&1)
PULL_STATUS=$?

if [ $PULL_STATUS -ne 0 ]; then
    echo -e "${YELLOW}[!] Git pull reported conflicts. Auto-resolving and retrying...${NC}"
    git stash --include-untracked 2>/dev/null || git stash 2>/dev/null || true
    git checkout -- . 2>/dev/null || true
    git pull origin main || git pull
else
    echo -e "$PULL_OUTPUT"
fi

# Re-enable set -e for strict error checking
set -e

# Restore live databases from backup to guarantee zero data loss
if [ -f "$HOME/app_database.db.live_backup" ]; then
    cp -p "$HOME/app_database.db.live_backup" "main_app/app_database.db"
fi
if [ -f "$HOME/db.sqlite3.live_backup" ]; then
    cp -p "$HOME/db.sqlite3.live_backup" "db.sqlite3"
fi
echo -e "${GREEN}✓ Code up to date & live databases 100% preserved.${NC}"

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
