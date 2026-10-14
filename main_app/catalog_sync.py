import os
import re
from tracker.models import ProcessItem, PartyDataRecord, ProcessItemHistory
from tracker.views import parse_catalog_file

STOP_WORDS = {
    'jewels', 'jewel', 'jewelry', 'fine', 'inc', 'ltd', 'usa', 'diamond', 'diamonds',
    'gold', 'silver', 'lab', 'true', 'shree', 'the', 'and', 'by', 'world', 'co'
}


def find_or_create_party(company_name):
    """
    Finds existing ProcessItem (Party) by matching company_name,
    or creates a new ProcessItem if not found.
    """
    if not company_name or not company_name.strip():
        return None
    c_clean = company_name.strip()

    # 1. Exact match (case-insensitive)
    party = ProcessItem.objects.filter(client_name__iexact=c_clean).first()
    if party:
        return party

    # 2. Substring match
    cl = c_clean.lower()
    for item in ProcessItem.objects.all():
        il = item.client_name.lower()
        if cl in il or il in cl:
            return item

    # 3. Meaningful word match (>= 4 chars, excluding STOP_WORDS)
    cw = [w for w in re.findall(r'[a-zA-Z0-9]+', cl) if len(w) >= 4 and w not in STOP_WORDS]
    if cw:
        for item in ProcessItem.objects.all():
            iw = [w for w in re.findall(r'[a-zA-Z0-9]+', item.client_name.lower()) if len(w) >= 4 and w not in STOP_WORDS]
            if any(w in iw for w in cw):
                return item

    # 4. If no existing client matches, create new ProcessItem for this company
    party, _ = ProcessItem.objects.get_or_create(client_name=c_clean)
    return party


