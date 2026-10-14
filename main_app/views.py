import os
import re
import json
import mimetypes
import traceback
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from tracker.models import UserAccessProfile

# Import MAIN and db_manager
from main_app import MAIN
from main_app import db_manager

WEB_HTML_DIR = os.path.join(MAIN.MAIN_APP_DIR, 'web_html')


def eel_js(request):
    """
    Universal Eel compatibility bridge script.
    Emulates the eel.js client library:
    Proxies all calls like `window.eel.my_func(...args)()` or `window.eel.my_func(...args)(callback)`
    to the Django backend API endpoint `/main-app/api/call/`.
    """
    js_content = """/**
 * Universal Eel -> Django HTTP Bridge
 * Automatically intercepts Eel RPC calls and routes them to Django Backend.
 */
(function() {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function callBackend(funcName, args) {
    const csrftoken = getCookie('csrftoken') || '';
    return fetch('/main-app/api/call/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ function: funcName, args: args })
    })
    .then(async (response) => {
      const data = await response.json();
      if (!response.ok || data.status === 'error') {
        const errMsg = data.error || ('Server error: ' + response.status);
        console.error(`Eel Backend API error for "${funcName}":`, errMsg);
        throw new Error(errMsg);
      }
      return data.result;
    });
  }

  const eel = {
    _callbacks: {},
    expose: function(fn, name) {
      const exposedName = name || (fn && fn.name);
      if (exposedName) {
        eel._callbacks[exposedName] = fn;
        window[exposedName] = fn;
      }
    },
    sleep: function(sec) {
      return new Promise(r => setTimeout(r, (sec || 0) * 1000));
    }
  };

  const eelProxy = new Proxy(eel, {
    get: function(target, prop) {
      if (prop in target) return target[prop];
      return function(...args) {
        return function(callback) {
          const promise = callBackend(prop, args);
          if (typeof callback === 'function') {
            promise.then(callback).catch(err => {
              console.error(`Callback error for ${prop}:`, err);
            });
          }
          return promise;
        };
      };
    }
  });

  window.eel = eelProxy;
  console.log('[Eel Bridge] Universal Django Eel Bridge active and connected.');
})();
"""
    return HttpResponse(js_content, content_type='application/javascript; charset=utf-8')


