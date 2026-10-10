# Step-by-Step Guide: Deploying to PythonAnywhere

Follow these straightforward steps to deploy your **Process Dashboard** onto [PythonAnywhere](https://www.pythonanywhere.com/).

---

### Step 1: Upload Your Project to PythonAnywhere

You have two simple options:

#### Option A: Via Git (Recommended)
1. Push your `process_dashboard` directory to GitHub / GitLab.
2. Open a **Bash console** on PythonAnywhere and run:
   ```bash
   git clone <your-repo-url> process_dashboard
   cd process_dashboard
   ```

#### Option B: Via Zip Upload
1. Zip the `process_dashboard` folder on your computer.
2. Go to the **Files** tab on PythonAnywhere, upload the `.zip` file into `/home/<username>/`.
3. Open a **Bash console** on PythonAnywhere and unzip it:
   ```bash
   unzip process_dashboard.zip
   ```

---

### Step 2: Create a Virtual Environment & Install Requirements

In the PythonAnywhere **Bash console**:
```bash
# 1. Create virtual environment with Python 3.10
mkvirtualenv --python=/usr/bin/python3.10 process_env

# 2. Navigate to your project folder
cd /home/<your-username>/process_dashboard

# 3. Install Django and openpyxl
pip install -r requirements.txt

# 4. Run database migrations & seed initial demo data from your Excel sheet
python manage.py migrate
python manage.py seed_data

# 5. Collect static files
python manage.py collectstatic --noinput
```

*(Note: Replace `<your-username>` with your actual PythonAnywhere account username)*

---

### Step 3: Configure the Web App on PythonAnywhere

1. Go to the **Web** tab in PythonAnywhere dashboard.
2. Click **Add a new web app**.
3. Select **Manual configuration** (do **not** select "Django" wizard since your project is already built), and pick **Python 3.10**.
4. Once created, fill in the following sections on the Web tab:

#### 1. Code Section:
- **Source code**: `/home/<your-username>/process_dashboard`
- **Working directory**: `/home/<your-username>/process_dashboard`

#### 2. Virtualenv Section:
- Enter your virtual environment path or name:
  `/home/<your-username>/.virtualenvs/process_env`

#### 3. WSGI configuration file:
- Click on the link next to **WSGI configuration file** (e.g., `/var/www/<your-username>_pythonanywhere_com_wsgi.py`).
- Delete any existing lines and paste:
  ```python
  import os
  import sys

  path = '/home/<your-username>/process_dashboard'
  if path not in sys.path:
      sys.path.append(path)

  os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

  from django.core.wsgi import get_wsgi_application
  application = get_wsgi_application()
  ```
- Click **Save**.

#### 4. Static Files Section:
Add a new entry:
- **URL**: `/static/`
- **Directory**: `/home/<your-username>/process_dashboard/staticfiles`

---

### Step 4: Reload & Open Your App

1. Click the green **Reload <your-username>.pythonanywhere.com** button at the top of the **Web** tab.
2. Visit `https://<your-username>.pythonanywhere.com/` in your browser!
3. Your dashboard with the Process Tab, real-time calculations, status highlights, search, and Excel import/export will be live!

---

### Superuser / Admin Access (Optional)
If you want to access the Django admin panel at `/admin/`, run in the PythonAnywhere Bash console:
```bash
python manage.py createsuperuser
```
Follow the prompt to set your username and password.
