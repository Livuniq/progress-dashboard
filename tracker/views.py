from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from django.contrib import messages
from datetime import date, datetime
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

from .models import ProcessItem, ProcessItemHistory, TableColumnConfig, StatusColorConfig
from .forms import ProcessItemForm

TRACKED_FIELDS = [
    ('client_name', 'Client / Account Name'),
    ('status', 'Status'),
    ('is_red_client', 'Highlight Client Red'),
    ('row_highlight_color', 'Row Highlight Color (Hex)'),
    ('lot_progress', 'LOT Progress'),
    ('completed_count', 'Completed Count'),
    ('pending_count', 'Pending Count'),
    ('ready_count', 'Ready Count'),
    ('target_date', 'Target Date'),
    ('notes', 'Notes / Remarks'),
    ('notes_is_red', 'Highlight Notes Red'),
    ('history_milestone', 'History / Milestone'),
    ('is_priority', 'High Priority'),
]


def dashboard(request):
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    
    # Query parameters
    status_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    
    items = ProcessItem.objects.all()

    # Apply Search
    if search_query:
        items = items.filter(
            Q(client_name__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(lot_progress__icontains=search_query)
        )

    # Filter logic
    if status_filter == 'working':
        items = [item for item in items if item.dynamic_status == 'working']
    elif status_filter == 'no_data':
        items = [item for item in items if item.dynamic_status == 'no_data']
    elif status_filter == 'finished':
        items = [item for item in items if item.dynamic_status == 'finished']
    elif status_filter == 'hold':
        items = [item for item in items if item.dynamic_status == 'hold']
    elif status_filter == 'pending':
        items = [item for item in items if item.dynamic_status == 'pending']
    elif status_filter == 'overdue':
        items = [item for item in items if item.is_overdue]

    # Metrics calculation (all items base)
    all_items = list(ProcessItem.objects.all())
    total_clients = len(all_items)
    hidden_count = sum(1 for item in all_items if item.is_hidden)
    working_count = sum(1 for item in all_items if item.dynamic_status == 'working')
    no_data_count = sum(1 for item in all_items if item.dynamic_status == 'no_data')
    finished_count = sum(1 for item in all_items if item.dynamic_status == 'finished')
    hold_count = sum(1 for item in all_items if item.dynamic_status == 'hold')
    pending_count = sum(1 for item in all_items if item.dynamic_status == 'pending')
    
    overdue_count = sum(1 for item in all_items if item.is_overdue)
    total_pending = sum((item.pending_count or 0) for item in all_items)
    total_ready = sum((item.ready_count or 0) for item in all_items)

    # Header Column Configuration
    columns_map = TableColumnConfig.get_columns_map()
    all_columns = TableColumnConfig.objects.all().order_by('order_index', 'id')
    ordered_columns = TableColumnConfig.objects.filter(is_visible=True).order_by('order_index', 'id')
    status_colors = StatusColorConfig.get_colors_map()

    context = {
        'items': items,
        'today': today,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_clients': total_clients,
        'hidden_count': hidden_count,
        'working_count': working_count,
        'no_data_count': no_data_count,
        'finished_count': finished_count,
        'hold_count': hold_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'total_pending': total_pending,
        'total_ready': total_ready,
        'form': ProcessItemForm(),
        'cols': columns_map,
        'all_columns': all_columns,
        'ordered_columns': ordered_columns,
        'status_colors': status_colors,
    }
    return render(request, 'tracker/dashboard.html', context)


def item_create(request):
    if request.method == 'POST':
        form = ProcessItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            
            # Record initial history
            initial_changes = []
            for field, label in TRACKED_FIELDS:
                val = getattr(item, field)
                if val is not None and val != '' and val is not False:
                    if isinstance(val, date):
                        val_str = val.strftime('%d/%m/%Y')
                    elif isinstance(val, bool):
                        val_str = 'Yes' if val else 'No'
                    elif field == 'status':
                        val_str = dict(ProcessItem.STATUS_CHOICES).get(val, str(val))
                    else:
                        val_str = str(val)
                    initial_changes.append({
                        'field': field,
                        'label': label,
                        'old': '-',
                        'new': val_str,
                    })

            ProcessItemHistory.objects.create(
                item=item,
                action_type='created',
                summary="Created initial record",
                changes=initial_changes,
            )
            messages.success(request, f"Added client '{item.client_name}' successfully!")
        else:
            messages.error(request, "Error adding item. Please check the form fields.")
    return redirect('tracker:dashboard')


def item_update(request, pk):
    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        # Capture old values
        old_values = {}
        for field, label in TRACKED_FIELDS:
            val = getattr(item, field)
            if isinstance(val, date):
                val = val.strftime('%d/%m/%Y')
            elif val is None:
                val = ''
            elif isinstance(val, bool):
                val = 'Yes' if val else 'No'
            else:
                val = str(val)
            old_values[field] = val

        form = ProcessItemForm(request.POST, instance=item)
        if form.is_valid():
            updated_item = form.save()

            # Compare and build diff
            changes = []
            for field, label in TRACKED_FIELDS:
                new_val = getattr(updated_item, field)
                if isinstance(new_val, date):
                    new_val = new_val.strftime('%d/%m/%Y')
                elif new_val is None:
                    new_val = ''
                elif isinstance(new_val, bool):
                    new_val = 'Yes' if new_val else 'No'
                else:
                    new_val = str(new_val)

                if old_values[field] != new_val:
                    old_disp = dict(ProcessItem.STATUS_CHOICES).get(old_values[field], old_values[field]) if field == 'status' else old_values[field]
                    new_disp = dict(ProcessItem.STATUS_CHOICES).get(new_val, new_val) if field == 'status' else new_val
                    changes.append({
                        'field': field,
                        'label': label,
                        'old': old_disp if old_disp != '' else '(empty)',
                        'new': new_disp if new_disp != '' else '(empty)',
                    })

            if changes:
                summary = f"Changed {len(changes)} field(s): " + ", ".join([c['label'] for c in changes[:3]])
                if len(changes) > 3:
                    summary += f" and {len(changes) - 3} more"
                ProcessItemHistory.objects.create(
                    item=updated_item,
                    action_type='updated',
                    summary=summary,
                    changes=changes,
                )

            messages.success(request, f"Updated '{item.client_name}' successfully!")
        else:
            messages.error(request, "Error updating item. Please check the values.")
    return redirect('tracker:dashboard')


def item_get_json(request, pk):
    item = get_object_or_404(ProcessItem, pk=pk)
    data = {
        'id': item.id,
        'client_name': item.client_name,
        'is_red_client': item.is_red_client,
        'status': item.status,
        'lot_progress': item.lot_progress,
        'current_lot': item.current_lot,
        'total_lot': item.total_lot,
        'completed_count': item.completed_count,
        'pending_count': item.pending_count,
        'ready_count': item.ready_count,
        'notes': item.notes,
        'notes_is_red': item.notes_is_red,
        'target_date': item.target_date.strftime('%Y-%m-%d') if item.target_date else '',
        'history_milestone': item.history_milestone,
        'row_highlight_color': item.row_highlight_color or '',
        'is_priority': item.is_priority,
    }
    return JsonResponse(data)


def item_quick_status(request, pk):
    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        import json
        try:
            body_data = json.loads(request.body)
            new_status = body_data.get('status')
        except Exception:
            new_status = request.POST.get('status')

        valid_statuses = dict(ProcessItem.STATUS_CHOICES)
        if new_status in valid_statuses:
            old_status = item.status
            if old_status != new_status:
                item.status = new_status
                item.row_highlight_color = ''
                item.save()

                # Record in history
                old_label = valid_statuses.get(old_status, old_status)
                new_label = valid_statuses.get(new_status, new_status)
                ProcessItemHistory.objects.create(
                    item=item,
                    action_type='updated',
                    summary=f"Status changed from '{old_label}' to '{new_label}'",
                    changes=[{
                        'field': 'status',
                        'label': 'Status',
                        'old': old_label,
                        'new': new_label
                    }]
                )

            return JsonResponse({
                'success': True,
                'status': item.status,
                'status_display': item.get_status_display(),
                'is_overdue': item.is_overdue,
                'days_diff': item.days_diff,
                'client_name': item.client_name,
            })
        return JsonResponse({'success': False, 'error': 'Invalid status choice'}, status=400)
    return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)


