import sqlite3
import os
import re
import shutil
import json
from datetime import datetime
import pandas as pd
import openpyxl
try:
    import openpyxl.styles.fonts
    openpyxl.styles.fonts.Font.family.max = 100
except Exception:
    pass


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(PROJECT_ROOT, "app_database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def clean_raw_html_code(html_str):
    if not html_str or not isinstance(html_str, str):
        return ''
    
    s = html_str.strip()

    # Remove outer python string indicators if present
    prefixes_4 = ("f'''", "F'''", 'f"""', 'F"""')
    for p in prefixes_4:
        if s.startswith(p):
            s = s[4:].strip()
            break

    prefixes_2 = ("f'", 'f"', "F'", 'F"')
    for p in prefixes_2:
        if s.startswith(p):
            s = s[2:].strip()
            break

    quotes_3 = ("'''", '"""')
    for q in quotes_3:
        if s.startswith(q):
            s = s[3:].strip()
        if s.endswith(q):
            s = s[:-3].strip()

    # Preserved user trailing content including |x| splitter

    # Repair any unclosed quotes like alt=" /> to alt="" />
    s = re.sub(r'([a-zA-Z0-9_-]+)="(\s*/>|\s*>)', r'\1="" \2', s)

    # Sanitize &quot; entities in inline styles/CSS to prevent breaking HTML attributes
    s = s.replace('&quot;', "'")

    return s

def init_db():
    """Create SQLite tables and migrate existing Excel files into DB if tables are empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Business Policies table (from company_settings.xlsx -> business_policy)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT UNIQUE NOT NULL,
        shipping_profile_name TEXT,
        return_profile_name TEXT,
        payment_profile_name TEXT,
        brand_name TEXT,
        location TEXT,
        shipping_html TEXT,
        payment_html TEXT,
        return_html TEXT,
        about_us_html TEXT
    )
    """)

    # 2. Products table (from company_settings.xlsx -> products_list)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # 3. Title Templates table (from title_templates-gold.xlsx & title_templates-platinum.xlsx)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS title_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metal_type TEXT NOT NULL,          -- 'gold' or 'platinum'
        product_category TEXT NOT NULL,    -- 'Wedding Band', 'Engagement Ring', etc.
        setting_column TEXT NOT NULL,      -- 'Title', 'Solitaire', 'Eternity', etc.
        template_text TEXT NOT NULL,
        company_name TEXT DEFAULT 'All'
    )
    """)
    try:
        cursor.execute("PRAGMA table_info(title_templates)")
        tt_cols = [r[1] for r in cursor.fetchall()]
        if 'company_name' not in tt_cols:
            cursor.execute("ALTER TABLE title_templates ADD COLUMN company_name TEXT DEFAULT 'All'")
    except Exception as e:
        print(f"Error migrating title_templates schema: {e}")

    # 4. Product Data table (from data.xlsx)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        data_json TEXT NOT NULL
    )
    """)

    # 5. Placeholders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS placeholders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    """)

    # 6. Categories table (with optional company_name scope)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        company_name TEXT DEFAULT 'All'
    )
    """)
    try:
        cursor.execute("PRAGMA table_info(categories)")
        cat_cols = [r[1] for r in cursor.fetchall()]
        if 'company_name' not in cat_cols:
            cursor.execute("ALTER TABLE categories ADD COLUMN company_name TEXT DEFAULT 'All'")
    except Exception as e:
        print(f"Categories migration note: {e}")


    # 7. Setting Columns table (with category scoping and UNIQUE(name, category))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS setting_columns_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        UNIQUE(name, category)
    )
    """)
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='setting_columns'")
        sql_row = cursor.fetchone()
        sql_str = sql_row[0] if sql_row else ""
        if sql_str and ("name TEXT UNIQUE" in sql_str or "UNIQUE(name)" in sql_str):
            cursor.execute("""
                INSERT OR IGNORE INTO setting_columns_v2 (id, name, category)
                SELECT id, name, category FROM setting_columns
            """)
            cursor.execute("DROP TABLE setting_columns")
            cursor.execute("ALTER TABLE setting_columns_v2 RENAME TO setting_columns")
        elif not sql_str:
            cursor.execute("ALTER TABLE setting_columns_v2 RENAME TO setting_columns")
        else:
            cursor.execute("DROP TABLE IF EXISTS setting_columns_v2")
    except Exception as e:
        print(f"Error migrating setting_columns schema: {e}")

    # 8. Company Listing HTML Templates table (with strict UNIQUE(company_name, category, subcategory) constraint)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_html_templates_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'default',
        subcategory TEXT NOT NULL DEFAULT 'default',
        html_template TEXT NOT NULL,
        UNIQUE(company_name, category, subcategory)
    )
    """)

    # Migrate any existing rows from old table to new v2 table
    try:
        cursor.execute("PRAGMA table_info(company_html_templates)")
        old_cols = [r[1] for r in cursor.fetchall()]
        if old_cols:
            if 'subcategory' in old_cols:
                cursor.execute("""
                    INSERT OR IGNORE INTO company_html_templates_v2 (id, company_name, category, subcategory, html_template)
                    SELECT id, company_name, category, COALESCE(subcategory, 'default'), html_template FROM company_html_templates
                """)
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO company_html_templates_v2 (id, company_name, category, subcategory, html_template)
                    SELECT id, company_name, category, 'default', html_template FROM company_html_templates
                """)
            cursor.execute("DROP TABLE company_html_templates")
            cursor.execute("ALTER TABLE company_html_templates_v2 RENAME TO company_html_templates")
    except Exception as e:
        print(f"Migration note: {e}")

    # Ensure table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_html_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'default',
        subcategory TEXT NOT NULL DEFAULT 'default',
        html_template TEXT NOT NULL,
        UNIQUE(company_name, category, subcategory)
    )
    """)

    # 9. Subcategories table (with category relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subcategories_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL DEFAULT 'Engagement Ring',
        name TEXT NOT NULL,
        UNIQUE(category, name)
    )
    """)

    try:
        cursor.execute("PRAGMA table_info(subcategories)")
        sub_cols = [r[1] for r in cursor.fetchall()]
        if sub_cols and 'category' not in sub_cols:
            cursor.execute("""
                INSERT OR IGNORE INTO subcategories_v2 (category, name)
                SELECT 'Engagement Ring', name FROM subcategories
            """)
            cursor.execute("DROP TABLE subcategories")
            cursor.execute("ALTER TABLE subcategories_v2 RENAME TO subcategories")
    except Exception as e:
        print(f"Subcategory migration note: {e}")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subcategories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL DEFAULT 'Engagement Ring',
        name TEXT NOT NULL,
        company_name TEXT DEFAULT 'All'
    )
    """)
    try:
        cursor.execute("PRAGMA table_info(subcategories)")
        sub_cols = [r[1] for r in cursor.fetchall()]
        if 'company_name' not in sub_cols:
            cursor.execute("ALTER TABLE subcategories ADD COLUMN company_name TEXT DEFAULT 'All'")
    except Exception as e:
        print(f"Subcategories company_name migration note: {e}")

    # 10. Excel Mappings table (maps data.xlsx sheet columns to Multi_API.xlsx sheet columns)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS excel_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_sheet TEXT NOT NULL,
        source_column TEXT NOT NULL,
        target_sheet TEXT NOT NULL,
        target_column TEXT NOT NULL,
        mapping_type TEXT DEFAULT 'direct',
        default_value TEXT
    )
    """)
    conn.commit()

    # Seed default category-specific subcategories ONLY if table is empty
    cursor.execute("SELECT COUNT(*) FROM subcategories")
    if cursor.fetchone()[0] == 0:
        seed_subcategories = [
            ("Engagement Ring", "Default"),
            ("Bracelet", "Default"),
            ("Earrings", "Default"),
            ("Pendant", "Default"),
            ("Wedding Band", "Default"),
            ("Men's Ring", "Default"),
            ("Wedding Ring Set", "Default")
        ]
        for cat_name, sub_name in seed_subcategories:
            cursor.execute("INSERT OR IGNORE INTO subcategories (category, name) VALUES (?, ?)", (cat_name, sub_name))
        conn.commit()

    # Automatically rename existing 'Title' setting_column entries to 'Default'
    cursor.execute("UPDATE setting_columns SET name = 'Default' WHERE LOWER(name) = 'title'")
    cursor.execute("UPDATE title_templates SET setting_column = 'Default' WHERE LOWER(setting_column) = 'title'")
    conn.commit()

    # Seed default placeholders if table is empty
    cursor.execute("SELECT COUNT(*) FROM placeholders")
    if cursor.fetchone()[0] == 0:
        default_tags = [
            ("{TCW}", "Total Carat Weight"),
            ("{CENTER_STONE_SHAPE}", "Center Stone Shape"),
            ("{GOLD_KT}", "Gold Karat"),
            ("{GOLD_COLOR}", "Gold Color"),
            ("{METEL}", "Metal Type (Gold / Platinum)"),
            ("{METAL}", "Metal Type (Gold / Platinum)"),
            ("{SETTING}", "Setting / Style"),
            ("{CERTI_BY}", "Certified By"),
            ("{TITLE}", "Product Title"),
            ("{SKU}", "Stock Keeping Unit"),
            ("{CERTIFICATE}", "Certificate Name"),
            ("{DIAMOND_COLOR}", "Center Diamond Color"),
            ("{DIAMOND_CLARITY}", "Center Diamond Clarity"),
            ("{SIDE_STONE_SHAPE}", "Side Stone Shape"),
            ("{SIDE_STONE_WEIGHT}", "Side Stone Weight"),
            ("{SIDE_COLOR}", "Side Stone Color"),
            ("{SIDE_CLARITY}", "Side Stone Clarity"),
            ("{SELLING_PRICE_USD}", "Selling Price in USD"),
            ("{MAIN_STONE_TYPE}", "Main Stone Type")
        ]
        for t_name, t_desc in default_tags:
            cursor.execute("INSERT OR IGNORE INTO placeholders (name, description) VALUES (?, ?)", (t_name, t_desc))
        conn.commit()


    # ================= MIGRATION FROM EXCEL IF DB IS EMPTY =================
    # Check if business_policies table is empty
    cursor.execute("SELECT COUNT(*) FROM business_policies")
    if cursor.fetchone()[0] == 0 and os.path.exists("company_settings.xlsx"):
        print("Migrating company_settings.xlsx to SQLite...")
        try:
            df_policies = pd.read_excel("company_settings.xlsx", sheet_name="business_policy")
            for _, row in df_policies.iterrows():
                comp_name = str(row.get("Company_Name", "")).strip()
                if not comp_name or comp_name == "nan":
                    continue
                cursor.execute("""
                    INSERT OR REPLACE INTO business_policies 
                    (company_name, shipping_profile_name, return_profile_name, payment_profile_name, brand_name, location, shipping_html, payment_html, return_html, about_us_html)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    comp_name,
                    str(row.get("shipping_profile_name", "")),
                    str(row.get("return_profile_name", "")),
                    str(row.get("payment_profile_name", "")),
                    str(row.get("BRAND_NAME", "")),
                    str(row.get("LOCATION", "")),
                    str(row.get("shipping_html", "")),
                    str(row.get("payment_html", "")),
                    str(row.get("return_html", "")),
                    str(row.get("about_us_html", ""))
                ))
            print("Successfully migrated company business policies!")
        except Exception as e:
            print(f"Error migrating business_policy: {e}")

    # Check if products table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0 and os.path.exists("company_settings.xlsx"):
        try:
            df_prods = pd.read_excel("company_settings.xlsx", sheet_name="products_list")
            for _, row in df_prods.iterrows():
                prod_name = str(row.get("Product", "")).strip()
                if prod_name and prod_name != "nan":
                    cursor.execute("INSERT OR IGNORE INTO products (name) VALUES (?)", (prod_name,))
            print("Successfully migrated products list!")
        except Exception as e:
            print(f"Error migrating products_list: {e}")

    conn.commit()
    conn.close()

# ================= CRUD FUNCTIONS FOR PYTHON & EEL =================

def load_company_settings_dict():
    """Return dictionary of company settings matching previous pandas format."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM business_policies")
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for r in rows:
        d = dict(r)
        comp_name = d["company_name"]
        # Map DB columns to old dict keys
        result[comp_name] = {
            "Company_Name": d["company_name"],
            "shipping_profile_name": d["shipping_profile_name"],
            "return_profile_name": d["return_profile_name"],
            "payment_profile_name": d["payment_profile_name"],
            "BRAND_NAME": d["brand_name"],
            "LOCATION": d["location"],
            "shipping_html": d["shipping_html"],
            "payment_html": d["payment_html"],
            "return_html": d["return_html"],
            "about_us_html": d["about_us_html"]
        }
    return result