def sync_data_to_catalog(data_file_path, company_name=None, import_mode='append'):
    """
    Parses data.xlsx and automatically syncs all rows into PartyDataRecord (Product & SKU Catalog)
    associated with the matched ProcessItem (Party).
    Supports multi-sheet files and updates existing records while preventing duplicate entries.
    """
    if not os.path.exists(data_file_path):
        return {'status': 'error', 'error': f'File not found: {data_file_path}'}

    party = find_or_create_party(company_name)
    if not party:
        return {'status': 'skipped', 'message': 'No company specified to sync catalog.'}

    try:
        with open(data_file_path, 'rb') as f:
            records_data, _, detected_sheets = parse_catalog_file(f)
    except Exception as e:
        return {'status': 'error', 'error': f'Failed to parse catalog file: {str(e)}'}

    if not records_data:
        return {'status': 'empty', 'message': 'No catalog records found in file.'}

    # Store detected sheets in party custom_fields for tab display in catalog
    if detected_sheets:
        if not isinstance(party.custom_fields, dict):
            party.custom_fields = {}
        party.custom_fields['catalog_sheets'] = detected_sheets
        party.save(update_fields=['custom_fields'])

    fields_to_compare = [
        'lot', 'category', 'certified', 'gold_kt', 'gold_color', 'gold_weight',
        'center_diamond_clarity', 'center_diamond_color', 'center_stone_shape',
        'center_stone_weight', 'side_stone_shape', 'side_stone_weight',
        'side_stone_color_clarity', 'setting', 'total_diamond_pcs', 'cost_usd',
        'selling_price_usd'
    ]

    def make_signature(d):
        return (
            str(d.get('category') or '').strip().upper(),
            str(d.get('lot') or '').strip().upper(),
            str(d.get('center_stone_shape') or '').strip().upper(),
            str(d.get('gold_weight') or '').strip(),
            str(d.get('cost_usd') or '').strip(),
            str(d.get('selling_price_usd') or '').strip(),
            str(d.get('center_diamond_clarity') or '').strip().upper(),
        )

    if import_mode == 'replace':
        party.data_records.all().delete()
        start_order = 1
        existing_by_combo = {}
        existing_by_sig = {}
    else:
        last_record = party.data_records.order_by('-order_index').first()
        start_order = (last_record.order_index + 1) if last_record else 1
        existing_by_combo = {}
        existing_by_sig = {}
        for rec in party.data_records.all():
            sku_norm = rec.sku.strip().upper() if rec.sku else None
            cat_norm = (rec.category or '').strip().upper()
            if sku_norm:
                combo_key = (sku_norm, cat_norm)
                if combo_key not in existing_by_combo:
                    existing_by_combo[combo_key] = rec
            rec_sig = (
                cat_norm,
                str(rec.lot or '').strip().upper(),
                str(rec.center_stone_shape or '').strip().upper(),
                str(rec.gold_weight or '').strip(),
                str(rec.cost_usd or '').strip(),
                str(rec.selling_price_usd or '').strip(),
                str(rec.center_diamond_clarity or '').strip().upper(),
            )
            if rec_sig not in existing_by_sig:
                existing_by_sig[rec_sig] = rec

    new_objs = []
    updated_count = 0
    skipped_duplicates = 0
    seen_file_combos = set()
    seen_file_sigs = set()

    for r_data in records_data:
        raw_sku = (r_data.get('sku') or '').strip()
        sku_norm = raw_sku.upper() if raw_sku else None
        cat_norm = (r_data.get('category') or '').strip().upper()
        combo_key = (sku_norm, cat_norm) if sku_norm else None
        sig = make_signature(r_data)

        if combo_key:
            if combo_key in seen_file_combos:
                skipped_duplicates += 1
                continue
            seen_file_combos.add(combo_key)
        else:
            if sig in seen_file_sigs:
                skipped_duplicates += 1
                continue
            seen_file_sigs.add(sig)

        if import_mode != 'replace':
            target_rec = None
            if combo_key and combo_key in existing_by_combo:
                target_rec = existing_by_combo[combo_key]
            elif not combo_key and sig in existing_by_sig:
                target_rec = existing_by_sig[sig]

            if target_rec:
                is_identical = True
                for f in fields_to_compare:
                    old_val = str(getattr(target_rec, f, '') or '').strip()
                    new_val = str(r_data.get(f, '') or '').strip()
                    if old_val != new_val:
                        is_identical = False
                        break
                if is_identical:
                    skipped_duplicates += 1
                    continue
                else:
                    for f in fields_to_compare:
                        setattr(target_rec, f, r_data.get(f, ''))
                    if r_data.get('sheet_name'):
                        target_rec.sheet_name = r_data['sheet_name']
                    if r_data.get('extra_data'):
                        target_rec.extra_data = r_data['extra_data']
                    target_rec.save()
                    updated_count += 1
                    continue

        new_objs.append(PartyDataRecord(
            party=party,
            order_index=start_order + len(new_objs),
            sheet_name=r_data.get('sheet_name', ''),
            sku=raw_sku,
            lot=r_data.get('lot', ''),
            category=r_data.get('category', ''),
            certified=r_data.get('certified', ''),
            gold_kt=r_data.get('gold_kt', ''),
            gold_color=r_data.get('gold_color', ''),
            gold_weight=r_data.get('gold_weight', ''),
            center_diamond_clarity=r_data.get('center_diamond_clarity', ''),
            center_diamond_color=r_data.get('center_diamond_color', ''),
            center_stone_shape=r_data.get('center_stone_shape', ''),
            center_stone_weight=r_data.get('center_stone_weight', ''),
            side_stone_shape=r_data.get('side_stone_shape', ''),
            side_stone_weight=r_data.get('side_stone_weight', ''),
            side_stone_color_clarity=r_data.get('side_stone_color_clarity', ''),
            setting=r_data.get('setting', ''),
            total_diamond_pcs=r_data.get('total_diamond_pcs', ''),
            cost_usd=r_data.get('cost_usd', ''),
            selling_price_usd=r_data.get('selling_price_usd', ''),
            extra_data=r_data.get('extra_data', {}),
        ))

    if new_objs:
        PartyDataRecord.objects.bulk_create(new_objs)

    return {
        'status': 'success',
        'party_id': party.id,
        'party_name': party.client_name,
        'added': len(new_objs),
        'updated': updated_count,
        'skipped': skipped_duplicates,
        'total': len(records_data),
        'sheets': detected_sheets
    }