def item_inline_update(request, pk):
    """
    Inline double-click edit for LOT / ITEM and TARGET DATE.
    Automatically logs change in ProcessItemHistory and returns updated values.
    """
    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        import json
        field = None
        value = None
        try:
            body = json.loads(request.body)
            field = body.get('field')
            value = body.get('value')
        except Exception:
            field = request.POST.get('field')
            value = request.POST.get('value')

        if field == 'lot_progress':
            old_lot = item.formatted_lot or item.lot_progress or '-'
            new_lot = str(value or '').strip()
            item.lot_progress = new_lot
            item.save()

            new_formatted = item.formatted_lot or new_lot or '-'
            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=f"LOT / ITEM updated to '{new_formatted}'",
                changes=[{
                    'field': 'lot_progress',
                    'label': 'LOT / ITEM',
                    'old': old_lot,
                    'new': new_formatted
                }]
            )

            return JsonResponse({
                'success': True,
                'field': 'lot_progress',
                'raw_value': item.lot_progress,
                'formatted_lot': item.formatted_lot or item.lot_progress,
                'is_finished': item.lot_progress.lower() == 'finished',
            })

        elif field == 'target_date':
            old_date_str = item.target_date.strftime('%d/%m/%Y') if item.target_date else '-'
            new_val_str = str(value or '').strip()
            new_date = None
            if new_val_str:
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                    try:
                        new_date = datetime.strptime(new_val_str, fmt).date()
                        break
                    except ValueError:
                        pass

            item.target_date = new_date
            item.save()

            new_date_display = item.target_date.strftime('%d/%m/%Y') if item.target_date else '-'
            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=f"Target Date updated from '{old_date_str}' to '{new_date_display}'",
                changes=[{
                    'field': 'target_date',
                    'label': 'Target Date',
                    'old': old_date_str,
                    'new': new_date_display
                }]
            )

            return JsonResponse({
                'success': True,
                'field': 'target_date',
                'target_date_iso': item.target_date.strftime('%Y-%m-%d') if item.target_date else '',
                'target_date_display': new_date_display,
                'days_diff': item.days_diff,
                'is_overdue': item.is_overdue,
                'dynamic_status': item.dynamic_status,
                'dynamic_status_display': item.dynamic_status_display,
            })

        elif field == 'notes':
            old_notes = item.notes or '-'
            new_notes = str(value or '').strip()
            item.notes = new_notes
            item.save()

            summary_text = f"Notes updated to '{new_notes[:40]}...'" if len(new_notes) > 40 else f"Notes updated to '{new_notes or '-'}'"
            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=summary_text,
                changes=[{
                    'field': 'notes',
                    'label': 'Process Notes / Remarks',
                    'old': old_notes,
                    'new': new_notes or '-'
                }]
            )

        elif field == 'status':
            valid_statuses = dict(ProcessItem.STATUS_CHOICES)
            new_status = str(value or '').strip()
            if new_status not in valid_statuses:
                return JsonResponse({'success': False, 'error': 'Invalid status choice'}, status=400)

            old_status = item.status
            if old_status != new_status:
                item.status = new_status
                item.row_highlight_color = ''
                item.save()

                old_label = valid_statuses.get(old_status, old_status)
                new_label = valid_statuses.get(new_status, new_status)
                ProcessItemHistory.objects.create(
                    item=item,
                    action_type='updated',
                    summary=f"Status changed from '{old_label}' to '{new_label}'",
                    changes=[{
                        'field': 'status',
                        'label': 'Status',
                        'old': old_label,
                        'new': new_label
                    }]
                )

            return JsonResponse({
                'success': True,
                'field': 'status',
                'status': item.status,
                'status_display': item.get_status_display(),
                'dynamic_status': item.dynamic_status,
                'dynamic_status_display': item.dynamic_status_display,
                'row_highlight_color': item.row_highlight_color or '',
            })

        elif field == 'is_priority':
            new_priority = bool(value is True or str(value).lower() in ['true', '1', 'yes'])
            old_priority = item.is_priority
            if old_priority != new_priority:
                item.is_priority = new_priority
                item.save()

                old_lbl = "High Priority" if old_priority else "Normal"
                new_lbl = "High Priority" if new_priority else "Normal"
                ProcessItemHistory.objects.create(
                    item=item,
                    action_type='updated',
                    summary=f"Priority updated to '{new_lbl}'",
                    changes=[{
                        'field': 'is_priority',
                        'label': 'Priority',
                        'old': old_lbl,
                        'new': new_lbl
                    }]
                )

            return JsonResponse({
                'success': True,
                'field': 'is_priority',
                'is_priority': item.is_priority,
                'client_name': item.client_name,
            })

        elif field == 'history_milestone':
            old_val = item.history_milestone or '-'
            new_val = str(value or '').strip()
            item.history_milestone = new_val
            item.save()

            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=f"History / Milestone updated to '{new_val or '-'}'",
                changes=[{
                    'field': 'history_milestone',
                    'label': 'History / Milestone',
                    'old': old_val,
                    'new': new_val or '-'
                }]
            )

            return JsonResponse({
                'success': True,
                'field': 'history_milestone',
                'raw_value': item.history_milestone,
            })

        return JsonResponse({'success': False, 'error': f'Unsupported field: {field}'}, status=400)
    return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)


