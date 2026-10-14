
def get_actual_max_row(ws):
    for r in range(ws.max_row, 0, -1):
        if any(ws.cell(r, c).value is not None and str(ws.cell(r, c).value).strip() != '' for c in range(1, max(10, ws.max_column + 1))):
            return r
    return 1
# ==================== 1. Module Imports (आवश्यक लाइब्रेरीज़) ====================
# यह सेक्शन एप्लीकेशन के लिए आवश्यक सभी पाइथन लाइब्रेरीज़ को इंपोर्ट करता है।
# 
# 1. eel: Python backend और Web UI (React/HTML/JS) के बीच संपर्क सेतु (Bridge) बनाता है।
#    - Python फ़ंक्शन्स को React से कॉल करने की अनुमति देता है।
# 2. re: रेगुलर एक्सप्रेशन (Regular Expressions) - टेक्स्ट सर्च और स्ट्रिंग क्लीनिंग के लिए।
# 3. random: रैंडम टाइटल टैम्प्लेट चुनने और यूनिक टाइमस्टैम्प फ़ाइल नाम बनाने के लिए।
# 4. datetime & timedelta: तारीख और समय (Timestamp) कैलकुलेशन के लिए।
# 5. pytz: टाइमज़ोन मैनेजमेंट (जैसे US/Pacific टाइमज़ोन) के लिए।
# 6. pandas (pd): data.xlsx एक्सेल फ़ाइल को तेज़ी से पढ़ने और डेटा प्रोसेस करने के लिए।
# 7. openpyxl: Multi_API.xlsx फ़ाइल की एक्सेल फ़ॉर्मैटिंग (styles/headers) बिना बिगाड़े डेटा जोड़ने (append करने) के लिए।
# 8. db_manager: SQLite डेटाबेस (app_database.db) से सेटिंग्स, प्रोडक्ट्स, पॉलिसीज़ और HTML कोड मैनेज करने के लिए।

import eel 
from gevent.lock import RLock

# Eel WebSocket Thread/Greenlet-safe Lock
# बड़े पेलोड्स (जैसे HTML टेम्पलेट्स) और स्टार्टअप पर एक साथ होने वाले कई API कॉल्स के दौरान 
# सॉकेट में कॉन्करेंट राइट्स (WinError 10035 / 10053) व ऐप क्रैश को रोकने के लिए
_eel_ws_lock = RLock()
_orig_eel_repeated_send = eel._repeated_send

def _threadsafe_eel_repeated_send(ws, msg):
    with _eel_ws_lock:
        for attempt in range(100):
            try:
                if getattr(ws, 'closed', False):
                    break
                ws.send(msg)
                break
            except Exception:
                eel.sleep(0.001)

eel._repeated_send = _threadsafe_eel_repeated_send
import threading
import re
import random
import time
import pytz 
import os
import shutil
import warnings
import pandas as pd 
from screeninfo import get_monitors 
from datetime import datetime, timedelta
import openpyxl
try:
    import openpyxl.styles.fonts
    openpyxl.styles.fonts.Font.family.max = 100
except Exception:
    pass
from openpyxl import load_workbook 


import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import db_manager
except ImportError:
    from main_app import db_manager


# ==================== 2. Global Configuration & Settings (ग्लोबल सेटिंग्स) ====================
# यह सेक्शन एप्लीकेशन के ग्लोबल वैरिएबल्स (Global Variables) को परिभाषित करता है जो पूरी एप्लीकेशन में शेयर होते हैं।
# 
# - selected_company: UI में यूज़र द्वारा चुनी गई कंपनी का नाम (जैसे SOLITAIRE, Livuniq आदि)।
# - SHEET_NAME: UI में यूज़र द्वारा चुना गया प्रोडक्ट या कैटेगरी शीट (जैसे Engagement Ring)।
# - c_variation: कलर वैरिएशन फ़्लैग (True/False)।
# - gold_kt_variation: गोल्ड प्योरिटी वैरिएशन फ़्लैग (True/False)।
# - company_settings: डेटाबेस से लोड की गई कंपनी सेटिंग्स और बिज़नेस पॉलिसीज़ की डिक्शनरी।
# - product_list: डेटाबेस से लोड की गई प्रोडक्ट्स की लिस्ट।

selected_company = ''
SHEET_NAME = ''
c_variation = False
gold_kt_variation = False