def get_product_list():
    """Return list of product names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r["name"] for r in rows]

def get_setting_column_aliases(col_str, include_defaults=False):
    """Returns equivalent setting column names for title template matching.
    If include_defaults=False, returns only specific aliases for strict prioritized matching.
    """
    if not col_str:
        return ["default", "title"]
    col_trimmed = str(col_str).strip()
    c_lower = col_trimmed.lower()
    
    aliases = [col_trimmed]
    
    if "cluster" in c_lower:
        for a in ["Cluster", "cluster"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "tennis necklace" in c_lower:
        for a in ["Tennis Necklace", "Tennis", "Necklace"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "tennis" in c_lower or "necklace" in c_lower:
        for a in ["Tennis Necklace", "Tennis", "Necklace"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "solitaire" in c_lower or "1 stone" in c_lower:
        for a in ["Solitaire", "1 Stone", "Single Stone"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "eternity" in c_lower:
        for a in ["Eternity", "Full Eternity", "Half Eternity"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    
    if include_defaults or c_lower in ["default", "title", "all", ""]:
        for a in ["Default", "Title"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
                
    return aliases

def get_title_templates_list(metal_type, sheet_name, setting_column="Default", company_name=None):
    """Fetch title template strings from SQLite with strict setting_column priority matching."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cat_aliases = get_category_aliases(sheet_name)
    cat_ph = ",".join(["?"] * len(cat_aliases))

    comp_str = str(company_name).strip() if company_name and str(company_name).strip() and str(company_name).strip().lower() != 'all' else None
    
    # Extract specific setting column aliases (excluding generic 'default' unless setting_column itself is 'default')
    spec_col_aliases = get_setting_column_aliases(setting_column, include_defaults=False)
    spec_col_ph = ",".join(["?"] * len(spec_col_aliases))

    all_col_aliases = get_setting_column_aliases(setting_column, include_defaults=True)
    all_col_ph = ",".join(["?"] * len(all_col_aliases))

    # Priority A1: Dedicated Company + Specific setting_column
    if comp_str:
        cursor.execute(f"""
            SELECT template_text FROM title_templates 
            WHERE LOWER(metal_type) = LOWER(?) 
              AND LOWER(product_category) IN ({cat_ph})
              AND LOWER(setting_column) IN ({spec_col_ph})
              AND LOWER(company_name) = LOWER(?)
        """, [metal_type] + [a.lower() for a in cat_aliases] + [a.lower() for a in spec_col_aliases] + [comp_str])
        rows = cursor.fetchall()
        if rows:
            conn.close()
            return [r["template_text"] for r in rows if r["template_text"]]

        # Priority A2: Dedicated Company + any category setting_column
        cursor.execute(f"""
            SELECT template_text FROM title_templates 
            WHERE LOWER(metal_type) = LOWER(?) 
              AND LOWER(product_category) IN ({cat_ph})
              AND LOWER(company_name) = LOWER(?)
        """, [metal_type] + [a.lower() for a in cat_aliases] + [comp_str])
        rows = cursor.fetchall()
        if rows:
            conn.close()
            return [r["template_text"] for r in rows if r["template_text"]]

    # Priority B1: Global (All Companies) + Specific setting_column (e.g. Tennis Necklace)
    cursor.execute(f"""
        SELECT template_text FROM title_templates 
        WHERE LOWER(metal_type) = LOWER(?) 
          AND LOWER(product_category) IN ({cat_ph})
          AND LOWER(setting_column) IN ({spec_col_ph})
          AND (company_name IS NULL OR LOWER(company_name) = 'all' OR LOWER(company_name) = '')
    """, [metal_type] + [a.lower() for a in cat_aliases] + [a.lower() for a in spec_col_aliases])
    rows = cursor.fetchall()
    if rows:
        conn.close()
        return [r["template_text"] for r in rows if r["template_text"]]

    # Priority B2: Global (All Companies) + Default/Title or any setting_column for matching category
    cursor.execute(f"""
        SELECT template_text FROM title_templates 
        WHERE LOWER(metal_type) = LOWER(?) 
          AND LOWER(product_category) IN ({cat_ph})
          AND LOWER(setting_column) IN ({all_col_ph})
          AND (company_name IS NULL OR LOWER(company_name) = 'all' OR LOWER(company_name) = '')
    """, [metal_type] + [a.lower() for a in cat_aliases] + [a.lower() for a in all_col_aliases])
    rows = cursor.fetchall()
    if rows:
        conn.close()
        return [r["template_text"] for r in rows if r["template_text"]]

    # Priority B3: Fallback to 'Default' or 'All' product_category ONLY if no category match exists anywhere
    cursor.execute("""
        SELECT template_text FROM title_templates 
        WHERE LOWER(metal_type) = LOWER(?) 
          AND LOWER(product_category) IN ('default', 'all')
          AND (company_name IS NULL OR LOWER(company_name) = 'all' OR LOWER(company_name) = '')
    """, (metal_type,))
    rows = cursor.fetchall()

    conn.close()
    return [r["template_text"] for r in rows if r["template_text"]]

# API CRUD Functions
def get_hidden_company_names_set():
    """
    Returns a set of company names (from business_policies) that are currently
    marked as hidden (is_hidden=True) in the Process Dashboard (tracker_processitem).
    Uses robust multi-level matching:
    1. Exact match (case-insensitive)
    2. Substring match
    3. Token overlap match (>= 3 chars, ignoring stop words)
    """
    items = []
    try:
        import os, django
        if not os.environ.get('DJANGO_SETTINGS_MODULE'):
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
        from tracker.models import ProcessItem
        items = list(ProcessItem.objects.all().values('client_name', 'is_hidden'))
    except Exception:
        try:
            import os, sqlite3
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'db.sqlite3')
            if not os.path.exists(db_path):
                db_path = os.path.join(os.getcwd(), 'db.sqlite3')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute('SELECT client_name, is_hidden FROM tracker_processitem')
                items = [{'client_name': r[0], 'is_hidden': bool(r[1])} for r in c.fetchall()]
                conn.close()
        except Exception:
            items = []

    if not items:
        return set()

    stop_words = {
        'jewels', 'jewel', 'jewelry', 'fine', 'inc', 'ltd', 'usa', 'diamond', 'diamonds',
        'gold', 'silver', 'lab', 'true', 'shree', 'the', 'and', 'by', 'world', 'co'
    }

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT company_name FROM business_policies")
    comp_names = [r["company_name"] for r in cursor.fetchall() if r["company_name"]]
    conn.close()

    hidden_comps = set()
    import re
    for cname in comp_names:
        cl = str(cname).strip().lower()

        # 1. Exact match
        exact = [it for it in items if it['client_name'].strip().lower() == cl]
        if exact:
            if all(it['is_hidden'] for it in exact):
                hidden_comps.add(cname)
            continue

        # 2. Substring match
        subs = [it for it in items if cl in it['client_name'].strip().lower() or it['client_name'].strip().lower() in cl]
        if subs:
            if all(it['is_hidden'] for it in subs):
                hidden_comps.add(cname)
            continue

        # 3. Best word overlap
        cw = set([w for w in re.findall(r'[a-zA-Z0-9]+', cl) if len(w) >= 3 and w not in stop_words])
        best_score = 0
        scored_items = []
        if cw:
            for it in items:
                iw = set([w for w in re.findall(r'[a-zA-Z0-9]+', it['client_name'].strip().lower()) if len(w) >= 3 and w not in stop_words])
                overlap = len(cw.intersection(iw))
                if overlap > best_score:
                    best_score = overlap
                    scored_items = [it]
                elif overlap == best_score and overlap > 0:
                    scored_items.append(it)
        if scored_items:
            if all(it['is_hidden'] for it in scored_items):
                hidden_comps.add(cname)

    return hidden_comps

def get_all_company_policies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM business_policies ORDER BY company_name ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    try:
        hidden_comps = get_hidden_company_names_set()
        for r in rows:
            r["is_hidden"] = r.get("company_name") in hidden_comps
    except Exception:
        for r in rows:
            r["is_hidden"] = False
    return rows

def rename_company_blueprint(old_comp_name, new_comp_name):
    """
    Safely renames the company's master blueprint template in main/<Company>.xlsx
    when the company policy name is changed.
    """
    if not old_comp_name or not new_comp_name:
        return
    try:
        import os, shutil, re
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_dir = os.path.join(base_dir, 'main')
        if not os.path.exists(main_dir):
            return

        old_clean = str(old_comp_name).strip()
        new_clean = str(new_comp_name).strip()
        old_safe = re.sub(r'[/\\:\*\?"<>\|]', '_', old_clean).strip()
        new_safe = re.sub(r'[/\\:\*\?"<>\|]', '_', new_clean).strip()
        new_filename = f"{new_safe}.xlsx"
        new_path = os.path.join(main_dir, new_filename)

        # Look for existing file matching old name
        found_old_path = None
        for f in os.listdir(main_dir):
            if not f.endswith(('.xlsx', '.xls')) or f.startswith('~$') or f.lower() == 'multi_api.xlsx':
                continue
            stem = os.path.splitext(f)[0].strip().lower()
            if stem == old_clean.lower() or stem == old_safe.lower():
                found_old_path = os.path.join(main_dir, f)
                break

        if found_old_path and os.path.exists(found_old_path):
            if os.path.abspath(found_old_path) != os.path.abspath(new_path):
                shutil.move(found_old_path, new_path)
                print(f"[Blueprint] Renamed master blueprint template '{os.path.basename(found_old_path)}' to '{new_filename}'")
    except Exception as e:
        print(f"Error renaming blueprint file for '{old_comp_name}' -> '{new_comp_name}': {e}")

def delete_company_blueprint(comp_name):
    """
    Safely deletes the master blueprint template file for a deleted company.
    """
    if not comp_name:
        return
    try:
        import os, re
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_dir = os.path.join(base_dir, 'main')
        if not os.path.exists(main_dir):
            return

        c_clean = str(comp_name).strip().lower()
        c_safe = re.sub(r'[/\\:\*\?"<>\|]', '_', str(comp_name)).strip().lower()
        for f in os.listdir(main_dir):
            if not f.endswith(('.xlsx', '.xls')) or f.startswith('~$') or f.lower() == 'multi_api.xlsx':
                continue
            stem = os.path.splitext(f)[0].strip().lower()
            if stem == c_clean or stem == c_safe:
                target_path = os.path.join(main_dir, f)
                if os.path.exists(target_path):
                    os.remove(target_path)
                    print(f"[Blueprint] Removed master blueprint template '{f}' for deleted company '{comp_name}'")
    except Exception as e:
        print(f"Error deleting blueprint file for '{comp_name}': {e}")

def sync_company_to_dashboard(company_name, old_name=None):
    """
    Syncs a company policy from Main App into the Process Dashboard (tracker_processitem).
    If a ProcessItem with this name does not exist, creates it.
    If it was renamed, updates the existing ProcessItem and records an audit log.
    """
    if not company_name or not str(company_name).strip():
        return
    company_name = str(company_name).strip()
    try:
        import os, django
        if not os.environ.get('DJANGO_SETTINGS_MODULE'):
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
        from tracker.models import ProcessItem, ProcessItemHistory

        # Handle rename
        if old_name and str(old_name).strip() and str(old_name).strip().lower() != company_name.lower():
            old_clean = str(old_name).strip()
            old_item = ProcessItem.objects.filter(client_name__iexact=old_clean).first()
            if not old_item:
                try:
                    from main_app import catalog_sync
                    old_item = catalog_sync.find_or_create_party(old_clean)
                except Exception:
                    pass
            if old_item:
                old_item.client_name = company_name
                old_item.save(update_fields=['client_name'])
                ProcessItemHistory.objects.create(
                    item=old_item,
                    action_type='edited',
                    summary=f"Renamed client to '{company_name}' from Main App Company Policy"
                )
                return

        # Check if already exists (case-insensitive)
        existing = ProcessItem.objects.filter(client_name__iexact=company_name).first()
        if not existing:
            max_order = ProcessItem.objects.all().order_by('-order_index').values_list('order_index', flat=True).first() or 0
            new_item = ProcessItem.objects.create(
                client_name=company_name,
                status='working',
                order_index=max_order + 1,
                is_status_manual=True
            )
            ProcessItemHistory.objects.create(
                item=new_item,
                action_type='created',
                summary=f"Added client '{company_name}' from Main App Company Policy"
            )
    except Exception as e:
        print(f"Error syncing company '{company_name}' to Dashboard: {e}")