def item_toggle_priority(request, pk):
    """
    Toggle High Priority on a ProcessItem (triggered via row long-press / context menu).
    """
    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        item.is_priority = not item.is_priority
        item.save()

        action_label = "Marked as High Priority (Neon Border)" if item.is_priority else "Removed High Priority"
        ProcessItemHistory.objects.create(
            item=item,
            action_type='updated',
            summary=action_label,
            changes=[{
                'field': 'is_priority',
                'label': 'Priority',
                'old': 'Normal' if item.is_priority else 'High Priority',
                'new': 'High Priority' if item.is_priority else 'Normal'
            }]
        )

        return JsonResponse({
            'success': True,
            'id': item.id,
            'is_priority': item.is_priority,
            'client_name': item.client_name,
        })
    return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)


def item_history_json(request, pk):
    item = get_object_or_404(ProcessItem, pk=pk)
    logs = item.history_logs.all().order_by('-edited_at')
    
    history_list = []
    for log in logs:
        local_time = timezone.localtime(log.edited_at) if hasattr(timezone, 'localtime') else log.edited_at
        history_list.append({
            'id': log.id,
            'datetime_str': local_time.strftime('%d/%m/%Y %I:%M %p'),
            'date_str': local_time.strftime('%d/%m/%Y'),
            'time_str': local_time.strftime('%I:%M %p'),
            'action_type': log.action_type,
            'summary': log.summary or ("Record Created" if log.action_type == 'created' else "Record Updated"),
            'changes': log.changes if isinstance(log.changes, list) else [],
        })
        
    return JsonResponse({
        'client_name': item.client_name,
        'history': history_list
    })



