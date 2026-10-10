# ==============================================================================
# PythonAnywhere WSGI Configuration Template
# ==============================================================================
# In your PythonAnywhere Web tab:
# 1. Click on the link next to "WSGI configuration file:"
#    (e.g., /var/www/<your-username>_pythonanywhere_com_wsgi.py)
# 2. Delete existing default content and paste this block.
# 3. Replace 'yourusername' with your actual PythonAnywhere username below.
# ==============================================================================

import os
import sys

# 1. Path to your project directory
path = '/home/yourusername/process_dashboard'
if path not in sys.path:
    sys.path.append(path)

# 2. Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# 3. WSGI application handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