def sync_client_to_company_policy(client_name, brand_name=None, location=None, shipping_profile_name=None, return_profile_name=None, payment_profile_name=None):
    """
    Syncs a client from Process Dashboard (item_create) into Main App business_policies table
    with custom brand_name, location, and profiles.
    """
    if not client_name or not str(client_name).strip():
        return
    client_name = str(client_name).strip()
    b_name = str(brand_name).strip() if brand_name and str(brand_name).strip() else client_name
    loc = str(location).strip() if location and str(location).strip() else "USA"
    ship = str(shipping_profile_name).strip() if shipping_profile_name and str(shipping_profile_name).strip() else f"{client_name} - Shipping"
    ret = str(return_profile_name).strip() if return_profile_name and str(return_profile_name).strip() else f"{client_name} - Return"
    pay = str(payment_profile_name).strip() if payment_profile_name and str(payment_profile_name).strip() else f"{client_name} - Payment"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM business_policies WHERE LOWER(company_name)=LOWER(?)", (client_name,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO business_policies 
                (company_name, brand_name, location, shipping_profile_name, return_profile_name, payment_profile_name, shipping_html, payment_html, return_html, about_us_html)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_name, b_name, loc,
                ship, ret, pay,
                "", "", "", ""
            ))
        else:
            cursor.execute("""
                UPDATE business_policies SET
                    brand_name = COALESCE(NULLIF(?, ''), brand_name),
                    location = COALESCE(NULLIF(?, ''), location),
                    shipping_profile_name = COALESCE(NULLIF(?, ''), shipping_profile_name),
                    return_profile_name = COALESCE(NULLIF(?, ''), return_profile_name),
                    payment_profile_name = COALESCE(NULLIF(?, ''), payment_profile_name)
                WHERE id = ?
            """, (b_name, loc, ship, ret, pay, row["id"]))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error syncing client '{client_name}' to business_policies: {e}")