def item_delete(request, pk):
    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        if password != '8264':
            messages.error(request, "Incorrect deletion password! Client was not deleted.")
            return redirect('tracker:dashboard')
        name = item.client_name
        item.delete()
        messages.success(request, f"Deleted '{name}' successfully.")
    return redirect('tracker:dashboard')


def item_toggle_hide(request, pk):
    """Toggle hidden status of a single process item"""
    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        item.is_hidden = not item.is_hidden
        item.save(update_fields=['is_hidden'])
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'id': item.id,
                'is_hidden': item.is_hidden,
                'client_name': item.client_name,
                'message': f"Client '{item.client_name}' {'hidden' if item.is_hidden else 'unhidden'}."
            })
        messages.success(request, f"Client '{item.client_name}' {'hidden' if item.is_hidden else 'restored'}.")
        return redirect('tracker:dashboard')
    return JsonResponse({'error': 'POST required'}, status=405)


def items_bulk_delete(request):
    """Bulk delete multiple clients protected by password 8264"""
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        if password != '8264':
            messages.error(request, "Incorrect deletion password! Bulk deletion cancelled.")
            return redirect('tracker:dashboard')
        
        ids_str = request.POST.get('selected_ids', '').strip()
        ids = []
        if ids_str:
            ids = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
        if not ids:
            ids = [int(x) for x in request.POST.getlist('selected_ids') if str(x).isdigit()]
        
        if ids:
            deleted_count, _ = ProcessItem.objects.filter(id__in=ids).delete()
            messages.success(request, f"Successfully deleted {deleted_count} client(s).")
        else:
            messages.warning(request, "No clients selected for deletion.")
            
    return redirect('tracker:dashboard')