def _check_user_permission(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        profile = UserAccessProfile.get_or_create_for_user(user)
        return bool(profile.is_admin or profile.role == 'admin' or profile.can_access_main_app)
    except Exception:
        return user.is_staff or user.is_superuser


@xframe_options_sameorigin
def main_app_index(request):
    """
    Renders Main App (Jewelry Data & API Engine).
    Can be loaded directly or embedded within the dashboard.
    """
    if not _check_user_permission(request.user):
        messages.error(request, "Permission denied: Aapko Main App access karne ki anumati nahi hai.")
        return redirect('tracker:dashboard')

    index_path = os.path.join(WEB_HTML_DIR, 'index.html')
    if not os.path.exists(index_path):
        return HttpResponse("Main App UI not found", status=404)

    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # If accessed directly (not embedded), inject a sleek back-to-dashboard top floating button
    is_embedded = request.GET.get('embedded') == '1'
    if not is_embedded:
        back_btn = """
        <div style="position: fixed; top: 12px; left: 12px; z-index: 99999;">
          <a href="/" style="display: inline-flex; align-items: center; gap: 8px; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); color: #e2e8f0; font-size: 13px; font-weight: 600; padding: 7px 14px; border-radius: 9999px; border: 1px solid rgba(255, 255, 255, 0.15); text-decoration: none; box-shadow: 0 4px 12px rgba(0,0,0,0.4); transition: all 0.2s;" onmouseover="this.style.background='rgba(30, 41, 59, 0.95)'; this.style.borderColor='rgba(99, 102, 241, 0.5)';" onmouseout="this.style.background='rgba(15, 23, 42, 0.85)'; this.style.borderColor='rgba(255, 255, 255, 0.15)';">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708L2.707 8.5H14.5A.5.5 0 0 0 15 8z"/>
            </svg>
            Process Dashboard
          </a>
        </div>
        """
        html = html.replace('</body>', back_btn + '\n</body>')

    return HttpResponse(html, content_type='text/html; charset=utf-8')


@csrf_exempt
def api_call(request):
    """
    Unified JSON API router handling calls from callEel(func_name, ...args).
    Routes call to MAIN or db_manager.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': f'Invalid JSON payload: {e}'}, status=400)

    func_name = data.get('function')
    args = data.get('args', [])
    kwargs = data.get('kwargs', {})

    if not func_name:
        return JsonResponse({'status': 'error', 'error': 'Missing "function" parameter'}, status=400)

    # Lookup function in MAIN then db_manager
    func = getattr(MAIN, func_name, None)
    if not func or not callable(func):
        func = getattr(db_manager, func_name, None)

    if not func or not callable(func):
        return JsonResponse({'status': 'error', 'error': f'Function "{func_name}" is not available'}, status=404)

    try:
        # Call the Python function
        result = func(*args, **kwargs)
        return JsonResponse({'status': 'success', 'result': result})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@csrf_exempt
def upload_data_file(request):
    """
    Upload and replace data.xlsx with auto sheet synchronization.
    """
    if not _check_user_permission(request.user):
        return JsonResponse({'status': 'error', 'error': 'Permission denied'}, status=403)

    if request.method != 'POST' or not request.FILES.get('file'):
        return JsonResponse({'status': 'error', 'error': 'Please select a valid Excel file (.xlsx)'}, status=400)

    uploaded_file = request.FILES['file']
    filename = uploaded_file.name
    if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
        return JsonResponse({'status': 'error', 'error': 'File must be an Excel spreadsheet (.xlsx or .xls)'}, status=400)

    target_path = os.path.join(MAIN.MAIN_APP_DIR, 'data.xlsx')
    try:
        with open(target_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Seed directly into SQLite database product_data table
        count = db_manager.seed_product_data_from_excel(target_path, clear_first=True)
        # Sync excel mappings with newly uploaded file
        db_manager.sync_excel_mappings_with_file(target_path)
        sheets = db_manager.get_data_file_sheets(target_path)

        # Synchronize into Product & SKU Catalog (PartyDataRecord) if company is provided
        company_name = request.POST.get('company', '').strip() or getattr(MAIN, 'selected_company', '')
        catalog_result = None
        if company_name:
            try:
                from main_app import catalog_sync
                catalog_result = catalog_sync.sync_data_to_catalog(target_path, company_name=company_name)
                MAIN.last_catalog_sync_info = catalog_result
            except Exception as e:
                print(f"Error syncing to catalog in upload_data_file: {e}")

        return JsonResponse({
            'status': 'success',
            'message': f'Successfully converted and stored {count} items into Database across sheets: {", ".join(sheets)}!',
            'sheets': sheets,
            'count': count,
            'catalog_sync': catalog_result
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': f'Failed to save file: {str(e)}'}, status=500)


@csrf_exempt
def upload_company_template(request):
    """
    Uploads a master blueprint Excel template for a company (saved to main/<Company>.xlsx).
    Automatically seeds template headers into company_template_headers table.
    """
    if not _check_user_permission(request.user):
        return JsonResponse({'status': 'error', 'error': 'Permission denied'}, status=403)

    if request.method != 'POST' or not request.FILES.get('file'):
        return JsonResponse({'status': 'error', 'error': 'Please select an Excel file (.xlsx)'}, status=400)

    company = request.POST.get('company', '').strip()
    if not company:
        return JsonResponse({'status': 'error', 'error': 'Company name is required'}, status=400)

    uploaded_file = request.FILES['file']
    filename = uploaded_file.name
    if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
        return JsonResponse({'status': 'error', 'error': 'File must be an Excel spreadsheet (.xlsx or .xls)'}, status=400)

    main_dir = os.path.join(MAIN.MAIN_APP_DIR, 'main')
    os.makedirs(main_dir, exist_ok=True)
    safe_company_name = re.sub(r'[/\\:\*\?"<>\|]', '_', company).strip()
    dest_path = os.path.join(main_dir, f"{safe_company_name}.xlsx")

    try:
        with open(dest_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        # Cache template headers in SQLite company_template_headers table
        db_manager.seed_template_headers_from_file(dest_path)

        # Auto-match or create party in tracker models
        try:
            from main_app import catalog_sync
            catalog_sync.find_or_create_party(safe_company_name)
        except Exception as pe:
            print(f"Party auto-sync error: {pe}")

        return JsonResponse({
            'status': 'success',
            'message': f"Master Blueprint for '{company}' uploaded successfully!",
            'filename': f"{safe_company_name}.xlsx"
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': f"Failed to save blueprint: {str(e)}"}, status=500)


def download_output_file(request):
    """
    Download Multi_API.xlsx, blueprint templates, or specified / latest generated API-*.xlsx file.
    Automatically cleans up temporary API-*.xlsx files older than 10 minutes (600s) to conserve server disk space.
    """
    if not _check_user_permission(request.user):
        return HttpResponse("Permission denied", status=403)

    # Clean up expired API-*.xlsx files older than 10 minutes
    MAIN.cleanup_old_api_files(max_age_seconds=600)

    target_type = request.GET.get('type')

    # 1. Download Master Company Blueprint Template
    if target_type == 'blueprint':
        company = request.GET.get('company', '').strip()
        if company:
            safe_comp = re.sub(r'[/\\:\*\?"<>\|]', '_', company).strip()
            comp_file = f"{safe_comp}.xlsx"
            path = os.path.join(MAIN.MAIN_APP_DIR, 'main', comp_file)
            if os.path.exists(path):
                return FileResponse(open(path, 'rb'), as_attachment=True, filename=comp_file)
        # Fallback to general Multi_API.xlsx template
        default_tpl = os.path.join(MAIN.MAIN_APP_DIR, 'main', 'Multi_API.xlsx')
        if os.path.exists(default_tpl):
            return FileResponse(open(default_tpl, 'rb'), as_attachment=True, filename='Multi_API_Template.xlsx')

    # 2. Download specific file by name
    specific_file = request.GET.get('file')
    if specific_file:
        safe_filename = os.path.basename(specific_file)
        file_path = os.path.join(MAIN.MAIN_APP_DIR, safe_filename)
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=safe_filename)

    # 3. Download latest generated API-*.xlsx file
    if target_type == 'latest':
        import glob
        pattern = os.path.join(MAIN.MAIN_APP_DIR, 'API-*.xlsx')
        matching_files = glob.glob(pattern)
        if matching_files:
            latest_file = max(matching_files, key=os.path.getmtime)
            filename = os.path.basename(latest_file)
            return FileResponse(open(latest_file, 'rb'), as_attachment=True, filename=filename)

    # 4. Default to Multi_API.xlsx
    file_path = os.path.join(MAIN.MAIN_APP_DIR, 'Multi_API.xlsx')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='Multi_API.xlsx')

    return HttpResponse("Output file not found", status=404)


@csrf_exempt
def get_schedule_time_view(request):
    """
    Returns US/Pacific schedule timestamp for eBay / Marketplace listings.
    Supports query parameters ?days=0&hours=7&minutes=15
    """
    try:
        days = int(request.GET.get('days', 0))
        hours = int(request.GET.get('hours', 7))
        minutes = int(request.GET.get('minutes', 15))
    except (ValueError, TypeError):
        days, hours, minutes = 0, 7, 15

    data = MAIN.get_schedule_time(days=days, hours=hours, minutes=minutes)
    return JsonResponse(data)



@xframe_options_sameorigin
def serve_web_html_file(request, path):
    """
    Serves static assets and sub-pages from main_app/web_html/
    e.g. css/app.css, js/app.jsx, vendor/..., html_app_modify.html, etc.
    """
    # Security check: prevent directory traversal
    clean_path = os.path.normpath(path).lstrip('\\/')
    full_path = os.path.join(WEB_HTML_DIR, clean_path)

    if not os.path.abspath(full_path).startswith(os.path.abspath(WEB_HTML_DIR)):
        raise Http404("File not found")

    if not os.path.exists(full_path) or os.path.isdir(full_path):
        raise Http404("File not found")

    content_type, _ = mimetypes.guess_type(full_path)
    if not content_type:
        if full_path.endswith('.jsx'):
            content_type = 'text/babel; charset=utf-8'
        else:
            content_type = 'application/octet-stream'

    with open(full_path, 'rb') as f:
        content = f.read()

    response = HttpResponse(content, content_type=content_type)
    return response