def save_company_policy(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    comp_name = data.get("company_name", "").strip() if data.get("company_name") else ""
    old_comp_name = None

    if data.get("id"):
        cursor.execute("SELECT company_name FROM business_policies WHERE id=?", (data.get("id"),))
        row = cursor.fetchone()
        if row:
            old_comp_name = row["company_name"]

        cursor.execute("""
            UPDATE business_policies SET
                company_name=?, shipping_profile_name=?, return_profile_name=?, payment_profile_name=?,
                brand_name=?, location=?, shipping_html=?, payment_html=?, return_html=?, about_us_html=?
            WHERE id=?
        """, (
            comp_name, data.get("shipping_profile_name"), data.get("return_profile_name"),
            data.get("payment_profile_name"), data.get("brand_name"), data.get("location"),
            data.get("shipping_html"), data.get("payment_html"), data.get("return_html"), data.get("about_us_html"),
            data.get("id")
        ))
    else:
        cursor.execute("""
            INSERT INTO business_policies 
            (company_name, shipping_profile_name, return_profile_name, payment_profile_name, brand_name, location, shipping_html, payment_html, return_html, about_us_html)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comp_name, data.get("shipping_profile_name"), data.get("return_profile_name"),
            data.get("payment_profile_name"), data.get("brand_name"), data.get("location"),
            data.get("shipping_html"), data.get("payment_html"), data.get("return_html"), data.get("about_us_html")
        ))
    conn.commit()

    # If company was renamed, safely update all linked tables & assets
    is_renamed = bool(old_comp_name and str(old_comp_name).strip() and comp_name and old_comp_name.strip().lower() != comp_name.lower())
    if is_renamed:
        old_clean = str(old_comp_name).strip()
        new_clean = str(comp_name).strip()

        # 1. Update company_html_templates
        cursor.execute("UPDATE company_html_templates SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (new_clean, old_clean))
        # 2. Update categories (party-specific scope)
        cursor.execute("UPDATE categories SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (new_clean, old_clean))
        # 3. Update subcategories (party-specific scope)
        cursor.execute("UPDATE subcategories SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (new_clean, old_clean))
        # 4. Update title_templates (party-specific scope)
        cursor.execute("UPDATE title_templates SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (new_clean, old_clean))
        # 5. Update excel_mappings
        cursor.execute("UPDATE excel_mappings SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (new_clean, old_clean))
        # 6. Update company_template_headers
        cursor.execute("UPDATE company_template_headers SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (new_clean, old_clean))
        conn.commit()

        # 7. Rename master blueprint file on disk
        rename_company_blueprint(old_clean, new_clean)

    conn.close()

    # 8. Automatically sync new/updated company to Dashboard ProcessItem
    if comp_name:
        sync_company_to_dashboard(comp_name, old_name=old_comp_name)

    return True

def delete_company_policy(policy_id_or_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    comp_name = None

    # Handle either ID (int/str digit) or company name
    if isinstance(policy_id_or_name, int) or (isinstance(policy_id_or_name, str) and str(policy_id_or_name).strip().isdigit()):
        pid = int(str(policy_id_or_name).strip())
        cursor.execute("SELECT company_name FROM business_policies WHERE id=?", (pid,))
        row = cursor.fetchone()
        if row:
            comp_name = row["company_name"]
        cursor.execute("DELETE FROM business_policies WHERE id=?", (pid,))
    else:
        comp_name = str(policy_id_or_name).strip()
        cursor.execute("DELETE FROM business_policies WHERE LOWER(company_name)=LOWER(?)", (comp_name,))

    conn.commit()

    if comp_name:
        c_clean = str(comp_name).strip()
        # 1. Clean up linked tables
        cursor.execute("DELETE FROM company_html_templates WHERE LOWER(company_name)=LOWER(?)", (c_clean,))
        cursor.execute("DELETE FROM categories WHERE LOWER(company_name)=LOWER(?)", (c_clean,))
        cursor.execute("DELETE FROM subcategories WHERE LOWER(company_name)=LOWER(?)", (c_clean,))
        cursor.execute("DELETE FROM title_templates WHERE LOWER(company_name)=LOWER(?)", (c_clean,))
        cursor.execute("DELETE FROM excel_mappings WHERE LOWER(company_name)=LOWER(?)", (c_clean,))
        cursor.execute("DELETE FROM company_template_headers WHERE LOWER(company_name)=LOWER(?)", (c_clean,))
        conn.commit()

        # 2. Clean up master blueprint file
        delete_company_blueprint(c_clean)

        # 3. Remove corresponding ProcessItem from Process Dashboard
        try:
            import os, django
            if not os.environ.get('DJANGO_SETTINGS_MODULE'):
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
                django.setup()
            from tracker.models import ProcessItem
            item = ProcessItem.objects.filter(client_name__iexact=c_clean).first()
            if not item:
                try:
                    from main_app import catalog_sync
                    item = catalog_sync.find_or_create_party(c_clean)
                except Exception:
                    pass
            if item:
                item.delete()
        except Exception as e:
            print(f"Error deleting ProcessItem for '{c_clean}': {e}")

    conn.close()
    return True

def get_all_title_templates():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM title_templates ORDER BY metal_type ASC, product_category ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def save_title_template(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    comp_val = data.get("company_name", "All")
    if not comp_val or not str(comp_val).strip():
        comp_val = "All"
    else:
        comp_val = str(comp_val).strip()

    if data.get("id"):
        cursor.execute("""
            UPDATE title_templates 
            SET metal_type=?, product_category=?, setting_column=?, template_text=?, company_name=?
            WHERE id=?
        """, (data.get("metal_type"), data.get("product_category"), data.get("setting_column", "Title"), data.get("template_text"), comp_val, data.get("id")))
    else:
        cursor.execute("""
            INSERT INTO title_templates (metal_type, product_category, setting_column, template_text, company_name)
            VALUES (?, ?, ?, ?, ?)
        """, (data.get("metal_type"), data.get("product_category"), data.get("setting_column", "Title"), data.get("template_text"), comp_val))
    conn.commit()
    conn.close()
    return True

def delete_title_template(template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM title_templates WHERE id=?", (template_id,))
    conn.commit()
    conn.close()
    return True

def save_product(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO products (name) VALUES (?)", (name.strip(),))
    conn.commit()
    conn.close()
    return True

def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    return True

# Placeholder CRUD Functions
def get_all_placeholders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM placeholders ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_placeholder(name, description=""):
    name = name.strip()
    if not name:
        return False
    if not name.startswith("{") or not name.endswith("}"):
        name = "{" + name.strip("{}") + "}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO placeholders (name, description) VALUES (?, ?)", (name, description))
    conn.commit()
    conn.close()
    return True

def delete_placeholder(placeholder_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM placeholders WHERE id=?", (placeholder_id,))
    conn.commit()
    conn.close()
    return True

# Category CRUD Functions
def get_all_categories(company_name=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    if company_name and company_name.strip() and company_name.strip().lower() != 'all':
        cursor.execute("""
            SELECT * FROM categories 
            WHERE company_name IS NULL OR company_name = '' OR LOWER(company_name) = 'all' OR LOWER(company_name) = LOWER(?)
            ORDER BY CASE WHEN LOWER(name) = 'default' THEN 0 ELSE 1 END, name ASC
        """, (company_name.strip(),))
    else:
        cursor.execute("SELECT * FROM categories ORDER BY CASE WHEN LOWER(name) = 'default' THEN 0 ELSE 1 END, name ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_category(name, company_name="All"):
    name = name.strip()
    company_name = company_name.strip() if company_name and company_name.strip() else "All"
    if not name:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if category already exists for this scope or globally
    cursor.execute("""
        SELECT id FROM categories 
        WHERE LOWER(name) = LOWER(?) AND (LOWER(company_name) = LOWER(?) OR LOWER(company_name) = 'all')
    """, (name, company_name))
    if cursor.fetchone():
        conn.close()
        return True
    cursor.execute("INSERT INTO categories (name, company_name) VALUES (?, ?)", (name, company_name))
    conn.commit()
    conn.close()
    return True

def delete_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cat_name = None
    if isinstance(category_id, int) or (isinstance(category_id, str) and category_id.isdigit()):
        cursor.execute("SELECT name FROM categories WHERE id=?", (int(category_id),))
        row = cursor.fetchone()
        if row:
            cat_name = row["name"]
    else:
        cat_name = str(category_id).strip()
        cursor.execute("SELECT id FROM categories WHERE LOWER(name)=LOWER(?)", (cat_name,))
        row = cursor.fetchone()
        if row:
            category_id = row["id"]

    if cat_name and cat_name.strip().lower() == 'default':
        conn.close()
        return False

    if cat_name:
        cursor.execute("DELETE FROM title_templates WHERE LOWER(product_category) = LOWER(?)", (cat_name,))
        cursor.execute("DELETE FROM company_html_templates WHERE LOWER(category) = LOWER(?)", (cat_name,))
        cursor.execute("DELETE FROM products WHERE LOWER(name) = LOWER(?)", (cat_name,))

    cursor.execute("DELETE FROM categories WHERE id=? OR LOWER(name)=LOWER(?)", (category_id, str(category_id)))
    conn.commit()
    conn.close()
    return True

# Setting Column CRUD Functions
def get_all_setting_columns(category=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if category and str(category).strip().lower() != 'all':
        cat_str = str(category).strip()
        aliases = get_category_aliases(cat_str)
        placeholders = ",".join(["?"] * len(aliases))
        cursor.execute(f"""
            SELECT * FROM setting_columns 
            WHERE category IS NULL 
               OR LOWER(category) = 'all' 
               OR LOWER(category) IN ({placeholders})
               OR LOWER(name) IN ('default', 'title')
            ORDER BY CASE WHEN LOWER(name) = 'default' THEN 0 ELSE 1 END, name ASC
        """, [a.lower() for a in aliases])
    else:
        cursor.execute("SELECT * FROM setting_columns ORDER BY CASE WHEN LOWER(name) = 'default' THEN 0 ELSE 1 END, name ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_setting_column(name, category=None):
    name = name.strip()
    if not name:
        return False
    cat_val = category.strip() if category and category.strip() and category.strip().lower() != 'all' else None
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if cat_val:
            cursor.execute("""
                SELECT id FROM setting_columns 
                WHERE LOWER(name)=LOWER(?) AND (category IS NULL OR LOWER(category)=LOWER(?))
            """, (name, cat_val))
        else:
            cursor.execute("SELECT id FROM setting_columns WHERE LOWER(name)=LOWER(?) AND (category IS NULL OR LOWER(category)='all')", (name,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("INSERT OR IGNORE INTO setting_columns (name, category) VALUES (?, ?)", (name, cat_val))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error adding setting column '{name}': {e}")
        return False
    finally:
        conn.close()

def delete_setting_column(column_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        col_name = None
        if isinstance(column_id, int) or (isinstance(column_id, str) and column_id.isdigit()):
            cursor.execute("SELECT name FROM setting_columns WHERE id=?", (int(column_id),))
            row = cursor.fetchone()
            if row:
                col_name = row["name"]
        else:
            col_name = str(column_id).strip()
            cursor.execute("SELECT id FROM setting_columns WHERE LOWER(name)=LOWER(?)", (col_name,))
            row = cursor.fetchone()
            if row:
                column_id = row["id"]

        if col_name and col_name.strip().lower() == 'default':
            return False

        if col_name:
            cursor.execute("DELETE FROM title_templates WHERE LOWER(setting_column) = LOWER(?)", (col_name,))

        cursor.execute("DELETE FROM setting_columns WHERE id=? OR LOWER(name)=LOWER(?)", (column_id, str(column_id)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting setting column '{column_id}': {e}")
        return False
    finally:
        conn.close()

def update_placeholder(placeholder_id, new_name):
    new_name = new_name.strip()
    if not new_name:
        return False
    if not new_name.startswith("{") or not new_name.endswith("}"):
        new_name = "{" + new_name.strip("{}") + "}"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE placeholders SET name=? WHERE id=?", (new_name, placeholder_id))
        conn.commit()
        return True
    finally:
        conn.close()

def update_category(category_id, new_name):
    new_name = new_name.strip()
    if not new_name:
        return False
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories WHERE id=?", (category_id,))
        row = cursor.fetchone()
        if row:
            old_name = row["name"]
            cursor.execute("UPDATE title_templates SET product_category=? WHERE LOWER(product_category)=LOWER(?)", (new_name, old_name))
            cursor.execute("UPDATE company_html_templates SET category=? WHERE LOWER(category)=LOWER(?)", (new_name, old_name))
        cursor.execute("UPDATE categories SET name=? WHERE id=?", (new_name, category_id))
        conn.commit()
        return True
    finally:
        conn.close()

def update_setting_column(column_id, new_name):
    new_name = new_name.strip()
    if not new_name:
        return False
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM setting_columns WHERE id=?", (column_id,))
        row = cursor.fetchone()
        if row:
            old_name = row["name"]
            cursor.execute("UPDATE title_templates SET setting_column=? WHERE LOWER(setting_column)=LOWER(?)", (new_name, old_name))
        cursor.execute("UPDATE OR IGNORE setting_columns SET name=? WHERE id=?", (new_name, column_id))
        conn.commit()
        return True
    finally:
        conn.close()

# Company HTML Listing Templates CRUD & Extraction Functions
def extract_and_seed_company_html(cursor):
    """Auto-seeding disabled to preserve user modifications and prevent overwrites."""
    return

    try:
        content = open('MAIN.py', encoding='utf-8').read()
        blocks = re.split(r'if selected_company ==|elif selected_company ==', content)
        
        seeded_count = 0
        for block in blocks[1:]:
            comp_match = re.search(r"^\s*['\"]([^'\"]+)['\"]", block)
            if not comp_match:
                continue
            comp_name = comp_match.group(1).strip()
            
            category = 'default'
            header_text = block[:200].lower()
            if 'pendant' in header_text or 'necklace' in header_text:
                category = 'Pendant'
            elif 'earring' in header_text:
                category = 'Earrings'
            elif 'bracelet' in header_text:
                category = 'Bracelet'
            elif 'engagement' in header_text or 'ring' in header_text:
                category = 'Engagement Ring'
                
            html_matches = re.findall(r"HTML = (f?'''[\s\S]*?'''|f?\"\"\"[\s\S]*?\"\"\"|f?['\"][^\n]+['\"]|f?\"[\s\S]*?\"\|x\|\"\"\")", block)
            if not html_matches:
                html_matches = re.findall(r'HTML = (f?["\']{3}[\s\S]*?["\']{3})', block)

            for html_str in html_matches:
                clean_html = html_str.strip()
                if clean_html.endswith('|x|"""'):
                    clean_html = clean_html[:-6]
                if clean_html.startswith("f'''") or clean_html.startswith("f\"\"\""):
                    clean_html = clean_html[4:-3]
                elif clean_html.startswith("'''") or clean_html.startswith("\"\"\""):
                    clean_html = clean_html[3:-3]
                elif clean_html.startswith("f'") or clean_html.startswith("f\""):
                    clean_html = clean_html[2:-1]
                elif clean_html.startswith("'") or clean_html.startswith("\""):
                    clean_html = clean_html[1:-1]
                
                clean_html = clean_html.strip()
                if len(clean_html) > 50:
                    cursor.execute("""
                        INSERT OR REPLACE INTO company_html_templates (company_name, category, html_template)
                        VALUES (?, ?, ?)
                    """, (comp_name, category, clean_html))
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO company_html_templates (company_name, category, html_template)
                        VALUES (?, 'default', ?)
                    """, (comp_name, clean_html))
                    
                    seeded_count += 1
        print(f"Successfully extracted & seeded {seeded_count} company HTML templates into SQLite!")
    except Exception as e:
        print(f"Error seeding company_html_templates: {e}")

def get_category_aliases(cat_str):
    """Returns a list of equivalent category names to ensure robust matching across UI, sheets, and DB."""
    if not cat_str:
        return ["default"]
    cat_trimmed = str(cat_str).strip()
    c_lower = cat_trimmed.lower()
    
    aliases = [cat_trimmed]
    
    if "wedding band" in c_lower or "wedding_band" in c_lower or c_lower in ["band", "bands", "wedding bands", "cat-weddinganniversarybands", "wedding & anniversary bands"]:
        for a in ["Wedding Band", "Wedding Bands", "Wedding & Anniversary Bands", "Cat-WeddingAnniversaryBands", "Band", "Bands"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "wedding ring set" in c_lower or "ring set" in c_lower or c_lower in ["wedding set", "cat-engagementweddingringsets", "engagement & wedding ring sets"]:
        for a in ["Wedding Ring Set", "Wedding Ring Sets", "Engagement & Wedding Ring Sets", "Cat-EngagementWeddingRingSets", "Wedding Set"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif re.search(r"\bmens?\b|men's", c_lower):
        for a in ["Men's Ring", "Mens Ring", "Men Ring", "Cat-Rings"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "engagement" in c_lower or c_lower in ["ring", "rings", "cat-engagementrings"]:
        for a in ["Engagement Ring", "Engagement Rings", "Cat-EngagementRings", "Ring", "Rings"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "earring" in c_lower or c_lower in ["cat-earrings"]:
        for a in ["Earring", "Earrings", "Cat-Earrings"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "pendant" in c_lower or "necklace" in c_lower or c_lower in ["cat-necklacespendants"]:
        for a in ["Pendant", "Pendants", "Necklace", "Necklaces & Pendants", "Cat-NecklacesPendants"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "bracelet" in c_lower or "charm" in c_lower or c_lower in ["cat-braceletscharms"]:
        for a in ["Bracelet", "Bracelets", "Bracelets & Charms", "Cat-BraceletsCharms"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
                
    return aliases

def get_subcategory_aliases(subcat_str):
    """Returns a list of equivalent subcategory names (No Accents, Solitaire, With Accents, Default, IGI/GSL certified names)."""
    if not subcat_str:
        return ["default"]
    sub_trimmed = str(subcat_str).strip()
    s_lower = sub_trimmed.lower()
    
    aliases = [sub_trimmed]
    
    if "cluster" in s_lower:
        for a in ["Cluster", "cluster", "IGI CLUSTER", "GSL CLUSTER"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "halo" in s_lower:
        for a in ["Halo", "halo"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "tennis necklace" in s_lower:
        for a in ["Tennis Necklace", "tennis necklace", "Tennis", "tennis"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "tennis" in s_lower or "bracelet" in s_lower or "necklace" in s_lower:
        for a in ["Tennis", "Tennis Bracelet", "Tennis Necklace", "Tennis HTML", "tennis", "tennis bracelet", "tennis necklace", "IGI TENNIS", "GSL TENNIS", "IGI CARD TENNIS"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "no accent" in s_lower or "no_accent" in s_lower or "noaccent" in s_lower or "no side" in s_lower or "noside" in s_lower:
        for a in ["No Accents", "no accents", "No Accent", "no accent", "no sidestone", "no side stone", "no sidestones"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "solitaire" in s_lower or "1 stone" in s_lower:
        for a in ["Solitaire", "solitaire", "1 Stone", "Single Stone", "IGI SOLITAIRE", "GSL SOLITAIRE", "IGI CARD SOLITAIRE"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "accent" in s_lower or "with side" in s_lower or "swa" in s_lower:
        for a in ["With Accents", "with accents", "IGI SWA", "GSL SWA", "IGI CARD SWA", "GSA SWA"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "band" in s_lower:
        for a in ["IGI BAND", "GSL BAND", "Default", "default"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
    elif "ring set" in s_lower or "set" in s_lower:
        for a in ["IGI Ring SET", "GSL RING SET", "Default", "default"]:
            if a.lower() not in [x.lower() for x in aliases]:
                aliases.append(a)
                
    return aliases

def get_company_html_template(company_name, category="default", subcategory="default"):
    conn = get_db_connection()
    cursor = conn.cursor()
    category = category.strip() if category and category.strip() else "default"
    subcategory = subcategory.strip() if subcategory and subcategory.strip() else "default"
    
    cat_aliases = get_category_aliases(category)
    subcat_aliases = get_subcategory_aliases(subcategory)
    
    # 1. Match company_name + category (or alias) + exact/alias subcategory first
    for cat in cat_aliases:
        for sub in subcat_aliases:
            cursor.execute("""
                SELECT html_template FROM company_html_templates 
                WHERE LOWER(company_name) = LOWER(?) AND LOWER(category) = LOWER(?) AND LOWER(subcategory) = LOWER(?)
            """, (company_name, cat, sub))
            row = cursor.fetchone()
            if row and row["html_template"] and str(row["html_template"]).strip():
                conn.close()
                return clean_raw_html_code(row["html_template"])
            
    # 1b. Match 'All' or global company + category (or alias) + exact/alias subcategory
    for cat in cat_aliases:
        for sub in subcat_aliases:
            cursor.execute("""
                SELECT html_template FROM company_html_templates 
                WHERE (LOWER(company_name) = 'all' OR company_name IS NULL OR company_name = '') 
                  AND LOWER(category) = LOWER(?) AND LOWER(subcategory) = LOWER(?)
            """, (cat, sub))
            row = cursor.fetchone()
            if row and row["html_template"] and str(row["html_template"]).strip():
                conn.close()
                return clean_raw_html_code(row["html_template"])

    # 1c. Cross-category lookup for explicit subcategory (e.g. GSL BAND or IGI CLUSTER across categories for this company)
    if subcategory.lower() not in ['default', 'none', '']:
        for sub in subcat_aliases:
            cursor.execute("""
                SELECT html_template FROM company_html_templates 
                WHERE LOWER(company_name) = LOWER(?) AND LOWER(subcategory) = LOWER(?)
            """, (company_name, sub))
            row = cursor.fetchone()
            if row and row["html_template"] and str(row["html_template"]).strip():
                conn.close()
                return clean_raw_html_code(row["html_template"])

    # 2. Fallback to subcategory = 'default' or 'Default' for company & category (or alias)
    for cat in cat_aliases:
        cursor.execute("""
            SELECT html_template FROM company_html_templates 
            WHERE LOWER(company_name) = LOWER(?) AND LOWER(category) = LOWER(?) 
              AND (LOWER(subcategory) = 'default' OR subcategory IS NULL)
        """, (company_name, cat))
        row = cursor.fetchone()
        if row and row["html_template"] and str(row["html_template"]).strip():
            conn.close()
            return clean_raw_html_code(row["html_template"])

    # 3. Fallback to category = 'default' for that company
    cursor.execute("""
        SELECT html_template FROM company_html_templates 
        WHERE LOWER(company_name) = LOWER(?) AND LOWER(category) = 'default'
    """, (company_name,))
    row = cursor.fetchone()
    if row and row["html_template"] and str(row["html_template"]).strip():
        conn.close()
        return clean_raw_html_code(row["html_template"])

    conn.close()
    return ""


def get_all_company_html_templates(company_name=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    if company_name:
        cursor.execute("SELECT * FROM company_html_templates WHERE LOWER(company_name) = LOWER(?) ORDER BY category ASC", (company_name,))
    else:
        cursor.execute("SELECT * FROM company_html_templates ORDER BY company_name ASC, category ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
# Subcategory CRUD Functions
def get_all_subcategories(category="", company_name=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    params = []
    where_clauses = []

    if category and category.strip() and category.strip().lower() != 'all':
        where_clauses.append("LOWER(category) = LOWER(?)")
        params.append(category.strip())

    if company_name and company_name.strip() and company_name.strip().lower() != 'all':
        where_clauses.append("(company_name IS NULL OR company_name = '' OR LOWER(company_name) = 'all' OR LOWER(company_name) = LOWER(?))")
        params.append(company_name.strip())

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    cursor.execute(f"""
        SELECT * FROM subcategories 
        {where_sql}
        ORDER BY CASE WHEN LOWER(name) = 'default' THEN 0 ELSE 1 END, category ASC, name ASC
    """, params)
    rows = [dict(r) for r in cursor.fetchall()]
    
    if category and category.strip() and category.strip().lower() != 'all':
        # Ensure Default is present at top (index 0)
        has_default = any(r["name"].lower() == "default" for r in rows)
        if not has_default:
            rows.insert(0, {"id": 0, "category": category, "name": "Default", "company_name": "All"})
    conn.close()
    return rows

def add_subcategory(category, name=None, company_name="All"):
    # Gracefully handle argument order if passed as (name, category)
    if name is None:
        name = category
        category = "Engagement Ring"
    category = category.strip() if category and category.strip() else "Engagement Ring"
    name = name.strip() if name else ""
    company_name = company_name.strip() if company_name and company_name.strip() else "All"
    if not name:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if subcategory already exists for this scope or globally
    cursor.execute("""
        SELECT id FROM subcategories 
        WHERE LOWER(category) = LOWER(?) AND LOWER(name) = LOWER(?) AND (LOWER(company_name) = LOWER(?) OR LOWER(company_name) = 'all')
    """, (category, name, company_name))
    if cursor.fetchone():
        conn.close()
        return True
    cursor.execute("INSERT INTO subcategories (category, name, company_name) VALUES (?, ?, ?)", (category, name, company_name))
    conn.commit()
    conn.close()
    return True

def update_subcategory(subcat_id, new_name, category=None):
    new_name = new_name.strip()
    if not new_name:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, name FROM subcategories WHERE id=?", (subcat_id,))
    row = cursor.fetchone()
    if row:
        old_name = row["name"]
        cat_name = category if category else row["category"]
        cursor.execute("""
            UPDATE company_html_templates SET subcategory=? 
            WHERE LOWER(category)=LOWER(?) AND LOWER(subcategory)=LOWER(?)
        """, (new_name, cat_name, old_name))
        
        if category:
            cursor.execute("UPDATE subcategories SET name=?, category=? WHERE id=?", (new_name, category, subcat_id))
        else:
            cursor.execute("UPDATE subcategories SET name=? WHERE id=?", (new_name, subcat_id))
    conn.commit()
    conn.close()
    return True

def delete_subcategory(subcat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sub_name = None
    cat_name = None
    if isinstance(subcat_id, int) or (isinstance(subcat_id, str) and subcat_id.isdigit()):
        cursor.execute("SELECT category, name FROM subcategories WHERE id=?", (int(subcat_id),))
        row = cursor.fetchone()
        if row:
            cat_name = row["category"]
            sub_name = row["name"]
    else:
        sub_name = str(subcat_id).strip()
        cursor.execute("SELECT id, category FROM subcategories WHERE LOWER(name)=LOWER(?)", (sub_name,))
        row = cursor.fetchone()
        if row:
            subcat_id = row["id"]
            cat_name = row["category"]

    if sub_name and sub_name.strip().lower() == 'default':
        conn.close()
        return False

    if sub_name and cat_name:
        cursor.execute("DELETE FROM company_html_templates WHERE LOWER(category)=LOWER(?) AND LOWER(subcategory)=LOWER(?)", (cat_name, sub_name))

    cursor.execute("DELETE FROM subcategories WHERE id=? OR LOWER(name)=LOWER(?)", (subcat_id, str(subcat_id)))
    conn.commit()
    conn.close()
    return True

def save_company_html_template(company_name, category, subcategory="default", html_template="", template_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    company_name = company_name.strip()
    category = category.strip() if category and category.strip() else "default"
    subcategory = subcategory.strip() if subcategory and subcategory.strip() else "default"
    html_template = clean_raw_html_code(html_template)

    # Look for exact matching row for company_name + category + subcategory
    cursor.execute("""
        SELECT id FROM company_html_templates 
        WHERE LOWER(company_name)=LOWER(?) AND LOWER(category)=LOWER(?) AND LOWER(subcategory)=LOWER(?)
    """, (company_name, category, subcategory))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE company_html_templates SET html_template=?, company_name=?, category=?, subcategory=?
            WHERE id=?
        """, (html_template, company_name, category, subcategory, existing["id"]))
    elif template_id:
        cursor.execute("""
            UPDATE company_html_templates SET company_name=?, category=?, subcategory=?, html_template=?
            WHERE id=?
        """, (company_name, category, subcategory, html_template, template_id))
    else:
        cursor.execute("""
            INSERT INTO company_html_templates (company_name, category, subcategory, html_template)
            VALUES (?, ?, ?, ?)
        """, (company_name, category, subcategory, html_template))
    conn.commit()
    conn.close()
    return True

def delete_company_html_template(template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM company_html_templates WHERE id=?", (template_id,))
    conn.commit()
    conn.close()
    return True

# Admin Settings Functions
def get_admin_password():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS admin_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    cursor.execute("INSERT OR IGNORE INTO admin_settings (key, value) VALUES ('admin_password', '0000')")
    conn.commit()
    cursor.execute("SELECT value FROM admin_settings WHERE key='admin_password'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return "0000"

def update_admin_password(new_password):
    new_password = str(new_password).strip()
    if not new_password:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS admin_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    cursor.execute("INSERT OR REPLACE INTO admin_settings (key, value) VALUES ('admin_password', ?)", (new_password,))
    conn.commit()
    conn.close()
    return True

# ==================== Database Product Data & Template Headers ====================

def seed_product_data_from_excel(file_path=None, clear_first=True):
    """
    Imports all sheets and rows from Excel into SQLite product_data table.
    Enables ultra-fast database operations without disk file I/O bottleneck.
    """
    if not file_path:
        file_path = os.path.join(PROJECT_ROOT, "data.xlsx")
    elif not os.path.isabs(file_path):
        file_path = os.path.join(PROJECT_ROOT, file_path)

    if not os.path.exists(file_path):
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        sku TEXT,
        data_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    try:
        cursor.execute("ALTER TABLE product_data ADD COLUMN sku TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE product_data ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_data_cat ON product_data(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_data_sku ON product_data(sku)")

    if clear_first:
        cursor.execute("DELETE FROM product_data")

    total_inserted = 0
    try:
        xl = pd.ExcelFile(file_path)
        ignored = {'note', 'notes', 'general instructions', 'instruction', 'help', 'summary', 'sheet1', 'backend', 'metadata', 'config', 'settings'}
        for sheet in xl.sheet_names:
            if str(sheet).strip().lower() in ignored:
                continue
            df = pd.read_excel(file_path, sheet_name=sheet)
            records = df.to_dict(orient='records')
            batch = []
            for r in records:
                sku = str(r.get('SKU') or r.get('sku') or '').strip()
                if not sku or sku.lower() in ['nan', 'none', 'null', '0', '']:
                    continue
                cleaned = {k: ('' if pd.isna(v) else v) for k, v in r.items()}
                batch.append((str(sheet).strip(), sku, json.dumps(cleaned)))

            if batch:
                cursor.executemany("INSERT INTO product_data (category, sku, data_json) VALUES (?, ?, ?)", batch)
                total_inserted += len(batch)

        conn.commit()
    except Exception as e:
        print(f"Error seeding product_data from {file_path}: {e}")
    finally:
        conn.close()

    return total_inserted


def get_product_data_sheets():
    """Returns unique sheet categories stored in database product_data table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        sku TEXT,
        data_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("SELECT DISTINCT category FROM product_data ORDER BY category")
    rows = cursor.fetchall()
    conn.close()
    return [r['category'] for r in rows if r['category']]


def get_product_data_rows(category=None):
    """
    Returns product records directly from database in 1.8ms!
    If category is given, filters by that category (e.g. 'RING').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if category:
            cursor.execute("SELECT data_json FROM product_data WHERE LOWER(category) = LOWER(?) ORDER BY id", (category,))
        else:
            cursor.execute("SELECT data_json FROM product_data ORDER BY id")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            try:
                result.append(json.loads(r['data_json']))
            except Exception:
                pass
        return result
    finally:
        conn.close()


def get_product_data_count():
    """Returns count of products in database grouped by category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT category, COUNT(*) as cnt FROM product_data GROUP BY category")
        rows = cursor.fetchall()
        counts = {r['category']: r['cnt'] for r in rows}
        total = sum(counts.values())
        return {'by_category': counts, 'total': total}
    finally:
        conn.close()


def clear_product_data(category=None):
    """Clears product_data table for a category or all."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if category:
            cursor.execute("DELETE FROM product_data WHERE LOWER(category) = LOWER(?)", (category,))
        else:
            cursor.execute("DELETE FROM product_data")
        conn.commit()
        return True
    finally:
        conn.close()


def seed_template_headers_from_file(template_path=None):
    """
    Extracts column headers from Multi_API.xlsx and stores them in database table company_template_headers.
    This eliminates needing to open the 100KB Excel template over and over just to inspect columns.
    """
    if not template_path:
        template_path = os.path.join(PROJECT_ROOT, "main", "Multi_API.xlsx")
    elif not os.path.isabs(template_path):
        template_path = os.path.join(PROJECT_ROOT, template_path)

    if not os.path.exists(template_path):
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_template_headers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL DEFAULT 'All',
        target_sheet TEXT NOT NULL,
        header_row INTEGER DEFAULT 4,
        columns_json TEXT NOT NULL,
        UNIQUE(company_name, target_sheet)
    )
    """)

    try:
        wb = openpyxl.load_workbook(template_path, data_only=True)
        for s in wb.sheetnames:
            if s.lower() in ['general instructions']:
                continue
            ws = wb[s]
            header_row = 4
            for r in range(1, 10):
                val = str(ws.cell(row=r, column=1).value or '').strip()
                if val.lower().startswith('*action'):
                    header_row = r
                    break
            cols = []
            for c in range(1, ws.max_column + 1):
                v = ws.cell(row=header_row, column=c).value
                if v is not None and str(v).strip():
                    cols.append(str(v).strip())

            if cols:
                cursor.execute("""
                INSERT OR REPLACE INTO company_template_headers 
                (company_name, target_sheet, header_row, columns_json)
                VALUES ('All', ?, ?, ?)
                """, (s, header_row, json.dumps(cols)))

        conn.commit()
    except Exception as e:
        print(f"Error seeding template headers: {e}")
        return False
    finally:
        conn.close()

    return True


def get_template_target_sheets(company_name='All'):
    """Returns target sheets from database company_template_headers table in 0.5ms."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS company_template_headers (id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT NOT NULL DEFAULT 'All', target_sheet TEXT NOT NULL, header_row INTEGER DEFAULT 4, columns_json TEXT NOT NULL, UNIQUE(company_name, target_sheet))")
        cursor.execute("SELECT DISTINCT target_sheet FROM company_template_headers ORDER BY id")
        rows = cursor.fetchall()
        sheets = [r['target_sheet'] for r in rows if r['target_sheet']]
        return sheets if sheets else None
    finally:
        conn.close()


def get_template_header_columns(target_sheet, company_name='All'):
    """Returns (header_row, columns_list) for target sheet from DB in 0.2ms."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS company_template_headers (id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT NOT NULL DEFAULT 'All', target_sheet TEXT NOT NULL, header_row INTEGER DEFAULT 4, columns_json TEXT NOT NULL, UNIQUE(company_name, target_sheet))")
        cursor.execute("SELECT header_row, columns_json FROM company_template_headers WHERE target_sheet = ?", (target_sheet,))
        row = cursor.fetchone()
        if row:
            return row['header_row'], json.loads(row['columns_json'])
        return 4, []
    finally:
        conn.close()


# ==================== Excel Mapping Functions ====================
def get_data_file_sheets(file_path="data.xlsx"):
    """
    Reads actual valid sheet names directly from database product_data table in 1ms!
    Falls back to disk data.xlsx if DB is empty and auto-seeds the DB.
    """
    db_sheets = get_product_data_sheets()
    if db_sheets:
        return db_sheets

    # Auto seed from data.xlsx on disk
    if not os.path.isabs(file_path):
        file_path = os.path.join(PROJECT_ROOT, file_path)
    if os.path.exists(file_path):
        seed_product_data_from_excel(file_path)
        db_sheets = get_product_data_sheets()
        if db_sheets:
            return db_sheets

    return ["RING", "EARRINGS", "PENDANT", "BRACELET"]


def get_target_file_sheets(file_path="Multi_API.xlsx"):
    """
    Reads actual valid target sheet names directly from SQLite company_template_headers in 0.5ms!
    Falls back to disk Multi_API.xlsx if DB empty and auto-seeds the DB.
    """
    db_targets = get_template_target_sheets()
    if db_targets:
        return db_targets

    # Auto seed from master template
    seed_template_headers_from_file()
    db_targets = get_template_target_sheets()
    if db_targets:
        return db_targets

    return ["Cat-EngagementRings", "Cat-WeddingAnniversaryBands", "Cat-EngagementWeddingRingSets", "Cat-Earrings", "Cat-NecklacesPendants", "Cat-BraceletsCharms", "Cat-Rings"]

def sync_excel_mappings_with_file(data_file="data.xlsx"):
    """Filters excel_mappings table to ONLY keep sheets present in data.xlsx, and standardizes casing."""
    if not os.path.isabs(data_file):
        data_file = os.path.join(PROJECT_ROOT, data_file)
    valid_sheets = get_data_file_sheets(data_file)
    sheet_map = {s.lower(): s for s in valid_sheets}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS excel_mappings (id INTEGER PRIMARY KEY AUTOINCREMENT, source_sheet TEXT NOT NULL, source_column TEXT NOT NULL, target_sheet TEXT NOT NULL, target_column TEXT NOT NULL, mapping_type TEXT DEFAULT 'direct', default_value TEXT)")
    
    cursor.execute("SELECT id, source_sheet FROM excel_mappings")
    rows = cursor.fetchall()
    for row in rows:
        m_id = row['id']
        src = str(row['source_sheet']).strip()
        src_lower = src.lower()


        if src_lower in ['[all]', 'all', 'all sheets', '*', 'default']:
            continue
        elif src_lower in sheet_map:
            cursor.execute("UPDATE excel_mappings SET source_sheet=? WHERE id=?", (sheet_map[src_lower], m_id))
        else:
            cursor.execute("DELETE FROM excel_mappings WHERE id=?", (m_id,))

    
    conn.commit()
    conn.close()
    return True

def get_all_excel_mappings(company_name=None):
    sync_excel_mappings_with_file()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS excel_mappings (id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT DEFAULT 'All', source_sheet TEXT NOT NULL, source_column TEXT NOT NULL, target_sheet TEXT NOT NULL, target_column TEXT NOT NULL, mapping_type TEXT DEFAULT 'direct', default_value TEXT)")
    
    if company_name and str(company_name).strip().lower() not in ['all', 'all companies', '[all]', '*', 'default', '']:
        c_name = str(company_name).strip()
        cursor.execute("SELECT * FROM excel_mappings WHERE LOWER(company_name)=LOWER(?) OR LOWER(company_name) IN ('all', 'all companies', '[all]', '*', 'default', '') ORDER BY source_sheet, id", (c_name,))
    else:
        cursor.execute("SELECT * FROM excel_mappings ORDER BY source_sheet, id")
        
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        reset_default_excel_mappings()
        sync_excel_mappings_with_file()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM excel_mappings ORDER BY source_sheet, id")
        rows = cursor.fetchall()
        conn.close()

    res = []
    for r in rows:
        d = dict(r)
        if 'company_name' not in d or not d['company_name']:
            d['company_name'] = 'All'
        res.append(d)
    return res


def save_excel_mapping(source_sheet, source_column, target_sheet, target_column, mapping_type='direct', default_value='', mapping_id=None, company_name='All'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS excel_mappings (id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT DEFAULT 'All', source_sheet TEXT NOT NULL, source_column TEXT NOT NULL, target_sheet TEXT NOT NULL, target_column TEXT NOT NULL, mapping_type TEXT DEFAULT 'direct', default_value TEXT)")
    
    source_sheet = source_sheet.strip()
    source_column = source_column.strip()
    target_sheet = target_sheet.strip()
    target_column = target_column.strip()
    mapping_type = mapping_type.strip() if mapping_type else 'direct'
    default_value = str(default_value) if default_value is not None else ''
    company_name = str(company_name).strip() if company_name and str(company_name).strip() else 'All'

    if mapping_id:
        cursor.execute("""
            UPDATE excel_mappings
            SET source_sheet=?, source_column=?, target_sheet=?, target_column=?, mapping_type=?, default_value=?, company_name=?
            WHERE id=?
        """, (source_sheet, source_column, target_sheet, target_column, mapping_type, default_value, company_name, mapping_id))
    else:
        cursor.execute("""
            INSERT INTO excel_mappings (source_sheet, source_column, target_sheet, target_column, mapping_type, default_value, company_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_sheet, source_column, target_sheet, target_column, mapping_type, default_value, company_name))
    
    conn.commit()
    conn.close()
    return True