def items_bulk_hide(request):
    """Bulk hide or unhide multiple clients"""
    if request.method == 'POST':
        ids_str = request.POST.get('selected_ids', '').strip()
        ids = []
        if ids_str:
            ids = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
        if not ids:
            ids = [int(x) for x in request.POST.getlist('selected_ids') if str(x).isdigit()]
        
        action = request.POST.get('action', 'hide').lower()
        new_val = (action != 'unhide')
        
        if ids:
            updated_count = ProcessItem.objects.filter(id__in=ids).update(is_hidden=new_val)
            action_word = "hidden" if new_val else "restored"
            messages.success(request, f"Successfully {action_word} {updated_count} client(s).")
        else:
            messages.warning(request, "No clients selected.")
            
    return redirect('tracker:dashboard')


def save_column_config(request):
    """Saves updated header labels, visibility toggles, ordering, and new custom columns"""
    if request.method == 'POST':
        # Check if comma-separated column IDs in order were passed
        column_order_str = request.POST.get('column_order_ids', '').strip()
        ordered_ids_map = {}
        if column_order_str:
            parts = [p.strip() for p in column_order_str.split(',') if p.strip().isdigit()]
            for rank, cid in enumerate(parts, start=1):
                ordered_ids_map[int(cid)] = rank

        all_cols = TableColumnConfig.objects.all()
        for col in all_cols:
            label_val = request.POST.get(f'label_{col.id}')
            visible_val = f'visible_{col.id}' in request.POST
            order_input_val = request.POST.get(f'order_{col.id}')

            if label_val:
                col.label = label_val.strip()
            
            # System columns like counter and actions always stay visible
            if not col.is_system:
                col.is_visible = visible_val
            else:
                col.is_visible = True

            # Determine new order index
            if col.id in ordered_ids_map:
                col.order_index = ordered_ids_map[col.id]
            elif order_input_val is not None and str(order_input_val).strip().isdigit():
                col.order_index = int(str(order_input_val).strip())

            col.save()

        # Handle adding a brand new custom column header
        new_col_name = request.POST.get('new_column_name', '').strip()
        if new_col_name:
            import re
            slug = re.sub(r'[^a-zA-Z0-9_]', '', new_col_name.lower().replace(' ', '_'))
            if not slug:
                slug = f'col_{timezone.now().strftime("%Y%m%d%H%M%S")}'
            key = f'custom_{slug}'
            
            from django.db.models import Max
            max_order = (TableColumnConfig.objects.all().aggregate(Max('order_index'))['order_index__max'] or 12) + 1
            TableColumnConfig.objects.create(
                key=key,
                label=new_col_name,
                is_visible=True,
                order_index=max_order,
                is_custom=True,
                is_system=False,
            )
            messages.success(request, f"Added new header column '{new_col_name}'!")
        else:
            messages.success(request, "Header column configuration and order updated successfully!")

    return redirect('tracker:dashboard')