class SafeDict(dict):
    """
    SafeDict (सुरक्षित डिक्शनरी क्लास):
    -----------------------------------
    1. Case-insensitive lookup (जैसे {TOTAL_DIAMOND_PCS}, {total_diamond_pcs}, {Metel}, {METEL}, {xxx}).
    2. raw excel columns तथा dynamic context variables को स्वतः रिप्लेस करता है।
    3. missing / undefined tag मिलने पर raw '{xxx}' प्रिंट करने के बजाय उसे खाली स्ट्रिंग "" से बदलता है।
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lower_map = {}
        for k, v in self.items():
            if v is not None and not pd.isna(v):
                self._lower_map[str(k).lower()] = str(v)

    def __getitem__(self, key):
        key_str = str(key)
        if key_str in self:
            val = super().__getitem__(key_str)
            return "" if (pd.isna(val) or val is None) else str(val)
        lower_key = key_str.lower()
        if lower_key in self._lower_map:
            return self._lower_map[lower_key]
        return ""

    def __missing__(self, key):
        return ""

company_settings = {}
product_list = []
MAIN_APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_app_path(rel_path):
    if not rel_path:
        return MAIN_APP_DIR
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(MAIN_APP_DIR, rel_path)


def cleanup_old_api_files(max_age_seconds=600):
    """
    Deletes all temporary API-*.xlsx files older than max_age_seconds (default 10 minutes / 600s).
    Saves disk space on the server.
    """
    import glob
    import time
    deleted_count = 0
    try:
        now = time.time()
        pattern = os.path.join(MAIN_APP_DIR, 'API-*.xlsx')
        for f in glob.glob(pattern):
            try:
                if (now - os.path.getmtime(f)) > max_age_seconds:
                    os.remove(f)
                    deleted_count += 1
                    print(f"[Auto-Cleanup] Deleted expired API file: {os.path.basename(f)}")
            except Exception as e:
                print(f"[Auto-Cleanup] Error deleting {f}: {e}")
    except Exception as err:
        print(f"[Auto-Cleanup] Error scanning old API files: {err}")
    return deleted_count


def schedule_file_deletion(filepath, delay_seconds=600):
    """
    Schedules deletion of a specific file after delay_seconds using a background timer.
    """
    import threading
    def _delete():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"[Auto-Timer] Deleted expired file after {delay_seconds}s: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[Auto-Timer] Error deleting {filepath}: {e}")

    timer = threading.Timer(delay_seconds, _delete)
    timer.daemon = True
    timer.start()


def _start_bg_cleaner():
    import time
    while True:
        try:
            cleanup_old_api_files(max_age_seconds=600)
        except Exception:
            pass
        time.sleep(30)

_bg_cleaner_thread = threading.Thread(target=_start_bg_cleaner, daemon=True)
_bg_cleaner_thread.start()


last_catalog_sync_info = {}

@eel.expose
def get_catalog_sync_info():
    global last_catalog_sync_info
    return last_catalog_sync_info or {}


@eel.expose
def check_company_blueprint(company_name):
    """
    Checks if a master blueprint Excel file exists in main/<Company>.xlsx.
    """
    if not company_name:
        return {'exists': False, 'filename': '', 'size_kb': 0}
    safe_name = re.sub(r'[/\\:\*\?"<>\|]', '_', str(company_name)).strip()
    comp_file = f"{safe_name}.xlsx"
    path = os.path.join(MAIN_APP_DIR, 'main', comp_file)
    exists = os.path.exists(path)
    size_kb = round(os.path.getsize(path) / 1024, 1) if exists else 0
    return {
        'exists': exists,
        'filename': comp_file,
        'size_kb': size_kb,
        'company': company_name
    }


@eel.expose
def list_company_blueprints():
    """
    Returns a dictionary of all companies and whether their blueprint file exists.
    """
    main_dir = os.path.join(MAIN_APP_DIR, 'main')
    result = {}
    if os.path.exists(main_dir):
        for f in os.listdir(main_dir):
            if f.endswith('.xlsx') and not f.startswith('~$'):
                c_name = os.path.splitext(f)[0]
                result[c_name.lower()] = {
                    'filename': f,
                    'size_kb': round(os.path.getsize(os.path.join(main_dir, f)) / 1024, 1)
                }
    return result


_multi_api_cleared_on_startup = False

@eel.expose
def clear_multiXlsx(file_name="Multi_API.xlsx", destination_path=None, force=False):
    """
    'main/' फोल्डर में मौजूद फ्रेश मास्टर Multi_API.xlsx (या चुनी गई कंपनी की फ़ाइल उदा. Pear Jewel.xlsx)
    को रूट फोल्डर में कॉपी करके पुरानी एक्सपोर्ट फ़ाइल को साफ़ (Reset) करता है।
    - StartUp पर केवल एक बार (Exactly once) चलेगा।
    - UI बटन से manual click करने या कंपनी चेंज करने पर force=True से हमेशा क्लीयर करेगा।
    """
    global _multi_api_cleared_on_startup, selected_company
    if destination_path is None:
        destination_path = MAIN_APP_DIR
    if not force and _multi_api_cleared_on_startup:
        return
    try:
        os.makedirs(destination_path, exist_ok=True)
        source_file = file_name
        if selected_company:
            comp_filename = f"{selected_company.strip()}.xlsx"
            possible_src = os.path.join(destination_path, "main", comp_filename)
            if os.path.exists(possible_src):
                source_file = comp_filename
                print(f"कंपनी '{selected_company}' के लिए 'main/{comp_filename}' फ़ाइल पाई गई!")
            else:
                print(f"कंपनी '{selected_company}' की एक्सेल फ़ाइल 'main/{comp_filename}' नहीं मिली, डिफ़ॉल्ट 'main/Multi_API.xlsx' फ़ाइल का उपयोग किया जा रहा है।")

        src = os.path.join(destination_path, "main", source_file)
        dest = os.path.join(destination_path, file_name)
        if os.path.exists(src):
            shutil.copy(src, dest)
            _multi_api_cleared_on_startup = True
            print(f"फ़ाइल '{src}' से '{dest}' में ऑटोमैटिकली रीसेट होकर कॉपी हुई: '{destination_path}'")
        else:
            print(f"Warning: Source file '{src}' does not exist.")
    except Exception as e:
        print(f"फ़ाइल कॉपी रीसेट एरर '{file_name}': {e}")



def load_settings():
    """
    load_settings() फ़ंक्शन:
    -----------------------
    यह फ़ंक्शन SQLite डेटाबेस (app_database.db) से जुड़ता है और:
    1. init_db() कॉल करके डेटाबेस टेबल्स सुनिश्चित करता है।
    2. सभी कंपनियों की बिज़नेस पॉलिसीज़ (Shipping, Return, Payment profiles) को `company_settings` में भरता है।
    3. सभी प्रोडक्ट्स की लिस्ट को `product_list` में भरता है।
    4. एप्लीकेशन स्टार्ट होते ही Multi_API.xlsx फ़ाइल को ऑटोमैटिकली रीसेट / क्लीयर करता है।
    """
    global company_settings, product_list
    try:
        db_manager.init_db()
        company_settings = db_manager.load_company_settings_dict()
        product_list = db_manager.get_product_list()
        clear_multiXlsx(force=False)
    except Exception as e:
        print(f"SQLite डेटाबेस से सेटिंग्स लोड करने में त्रुटि: {e}")


# एप्लीकेशन स्टार्ट होते ही इनिशियल सेटिंग्स लोड करें व Multi_API.xlsx ऑटोमैटिक साफ़ करें
load_settings()



# ==================== 3. Template & Title Generation Helpers (टैम्प्लेट हेल्पर्स) ====================

def get_row_subcategory(row_data):
    """
    Returns subcategory key for product row with user-specified priority order (without using SETTING column):
    1st Priority: HTML column explicit subcategory / keyword (Cluster, Tennis, Tennis Necklace, Solitaire, No Accents, etc.)
    2nd Priority: Pure structural diamond properties (TOTAL_DIAMOND_PCS, CENTER_STONE_SHAPE, SIDE_STONE_SHAPE, SIDE_STONE_WEIGHT)
    """
    # Detect category context
    cat_str = str(
        row_data.get('TYPE', '') or 
        row_data.get('CATEGORY', '') or 
        row_data.get('category', '') or 
        row_data.get('type', '') or 
        row_data.get('target_sheet', '') or 
        row_data.get('curr_sheet', '') or ''
    ).strip().lower()

    # 1st Priority: Check HTML column specifically first
    for html_key in ['HTML', 'html', 'Html', 'HTML_TEMPLATE', 'html_template']:
        if html_key in row_data and pd.notna(row_data[html_key]):
            raw_h = str(row_data[html_key]).strip()
            if raw_h and raw_h.lower() not in ['nan', 'none', 'null', ''] and not ('<' in raw_h or '>' in raw_h or '{' in raw_h):
                return raw_h

    # Extract stone specs and pcs_val
    pcs_raw = None
    for pcs_key in ['TOTAL_DIAMOND_PCS', 'total_diamond_pcs', 'TOTAL DIAMOND PCS', 'Total Diamond Pcs', 'DIAMOND_PCS', 'diamond_pcs', 'PCS', 'pcs', 'QTY', 'qty']:
        if pcs_key in row_data and pd.notna(row_data[pcs_key]):
            pcs_raw = row_data[pcs_key]
            break

    side_wt_raw = str(row_data.get('SIDE_STONE_WEIGHT', '0')).strip()
    side_shape_raw = str(row_data.get('SIDE_STONE_SHAPE', '')).strip().lower()
    center_shape_raw = str(row_data.get('CENTER_STONE_SHAPE', '')).strip().lower()

    has_center_shape = center_shape_raw not in ['', 'nan', 'none', 'null', '--', '0']
    has_side_shape = side_shape_raw not in ['', 'nan', 'none', 'null', '--', '0']

    pcs_val = None
    if pcs_raw is not None and pd.notna(pcs_raw):
        try:
            val = float(pcs_raw)
            if val > 0:
                pcs_val = int(val)
        except (ValueError, TypeError):
            pass

    has_side_stones = False
    try:
        if side_wt_raw not in ['0', '0.00', 'nan', 'none', 'null', ''] and float(side_wt_raw) > 0:
            has_side_stones = True
    except (ValueError, TypeError):
        pass

    if has_side_shape:
        has_side_stones = True

    # 2nd Priority: Structural logic without SETTING column

    # A. Earrings
    if 'earring' in cat_str or 'earrings' in cat_str or 'cat-earrings' in cat_str:
        # If center stone and side stone both present -> Default
        if has_center_shape and has_side_shape:
            return "Default"
        # If total diamond pcs is 2 (or 1) without side stones -> Solitaire
        if pcs_val in [1, 2] and not has_side_stones:
            return "Solitaire"
        # If total diamond pcs > 2 without side stones -> Cluster
        if pcs_val is not None and pcs_val > 2 and not has_side_stones:
            return "Cluster"
        return "Default"

    # B. Pendants / Necklaces
    if 'pendant' in cat_str or 'necklace' in cat_str:
        if has_center_shape and has_side_shape:
            return "Default"
        if pcs_val == 1 and not has_side_stones:
            return "Solitaire"
        if pcs_val is not None and pcs_val > 1 and not has_side_stones:
            return "Cluster"
        return "Default"

    # C. Bracelets
    if 'bracelet' in cat_str or 'charm' in cat_str or 'cat-braceletscharms' in cat_str:
        if pcs_val is not None and pcs_val > 1:
            return "Tennis"
        elif pcs_val == 1:
            return "Solitaire"
        return "Default"

    # D. Wedding Band & Wedding Ring Sets
    if "wedding band" in cat_str or "wedding ring set" in cat_str or (cat_str.startswith("band") and "men" not in cat_str):
        return "Default"

    # E. Rings (Engagement Ring, Men's Ring, etc.)
    if pcs_val == 1 and not has_side_stones:
        return "Solitaire"
    elif has_side_stones or (pcs_val is not None and pcs_val > 1):
        return "Default"
    elif pcs_val == 1:
        return "Solitaire"

    return "No Accents"


def evaluate_template_expressions(html_str, context):
    """
    evaluate_template_expressions() फ़ंक्शन:
    -------------------------------------------
    यह फ़ंक्शन HTML टैम्प्लेट में मौजूद inline math expressions (जैसे {float(CENTER_STONE_WEIGHT)/2:.2f} या {CENTER_STONE_WEIGHT/2:.2f})
    और dynamic placeholders को स्वचालिक रूप से Evaluate व Replace करता है।
    """
    if not html_str or not isinstance(html_str, str):
        return ""

    safe_map = SafeDict(context)

    # Automatically calculate half-weight helper variables for earrings/pairs
    for key in ['CENTER_STONE_WEIGHT', 'TCW', 'SIDE_STONE_WEIGHT']:
        raw_val = safe_map.get(key, '')
        try:
            val_num = float(raw_val) if raw_val not in ['', 'None', 'nan', 'null'] else 0.0
            half_val = f"{val_num / 2.0:.2f}"
        except (ValueError, TypeError):
            half_val = "0.00"
        safe_map[f"{key}_HALF"] = half_val
        safe_map[f"{key.lower()}_half"] = half_val

    formatted = html_str

    # Protect <style>...</style> blocks during expression evaluation to prevent stripping CSS rules
    style_blocks = []
    def save_style(match):
        style_blocks.append(match.group(0))
        return f"___STYLE_BLOCK_{len(style_blocks)-1}___"

    formatted = re.sub(r'<style[^>]*>.*?</style>', save_style, formatted, flags=re.DOTALL | re.IGNORECASE)

    # Extract all {expression} occurrences
    found_tags = re.findall(r'\{([^{}\n]+)\}', formatted)

    for expr in set(found_tags):
        expr_str = expr.strip()
        
        # 0. Preserve image placeholders as-is (e.g. IMG_1, THUMB_1, THMB_1, etc.) in output HTML
        if re.match(r'^(IMG_\d+|THUMB_\d+|THMB_\d+)$', expr_str, re.IGNORECASE):
            formatted = formatted.replace(f"{{{expr}}}", expr_str.upper())
            continue

        # 1. Direct tag lookup in safe_map
        if expr_str in safe_map or expr_str.lower() in safe_map._lower_map:
            val = safe_map[expr_str]
            if expr_str.lower() == 'center_stone_spec' and not val:
                val = "Stone Details"
            formatted = formatted.replace(f"{{{expr}}}", str(val))
            continue

        # 2. Evaluate inline math expression (e.g. float(CENTER_STONE_WEIGHT)/2:.2f or CENTER_STONE_WEIGHT/2:.2f)
        try:
            format_spec = ""
            calc_expr = expr_str
            if ":" in expr_str and not expr_str.startswith("http"):
                parts = expr_str.rsplit(":", 1)
                calc_expr = parts[0].strip()
                format_spec = parts[1].strip()

            substituted = calc_expr
            tokens = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', calc_expr)
            for token in set(tokens):
                if token in ['float', 'int', 'round', 'abs', 'str', 'max', 'min']:
                    continue
                token_val = safe_map.get(token, '')
                try:
                    num_val = float(token_val) if token_val not in ['', 'None', 'nan', 'null'] else 0.0
                except (ValueError, TypeError):
                    num_val = 0.0
                substituted = re.sub(r'\b' + re.escape(token) + r'\b', str(num_val), substituted)

            res_val = eval(substituted, {"__builtins__": None, "float": float, "int": int, "round": round, "abs": abs, "max": max, "min": min})
            
            if format_spec:
                res_str = f"{res_val:{format_spec}}"
            else:
                res_str = f"{float(res_val):.2f}" if isinstance(res_val, (int, float)) else str(res_val)

            formatted = formatted.replace(f"{{{expr}}}", res_str)
        except Exception:
            val = safe_map.get(expr_str, "")
            formatted = formatted.replace(f"{{{expr}}}", str(val))

    # Restore protected <style>...</style> blocks
    for idx, block in enumerate(style_blocks):
        formatted = formatted.replace(f"___STYLE_BLOCK_{idx}___", block)

    return formatted


def get_row_html_subcategory(row_data):
    """
    Returns subcategory key for HTML template lookup WITHOUT using the SETTING column.
    1st Priority: HTML column explicit subcategory / keyword (Cluster, Tennis, Tennis Necklace, Solitaire, No Accents, Halo, etc.)
    2nd Priority: Pure structural diamond properties (TOTAL_DIAMOND_PCS, CENTER_STONE_SHAPE, SIDE_STONE_SHAPE, SIDE_STONE_WEIGHT)
    """
    return get_row_subcategory(row_data)


def generate_company_html_from_db(selected_company, target_category, row_data, context):
    """
    generate_company_html_from_db() function:
    1st Priority for HTML subcategory lookup: HTML column
    2nd Priority for HTML subcategory lookup: Setting / Subcategory column
    """
    raw_html_val = None
    for html_key in ['HTML', 'html', 'Html', 'HTML_TEMPLATE', 'html_template']:
        if html_key in row_data and pd.notna(row_data[html_key]):
            v = str(row_data[html_key]).strip()
            if v and ('<' in v or '>' in v):
                raw_html_val = v
                break

    if raw_html_val:
        db_tmpl = raw_html_val
    else:
        row_style = get_row_html_subcategory(row_data)

        # Ensure center_stone_spec is set
        if not context.get('center_stone_spec'):
            context['center_stone_spec'] = "Main Stone Specifications" if context.get('hide') == "" else "Stone Details"

        # Fetch HTML template from database
        db_tmpl = db_manager.get_company_html_template(selected_company, target_category, row_style)
        if not db_tmpl and target_category and target_category.lower() != 'default':
            db_tmpl = db_manager.get_company_html_template(selected_company, 'Engagement Ring', row_style)
        if not db_tmpl and target_category and target_category.lower() != 'default':
            db_tmpl = db_manager.get_company_html_template(selected_company, 'default', row_style)

    if not db_tmpl:
        return ""

    formatted = db_manager.clean_raw_html_code(db_tmpl)
    formatted = evaluate_template_expressions(formatted, context)
    return db_manager.clean_raw_html_code(formatted)


def generate_title(template_file, sheet_name, setting_column, company_name=None, **vals):
    """
    generate_title() function:
    Pass company_name to get_title_templates_list to support company-dedicated title templates.
    Auto-detects SKU suffixes (bbx -> Wedding Band, mmx -> Men's Ring, ssx -> Wedding Ring Set, frx -> Engagement Ring).
    """
    try:
        raw_sku = str(vals.get('SKU') or vals.get('sku') or vals.get('raw_sku') or '').strip().lower()
        has_ring_suffix = False
        if 'bbx' in raw_sku:
            sheet_name = 'Wedding Band'
            has_ring_suffix = True
        elif 'mmx' in raw_sku:
            sheet_name = "Men's Ring"
            has_ring_suffix = True
        elif 'ssx' in raw_sku:
            sheet_name = 'Wedding Ring Set'
            has_ring_suffix = True
        elif 'frx' in raw_sku:
            sheet_name = 'Engagement Ring'
            has_ring_suffix = True

        # Check if TITLE or SETTING or explicit setting column was provided in row data
        has_explicit_file_setting = False
        file_setting_val = None

        for k in ['TITLE', 'Title', 'title', 'SETTING', 'setting', 'Setting', 'Style', 'style', 'Subcategory', 'subcategory']:
            if k in vals and pd.notna(vals[k]):
                v_str = str(vals[k]).strip()
                if v_str and v_str.lower() not in ['nan', 'none', 'null', ''] and not ('<' in v_str or '>' in v_str or '}' in v_str):
                    has_explicit_file_setting = True
                    file_setting_val = v_str
                    break

        if not has_explicit_file_setting and setting_column and str(setting_column).strip().lower() != 'default':
            has_explicit_file_setting = True
            file_setting_val = str(setting_column).strip()

        is_ring_category = str(sheet_name).strip().lower() in ['engagement ring', 'ring', 'rings', 'cat-engagementrings', 'default', '']
        if not has_ring_suffix and is_ring_category:
            sheet_name = 'Engagement Ring'
            if has_explicit_file_setting and file_setting_val:
                setting_column = file_setting_val
            else:
                setting_column = 'Default'
        elif has_explicit_file_setting and file_setting_val:
            setting_column = file_setting_val

        metal_type = "gold" if "gold" in str(template_file).lower() else "platinum"
        comp = company_name or vals.get('selected_company') or vals.get('COMPANY_NAME') or vals.get('company_name')
        templates = db_manager.get_title_templates_list(metal_type, sheet_name, setting_column, company_name=comp)
        
        safe_vals = SafeDict(vals)
        if not templates:
            default_tmpl = "{TCW} ct {CENTER_STONE_SHAPE} {GOLD_KT} {GOLD_COLOR}"
            return re.sub(r'\s+', ' ', default_tmpl.format_map(safe_vals)).strip()
        
        chosen = random.choice(templates)
        formatted_title = chosen.format_map(safe_vals).strip()
        return re.sub(r'\s+', ' ', formatted_title)
    except Exception as e:
        print(f"Title generation warning: {e}")
        safe_vals = SafeDict(vals)
        return re.sub(r'\s+', ' ', "{TCW} ct {CENTER_STONE_SHAPE} {GOLD_KT} {GOLD_COLOR}".format_map(safe_vals)).strip()




def process_center_stone(CENTER_STONE_SHAPE, TITLE):
    """
    process_center_stone() फ़ंक्शन:
    -------------------------------
    यह फ़ंक्शन मुख्य डायमंड/स्टोन की जानकारी विश्लेषित (Analyze) करता है।
    
    यह क्या करता है:
    - यदि स्टोन शेप में 'Simulated' या 'CZ' शब्द है -> स्टोन टाइप को 'Cubic Zirconia' और निर्माण को 'Simulated' सेट करता है।
    - यदि 'CVD' या 'Lab' शब्द है -> स्टोन टाइप को 'Diamond' और निर्माण को 'Lab-Created' सेट करता है।
    - यदि 'Moissanite' है -> 'Moissanite' और 'Lab-Created' सेट करता है।
    - यदि 'Natural' है -> 'Diamond' और 'Natural' सेट करता है।
    - शुद्ध किया गया स्टोन शेप, स्टोन प्रकार, निर्माण प्रकार और टाइटल रिटर्न करता है।
    """
    MAIN_STONE_TYPE = 'Diamond'
    main_stone_creation = 'Lab-Created'
    
    shape_lower = CENTER_STONE_SHAPE.lower()
    
    if 'simulated' in shape_lower:
        MAIN_STONE_TYPE = 'Cubic Zirconia'
        main_stone_creation = 'Simulated'
        CENTER_STONE_SHAPE = CENTER_STONE_SHAPE.replace('Simulated', '').replace('simulated', '').strip()
    elif 'cvd' in shape_lower or 'lab' in shape_lower:
        MAIN_STONE_TYPE = 'Diamond'
        main_stone_creation = 'Lab-Created'
    elif 'moissanite' in shape_lower:
        MAIN_STONE_TYPE = 'Moissanite'
        main_stone_creation = 'Lab-Created'
    elif 'natural' in shape_lower:
        MAIN_STONE_TYPE = 'Diamond'
        main_stone_creation = 'Natural'
        
    return CENTER_STONE_SHAPE, MAIN_STONE_TYPE, main_stone_creation, TITLE



def is_match(cell_value, criteria):
    """सेल मान की क्राइटेरिया से समानता जांचने का हेल्पर फ़ंक्शन"""
    if pd.isna(cell_value):
        return False
    return str(cell_value).strip().lower() == str(criteria).strip().lower()


def parse_shapes(cell_value):
    """अल्पविराम (comma) से अलग की गई स्टोन शेप्स को लिस्ट में बदलने का फ़ंक्शन"""
    if pd.isna(cell_value):
        return []
    return [s.strip() for s in str(cell_value).split(',') if s.strip()]


def if_else(condition, true_val, false_val):
    """सरल If-Else टर्नरी हेल्पर फ़ंक्शन"""
    return true_val if condition else false_val


# ==================== 4. Excel & Helper Utility Functions (यूटीलिटी फंक्शन्स) ====================

def get_shuffled_datetime_string():
    """
    यूनिक आउटपुट फ़ाइल नाम बनाने का फ़ंक्शन:
    वर्तमान तारीख और समय का टाइमस्टैम्प (जैसे 20260803134900) लेता है
    और उसके अंकों को शफ़ल करके अद्वितीय फ़ाइल नाम जनरेट करता है।
    """
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    digits = list(now_str)
    random.shuffle(digits)
    return "".join(digits)


def copy_and_rename_excel_file(source_path, destination_path):
    """एक्सेल फ़ाइल को एक स्थान से दूसरे स्थान कॉपी और रीनेम (Rename) करने का फ़ंक्शन।"""
    try:
        source_path = get_app_path(source_path)
        destination_path = get_app_path(destination_path)
        shutil.copy(source_path, destination_path)
        print(f"फ़ाइल सफलता से कॉपी हुई: '{destination_path}'")
    except Exception as e:
        print(f"फ़ाइल कॉपी करने में त्रुटि: {e}")


def clean_sku(sku, suffix):
    """
    SKU साफ़ और चेक करने का फ़ंक्शन:
    जाँच करता है कि SKU में या अंत में विशिष्ट सफ़िक्स (जैसे bbx, mmx, ssx, frx) लगा है या नहीं।
    यदि लगा है, तो सफ़िक्स को हटाकर केवल क्लीन मूल SKU रिटर्न करता है (उदा. R5483ssx -> R5483)।
    """
    sku_str = str(sku).strip()
    if not sku_str or sku_str.lower() in ['nan', 'none', 'null', '']:
        return ""
    s_lower = suffix.lower()
    val_lower = sku_str.lower()
    
    if val_lower.endswith(s_lower):
        res = sku_str[:-len(suffix)].rstrip(" -_")
        return res if res else sku_str
    
    if s_lower in val_lower:
        pattern = re.compile(re.escape(s_lower), re.IGNORECASE)
        res = pattern.sub('', sku_str).strip(" -_")
        return res if res else sku_str
        
    return ""



def keepOnly(text, include):
    """टेक्स्ट में से केवल निर्दिष्ट कैरेक्टर्स (characters) रखने का फ़ंक्शन।"""
    return "".join([c for c in str(text) if c in include])


def modify_string(input_str):
    """स्ट्रिंग फ़ॉर्मैटिंग साफ़ करने का हेल्पर फ़ंक्शन"""
    return str(input_str).strip()


def check_and_remove(input_str):
    """अनावश्यक डैश (---) हटाने का फ़ंक्शन"""
    return str(input_str).replace("---", "").strip()


def remove_first_row_except_first_sheet(file_path):
    """
    यदि किसी शीट में शीर्ष पर डुप्लिकेट *Action हेडर रो है (Row 1), तो उसे सुरक्षित रूप से हटाता है।
    """
    try:
        file_path = get_app_path(file_path)
        wb = load_workbook(file_path)
        modified = False
        for index, sheet_name in enumerate(wb.sheetnames):
            if index > 0:
                sheet = wb[sheet_name]
                r1_val = str(sheet.cell(1, 1).value or '').strip()
                if r1_val.lower().startswith('*action'):
                    for r in range(2, 6):
                        if str(sheet.cell(r, 1).value or '').strip().lower().startswith('*action'):
                            sheet.delete_rows(1)
                            modified = True
                            break
        if modified:
            wb.save(file_path)
    except Exception as e:
        print(f"शीट्स रो डिलीट करने में एरर: {e}")


def save_excel_mapped_rows(rows_ctx_list, excel_file_to_write, target_sheet_name, source_sheet_name):
    """
    save_excel_mapped_rows():
    -------------------------
    1. openpyxl से Multi_API.xlsx की टारगेट शीट लोड करता है।
    2. Header row (Row 5 / Row 1) के हर कॉलम का exact position map (1-based column index) निकालता है।
    3. SQLite db_manager.get_all_excel_mappings() से कॉलम मैपिंग रूल्स फेच करता है।
    4. डेटा को मूल टेम्पलेट के अनुसार Row 6 से सटिक Header positions पर लिखता है (0 misalignment / shift)।
    """
    excel_file_to_write = get_app_path(excel_file_to_write)
    if not os.path.exists(excel_file_to_write):
        print(f"त्रुटि: आउटपुट एक्सेल फ़ाइल '{excel_file_to_write}' नहीं मिली!")
        return False

    try:
        wb = load_workbook(excel_file_to_write)
        if target_sheet_name not in wb.sheetnames:
            print(f"चेतावनी: शीट '{target_sheet_name}' फ़ाइल में नहीं मिली!")
            return False

        ws = wb[target_sheet_name]

        # Header Name -> exact 1-based column index in worksheet
        header_map = {}
        header_row = 4
        for r in range(1, 10):
            val = str(ws.cell(row=r, column=1).value or '').strip()
            if val.lower().startswith('*action'):
                header_row = r
                for r2 in range(r + 1, 10):
                    val2 = str(ws.cell(row=r2, column=1).value or '').strip()
                    if val2.lower().startswith('*action'):
                        header_row = r2
                        break
                break
        for col_idx in range(1, ws.max_column + 1):
            h_val = ws.cell(row=header_row, column=col_idx).value
            if h_val is not None:
                s = str(h_val).strip()
                if s:
                    header_map[s.lower()] = col_idx
                    if '(' in s:
                        clean_name = s.split('(')[0].strip().lower()
                        header_map[clean_name] = col_idx
                    if s.lower().startswith('*action'):
                        header_map['*action'] = col_idx





        # Helper to check if rule matches current target & source sheet
        def matches_sheet(rule_val, current_sheet_name):
            if not rule_val:
                return True
            v = str(rule_val).strip().lower()
            curr = str(current_sheet_name).strip().lower()
            if v in ['[all]', 'all', 'all sheets', '*', 'default']:
                return True
            return v == curr

        # Fetch SQLite database mapping rules
        all_rules = db_manager.get_all_excel_mappings(selected_company)

        def matches_company(rule_comp, current_company):
            if not rule_comp:
                return True
            rc = str(rule_comp).strip().lower()
            curr = str(current_company).strip().lower()
            if rc in ['all', 'all companies', '[all]', '*', 'default', '']:
                return True
            return rc == curr

        sheet_rules = [
            r for r in all_rules 
            if matches_sheet(r.get('source_sheet', ''), source_sheet_name)
            and matches_sheet(r.get('target_sheet', ''), target_sheet_name)
            and matches_company(r.get('company_name', 'All'), selected_company)
        ]
        # Sort so company-specific rules take precedence over general 'All' rules
        sheet_rules.sort(key=lambda r: 1 if str(r.get('company_name', 'All')).strip().lower() not in ['all', 'all companies', '[all]', '*', 'default', ''] else 0)


        for ctx in rows_ctx_list:
            max_r = max(header_row + 1, get_actual_max_row(ws) + 1)

            # Standard default row dictionary mapped by normalized lowercase header key
            row_dict = {}

            def set_row_val(key, val):
                if val is not None and str(val).strip() != '':
                    row_dict[key.strip().lower()] = str(val).strip()

            set_row_val('*action', 'Add')
            set_row_val('custom label (sku)', ctx.get('SKU'))
            set_row_val('category id', ctx.get('cat_id'))
            set_row_val('category name', ctx.get('cat_name'))
            set_row_val('title', ctx.get('TITLE'))
            set_row_val('start price', ctx.get('SELLING_PRICE_USD'))
            set_row_val('quantity', '5')
            set_row_val('item photo url', ctx.get('MAIN_IMG_URL'))
            set_row_val('condition id', '1000')
            set_row_val('description', ctx.get('HTML'))
            set_row_val('format', 'FixedPrice')
            set_row_val('duration', 'GTC')
            set_row_val('location', ctx.get('LOCATION', 'US'))
            set_row_val('shipping profile name', ctx.get('shipping_profile_name'))
            set_row_val('return profile name', ctx.get('return_profile_name'))
            set_row_val('payment profile name', ctx.get('payment_profile_name'))
            set_row_val('c:brand', ctx.get('BRAND_NAME'))
            set_row_val('c:type', ctx.get('TYPE'))
            set_row_val('c:metal', ctx.get('METEL'))
            set_row_val('c:metal purity', ctx.get('GOLD_KT'))
            set_row_val('c:main stone', ctx.get('MAIN_STONE_TYPE', 'Diamond'))
            set_row_val('c:main stone shape', ctx.get('CENTER_STONE_SHAPE'))
            set_row_val('c:main stone creation', ctx.get('main_stone_creation', 'Lab-Created'))
            set_row_val('c:total carat weight', ctx.get('TCW'))
            set_row_val('c:setting style', ctx.get('SETTING'))
            set_row_val('c:certification', ctx.get('CERTIFICATE'))
            set_row_val('c:secondary stone', ctx.get('SECONDARY_STONE'))

            item_len_val = (
                ctx.get('ITEM_LENGTH') or 
                ctx.get('item_length') or 
                ctx.get('Item Length') or 
                ctx.get('Item_Length') or 
                ctx.get('LENGTH') or 
                ctx.get('length') or 
                ctx.get('Length') or 
                ctx.get('CHAIN_LENGTH') or 
                ctx.get('Chain Length') or 
                ctx.get('C:Item Length')
            )
            if item_len_val and str(item_len_val).strip() not in ['', 'nan', 'none', 'null', '0']:
                set_row_val('c:item length', str(item_len_val).strip())

            display_header_map = {
                '*action': '*Action(SiteID=US|Country=US|Currency=USD|Version=1193)',
                'custom label (sku)': 'Custom label (SKU)',
                'category id': 'Category ID',
                'category name': 'Category name',
                'title': 'Title',
                'start price': 'Start price',
                'quantity': 'Quantity',
                'item photo url': 'Item photo URL',
                'condition id': 'Condition ID',
                'description': 'Description',
                'format': 'Format',
                'duration': 'Duration',
                'location': 'Location',
                'shipping profile name': 'ShippingProfileName',
                'return profile name': 'ReturnProfileName',
                'payment profile name': 'PaymentProfileName',
                'c:brand': 'C:Brand',
                'c:type': 'C:Type',
                'c:metal': 'C:Metal',
                'c:metal purity': 'C:Metal Purity',
                'c:main stone': 'C:Main Stone',
                'c:main stone shape': 'C:Main Stone Shape',
                'c:main stone creation': 'C:Main Stone Creation',
                'c:total carat weight': 'C:Total Carat Weight',
                'c:setting style': 'C:Style',
                'c:certification': 'C:Certification',
                'c:secondary stone': 'C:Secondary Stone',
                'c:item length': 'C:Item Length'
            }

            # Apply SQLite database mapping rules
            for rule in sheet_rules:
                tgt_col = str(rule.get('target_column', '')).strip()
                if tgt_col:
                    display_header_map[tgt_col.lower()] = tgt_col
                m_type = str(rule.get('mapping_type', 'direct')).strip().lower()
                src_col = str(rule.get('source_column', '')).strip()
                def_val = str(rule.get('default_value', '')).strip()

                if not tgt_col:
                    continue

                tgt_key = tgt_col.lower()

                if m_type == 'static':
                    if def_val:
                        formatted = def_val
                        if '{' in formatted and '}' in formatted:
                            for k, v in ctx.items():
                                tag = f"{{{k}}}"
                                formatted = formatted.replace(tag, str(v) if v is not None else "")
                        row_dict[tgt_key] = formatted
                elif m_type == 'direct':
                    val = ctx.get(src_col, None)
                    if val is None or str(val).strip() == '':
                        for k, v in ctx.items():
                            if str(k).strip().lower() == src_col.lower():
                                val = v
                                break
                    if val is not None and str(val).strip() != '':
                        row_dict[tgt_key] = str(val).strip()
                    elif def_val:
                        row_dict[tgt_key] = def_val
                    elif src_col.lower() in ['cat_id', 'category id'] and ctx.get('cat_id'):
                        row_dict[tgt_key] = str(ctx['cat_id']).strip()
                    elif src_col.lower() in ['cat_name', 'category name'] and ctx.get('cat_name'):
                        row_dict[tgt_key] = str(ctx['cat_name']).strip()
                elif m_type == 'template':
                    formatted = def_val
                    for k, v in ctx.items():
                        tag = f"{{{k}}}"
                        formatted = formatted.replace(tag, str(v) if v is not None else "")
                    row_dict[tgt_key] = formatted

            # Write values into exact header column positions
            for col_key, val in row_dict.items():
                if val is None or str(val).strip() == '':
                    continue
                col_idx = header_map.get(col_key)

                if not col_idx:
                    # Auto-add missing target column header to worksheet preserving exact user mapped case (e.g. C:Occasion)
                    col_idx = ws.max_column + 1
                    header_title = display_header_map.get(col_key, str(col_key).strip())
                    ws.cell(row=header_row, column=col_idx, value=header_title)

                    header_map[col_key] = col_idx

                clean_val = val
                if isinstance(val, str):
                    s_val = val.strip()
                    if s_val.isdigit():
                        if not (len(s_val) > 1 and s_val.startswith('0')):
                            try:
                                clean_val = int(s_val)
                            except ValueError:
                                clean_val = s_val
                    elif s_val.replace('.', '', 1).isdigit() and s_val.count('.') == 1:
                        if not (s_val.startswith('0') and not s_val.startswith('0.')):
                            try:
                                val_f = float(s_val)
                                clean_val = int(val_f) if val_f.is_integer() else val_f
                            except ValueError:
                                clean_val = s_val

                ws.cell(row=max_r, column=col_idx, value=clean_val)

        wb.save(excel_file_to_write)
        print(f"डेटा सफलता से शीट '{target_sheet_name}' में सही हेडर्स के साथ लिखा गया!")
        return True
    except Exception as e:
        print(f"Excel मैपिंग सेव करने में एरर: {e}")
        return False



@eel.expose
def get_schedule_time(days=0, hours=7, minutes=15):
    """
    US/Pacific टाइमस्टैम्प (eBay / Marketplace listing schedule format: YYYY-MM-DDTHH:MM:SS) 
    कैलकुलेट करता है। By default 0 days, 7 hours, 15 minutes add karta hai.
    """
    try:
        days = int(days)
        hours = int(hours)
        minutes = int(minutes)
    except (ValueError, TypeError):
        days, hours, minutes = 0, 7, 15
    utc_now = datetime.now(pytz.utc)
    pdt_tz = pytz.timezone('US/Pacific')
    pdt_now = utc_now.astimezone(pdt_tz)
    new_date = pdt_now + timedelta(days=days, hours=hours, minutes=minutes)
    new_date = new_date.replace(microsecond=0)
    formatted = new_date.strftime('%Y-%m-%dT%H:%M:%S')
    return {
        'status': 'success',
        'schedule_time': formatted,
        'current_pdt': pdt_now.strftime('%Y-%m-%d %I:%M:%S %p %Z'),
        'target_pdt': new_date.strftime('%Y-%m-%d %I:%M:%S %p %Z'),
        'days': days,
        'hours': hours,
        'minutes': minutes
    }


@eel.expose
def schedule():
    """वर्तमान US/Pacific टाइमस्टैम्प फ़ॉर्मेट करने का फ़ंक्शन (+7h 15m default)."""
    res = get_schedule_time(0, 7, 15)
    return res['schedule_time']



# ==================== 5. Core Application Engine (डेटा प्रोसेसिंग इंजन) ====================

@eel.expose
def get_company_name(name):
    """UI में यूज़र द्वारा चुनी गई कंपनी का नाम ग्लोबल वैरिएबल में सेट करता है और उसके अनुसार एक्सेल फ़ाइल रीसेट करता है।"""
    global selected_company
    selected_company = name
    print(f"चुनी गई कंपनी: {selected_company}")
    clear_multiXlsx(force=True)


@eel.expose
def get_product_name(value):
    """UI में यूज़र द्वारा चुना गया प्रोडक्ट शिट नेम सेट करता है।"""
    global SHEET_NAME
    SHEET_NAME = value
    print(f"चुना गया प्रोडक्ट शीट: {SHEET_NAME}")


@eel.expose
def color_variation(c_var):
    """कलर वैरिएशन ऑन/ऑफ़ फ़्लैग सेट करता है।"""
    global c_variation
    c_variation = bool(c_var)


@eel.expose
def gold_purity_variation(gold_kt_var):
    """गोल्ड प्योरिटी वैरिएशन ऑन/ऑफ़ फ़्लैग सेट करता है।"""
    global gold_kt_variation
    gold_kt_variation = bool(gold_kt_var)





@eel.expose
def app1():
    """
    app1() - ऑटोमैटिक मल्टी-शीट डेटा प्रोसेसिंग पाइपलाइन फ़ंक्शन:
    ----------------------------------------------------------
    'data.xlsx' में मौजूद सभी शीट्स (RING, EARRINGS, PENDANT, BRACELET) का डेटा स्वतः एक बार में प्रोसेस करके 'Multi_API.xlsx' में सहेजा जाता है।
    """
    global selected_company

    load_settings()

    cfg = company_settings.get(selected_company)
    if not cfg:
        print(f"त्रुटि: कंपनी '{selected_company}' की सेटिंग्स डेटाबेस में नहीं मिलीं!")
        return "Please select a Company first!"

    data_file = get_app_path('data.xlsx')
    valid_sheets = db_manager.get_data_file_sheets(data_file)
    if not valid_sheets:
        print("त्रुटि: डेटाबेस में कोई प्रोडक्ट डेटा नहीं मिला!")
        return "No product data found in database!"

    # Multi_API.xlsx फ़ाइल को रीसेट करें
    clear_multiXlsx(force=True)

    print(f"ऑटो-प्रोसेसिंग स्टार्ट: शीट्स = {valid_sheets}, कंपनी = {selected_company}")

    shipping_profile_name = cfg.get("shipping_profile_name", "")
    return_profile_name = cfg.get("return_profile_name", "")
    payment_profile_name = cfg.get("payment_profile_name", "")
    BRAND_NAME = cfg.get("BRAND_NAME", "")
    LOCATION = cfg.get("LOCATION", "US")

    new_rows_lst = []

    for curr_sheet in valid_sheets:
        # First query directly from SQLite database product_data (instant!)
        data_rows = db_manager.get_product_data_rows(curr_sheet)
        if not data_rows and os.path.exists(data_file):
            try:
                data_rows = pd.read_excel(data_file, sheet_name=curr_sheet).to_dict(orient='records')
            except Exception as e:
                print(f"data.xlsx की शीट '{curr_sheet}' पढ़ने में एरर: {e}")
                continue

        if not data_rows:
            continue

        for data in data_rows:
            raw_sku = str(data.get('SKU', '')).strip()
            # If SKU is empty, NaN, or invalid, skip processing empty row
            if not raw_sku or raw_sku.lower() in ['nan', 'none', 'null', '0', '']:
                continue
            MAIN_IMG_URL = r'https://livuniq.pythonanywhere.com/media/000000.png'
            MAIN_STONE_TYPE = 'Diamond'
            main_stone_creation = 'Lab-Created'
            HTML = ""

            # बेसिक रो डेटा निकालें
            CATEGORY = str(data.get('CATEGORY', '')).lower()
            SKU = str(data.get('SKU', ''))
            SELLING_PRICE_USD = f"{float(data.get('SELLING_PRICE_USD', 0)):.2f}"
            CENTER_STONE_SHAPE = str(data.get('CENTER_STONE_SHAPE', '')).title()
            CENTER_STONE_WEIGHT = f"{float(data.get('CENTER_STONE_WEIGHT', 0)):.2f}"
            TOTAL_DIAMOND_PCS = data.get('TOTAL_DIAMOND_PCS', 1)
            GOLD_KT = str(data.get('GOLD_KT', '')).lower()
            GOLD_COLOR = str(data.get('GOLD_COLOR', '')).title()
            DIAMOND_COLOR = str(data.get('CENTER_DIAMOND_COLOR', ''))
            DIAMOND_CLARITY = str(data.get('CENTER_DIAMOND_CLARITY', ''))
            SIDE_STONE_SHAPE = str(data.get('SIDE_STONE_SHAPE', '')).title()
            SIDE_STONE_CLARITY = str(data.get('SIDE_STONE_COLOR_CLARITY', ''))
            SIDE_STONE_WEIGHT = str(data.get('SIDE_STONE_WEIGHT', '0'))
            CERTIFICATE = str(data.get('Certified', '---'))
            CERTI_BY = f"{CERTIFICATE} Certified"
            SETTING = str(data.get('SETTING', ''))
            METEL = "Gold"

            if GOLD_COLOR.lower() == 'yellow':
                MAIN_IMG_URL = r'https://livuniq.pythonanywhere.com/media/11111.png'
            elif GOLD_COLOR.lower() == 'rose':
                MAIN_IMG_URL = r'https://livuniq.pythonanywhere.com/media/22222.png'

            if SIDE_STONE_SHAPE.lower() != 'nan' and SIDE_STONE_WEIGHT.lower() != 'nan' and float(SIDE_STONE_WEIGHT or 0) > 0:
                center_stone_spec = "Main Stone Specifications"
                TCW = f"{round(float(CENTER_STONE_WEIGHT) + float(SIDE_STONE_WEIGHT), 2):.2f}"
                SIDE_STONE_WEIGHT = f"{float(SIDE_STONE_WEIGHT):.2f}"
                hide = ""
                try:
                    SIDE_COLOR, SIDE_CLARITY = SIDE_STONE_CLARITY.split('/')
                except ValueError:
                    SIDE_COLOR, SIDE_CLARITY = '', ''
            else:
                center_stone_spec = "Stone Details"
                TCW = CENTER_STONE_WEIGHT
                hide = "hide"
                SIDE_STONE_SHAPE = "--"
                SIDE_STONE_WEIGHT = "0.00"
                SIDE_COLOR = ''
                SIDE_CLARITY = ''

            # Calculate SECONDARY_STONE (Diamond if side stones exist, else empty)
            side_shape_str = str(SIDE_STONE_SHAPE).strip().lower()
            if side_shape_str and side_shape_str not in ['--', 'none', 'null', 'nan', 'n/a', '0', '']:
                SECONDARY_STONE = 'Diamond'
            else:
                SECONDARY_STONE = ''

            if GOLD_KT.lower() in ["950", "pt", "platinum"]:
                METEL = "Platinum"
                TITLE_FILE = "title_templates-platinum.xlsx"
            else:
                TITLE_FILE = "title_templates-gold.xlsx"

            sheet_upper = str(curr_sheet).strip().upper()
            cat_col_upper = str(data.get('CATEGORY', '')).strip().upper()

            def is_mens(val):
                if not val:
                    return False
                return bool(re.search(r"\bMENS?\b|MEN'S", str(val).upper()))

            if sheet_upper == 'EARRINGS' or 'EARRING' in cat_col_upper:
                TYPE = 'Earring'
                target_sheet = "Cat-Earrings"
                cat_id = 10970
                cat_name = r"/Jewelry & Watches/Fine Jewelry/Earrings"
            elif sheet_upper == 'PENDANT' or 'PENDANT' in cat_col_upper or 'NECKLACE' in cat_col_upper:
                TYPE = 'Pendant'
                target_sheet = "Cat-NecklacesPendants"
                cat_id = 10976
                cat_name = r"/Jewelry & Watches/Fine Jewelry/Necklaces & Pendants"
            elif sheet_upper == 'BRACELET' or 'BRACELET' in cat_col_upper or 'CHARM' in cat_col_upper:
                TYPE = 'Bracelet'
                target_sheet = "Cat-BraceletsCharms"
                cat_id = 10972
                cat_name = r"/Jewelry & Watches/Fine Jewelry/Bracelets & Charms"
            else:
                # 1. Primary check: SKU Suffixes for Rings
                raw_sku_str = str(SKU).strip().lower()
                c_bbx = clean_sku(SKU, 'bbx') or ('bbx' in raw_sku_str)
                c_mmx = clean_sku(SKU, 'mmx') or ('mmx' in raw_sku_str)
                c_ssx = clean_sku(SKU, 'ssx') or ('ssx' in raw_sku_str)
                c_frx = clean_sku(SKU, 'frx') or ('frx' in raw_sku_str)

                if c_bbx:
                    TYPE = 'Wedding Band'
                    SKU = clean_sku(SKU, 'bbx') or SKU
                    cat_id = 261977
                    cat_name = r'/Jewelry & Watches/Engagement & Wedding/Wedding & Anniversary Bands'
                    target_sheet = "Cat-WeddingAnniversaryBands"
                elif c_mmx:
                    TYPE = "Men's Ring"
                    SKU = clean_sku(SKU, 'mmx') or SKU
                    cat_id = 137856
                    cat_name = r"/Jewelry & Watches/Men's Jewelry/Rings"
                    target_sheet = "Cat-Rings"
                elif c_ssx:
                    TYPE = 'Wedding Ring Set'
                    SKU = clean_sku(SKU, 'ssx') or SKU
                    cat_id = 261976
                    cat_name = r"/Jewelry & Watches/Engagement & Wedding/Engagement & Wedding Ring Sets"
                    target_sheet = "Cat-EngagementWeddingRingSets"
                elif c_frx:
                    TYPE = 'Engagement Ring'
                    SKU = clean_sku(SKU, 'frx') or SKU
                    target_sheet = "Cat-EngagementRings"
                    cat_id = 261994
                    cat_name = r"/Jewelry & Watches/Fine Jewelry/Rings"
                # 2. Secondary check: Specific sheet name or category column (for dedicated sheets without SKU suffixes)
                elif 'WEDDING BAND' in sheet_upper or 'WEDDING BAND' in cat_col_upper or sheet_upper in ['BAND', 'BANDS']:
                    TYPE = 'Wedding Band'
                    cat_id = 261977
                    cat_name = r'/Jewelry & Watches/Engagement & Wedding/Wedding & Anniversary Bands'
                    target_sheet = "Cat-WeddingAnniversaryBands"
                elif 'WEDDING RING SET' in sheet_upper or 'WEDDING SET' in cat_col_upper:
                    TYPE = 'Wedding Ring Set'
                    cat_id = 261976
                    cat_name = r"/Jewelry & Watches/Engagement & Wedding/Engagement & Wedding Ring Sets"
                    target_sheet = "Cat-EngagementWeddingRingSets"
                elif is_mens(sheet_upper) or is_mens(cat_col_upper):
                    TYPE = "Men's Ring"
                    cat_id = 137856
                    cat_name = r"/Jewelry & Watches/Men's Jewelry/Rings"
                    target_sheet = "Cat-Rings"
                else:
                    TYPE = 'Engagement Ring'
                    target_sheet = "Cat-EngagementRings"
                    cat_id = 261975
                    cat_name = r'/Jewelry & Watches/Engagement & Wedding/Engagement Rings'

            # Calculate subcategory style (Solitaire, 3 Stone, etc.)
            sub_category = get_row_subcategory(data)

            # Build unified row context combining all raw data.xlsx columns + calculated variables
            row_context = {str(k): v for k, v in data.items() if pd.notna(v) and v is not None}
            # Item Length extraction for Bracelets / Necklaces / Pendants
            item_length_val = None
            for l_key in ['LENGTH', 'length', 'Length', 'ITEM_LENGTH', 'item_length', 'Item Length', 'Item_Length', 'CHAIN_LENGTH', 'chain_length', 'Chain Length', 'C:Item Length', 'c:item length', 'BRACELET_LENGTH', 'bracelet_length']:
                if l_key in data and pd.notna(data[l_key]) and str(data[l_key]).strip() not in ['', 'nan', 'none', 'null', '0']:
                    item_length_val = str(data[l_key]).strip()
                    break

            if item_length_val:
                clean_len = item_length_val.strip()
                if clean_len.isdigit() or (clean_len.replace('.', '', 1).isdigit() and 'inch' not in clean_len.lower()):
                    item_length_str = f"{clean_len} Inch"
                else:
                    item_length_str = clean_len
            else:
                item_length_str = ""

            row_context.update({
                'SKU': SKU,
                'TCW': TCW,
                'CENTER_STONE_SHAPE': CENTER_STONE_SHAPE,
                'CENTER_STONE_WEIGHT': CENTER_STONE_WEIGHT,
                'TOTAL_DIAMOND_PCS': TOTAL_DIAMOND_PCS,
                'GOLD_KT': GOLD_KT,
                'GOLD_COLOR': GOLD_COLOR,
                'METEL': METEL,
                'METAL': METEL,
                'CERTIFICATE': CERTIFICATE,
                'CERTI_BY': CERTI_BY,
                'DIAMOND_CLARITY': DIAMOND_CLARITY,
                'DIAMOND_COLOR': DIAMOND_COLOR,
                'SIDE_STONE_SHAPE': SIDE_STONE_SHAPE,
                'SIDE_STONE_WEIGHT': SIDE_STONE_WEIGHT,
                'SIDE_COLOR': SIDE_COLOR,
                'SIDE_CLARITY': SIDE_CLARITY,
                'SECONDARY_STONE': SECONDARY_STONE,
                'SETTING': sub_category if sub_category != 'default' else SETTING,
                'TYPE': TYPE,
                'CATEGORY': CATEGORY,
                'SELLING_PRICE_USD': SELLING_PRICE_USD,
                'BRAND_NAME': BRAND_NAME,
                'LOCATION': LOCATION,
                'shipping_profile_name': shipping_profile_name,
                'return_profile_name': return_profile_name,
                'payment_profile_name': payment_profile_name,
                'hide': hide,
                'center_stone_spec': center_stone_spec,
                'ITEM_LENGTH': item_length_str,
                'item_length': item_length_str,
                'Item Length': item_length_str,
                'Item_Length': item_length_str,
                'LENGTH': item_length_str,
                'length': item_length_str,
                'Length': item_length_str,
                'CHAIN_LENGTH': item_length_str,
                'Chain Length': item_length_str,
                'C:Item Length': item_length_str,
                'c:item length': item_length_str
            })

            if 'xyz' in locals():
                row_context['xyz'] = locals()['xyz']

            TITLE = generate_title(
                TITLE_FILE,
                TYPE,
                sub_category,
                company_name=selected_company,
                **row_context
            )

            CENTER_STONE_SHAPE, MAIN_STONE_TYPE, main_stone_creation, TITLE = process_center_stone(CENTER_STONE_SHAPE, TITLE)

            # Update TITLE & stone specs in context after processing
            row_context['TITLE'] = TITLE
            row_context['CENTER_STONE_SHAPE'] = CENTER_STONE_SHAPE
            row_context['MAIN_STONE_TYPE'] = MAIN_STONE_TYPE
            row_context['main_stone_creation'] = main_stone_creation

            cat_for_html = TYPE if TYPE else CATEGORY
            html_ctx = row_context

            HTML = generate_company_html_from_db(selected_company, cat_for_html, data, html_ctx)


            full_ctx = {**data, **html_ctx}
            full_ctx.update({
                'source_sheet': curr_sheet,
                'cat_id': cat_id,
                'cat_name': cat_name,
                'target_sheet': target_sheet,
                'MAIN_IMG_URL': MAIN_IMG_URL,
                'LOCATION': LOCATION,
                'shipping_profile_name': shipping_profile_name,
                'return_profile_name': return_profile_name,
                'payment_profile_name': payment_profile_name,
                'BRAND_NAME': BRAND_NAME,
                'TYPE': TYPE,
                'METEL': METEL,
                'GOLD_KT': GOLD_KT,
                'MAIN_STONE_TYPE': MAIN_STONE_TYPE,
                'CENTER_STONE_SHAPE': CENTER_STONE_SHAPE,
                'main_stone_creation': main_stone_creation,
                'TCW': TCW,
                'SETTING': SETTING,
                'HTML': HTML,
                'SELLING_PRICE_USD': SELLING_PRICE_USD,
                'SKU': SKU
            })
            new_rows_lst.append(full_ctx)

    if new_rows_lst:
        rows_by_target = {}
        for row_ctx in new_rows_lst:
            t_sheet = row_ctx.get('target_sheet', 'Cat-EngagementRings')
            if t_sheet not in rows_by_target:
                rows_by_target[t_sheet] = []
            rows_by_target[t_sheet].append(row_ctx)

        multi_api_file = get_app_path("Multi_API.xlsx")
        for t_sheet, rows in rows_by_target.items():
            src_sheet = rows[0].get('source_sheet', 'RING')
            save_excel_mapped_rows(rows, multi_api_file, t_sheet, src_sheet)

        output_filename = f"API-{get_shuffled_datetime_string()}.xlsx"
        output_filepath = get_app_path(output_filename)
        copy_and_rename_excel_file(multi_api_file, output_filepath)
        remove_first_row_except_first_sheet(output_filepath)

        # Schedule auto-deletion of this file after 10 minutes (600 seconds)
        schedule_file_deletion(output_filepath, delay_seconds=600)
        # Clean up any other leftover temporary API files older than 10 minutes
        cleanup_old_api_files(max_age_seconds=600)

        # Synchronize data into Product & SKU Catalog (PartyDataRecord)
        global last_catalog_sync_info
        try:
            from main_app import catalog_sync
            last_catalog_sync_info = catalog_sync.sync_data_to_catalog(data_file, company_name=selected_company)
            print(f"Product & SKU Catalog Synced: {last_catalog_sync_info.get('added', 0)} added, {last_catalog_sync_info.get('updated', 0)} updated for '{last_catalog_sync_info.get('party_name', selected_company)}'")
        except Exception as e:
            print(f"Error syncing to Product & SKU Catalog: {e}")

        print("ऑटोमैटिक मल्टी-शीट डेटा प्रोसेसिंग सफलता से पूरी हुई!")
        return f"Successfully processed {len(new_rows_lst)} items across all sheets! Saved as {output_filename}"

    return "No items were found or processed."






# ==================== 6. Database API Routes (Eel Exposed APIs) ====================
# यह सेक्शन React UI से सीधे जुड़े हुए सभी 30+ SQLite API फ़ंक्शन्स को रखता है।
# प्रत्येक फ़ंक्शन में `@eel.expose` डैकोरेटर लगा है ताकि JavaScript इसे `await callEel(...)` से कॉल कर सके।

@eel.expose
def get_company_list():
    """डेटाबेस से सभी उपलब्ध कंपनियों की सूची (List) रिटर्न करता है।"""
    load_settings()
    return list(company_settings.keys())

@eel.expose
def get_product_list():
    """डेटाबेस से सभी उपलब्ध प्रोडक्ट्स की लिस्ट रिटर्न करता है।"""
    load_settings()
    return product_list

@eel.expose
def get_all_company_policies():
    """डेटाबेस से सभी कंपनियों की बिज़नेस पॉलिसीज़ (Shipping/Return/Payment) फेच करता है।"""
    return db_manager.get_all_company_policies()

@eel.expose
def save_company_policy(company_data):
    """कंपनी की बिज़नेस पॉलिसी डेटाबेस में जोड़ता या अपडेट करता है।"""
    res = db_manager.save_company_policy(company_data)
    load_settings()
    return res

@eel.expose
def delete_company_policy(company_name):
    """कंपनी पॉलिसी को डेटाबेस से डिलीट (Hataana) करता है।"""
    res = db_manager.delete_company_policy(company_name)
    load_settings()
    return res

@eel.expose
def get_all_title_templates():
    """डेटाबेस से सभी मेटल और कैटेगरी के लिए टाइटल टैम्प्लेट्स लाता है।"""
    return db_manager.get_all_title_templates()

@eel.expose
def save_title_template(template_data):
    """नया टाइटल टैम्प्लेट डेटाबेस में सेव करता है।"""
    return db_manager.save_title_template(template_data)

@eel.expose
def delete_title_template(template_id):
    """टाइटल टैम्प्लेट आईडी द्वारा डेटाबेस से हटाता है।"""
    return db_manager.delete_title_template(template_id)

@eel.expose
def save_product(product_name):
    """नया प्रोडक्ट नेम डेटाबेस में जोड़ता है।"""
    res = db_manager.save_product(product_name)
    load_settings()
    return res

@eel.expose
def delete_product(product_id):
    """प्रोडक्ट आईडी द्वारा डिलीट करता है।"""
    res = db_manager.delete_product(product_id)
    load_settings()
    return res

@eel.expose
def get_all_placeholders():
    """सभी प्लेसहोल्डर वैरिएबल्स (जैसे {TITLE}, {TCW}, {GOLD_KT}) की लिस्ट लाता है।"""
    return db_manager.get_all_placeholders()

@eel.expose
def add_placeholder(name):
    """नया प्लेसहोल्डर नाम जोड़ता है।"""
    return db_manager.add_placeholder(name)

@eel.expose
def update_placeholder(p_id, new_name):
    """प्लेसहोल्डर का नाम अपडेट करता है।"""
    return db_manager.update_placeholder(p_id, new_name)

@eel.expose
def delete_placeholder(p_id):
    """प्लेसहोल्डर डिलीट करता है।"""
    return db_manager.delete_placeholder(p_id)

@eel.expose
def get_all_categories():
    """डेटाबेस से सभी कैटेगरीज़ फेच करता है।"""
    return db_manager.get_all_categories()

@eel.expose
def add_category(name):
    """नई कैटेगरी का नाम जोड़ता है।"""
    return db_manager.add_category(name)

@eel.expose
def update_category(c_id, new_name):
    """कैटेगरी का नाम अपडेट करता है।"""
    return db_manager.update_category(c_id, new_name)

@eel.expose
def delete_category(c_id):
    """कैटेगरी डिलीट करता है।"""
    return db_manager.delete_category(c_id)

@eel.expose
def get_all_setting_columns(category=None):
    """Fetch setting columns filtered by category if provided."""
    return db_manager.get_all_setting_columns(category)

@eel.expose
def add_setting_column(name, category=None):
    """Add setting column with optional category scope."""
    return db_manager.add_setting_column(name, category)

@eel.expose
def update_setting_column(col_id, new_name):
    """Update setting column name."""
    return db_manager.update_setting_column(col_id, new_name)

@eel.expose
def delete_setting_column(col_id):
    """Delete setting column."""
    return db_manager.delete_setting_column(col_id)

@eel.expose
def backup_database(description=""):
    """Create timestamped DB backup with optional description."""
    return db_manager.backup_database(description)

@eel.expose
def save_backup_note(filename, note):
    """Save or update description note for a backup file."""
    return db_manager.save_backup_note(filename, note)

@eel.expose
def delete_backup(filename):
    """Delete a database backup file."""
    return db_manager.delete_backup(filename)

@eel.expose
def list_database_backups():
    """List existing DB backups."""
    return db_manager.list_database_backups()

@eel.expose
def restore_database(file_path=None, file_b64=None):
    """Restore database from backup file path or base64 string."""
    import base64
    try:
        file_bytes = None
        if file_b64:
            if ',' in file_b64:
                file_b64 = file_b64.split(',', 1)[1]
            file_bytes = base64.b64decode(file_b64)
        return db_manager.restore_database(backup_file_path=file_path, file_bytes=file_bytes)
    except Exception as e:
        return {"status": "error", "message": f"Restore failed: {str(e)}"}

@eel.expose
def get_all_subcategories(category_name=None):
    """सब-कैटेगरीज़ की लिस्ट फेच करता है।"""
    return db_manager.get_all_subcategories(category_name)

@eel.expose
def add_subcategory(name, category_name):
    """नई सब-कैटेगरी जोड़ता है।"""
    return db_manager.add_subcategory(name, category_name)

@eel.expose
def update_subcategory(sub_id, new_name, category_name=None):
    """सब-कैटेगरी का नाम अपडेट करता है।"""
    return db_manager.update_subcategory(sub_id, new_name, category_name)

@eel.expose
def delete_subcategory(sub_id):
    """सब-कैटेगरी डिलीट करता है।"""
    return db_manager.delete_subcategory(sub_id)

@eel.expose
def get_all_company_html_templates():
    """डेटाबेस में मौजूद सभी कंपनी HTML कोड टैम्प्लेट्स फेच करता है।"""
    return db_manager.get_all_company_html_templates()

@eel.expose
def save_company_html_template(company_name, category="default", subcategory="default", html_code="", tmpl_id=None, *args, **kwargs):
    """
    कंपनी का कस्टम HTML लिस्टिंग कोड डेटाबेस में सेव करता है।
    React UI से (company_name, category, subcategory, html_code, tmpl_id) 5 पैरामीटर्स प्राप्त करता है।
    """
    if args:
        if len(args) == 1 and tmpl_id is None:
            tmpl_id = args[0]
        elif len(args) >= 2:
            if not html_code:
                html_code = args[0]
            if tmpl_id is None:
                tmpl_id = args[1]
    return db_manager.save_company_html_template(company_name, category, subcategory, html_code, tmpl_id)

@eel.expose
def delete_company_html_template(tmpl_id):
    """कंपनी HTML कोड टैम्प्लेट डिलीट करता है।"""
    return db_manager.delete_company_html_template(tmpl_id)

@eel.expose
def export_html_templates_to_excel(company_name=""):
    """Export saved HTML templates to Excel b64."""
    return db_manager.export_html_templates_to_excel(company_name)

@eel.expose
def import_html_templates_from_excel(file_b64=None, file_path=None):
    """Bulk import HTML templates from Excel (.xlsx) file base64 or path."""
    return db_manager.import_html_templates_from_excel(file_path=file_path, file_b64=file_b64)

@eel.expose
def get_sample_html_excel_data():
    """Get sample HTML templates Excel file base64."""
    return db_manager.get_sample_html_excel_data()

@eel.expose
def get_admin_password():
    """एडमिन सेटिंग्स का वर्तमान पासवर्ड फेच करता है (डिफ़ॉल्ट 0000)।"""
    return db_manager.get_admin_password()

@eel.expose
def update_admin_password(new_password):
    """एडमिन पासवर्ड को अपडेट करता है।"""
    return db_manager.update_admin_password(new_password)

# ==================== Excel Mappings Exposed API ====================
@eel.expose
def get_all_excel_mappings():
    """डेटाबेस से सभी एक्सेल मैपिंग रूल्स फेच करता है।"""
    return db_manager.get_all_excel_mappings()

@eel.expose
def save_excel_mapping(source_sheet, source_column, target_sheet, target_column, mapping_type='direct', default_value='', mapping_id=None, company_name='All', *args, **kwargs):
    """एक्सेल कॉलम मैपिंग रूल को सेव या अपडेट करता है।"""
    if args:
        if len(args) == 1 and company_name == 'All':
            company_name = args[0]
    return db_manager.save_excel_mapping(source_sheet, source_column, target_sheet, target_column, mapping_type, default_value, mapping_id, company_name)

@eel.expose
def delete_excel_mapping(mapping_id):
    """एक्सेल कॉलम मैपिंग रूल को डिलीट करता है।"""
    return db_manager.delete_excel_mapping(mapping_id)

@eel.expose
def reset_default_excel_mappings():
    """एक्सेल कॉलम मैपिंग रूल्स को डिफ़ॉल्ट पर रीसेट करता है।"""
    return db_manager.reset_default_excel_mappings()

@eel.expose
def get_data_file_sheets(file_path="data.xlsx"):
    """data.xlsx फ़ाइल की वास्तविक वर्किंग शीट्स प्राप्त करता है।"""
    return db_manager.get_data_file_sheets(file_path)

@eel.expose
def get_target_file_sheets(file_path="Multi_API.xlsx"):
    """Multi_API.xlsx फ़ाइल की टारगेट शीट्स प्राप्त करता है।"""
    return db_manager.get_target_file_sheets(file_path)

@eel.expose
def sync_excel_mappings(data_file="data.xlsx"):
    """data.xlsx की शीट्स के साथ मैपिंग रूल्स सिंक करता है।"""
    return db_manager.sync_excel_mappings_with_file(data_file)

@eel.expose
def get_product_data_count():
    """डेटाबेस में सेव प्रोडक्ट आइटम्स की कुल संख्या प्राप्त करता है।"""
    return db_manager.get_product_data_count()

@eel.expose
def get_product_data_rows(category=None):
    """डेटाबेस से सीधे प्रोडक्ट रो डाटा प्राप्त करता है।"""
    return db_manager.get_product_data_rows(category)

@eel.expose
def clear_product_data(category=None):
    """डेटाबेस से प्रोडक्ट डाटा साफ़ करता है।"""
    return db_manager.clear_product_data(category)

@eel.expose
def seed_product_data_from_excel(file_path=None):
    """एक्सेल फ़ाइल को सीधे डेटाबेस में कन्वर्ट करके सेव करता है।"""
    return db_manager.seed_product_data_from_excel(file_path)

@eel.expose
def seed_template_headers_from_file(template_path=None):
    """मास्टर टेम्पलेट हेडर्स को डेटाबेस में सेव करता है।"""
    return db_manager.seed_template_headers_from_file(template_path)

# ==================== eBay HTML Modifier & Floating Quick Action Widget ====================
import json

try:
    import pyperclip
except Exception:
    class PyperClipFallback:
        @staticmethod
        def paste():
            return ""
        @staticmethod
        def copy(text):
            pass
    pyperclip = PyperClipFallback()

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'widget_config.json')
for_new_code = "|x|"
for_old_code = "zzz"

current_replace_from = ""
current_replace_to = ""
current_remove_video = True
floating_window = None

def load_widget_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('width', 280), data.get('height', 150)
    except Exception:
        pass
    return 280, 150

@eel.expose
def save_widget_size(width, height):
    try:
        w = max(180, int(width))
        h = max(100, int(height))
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'width': w, 'height': h}, f)
    except Exception as e:
        print(f"Error saving widget size: {e}")

@eel.expose
def resize_widget(width, height):
    global floating_window
    try:
        w = max(180, int(width))
        h = max(100, int(height))
        if floating_window:
            try:
                floating_window.resize(w, h)
            except Exception:
                pass
        save_widget_size(w, h)
        return True
    except Exception as e:
        print(f"Error resizing widget: {e}")
        return False

def remove_video_tags(code):
    if not code:
        return code
    code = re.sub(r'<button[^>]*class="[^"]*uploader-thumbnails-ux__video[^"]*"[\s\S]*?</button>', '', code, flags=re.IGNORECASE)
    code = re.sub(r'<button[^>]*aria-label="[^"]*video[^"]*"[\s\S]*?</button>', '', code, flags=re.IGNORECASE)
    code = re.sub(r'<button[^>]*aria-label="Delete video[^"]*"[\s\S]*?</button>', '', code, flags=re.IGNORECASE)
    return code

@eel.expose
def update_video_rule(remove_video):
    global current_remove_video
    current_remove_video = bool(remove_video)
    try:
        if hasattr(eel, 'sync_video_toggle_ui'):
            eel.sync_video_toggle_ui(current_remove_video)()
    except Exception as e:
        print(f"Sync video toggle UI error: {e}")
    return current_remove_video

def replace_image_format(input_string):
    return re.sub(r'\b(png|webp)\b', 'JPG', input_string, flags=re.IGNORECASE)

def apply_replacements(template_code, replacements):
    for old, new in replacements.items():
        template_code = template_code.replace(old, new)
    return template_code

def imgDict(images_list):
    big_imgs_list = []
    thumb_imgs_list = []
    for image_token in images_list:
        parts = image_token.split('/')
        token = parts[-2] if len(parts) >= 2 else image_token
        big_img = rf'https://i.ebayimg.com/images/g/{token}/s-l1600.webp'
        thumb_img = rf'https://i.ebayimg.com/images/g/{token}/s-l100.webp'
        thumb_imgs_list.append(thumb_img)
        big_imgs_list.append(big_img)
    return {'main': big_imgs_list, 'thumb': thumb_imgs_list}

@eel.expose
def modify(html, replace_from, replace_to, remove_video=None):
    try:
        should_remove_video = current_remove_video if remove_video is None else bool(remove_video)
        code = (html or "").strip()
        if not code:
            try:
                code = (pyperclip.paste() or "").strip()
            except Exception:
                code = ""

        if not code:
            return 'EMPTY_INPUT'

        if should_remove_video:
            print("Stripping eBay video tags from input HTML...")
            code = remove_video_tags(code)

        if replace_from:
            replace_to_str = replace_to or ""
            from_list = replace_from.split('||')
            to_list = replace_to_str.split('||')
            for i, from_item in enumerate(from_list):
                if from_item:
                    to_item = to_list[i] if i < len(to_list) else ""
                    code = code.replace(from_item, to_item)

        if for_new_code in code:
            print("Processing new code format (|x|)")
            parts = code.split(for_new_code)
            if len(parts) < 2:
                return 'ERROR'

            HTML = {
                'imgs_code': replace_image_format(parts[1]),
                'ebay_template_code': parts[0]
            }

            pattern = r'https.*?2\.JPG'
            images_dict = imgDict(re.findall(pattern, HTML['imgs_code']))

            try:
                IMG_1 = images_dict['main'][0]
                THUMB_1 = images_dict['thumb'][0]
                d1 = None
            except IndexError:
                IMG_1 = ''
                THUMB_1 = ''
                d1 = 'for="img1" style="display:none"'

            try:
                IMG_2 = images_dict['main'][1]
                THUMB_2 = images_dict['thumb'][1]
                d2 = None
            except IndexError:
                IMG_2 = ''
                THUMB_2 = ''
                d2 = 'for="img2" style="display:none"'

            try:
                IMG_3 = images_dict['main'][2]
                THUMB_3 = images_dict['thumb'][2]
                d3 = None
            except IndexError:
                IMG_3 = ''
                THUMB_3 = ''
                d3 = 'for="img3" style="display:none"'

            try:
                IMG_4 = images_dict['main'][3]
                THUMB_4 = images_dict['thumb'][3]
                d4 = None
            except IndexError:
                IMG_4 = ''
                THUMB_4 = ''
                d4 = 'for="img4" style="display:none"'

            try:
                IMG_5 = images_dict['main'][4]
                THUMB_5 = images_dict['thumb'][4]
                d5 = None
            except IndexError:
                IMG_5 = ''
                THUMB_5 = ''
                d5 = 'for="img5" style="display:none"'

            replacements = {
                'IMG_1': IMG_1, 'THUMB_1': THUMB_1,
                'IMG_2': IMG_2, 'THUMB_2': THUMB_2,
                'IMG_3': IMG_3, 'THUMB_3': THUMB_3,
                'IMG_4': IMG_4, 'THUMB_4': THUMB_4,
                'IMG_5': IMG_5, 'THUMB_5': THUMB_5,
            }

            ebay_template_code = apply_replacements(HTML['ebay_template_code'], replacements)

            if d1 is not None: ebay_template_code = ebay_template_code.replace('for="img1"', d1)
            if d2 is not None: ebay_template_code = ebay_template_code.replace('for="img2"', d2)
            if d3 is not None: ebay_template_code = ebay_template_code.replace('for="img3"', d3)
            if d4 is not None: ebay_template_code = ebay_template_code.replace('for="img4"', d4)
            if d5 is not None: ebay_template_code = ebay_template_code.replace('for="img5"', d5)

            retrn = ebay_template_code
            try:
                pyperclip.copy(retrn)
            except Exception:
                pass
            return retrn

        elif for_old_code in code:
            print("Processing old code format (zzz)")
            template_html = code
            def split_with_zzz_to_list(text):
                return [part.strip() for part in text.split(for_old_code)]

            def get_new_token(text):
                pattern = r"https[^\s]*2\.(?:jpg|png|webp)"
                links = re.findall(pattern, text, flags=re.IGNORECASE)
                return [url.split('/')[-2] if '/' in url else None for url in links]

            def replace_links(text, pattern, replacements):
                links = re.findall(pattern, text, flags=re.IGNORECASE)
                for i, link in enumerate(links):
                    if i < len(replacements):
                        parts = link.split("/")
                        if len(parts) >= 2:
                            parts[-2] = replacements[i]
                            text = text.replace(link, "/".join(parts))
                return text

            main_pattern = r"https://i\.ebayimg[^\s]*1600\.webp"
            thumb_pattern = r"https://i\.ebayimg[^\s]*100\.webp"

            full_html = split_with_zzz_to_list(template_html)
            if len(full_html) < 2:
                return 'ERROR'

            tokens = get_new_token(full_html[1])
            res_html = replace_links(full_html[0], main_pattern, tokens)
            res_html = replace_links(res_html, thumb_pattern, tokens)

            try:
                pyperclip.copy(res_html)
            except Exception:
                pass
            return res_html
        else:
            return 'NO_MARKER'

    except Exception as e:
        print(f"Error in modify: {e}")
        return 'ERROR'

@eel.expose
def replace_only(html, replace_from, replace_to, remove_video=None):
    try:
        should_remove_video = current_remove_video if remove_video is None else bool(remove_video)
        code = (html or "").strip()
        if not code:
            try:
                code = (pyperclip.paste() or "").strip()
            except Exception:
                code = ""

        if not code:
            return 'EMPTY_INPUT'

        if should_remove_video:
            print("Stripping eBay video tags in replace_only...")
            code = remove_video_tags(code)

        if replace_from:
            replace_to_str = replace_to or ""
            from_list = replace_from.split('||')
            to_list = replace_to_str.split('||')
            for i, from_item in enumerate(from_list):
                if from_item:
                    to_item = to_list[i] if i < len(to_list) else ""
                    code = code.replace(from_item, to_item)

        try:
            pyperclip.copy(code)
        except Exception:
            pass
        return code
    except Exception as e:
        print(f"Error in replace_only: {e}")
        return 'ERROR'

@eel.expose
def update_replace_rules(replace_from, replace_to):
    global current_replace_from, current_replace_to
    current_replace_from = replace_from or ""
    current_replace_to = replace_to or ""

def send_notify_main(res):
    try:
        if hasattr(eel, 'notify_main_updated'):
            eel.notify_main_updated(res)()
    except Exception as e:
        print(f"Notify error: {e}")

@eel.expose
def modify_from_widget():
    global current_replace_from, current_replace_to
    res = modify('', current_replace_from, current_replace_to)
    send_notify_main(res)
    return res

@eel.expose
def replace_only_from_widget():
    global current_replace_from, current_replace_to
    res = replace_only('', current_replace_from, current_replace_to)
    send_notify_main(res)
    return res

def on_floating_closed():
    global floating_window
    floating_window = None

def find_available_port(start_port=8000):
    import socket
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return start_port

app_port = find_available_port(8000)

@eel.expose
def open_floating_widget():
    global floating_window
    try:
        import webview
        if floating_window is not None:
            try:
                floating_window.show()
                floating_window.restore()
                return True
            except Exception:
                floating_window = None

        widget_w, widget_h = load_widget_config()
        floating_window = webview.create_window(
            'Quick Action Widget',
            f'http://localhost:{app_port}/floating_widget.html',
            width=widget_w,
            height=widget_h,
            frameless=False,
            on_top=True,
            resizable=True,
        )
        try:
            floating_window.events.closed += on_floating_closed
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"Error opening floating widget: {e}")
        return False

@eel.expose
def close_floating_widget():
    global floating_window
    try:
        if floating_window:
            try:
                floating_window.hide()
            except Exception:
                pass
            return True
    except Exception as e:
        print(f"Error hiding floating widget: {e}")
    return False




# ==================== 7. Application Startup & Server (स्टार्ट-अप एवं सर्वर) ====================
# यह फ़ाइल का मुख्य निष्पादक (Entry Point) है। यह विंडो साइज कैलकुलेट करके Eel Web Server चालू करता है।

def get_screen_dimensions():
    """
    get_screen_dimensions() फ़ंक्शन:
    -------------------------------
    सिस्टम के प्राइमरी मॉनिटर (Monitor) की चौड़ाई (width), ऊँचाई (height) और X/Y कोऑर्डिनेट्स निकालता है।
    ताकि एप्लीकेशन डेस्कटॉप पर सही आकार में खुले।
    """
    monitors = get_monitors()
    primary_monitor = next((m for m in monitors if m.is_primary), monitors[0]) if monitors else None
    
    if primary_monitor:
        screen_width = primary_monitor.width
        screen_height = primary_monitor.height
        start_x = primary_monitor.x
        start_y = primary_monitor.y
    else:
        screen_width = 1920
        screen_height = 1080
        start_x = 0
        start_y = 0
        
    return screen_width, screen_height, start_x, start_y


if __name__ == '__main__':
    # 1. Eel के लिए वेब एसेट्स फोल्डर (web_html) रजिस्टर करें
    eel.init('web_html')

    # 2. स्क्रीन की चौड़ाई और ऊँचाई प्राप्त करें
    screen_width, screen_height, start_x, start_y = get_screen_dimensions()

    # 3. एप्लीकेशन विंडो चालू (Launch) करें
    try:
        eel.start(
            'index.html',
            size=(screen_width, screen_height),
            position=(start_x, start_y),
            host='localhost',
            port=app_port,
            cmdline_args=['--disable-gpu', '--disable-gpu-compositing'],
            shutdown_delay=5.0
        )
    except (SystemExit, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f"Eel launch error: {e}, attempting edge fallback...")
        try:
            eel.start(
                'index.html',
                mode='edge',
                size=(screen_width, screen_height),
                position=(start_x, start_y),
                host='localhost',
                port=app_port,
                shutdown_delay=5.0
            )
        except Exception as e2:
            print(f"Edge launch error: {e2}, opening default browser...")
            eel.start(
                'index.html',
                mode='default',
                host='localhost',
                port=app_port,
                shutdown_delay=5.0
            )