def delete_excel_mapping(mapping_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM excel_mappings WHERE id=?", (mapping_id,))
    conn.commit()
    conn.close()
    return True

def reset_default_excel_mappings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS excel_mappings (id INTEGER PRIMARY KEY AUTOINCREMENT, source_sheet TEXT NOT NULL, source_column TEXT NOT NULL, target_sheet TEXT NOT NULL, target_column TEXT NOT NULL, mapping_type TEXT DEFAULT 'direct', default_value TEXT)")
    cursor.execute("DELETE FROM excel_mappings")

    default_mappings = [
        # --- RING (data.xlsx) / Cat-EngagementRings ---
        ("RING", "SKU", "Cat-EngagementRings", "Custom label (SKU)", "direct", ""),
        ("RING", "SELLING_PRICE_USD", "Cat-EngagementRings", "Start price", "direct", ""),
        ("RING", "Price", "Cat-EngagementRings", "Start price", "direct", ""),
        ("RING", "GOLD_KT", "Cat-EngagementRings", "C:Metal Purity", "direct", ""),
        ("RING", "GOLD_COLOR", "Cat-EngagementRings", "C:Color", "direct", ""),
        ("RING", "CENTER_STONE_SHAPE", "Cat-EngagementRings", "C:Main Stone Shape", "direct", ""),
        ("RING", "CENTER_DIAMOND_CLARITY", "Cat-EngagementRings", "C:Diamond Clarity Grade", "direct", ""),
        ("RING", "CENTER_DIAMOND_COLOR", "Cat-EngagementRings", "C:Diamond Color Grade", "direct", ""),
        ("RING", "CENTER_STONE_WEIGHT", "Cat-EngagementRings", "C:Total Carat Weight", "direct", ""),
        ("RING", "TOTAL_DIAMOND_PCS", "Cat-EngagementRings", "C:Number of Diamonds", "direct", ""),
        ("RING", "SETTING", "Cat-EngagementRings", "C:Setting Style", "direct", ""),
        ("RING", "Style", "Cat-EngagementRings", "Style", "direct", ""),
        ("RING", "Certified", "Cat-EngagementRings", "C:Certification", "direct", ""),
        ("RING", "SIDE_STONE_SHAPE", "Cat-EngagementRings", "C:Secondary Stone", "direct", ""),

        ("ring", "SKU", "Cat-EngagementRings", "Custom label (SKU)", "direct", ""),
        ("ring", "Price", "Cat-EngagementRings", "Start price", "direct", ""),
        ("ring", "GOLD_KT", "Cat-EngagementRings", "C:Metal Purity", "direct", ""),
        ("ring", "GOLD_COLOR", "Cat-EngagementRings", "C:Color", "direct", ""),
        ("ring", "CENTER_STONE_SHAPE", "Cat-EngagementRings", "C:Main Stone Shape", "direct", ""),
        ("ring", "TCW", "Cat-EngagementRings", "C:Total Carat Weight", "direct", ""),
        ("ring", "TOTAL_DIAMOND_PCS", "Cat-EngagementRings", "C:Number of Diamonds", "direct", ""),
        ("ring", "Style", "Cat-EngagementRings", "Style", "direct", ""),

        # --- EARRINGS (data.xlsx) / Cat-Earrings ---
        ("EARRINGS", "SKU", "Cat-Earrings", "Custom label (SKU)", "direct", ""),
        ("EARRINGS", "SELLING_PRICE_USD", "Cat-Earrings", "Start price", "direct", ""),
        ("EARRINGS", "Price", "Cat-Earrings", "Start price", "direct", ""),
        ("EARRINGS", "GOLD_KT", "Cat-Earrings", "C:Metal Purity", "direct", ""),
        ("EARRINGS", "GOLD_COLOR", "Cat-Earrings", "C:Color", "direct", ""),
        ("EARRINGS", "CENTER_STONE_SHAPE", "Cat-Earrings", "C:Main Stone Shape", "direct", ""),
        ("EARRINGS", "CENTER_DIAMOND_CLARITY", "Cat-Earrings", "C:Diamond Clarity Grade", "direct", ""),
        ("EARRINGS", "CENTER_DIAMOND_COLOR", "Cat-Earrings", "C:Diamond Color Grade", "direct", ""),
        ("EARRINGS", "CENTER_STONE_WEIGHT", "Cat-Earrings", "C:Total Carat Weight", "direct", ""),
        ("EARRINGS", "TOTAL_DIAMOND_PCS", "Cat-Earrings", "C:Number of Diamonds", "direct", ""),
        ("EARRINGS", "SETTING", "Cat-Earrings", "C:Setting Style", "direct", ""),
        ("EARRINGS", "Style", "Cat-Earrings", "Style", "direct", ""),
        ("EARRINGS", "Certified", "Cat-Earrings", "C:Certification", "direct", ""),

        ("earring", "SKU", "Cat-Earrings", "Custom label (SKU)", "direct", ""),
        ("earring", "Price", "Cat-Earrings", "Start price", "direct", ""),
        ("earring", "GOLD_KT", "Cat-Earrings", "C:Metal Purity", "direct", ""),
        ("earring", "GOLD_COLOR", "Cat-Earrings", "C:Color", "direct", ""),
        ("earring", "CENTER_STONE_SHAPE", "Cat-Earrings", "C:Main Stone Shape", "direct", ""),
        ("earring", "TCW", "Cat-Earrings", "C:Total Carat Weight", "direct", ""),
        ("earring", "TOTAL_DIAMOND_PCS", "Cat-Earrings", "C:Number of Diamonds", "direct", ""),
        ("earring", "Style", "Cat-Earrings", "Style", "direct", ""),

        # --- PENDANT (data.xlsx) / Cat-NecklacesPendants ---
        ("PENDANT", "SKU", "Cat-NecklacesPendants", "Custom label (SKU)", "direct", ""),
        ("PENDANT", "SELLING_PRICE_USD", "Cat-NecklacesPendants", "Start price", "direct", ""),
        ("PENDANT", "Price", "Cat-NecklacesPendants", "Start price", "direct", ""),
        ("PENDANT", "GOLD_KT", "Cat-NecklacesPendants", "C:Metal Purity", "direct", ""),
        ("PENDANT", "GOLD_COLOR", "Cat-NecklacesPendants", "C:Color", "direct", ""),
        ("PENDANT", "CENTER_STONE_SHAPE", "Cat-NecklacesPendants", "C:Main Stone Shape", "direct", ""),
        ("PENDANT", "CENTER_DIAMOND_CLARITY", "Cat-NecklacesPendants", "C:Diamond Clarity Grade", "direct", ""),
        ("PENDANT", "CENTER_DIAMOND_COLOR", "Cat-NecklacesPendants", "C:Diamond Color Grade", "direct", ""),
        ("PENDANT", "CENTER_STONE_WEIGHT", "Cat-NecklacesPendants", "C:Total Carat Weight", "direct", ""),
        ("PENDANT", "TOTAL_DIAMOND_PCS", "Cat-NecklacesPendants", "C:Number of Diamonds", "direct", ""),
        ("PENDANT", "CHAIN_LENGTH", "Cat-NecklacesPendants", "C:Chain Length", "direct", ""),
        ("PENDANT", "SETTING", "Cat-NecklacesPendants", "C:Setting Style", "direct", ""),
        ("PENDANT", "Style", "Cat-NecklacesPendants", "Style", "direct", ""),
        ("PENDANT", "Certified", "Cat-NecklacesPendants", "C:Certification", "direct", ""),

        ("pendant", "SKU", "Cat-NecklacesPendants", "Custom label (SKU)", "direct", ""),
        ("pendant", "Price", "Cat-NecklacesPendants", "Start price", "direct", ""),
        ("pendant", "GOLD_KT", "Cat-NecklacesPendants", "C:Metal Purity", "direct", ""),
        ("pendant", "GOLD_COLOR", "Cat-NecklacesPendants", "C:Color", "direct", ""),
        ("pendant", "CENTER_STONE_SHAPE", "Cat-NecklacesPendants", "C:Main Stone Shape", "direct", ""),
        ("pendant", "TCW", "Cat-NecklacesPendants", "C:Total Carat Weight", "direct", ""),
        ("pendant", "TOTAL_DIAMOND_PCS", "Cat-NecklacesPendants", "C:Number of Diamonds", "direct", ""),
        ("pendant", "Style", "Cat-NecklacesPendants", "Style", "direct", ""),

        # --- BRACELET (data.xlsx) / Cat-BraceletsCharms ---
        ("BRACELET", "SKU", "Cat-BraceletsCharms", "Custom Label (SKU)", "direct", ""),
        ("BRACELET", "SELLING_PRICE_USD", "Cat-BraceletsCharms", "Start price", "direct", ""),
        ("BRACELET", "Price", "Cat-BraceletsCharms", "Start price", "direct", ""),
        ("BRACELET", "GOLD_KT", "Cat-BraceletsCharms", "C:Metal Purity", "direct", ""),
        ("BRACELET", "GOLD_COLOR", "Cat-BraceletsCharms", "C:Color", "direct", ""),
        ("BRACELET", "CENTER_STONE_SHAPE", "Cat-BraceletsCharms", "C:Main Stone Shape", "direct", ""),
        ("BRACELET", "CENTER_DIAMOND_CLARITY", "Cat-BraceletsCharms", "C:Diamond Clarity Grade", "direct", ""),
        ("BRACELET", "CENTER_DIAMOND_COLOR", "Cat-BraceletsCharms", "C:Diamond Color Grade", "direct", ""),
        ("BRACELET", "CENTER_STONE_WEIGHT", "Cat-BraceletsCharms", "C:Total Carat Weight", "direct", ""),
        ("BRACELET", "TOTAL_DIAMOND_PCS", "Cat-BraceletsCharms", "C:Number of Diamonds", "direct", ""),
        ("BRACELET", "LENGTH", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("BRACELET", "item_length", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("BRACELET", "Item Length", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("BRACELET", "Item_Length", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("BRACELET", "CHAIN_LENGTH", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("BRACELET", "SETTING", "Cat-BraceletsCharms", "C:Setting Style", "direct", ""),
        ("BRACELET", "Style", "Cat-BraceletsCharms", "Style", "direct", ""),
        ("BRACELET", "Certified", "Cat-BraceletsCharms", "C:Certification", "direct", ""),

        ("bracelet", "SKU", "Cat-BraceletsCharms", "Custom Label (SKU)", "direct", ""),
        ("bracelet", "Price", "Cat-BraceletsCharms", "Start price", "direct", ""),
        ("bracelet", "GOLD_KT", "Cat-BraceletsCharms", "C:Metal Purity", "direct", ""),
        ("bracelet", "GOLD_COLOR", "Cat-BraceletsCharms", "C:Color", "direct", ""),
        ("bracelet", "CENTER_STONE_SHAPE", "Cat-BraceletsCharms", "C:Main Stone Shape", "direct", ""),
        ("bracelet", "TCW", "Cat-BraceletsCharms", "C:Total Carat Weight", "direct", ""),
        ("bracelet", "TOTAL_DIAMOND_PCS", "Cat-BraceletsCharms", "C:Number of Diamonds", "direct", ""),
        ("bracelet", "LENGTH", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("bracelet", "item_length", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("bracelet", "Item Length", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("bracelet", "Item_Length", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("bracelet", "CHAIN_LENGTH", "Cat-BraceletsCharms", "C:Item Length", "direct", ""),
        ("bracelet", "Style", "Cat-BraceletsCharms", "Style", "direct", ""),

        # --- WEDDING BAND / Cat-WeddingAnniversaryBands ---
        ("wedding band", "SKU", "Cat-WeddingAnniversaryBands", "Custom label (SKU)", "direct", ""),
        ("wedding band", "Price", "Cat-WeddingAnniversaryBands", "Start price", "direct", ""),
        ("wedding band", "GOLD_KT", "Cat-WeddingAnniversaryBands", "C:Metal Purity", "direct", ""),
        ("wedding band", "GOLD_COLOR", "Cat-WeddingAnniversaryBands", "C:Color", "direct", ""),
        ("wedding band", "CENTER_STONE_SHAPE", "Cat-WeddingAnniversaryBands", "C:Main Stone Shape", "direct", ""),
        ("wedding band", "TCW", "Cat-WeddingAnniversaryBands", "C:Total Carat Weight", "direct", ""),
        ("wedding band", "TOTAL_DIAMOND_PCS", "Cat-WeddingAnniversaryBands", "C:Number of Diamonds", "direct", ""),
        ("wedding band", "Style", "Cat-WeddingAnniversaryBands", "Style", "direct", ""),

        # --- WEDDING RING SET / Cat-EngagementWeddingRingSets ---
        ("wedding ring set", "SKU", "Cat-EngagementWeddingRingSets", "Custom label (SKU)", "direct", ""),
        ("wedding ring set", "Price", "Cat-EngagementWeddingRingSets", "Start price", "direct", ""),
        ("wedding ring set", "GOLD_KT", "Cat-EngagementWeddingRingSets", "C:Metal Purity", "direct", ""),
        ("wedding ring set", "GOLD_COLOR", "Cat-EngagementWeddingRingSets", "C:Color", "direct", ""),
        ("wedding ring set", "CENTER_STONE_SHAPE", "Cat-EngagementWeddingRingSets", "C:Main Stone Shape", "direct", ""),
        ("wedding ring set", "TCW", "Cat-EngagementWeddingRingSets", "C:Total Carat Weight", "direct", ""),
        ("wedding ring set", "TOTAL_DIAMOND_PCS", "Cat-EngagementWeddingRingSets", "C:Number of Diamonds", "direct", ""),
        ("wedding ring set", "Style", "Cat-EngagementWeddingRingSets", "Style", "direct", ""),

        # --- GLOBAL DEFAULT MAPPINGS FOR ALL SHEETS ---
        ("[ALL]", "[DEFAULT]", "[ALL]", "Best Offer Enabled", "static", "TRUE"),

        # --- STATIC DEFAULT VALUES FOR ALL SHEETS ---
        # Engagement Rings
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "*Action(SiteID=US|Country=US|Currency=USD|Version=1193)", "static", "Add"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Condition ID", "static", "1000"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Format", "static", "FixedPrice"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Duration", "static", "GTC"),

        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Quantity", "static", "1"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "C:Main Stone Creation", "static", "Lab-Created"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "C:Main Stone", "static", "Diamond"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "C:Type", "static", "Engagement Ring"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "C:Department", "static", "Women"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "C:Country of Origin", "static", "United States"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Returns accepted option", "static", "ReturnsAccepted"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Returns within option", "static", "Days_30"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Refund option", "static", "MoneyBack"),
        ("RING", "[DEFAULT]", "Cat-EngagementRings", "Return shipping cost paid by", "static", "Seller"),

        # Earrings
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "*Action(SiteID=US|Country=US|Currency=USD|Version=1193)", "static", "Add"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Condition ID", "static", "1000"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Format", "static", "FixedPrice"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Duration", "static", "GTC"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Quantity", "static", "1"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "C:Main Stone Creation", "static", "Lab-Created"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "C:Main Stone", "static", "Diamond"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "C:Type", "static", "Earrings"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "C:Department", "static", "Women"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "C:Country of Origin", "static", "United States"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Returns accepted option", "static", "ReturnsAccepted"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Returns within option", "static", "Days_30"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Refund option", "static", "MoneyBack"),
        ("EARRINGS", "[DEFAULT]", "Cat-Earrings", "Return shipping cost paid by", "static", "Seller"),

        # Pendants
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "*Action(SiteID=US|Country=US|Currency=USD|Version=1193)", "static", "Add"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Condition ID", "static", "1000"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Format", "static", "FixedPrice"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Duration", "static", "GTC"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Quantity", "static", "1"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "C:Main Stone Creation", "static", "Lab-Created"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "C:Main Stone", "static", "Diamond"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "C:Type", "static", "Pendant"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "C:Department", "static", "Women"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "C:Country of Origin", "static", "United States"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Returns accepted option", "static", "ReturnsAccepted"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Returns within option", "static", "Days_30"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Refund option", "static", "MoneyBack"),
        ("PENDANT", "[DEFAULT]", "Cat-NecklacesPendants", "Return shipping cost paid by", "static", "Seller"),

        # Bracelets
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "*Action(SiteID=US|Country=US|Currency=USD|Version=1193)", "static", "Add"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Condition ID", "static", "1000"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Format", "static", "FixedPrice"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Duration", "static", "GTC"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Quantity", "static", "1"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "C:Main Stone Creation", "static", "Lab-Created"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "C:Main Stone", "static", "Diamond"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "C:Type", "static", "Bracelet"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "C:Department", "static", "Women"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "C:Country of Origin", "static", "United States"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Returns accepted option", "static", "ReturnsAccepted"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Returns within option", "static", "Days_30"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Refund option", "static", "MoneyBack"),
        ("BRACELET", "[DEFAULT]", "Cat-BraceletsCharms", "Return shipping cost paid by", "static", "Seller"),

        # Wedding Bands
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "*Action(SiteID=US|Country=US|Currency=USD|Version=1193)", "static", "Add"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "Condition ID", "static", "1000"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "Format", "static", "FixedPrice"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "Duration", "static", "GTC"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "Quantity", "static", "1"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "C:Main Stone Creation", "static", "Lab-Created"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "C:Main Stone", "static", "Diamond"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "C:Type", "static", "Wedding Band"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "C:Department", "static", "Unisex Adult"),
        ("wedding band", "[DEFAULT]", "Cat-WeddingAnniversaryBands", "Returns accepted option", "static", "ReturnsAccepted"),

        # Wedding Ring Sets
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "*Action(SiteID=US|Country=US|Currency=USD|Version=1193)", "static", "Add"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "Condition ID", "static", "1000"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "Format", "static", "FixedPrice"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "Duration", "static", "GTC"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "Quantity", "static", "1"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "C:Main Stone Creation", "static", "Lab-Created"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "C:Main Stone", "static", "Diamond"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "C:Type", "static", "Ring Set"),
        ("wedding ring set", "[DEFAULT]", "Cat-EngagementWeddingRingSets", "C:Department", "static", "Women")
    ]



    for src_s, src_c, tgt_s, tgt_c, m_type, def_v in default_mappings:
        cursor.execute("""
            INSERT INTO excel_mappings (source_sheet, source_column, target_sheet, target_column, mapping_type, default_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (src_s, src_c, tgt_s, tgt_c, m_type, def_v))

    conn.commit()
    conn.close()
    return True

# Database Backup & Restore Functions
def get_backup_notes():
    """Load notes dictionary from backups/backup_notes.json."""
    try:
        notes_file = os.path.join(PROJECT_ROOT, "backups", "backup_notes.json")
        if os.path.exists(notes_file):
            with open(notes_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading backup notes: {e}")
    return {}

def save_backup_note(filename, note):
    """Save or update description note for a backup file in backups/backup_notes.json."""
    try:
        backups_dir = os.path.join(PROJECT_ROOT, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        notes_file = os.path.join(backups_dir, "backup_notes.json")
        notes = get_backup_notes()
        notes[filename] = str(note).strip()
        with open(notes_file, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": f"Note saved for {filename}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to save backup note: {str(e)}"}

def delete_backup(filename):
    """Delete a backup file from backups directory."""
    try:
        backups_dir = os.path.join(PROJECT_ROOT, "backups")
        full_p = os.path.join(backups_dir, filename)
        if os.path.exists(full_p):
            os.remove(full_p)
            notes = get_backup_notes()
            if filename in notes:
                del notes[filename]
                notes_file = os.path.join(backups_dir, "backup_notes.json")
                with open(notes_file, "w", encoding="utf-8") as f:
                    json.dump(notes, f, indent=2, ensure_ascii=False)
            return {"status": "success", "message": f"Backup file {filename} deleted."}
        return {"status": "error", "message": "Backup file not found."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete backup: {str(e)}"}

def backup_database(description=""):
    """Create a timestamped backup copy of app_database.db in backups directory with optional description."""
    try:
        if not os.path.exists(DB_FILE):
            return {"status": "error", "message": "Database file app_database.db not found."}
        
        backups_dir = os.path.join(PROJECT_ROOT, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"app_database_backup_{timestamp}.db"
        backup_path = os.path.join(backups_dir, backup_filename)
        
        shutil.copy2(DB_FILE, backup_path)
        
        if description and str(description).strip():
            save_backup_note(backup_filename, str(description).strip())
            
        return {
            "status": "success",
            "message": f"Database backup created successfully: {backup_filename}",
            "filename": backup_filename,
            "path": backup_path,
            "timestamp": timestamp,
            "description": str(description).strip() if description else ""
        }
    except Exception as e:
        return {"status": "error", "message": f"Backup failed: {str(e)}"}

def list_database_backups():
    """List existing database backups in backups directory with descriptions."""
    try:
        backups_dir = os.path.join(PROJECT_ROOT, "backups")
        if not os.path.exists(backups_dir):
            return []
        
        notes = get_backup_notes()
        files = []
        for f in os.listdir(backups_dir):
            if (f.endswith(".db") or f.endswith(".sqlite")) and not f.startswith("pre_restore_safety_"):
                full_p = os.path.join(backups_dir, f)
                stat = os.stat(full_p)
                files.append({
                    "filename": f,
                    "path": full_p,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "description": notes.get(f, "")
                })
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return files
    except Exception as e:
        print(f"Error listing backups: {e}")
        return []

def restore_database(backup_file_path=None, file_bytes=None):
    """Restore app_database.db from a specified backup file path or raw binary data."""
    try:
        backups_dir = os.path.join(PROJECT_ROOT, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        
        target_file = None
        if backup_file_path and os.path.exists(backup_file_path):
            target_file = backup_file_path
        elif file_bytes:
            temp_target = os.path.join(backups_dir, "temp_restore.db")
            with open(temp_target, "wb") as f:
                f.write(file_bytes)
            target_file = temp_target
        else:
            return {"status": "error", "message": "No valid backup file specified for restoration."}

        # 2. Validate SQLite format and required tables of target file
        temp_conn = sqlite3.connect(target_file)
        c = temp_conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        temp_conn.close()

        required = ['categories', 'subcategories', 'setting_columns', 'title_templates', 'company_html_templates', 'business_policies', 'products', 'placeholders']
        missing = [req for req in required if req not in tables]
        if missing:
            return {"status": "error", "message": f"Invalid backup file! Missing required master tables: {', '.join(missing)}"}

        # 3. Replace app_database.db safely
        shutil.copy2(target_file, DB_FILE)
        
        # 4. Refresh connection/settings
        init_db()
        return {"status": "success", "message": "Database restored successfully! App data reloaded."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to restore database: {str(e)}"}

def export_html_templates_to_excel(company_name=""):
    """
    Export HTML templates to an Excel (.xlsx) file base64 string.
    Ensures that for the selected company (or all companies), ALL registered
    categories and their subcategories are exported in the Excel file,
    even if their HTML template is currently blank/empty.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Determine target companies
        target_companies = []
        is_single_company = False
        if company_name and company_name.strip() and company_name.strip().lower() != 'all':
            req_comp = company_name.strip()
            # Match canonical company name from business_policies if possible
            cursor.execute("SELECT company_name FROM business_policies WHERE LOWER(company_name)=LOWER(?)", (req_comp,))
            matched = cursor.fetchone()
            if matched:
                target_companies = [matched["company_name"]]
            else:
                target_companies = [req_comp]
            is_single_company = True
        else:
            cursor.execute("SELECT company_name FROM business_policies ORDER BY company_name ASC")
            target_companies = [r["company_name"] for r in cursor.fetchall()]
            # Also add any company present in company_html_templates that might not have a business policy
            cursor.execute("SELECT DISTINCT company_name FROM company_html_templates")
            existing_comps = [r["company_name"] for r in cursor.fetchall()]
            for ec in existing_comps:
                if ec and not any(ec.lower() == tc.lower() for tc in target_companies):
                    target_companies.append(ec)
            if not target_companies:
                target_companies = ["Default Company"]

        # 2. Fetch existing HTML templates into a fast lookup map
        if is_single_company:
            cursor.execute("""
                SELECT company_name, category, subcategory, html_template 
                FROM company_html_templates 
                WHERE LOWER(company_name)=LOWER(?)
            """, (target_companies[0],))
        else:
            cursor.execute("""
                SELECT company_name, category, subcategory, html_template 
                FROM company_html_templates
            """)
        existing_tpls = cursor.fetchall()
        conn.close()

        # lookup key: (comp.lower(), cat.lower(), subcat.lower()) -> html_template
        existing_map = {}
        extra_pairs_by_comp = {}
        for row in existing_tpls:
            c_name = row["company_name"]
            cat_name = row["category"]
            subcat_name = row["subcategory"]
            tpl = row["html_template"] or ""
            key = (c_name.lower().strip(), cat_name.lower().strip(), subcat_name.lower().strip())
            existing_map[key] = tpl

            comp_lower = c_name.lower().strip()
            if comp_lower not in extra_pairs_by_comp:
                extra_pairs_by_comp[comp_lower] = []
            extra_pairs_by_comp[comp_lower].append((cat_name, subcat_name))

        # 3. Build comprehensive row list
        rows = []
        for comp in target_companies:
            comp_lower = comp.lower().strip()
            visited_keys = set()

            # Fetch categories applicable to this company (All + Company-specific)
            comp_categories = [c["name"] for c in get_all_categories(comp)]
            if not comp_categories:
                comp_categories = ['Engagement Ring', 'Wedding Band', 'Wedding Ring Set', "Men's Ring", 'Pendant', 'Earrings', 'Bracelet']

            for cat in comp_categories:
                # Fetch subcategories applicable to this company and category
                subcats_objs = get_all_subcategories(cat, comp)
                subcats = [s["name"] for s in subcats_objs]
                if not any(s.lower() == 'default' for s in subcats):
                    subcats.insert(0, 'Default')

                for subcat in subcats:
                    key = (comp_lower, cat.lower().strip(), subcat.lower().strip())
                    visited_keys.add(key)
                    html_code = existing_map.get(key, "")

                    rows.append({
                        "Company Scope": comp,
                        "Category": cat,
                        "Subcategory": subcat,
                        "HTML Code": html_code
                    })

            # Include any custom/legacy template rows (like 'default / default') that were already saved in the DB
            for cat_name, subcat_name in extra_pairs_by_comp.get(comp_lower, []):
                key = (comp_lower, cat_name.lower().strip(), subcat_name.lower().strip())
                if key not in visited_keys and key in existing_map:
                    visited_keys.add(key)
                    rows.append({
                        "Company Scope": comp,
                        "Category": cat_name,
                        "Subcategory": subcat_name,
                        "HTML Code": existing_map[key]
                    })

        df = pd.DataFrame(rows)

        import io
        import base64
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='HTML_Templates')
            
            # Format column widths nicely
            try:
                ws = writer.sheets['HTML_Templates']
                ws.column_dimensions['A'].width = 28 # Company Scope
                ws.column_dimensions['B'].width = 22 # Category
                ws.column_dimensions['C'].width = 20 # Subcategory
                ws.column_dimensions['D'].width = 60 # HTML Code
            except Exception:
                pass
        
        excel_bytes = output.getvalue()
        b64_str = base64.b64encode(excel_bytes).decode('utf-8')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if is_single_company:
            clean_name = re.sub(r'[^\w\-_.]', '_', target_companies[0].strip())
            filename = f"HTML_Templates_{clean_name}_{timestamp}.xlsx"
            msg = f"Successfully exported all {len(rows)} categories & subcategories for {target_companies[0]} to Excel!"
        else:
            filename = f"HTML_Templates_All_Companies_{timestamp}.xlsx"
            msg = f"Successfully exported {len(rows)} template slots across {len(target_companies)} companies to Excel!"

        return {
            "status": "success",
            "count": len(rows),
            "filename": filename,
            "file_b64": b64_str,
            "message": msg
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Export failed: {str(e)}"}

def import_html_templates_from_excel(file_path=None, file_b64=None):
    """Import and bulk add/update HTML templates from Excel (.xlsx) file."""
    import base64
    import io
    try:
        if file_b64:
            if ',' in file_b64:
                file_b64 = file_b64.split(',', 1)[1]
            file_bytes = base64.b64decode(file_b64)
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif file_path and os.path.exists(file_path):
            df = pd.read_excel(file_path)
        else:
            return {"status": "error", "message": "No valid file or data provided for import."}

        # Normalize column names
        col_map = {}
        for col in df.columns:
            c_lower = str(col).strip().lower()
            if any(k in c_lower for k in ['company', 'brand']):
                col_map['company'] = col
            elif 'sub' in c_lower and ('cat' in c_lower or 'type' in c_lower or 'name' in c_lower):
                col_map['subcategory'] = col
            elif 'cat' in c_lower:
                col_map['category'] = col
            elif any(k in c_lower for k in ['html', 'code', 'template', 'body']):
                col_map['html_code'] = col

        if 'company' not in col_map or 'html_code' not in col_map:
            return {
                "status": "error", 
                "message": f"Invalid Excel headers! Required columns: 'Company Scope', 'Category', 'Subcategory', 'HTML Code'. Found columns: {list(df.columns)}"
            }

        imported_count = 0
        updated_count = 0
        
        conn = get_db_connection()
        cursor = conn.cursor()

        for idx, row in df.iterrows():
            comp = str(row[col_map['company']]).strip() if pd.notna(row[col_map['company']]) else ""
            if not comp or comp.lower() == 'nan':
                continue

            cat = str(row[col_map['category']]).strip() if ('category' in col_map and pd.notna(row[col_map['category']])) else "default"
            if not cat or cat.lower() == 'nan':
                cat = "default"

            subcat = str(row[col_map['subcategory']]).strip() if ('subcategory' in col_map and pd.notna(row[col_map['subcategory']])) else "default"
            if not subcat or subcat.lower() == 'nan':
                subcat = "default"

            html = str(row[col_map['html_code']]).strip() if pd.notna(row[col_map['html_code']]) else ""
            if not html or html.lower() == 'nan':
                continue

            # Auto-ensure category exists in categories table
            if cat.lower() != 'default':
                cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

            # Auto-ensure subcategory exists in subcategories table
            if subcat.lower() != 'default':
                cursor.execute("INSERT OR IGNORE INTO subcategories (category, name) VALUES (?, ?)", (cat, subcat))

            # Upsert into company_html_templates
            cursor.execute("""
                SELECT id FROM company_html_templates 
                WHERE LOWER(company_name)=LOWER(?) AND LOWER(category)=LOWER(?) AND LOWER(subcategory)=LOWER(?)
            """, (comp, cat, subcat))
            existing = cursor.fetchone()

            clean_html = clean_raw_html_code(html)
            if existing:
                cursor.execute("""
                    UPDATE company_html_templates 
                    SET html_template=?, company_name=?, category=?, subcategory=?
                    WHERE id=?
                """, (clean_html, comp, cat, subcat, existing["id"]))
                updated_count += 1
            else:
                cursor.execute("""
                    INSERT INTO company_html_templates (company_name, category, subcategory, html_template)
                    VALUES (?, ?, ?, ?)
                """, (comp, cat, subcat, clean_html))
                imported_count += 1

        conn.commit()
        conn.close()

        total = imported_count + updated_count
        return {
            "status": "success",
            "imported": imported_count,
            "updated": updated_count,
            "total": total,
            "message": f"Successfully processed {total} templates! ({imported_count} new added, {updated_count} updated)"
        }
    except Exception as e:
        return {"status": "error", "message": f"Import failed: {str(e)}"}

def get_sample_html_excel_data():
    """Generates a sample Excel workbook b64 for user guidance."""
    sample_rows = [
        {
            "Company Scope": "Alisi Jewel",
            "Category": "Earrings",
            "Subcategory": "Solitaire",
            "HTML Code": '<div><h1>Alisi Solitaire Earrings</h1><p>{DESCRIPTION}</p><div>{PAYMENT_HTML}</div></div>'
        },
        {
            "Company Scope": "ANANTA JEWELS by Keeva",
            "Category": "Bracelet",
            "Subcategory": "Default",
            "HTML Code": '<div><h1>Ananta Fine Bracelet</h1><p>{ITEM_TITLE}</p></div>'
        },
        {
            "Company Scope": "Avani Jewels",
            "Category": "Engagement Ring",
            "Subcategory": "No Accents",
            "HTML Code": '<div><h1>Avani Engagement Ring</h1><p>Metal: {GOLD_KT} {GOLD_COLOR}</p></div>'
        }
    ]
    df = pd.DataFrame(sample_rows)
    import io
    import base64
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='HTML_Templates_Sample')
    
    b64_str = base64.b64encode(output.getvalue()).decode('utf-8')
    return {
        "filename": "Sample_HTML_Templates.xlsx",
        "file_b64": b64_str
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")