def delete_column_config(request, pk):
    """Deletes a custom column header"""
    if request.method == 'POST':
        col = get_object_or_404(TableColumnConfig, pk=pk)
        if col.is_custom:
            name = col.label
            col.delete()
            messages.success(request, f"Removed custom header '{name}'.")
        else:
            messages.error(request, "Core system columns cannot be removed.")
    return redirect('tracker:dashboard')


def reset_column_config(request):
    """Resets all header columns to original default labels"""
    TableColumnConfig.reset_to_defaults()
    messages.success(request, "Header columns reset to default successfully!")
    return redirect('tracker:dashboard')


def save_status_colors(request):
    """Saves customized status row highlight hex colors"""
    if request.method == 'POST':
        colors_map = StatusColorConfig.get_colors_map()
        for key, conf in colors_map.items():
            hex_val = request.POST.get(f'color_{key}', '').strip()
            border_val = request.POST.get(f'border_{key}', '').strip()
            conf.is_enabled = f'enabled_{key}' in request.POST
            if hex_val:
                conf.hex_color = hex_val
            if border_val:
                conf.border_color = border_val
            conf.save()
        messages.success(request, "Status highlight hex colors updated successfully!")
    return redirect('tracker:dashboard')


def reset_status_colors(request):
    """Resets status highlight hex colors back to system defaults"""
    StatusColorConfig.reset_to_defaults()
    messages.success(request, "Status highlight colors reset to default hex colors!")
    return redirect('tracker:dashboard')


def reset_demo_data(request):
    from django.core.management import call_command
    call_command('seed_data')
    messages.success(request, "Demo process sheet data restored successfully from Excel screenshot!")
    return redirect('tracker:dashboard')


def export_excel(request):
    """
    Exports the Process Sheet to an Excel (.xlsx) file matching the original screenshot style
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Process Dashboard"

    # Styling definitions
    header_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    green_fill = PatternFill(start_color="D1E7DD", end_color="D1E7DD", fill_type="solid")
    green_font = Font(name="Calibri", size=11, color="0F5132", bold=True)
    
    pink_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
    pink_font = Font(name="Calibri", size=11, color="842029", bold=True)
    
    gray_fill = PatternFill(start_color="E2E3E5", end_color="E2E3E5", fill_type="solid")
    gray_font = Font(name="Calibri", size=11, color="41464B", bold=True)
    
    thin_border = Border(
        left=Side(style='thin', color='DDDDDD'),
        right=Side(style='thin', color='DDDDDD'),
        top=Side(style='thin', color='DDDDDD'),
        bottom=Side(style='thin', color='DDDDDD')
    )

    headers = [
        "Client / Account Name",
        "Status",
        "LOT Progress",
        "Completed",
        "Pending",
        "Ready / Pipeline",
        "Process Notes / Remarks",
        "Target Date",
        "Days Diff",
        "History / Milestone"
    ]

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    items = ProcessItem.objects.all()
    for row_idx, item in enumerate(items, start=2):
        target_str = item.target_date.strftime("%d/%m/%Y") if item.target_date else ""
        days_diff_val = item.days_diff if item.days_diff is not None else ""

        ws.append([
            item.client_name,
            item.get_status_display(),
            item.formatted_lot or item.lot_progress,
            item.completed_count or 0,
            item.pending_count or 0,
            item.ready_count or 0,
            item.notes,
            target_str,
            days_diff_val,
            item.history_milestone
        ])

        # Cell styling
        # Client Name
        c1 = ws.cell(row=row_idx, column=1)
        if item.is_red_client:
            c1.font = Font(name="Calibri", size=11, color="DC3545", bold=True)
        
        # Status
        c2 = ws.cell(row=row_idx, column=2)
        c2.alignment = Alignment(horizontal="center")
        if item.status == 'working':
            c2.fill = green_fill
            c2.font = green_font
        elif item.status == 'no_data':
            c2.fill = pink_fill
            c2.font = pink_font
        elif item.status == 'finished':
            c2.fill = gray_fill
            c2.font = gray_font

        # LOT Progress
        c3 = ws.cell(row=row_idx, column=3)
        c3.alignment = Alignment(horizontal="center")
        if item.lot_progress.lower() == 'finished':
            c3.fill = pink_fill
            c3.font = pink_font

        # Counts
        for col in [4, 5, 6]:
            c = ws.cell(row=row_idx, column=col)
            c.alignment = Alignment(horizontal="center")
        
        # Pending count pink highlight if 0
        c5 = ws.cell(row=row_idx, column=5)
        if item.pending_count == 0:
            c5.fill = pink_fill

        # Notes
        c7 = ws.cell(row=row_idx, column=7)
        if item.notes_is_red:
            c7.font = Font(name="Calibri", size=11, color="DC3545")

        # Target date & Days diff
        c8 = ws.cell(row=row_idx, column=8)
        c8.alignment = Alignment(horizontal="center")
        
        c9 = ws.cell(row=row_idx, column=9)
        c9.alignment = Alignment(horizontal="center")
        if isinstance(days_diff_val, int) and days_diff_val > 0:
            c9.fill = pink_fill
            c9.font = pink_font

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_idx, column=col).border = thin_border

    # Adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Process_Dashboard_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


def import_excel(request):
    """
    Imports process data from uploaded Excel file (.xlsx)
    """
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            
            if len(rows) < 2:
                messages.error(request, "Excel sheet is empty or missing headers.")
                return redirect('tracker:dashboard')

            # Process data rows starting from row 2
            count = 0
            for r in rows[1:]:
                if not r or not any(r):
                    continue
                client_name = str(r[0]).strip() if r[0] is not None else ""
                if not client_name:
                    continue

                status_raw = str(r[1]).lower() if len(r) > 1 and r[1] is not None else "working"
                status = "working"
                if "no" in status_raw or "data" in status_raw:
                    status = "no_data"
                elif "finish" in status_raw:
                    status = "finished"

                lot_prog = str(r[2]).strip() if len(r) > 2 and r[2] is not None else ""
                completed = int(r[3]) if len(r) > 3 and str(r[3]).isdigit() else 0
                pending = int(r[4]) if len(r) > 4 and str(r[4]).isdigit() else 0
                ready = int(r[5]) if len(r) > 5 and str(r[5]).isdigit() else 0
                notes = str(r[6]).strip() if len(r) > 6 and r[6] is not None else ""
                
                target_date = None
                if len(r) > 7 and r[7]:
                    if isinstance(r[7], datetime):
                        target_date = r[7].date()
                    elif isinstance(r[7], date):
                        target_date = r[7]
                    else:
                        try:
                            target_date = datetime.strptime(str(r[7]).strip(), "%d/%m/%Y").date()
                        except ValueError:
                            try:
                                target_date = datetime.strptime(str(r[7]).strip(), "%Y-%m-%d").date()
                            except ValueError:
                                pass

                history = str(r[9]).strip() if len(r) > 9 and r[9] is not None else ""

                ProcessItem.objects.create(
                    client_name=client_name,
                    status=status,
                    lot_progress=lot_prog,
                    completed_count=completed,
                    pending_count=pending,
                    ready_count=ready,
                    notes=notes,
                    target_date=target_date,
                    history_milestone=history,
                )
                count += 1

            messages.success(request, f"Successfully imported {count} items from Excel!")
        except Exception as e:
            messages.error(request, f"Failed to import Excel: {str(e)}")

    return redirect('tracker:dashboard')
