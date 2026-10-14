from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_sameorigin
from django.conf import settings
from datetime import date, datetime
import os
import json
import csv
import io
import re
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

from .models import (
    ProcessItem, ProcessItemHistory, TableColumnConfig, StatusColorConfig,
    StatusOption, PartyCustomTab, PartyCustomTable, UserAccessProfile,
    PartyDataRecord
)
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


def get_user_access_profile(user):
    """Retrieve or create the access control profile for the authenticated user"""
    if not user or not user.is_authenticated:
        return None
    profile, _ = UserAccessProfile.objects.get_or_create(user=user)
    return profile


# ==========================================
# AUTHENTICATION & LOCK SYSTEM VIEWS
# ==========================================

def login_view(request):
    """User Login Page (Unique Password Authentication - No Username Required)"""
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        if not password:
            messages.error(request, 'Please enter your password.')
            return render(request, 'tracker/login.html', {'next': request.GET.get('next', '')})

        # Match user by unique password among active users
        matched_user = None
        for user in User.objects.filter(is_active=True).select_related('access_profile'):
            if user.check_password(password):
                matched_user = user
                break

        # First-Time / Default Admin Fallback:
        # If no active user matched and password is 'admin123', auto-initialize or sync default admin
        if matched_user is None and password == 'admin123':
            admin_user = User.objects.filter(username__in=['admin', 'administrator']).first()
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_user(
                    username='admin',
                    password='admin123',
                    is_staff=True,
                    is_superuser=True
                )
            else:
                admin_user.set_password('admin123')
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.is_active = True
                admin_user.save()

            profile = UserAccessProfile.get_or_create_for_user(admin_user)
            profile.role = 'admin'
            profile.is_admin = True
            profile.all_parties_access = True
            profile.all_columns_access = True
            profile.all_tabs_access = True
            profile.can_view_party_details = True
            profile.can_view_problem_badge = True
            profile.can_view_history = True
            profile.save()
            matched_user = admin_user

        if matched_user is not None:
            login(request, matched_user)
            UserAccessProfile.get_or_create_for_user(matched_user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'tracker:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid password. Access denied.')

    return render(request, 'tracker/login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    """Log out user and redirect to login"""
    logout(request)
    return redirect('tracker:login')


@csrf_exempt
def unlock_ajax(request):
    """AJAX unlock for screen lock overlay without full page reload"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    password = ''
    try:
        if request.body:
            data = json.loads(request.body.decode('utf-8'))
            password = data.get('password', '')
    except Exception:
        pass
    if not password:
        password = request.POST.get('password', '')

    password = password.strip()
    if not password:
        return JsonResponse({'success': False, 'error': 'Password is required'})

    # 1. If currently logged in user entered their own password
    if request.user.is_authenticated and request.user.check_password(password):
        profile = getattr(request.user, 'access_profile', None)
        disp_name = profile.display_name if profile and profile.display_name else request.user.username
        return JsonResponse({'success': True, 'username': disp_name})

    # 2. Or if any active user entered their unique password (e.g. switching users or session expired)
    for user in User.objects.filter(is_active=True).select_related('access_profile'):
        if user.check_password(password):
            login(request, user)
            profile = UserAccessProfile.get_or_create_for_user(user)
            disp_name = profile.display_name if profile and profile.display_name else user.username
    # 3. Default Admin fallback for first-time / recovery unlock
    if password == 'admin123':
        admin_user = User.objects.filter(username__in=['admin', 'administrator']).first()
        if not admin_user:
            admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            admin_user.set_password('admin123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.save()
            login(request, admin_user)
            profile = UserAccessProfile.get_or_create_for_user(admin_user)
            disp_name = profile.display_name if profile and profile.display_name else admin_user.username
            return JsonResponse({'success': True, 'username': disp_name, 'reloaded': True})

    return JsonResponse({'success': False, 'error': 'Incorrect password'})


# ==========================================
# ADMIN PANEL & USER MANAGEMENT VIEWS
# ==========================================

@login_required
def admin_panel(request):
    """Admin Panel for managing users, roles, and granular visibility rights"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or request.user.is_superuser):
        messages.error(request, "Permission denied. Only Administrators can access the Admin Panel.")
        return redirect('tracker:dashboard')

    users = User.objects.all().select_related('access_profile').order_by('-is_superuser', 'username')
    all_parties = ProcessItem.objects.all().order_by('order_index', 'client_name')
    all_columns = TableColumnConfig.objects.all().order_by('order_index')
    if not all_columns.exists():
        TableColumnConfig.reset_to_defaults()
        all_columns = TableColumnConfig.objects.all().order_by('order_index')

    raw_tab_titles = list(PartyCustomTab.objects.values_list('title', flat=True).distinct())
    all_tab_titles = sorted(list({t.strip() for t in raw_tab_titles if t and t.strip()}))

    context = {
        'users': users,
        'all_parties': all_parties,
        'all_columns': all_columns,
        'all_tab_titles': all_tab_titles,
        'user_profile': profile,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'admin_count': sum(1 for u in users if getattr(u, 'access_profile', None) and u.access_profile.is_admin or u.is_superuser),
        'total_parties': all_parties.count(),
    }
    return render(request, 'tracker/admin_panel.html', context)


@login_required
@csrf_exempt
def admin_user_save(request):
    """Create or update a user and their access profile from Admin Panel"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied. Admin access required.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    data = {}
    if request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            pass
    if not data:
        data = request.POST

    try:
        user_id = data.get('user_id')
        username = data.get('username', '').strip()
        display_name = data.get('display_name', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'editor')

        # Permissions
        all_parties_access = bool(data.get('all_parties_access', True))
        allowed_party_ids = data.get('allowed_parties', [])
        all_columns_access = bool(data.get('all_columns_access', True))
        allowed_columns = data.get('allowed_columns', [])
        can_view_party_details = bool(data.get('can_view_party_details', True))
        all_tabs_access = bool(data.get('all_tabs_access', True))
        allowed_tab_titles = data.get('allowed_tab_titles', [])

        can_view_history = bool(data.get('can_view_history', True))
        can_view_problem_badge = bool(data.get('can_view_problem_badge', True))
        can_edit_status = bool(data.get('can_edit_status', True))
        can_edit_lot = bool(data.get('can_edit_lot', True))
        can_edit_target_date = bool(data.get('can_edit_target_date', True))
        can_edit_notes = bool(data.get('can_edit_notes', True))
        can_add_party = bool(data.get('can_add_party', True))
        can_delete_party = bool(data.get('can_delete_party', False))
        can_hide_party = bool(data.get('can_hide_party', True))
        can_edit_custom_tabs = bool(data.get('can_edit_custom_tabs', True))
        can_export_excel = bool(data.get('can_export_excel', True))
        can_import_excel = bool(data.get('can_import_excel', False))
        can_view_party_data = bool(data.get('can_view_party_data', False))
        can_clear_party_data = bool(data.get('can_clear_party_data', False))
        can_access_main_app = bool(data.get('can_access_main_app', True))
        can_manage_settings = bool(data.get('can_manage_settings', False))
        is_admin = bool(data.get('is_admin', False)) or (role == 'admin')

        # Enforce preset defaults if admin / viewer
        if role == 'admin':
            is_admin = True
            all_parties_access = True
            all_columns_access = True
            all_tabs_access = True
            can_view_history = True
            can_delete_party = True
            can_import_excel = True
            can_view_party_data = True
            can_clear_party_data = True
            can_access_main_app = True
            can_manage_settings = True
        elif role == 'viewer':
            is_admin = False
            can_edit_status = False
            can_edit_lot = False
            can_edit_target_date = False
            can_edit_notes = False
            can_add_party = False
            can_delete_party = False
            can_hide_party = False
            can_edit_custom_tabs = False
            can_import_excel = False
            can_view_party_data = False
            can_clear_party_data = False
            can_access_main_app = False
            can_manage_settings = False

        # Auto-derive or fallback username if empty
        if not username:
            if display_name:
                import re
                clean_base = re.sub(r'[^a-zA-Z0-9_]', '', display_name.lower()) or 'user'
            else:
                clean_base = 'user'
            candidate = clean_base
            counter = 1
            while User.objects.filter(username=candidate).exclude(pk=user_id if user_id else 0).exists():
                candidate = f"{clean_base}_{counter}"
                counter += 1
            username = candidate

        # Enforce Password Uniqueness across ALL users so password-only login works reliably
        if password:
            other_users = User.objects.exclude(pk=user_id) if user_id else User.objects.all()
            for other_u in other_users:
                if other_u.check_password(password):
                    other_name = getattr(getattr(other_u, 'access_profile', None), 'display_name', '') or other_u.username
                    return JsonResponse({
                        'success': False,
                        'error': f'Yeh password already "{other_name}" ke liye set hai. Password-only login ke liye har person ka password unique hona zaroori hai.'
                    }, status=400)

        if user_id:
            # Update existing user
            user = get_object_or_404(User, pk=user_id)
            if username and username != user.username:
                if User.objects.filter(username=username).exclude(pk=user_id).exists():
                    return JsonResponse({'success': False, 'error': f'Username "{username}" is already taken.'}, status=400)
                user.username = username
            if password:
                user.set_password(password)
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.save()
            action = 'updated'
        else:
            # Create new user
            if not password:
                return JsonResponse({'success': False, 'error': 'Password is required for new users.'}, status=400)
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': f'Username "{username}" already exists.'}, status=400)

            user = User.objects.create_user(
                username=username,
                password=password,
                is_staff=is_admin,
                is_superuser=is_admin
            )
            action = 'created'

        user_prof = UserAccessProfile.get_or_create_for_user(user)
        user_prof.display_name = display_name or username
        user_prof.role = role
        user_prof.is_admin = is_admin
        user_prof.all_parties_access = all_parties_access
        user_prof.all_columns_access = all_columns_access
        user_prof.allowed_columns = allowed_columns if isinstance(allowed_columns, list) else []
        user_prof.can_view_party_details = can_view_party_details
        user_prof.all_tabs_access = all_tabs_access
        user_prof.allowed_tab_titles = [str(t).strip() for t in allowed_tab_titles if str(t).strip()] if isinstance(allowed_tab_titles, list) else []

        user_prof.can_view_history = can_view_history
        user_prof.can_view_problem_badge = can_view_problem_badge
        user_prof.can_edit_status = can_edit_status
        user_prof.can_edit_lot = can_edit_lot
        user_prof.can_edit_target_date = can_edit_target_date
        user_prof.can_edit_notes = can_edit_notes
        user_prof.can_add_party = can_add_party
        user_prof.can_delete_party = can_delete_party
        user_prof.can_hide_party = can_hide_party
        user_prof.can_edit_custom_tabs = can_edit_custom_tabs
        user_prof.can_export_excel = can_export_excel
        user_prof.can_import_excel = can_import_excel
        user_prof.can_view_party_data = can_view_party_data
        user_prof.can_clear_party_data = can_clear_party_data
        user_prof.can_access_main_app = can_access_main_app
        user_prof.can_manage_settings = can_manage_settings
        user_prof.save()

        # Set allowed parties
        if not all_parties_access and isinstance(allowed_party_ids, list):
            valid_items = ProcessItem.objects.filter(id__in=allowed_party_ids)
            user_prof.allowed_parties.set(valid_items)
        else:
            user_prof.allowed_parties.clear()

        return JsonResponse({
            'success': True,
            'action': action,
            'user': {
                'id': user.id,
                'username': user.username,
                'display_name': user_prof.display_name,
                'role': user_prof.role,
                'role_display': user_prof.get_role_display(),
                'is_admin': user_prof.is_admin,
                'is_active': user.is_active
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def admin_user_get_json(request, user_id):
    """Fetch user configuration for editing modal"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    user = get_object_or_404(User, pk=user_id)
    u_prof = UserAccessProfile.get_or_create_for_user(user)

    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'display_name': u_prof.display_name,
            'role': u_prof.role,
            'is_admin': u_prof.is_admin,
            'is_active': user.is_active,
            'all_parties_access': u_prof.all_parties_access,
            'allowed_parties': list(u_prof.allowed_parties.values_list('id', flat=True)),
            'all_columns_access': u_prof.all_columns_access,
            'allowed_columns': u_prof.allowed_columns or [],
            'can_view_party_details': u_prof.can_view_party_details,
            'all_tabs_access': u_prof.all_tabs_access,
            'allowed_tab_titles': u_prof.allowed_tab_titles or [],
            'can_view_history': u_prof.can_view_history,
            'can_view_problem_badge': u_prof.can_view_problem_badge,
            'can_edit_status': u_prof.can_edit_status,
            'can_edit_lot': u_prof.can_edit_lot,
            'can_edit_target_date': u_prof.can_edit_target_date,
            'can_edit_notes': u_prof.can_edit_notes,
            'can_add_party': u_prof.can_add_party,
            'can_delete_party': u_prof.can_delete_party,
            'can_hide_party': u_prof.can_hide_party,
            'can_edit_custom_tabs': u_prof.can_edit_custom_tabs,
            'can_export_excel': u_prof.can_export_excel,
            'can_import_excel': u_prof.can_import_excel,
            'can_view_party_data': u_prof.can_view_party_data,
            'can_clear_party_data': u_prof.can_clear_party_data,
            'can_access_main_app': u_prof.can_access_main_app,
            'can_manage_settings': u_prof.can_manage_settings,
        }
    })


@login_required
@csrf_exempt
def admin_user_delete(request, user_id):
    """Delete a user account from Admin Panel"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    if request.user.id == user_id:
        return JsonResponse({'success': False, 'error': 'You cannot delete your own logged-in admin account!'}, status=400)

    user = get_object_or_404(User, pk=user_id)
    username = user.username
    user.delete()
    return JsonResponse({'success': True, 'message': f'User "{username}" deleted successfully'})


@login_required
@csrf_exempt
def admin_user_toggle_status(request, user_id):
    """Toggle user active / inactive status"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

    if request.user.id == user_id:
        return JsonResponse({'success': False, 'error': 'You cannot deactivate your own account!'}, status=400)

    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save()
    return JsonResponse({'success': True, 'is_active': user.is_active})


# ==========================================
# DASHBOARD VIEW
# ==========================================

@login_required
def dashboard(request):
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    
    # Query parameters
    status_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    
    # Filter items based on user party permissions
    base_qs = ProcessItem.objects.all()
    if not profile.all_parties_access and not (profile.is_admin or request.user.is_superuser):
        base_qs = base_qs.filter(id__in=profile.allowed_parties.values_list('id', flat=True))

    items = base_qs

    # Apply Search
    if search_query:
        items = items.filter(
            Q(client_name__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(lot_progress__icontains=search_query)
        )

    all_statuses = StatusOption.get_all_statuses()
    status_keys = {s.key for s in all_statuses}

    # Filter logic
    if status_filter != 'all':
        if status_filter == 'overdue':
            items = [item for item in items if item.is_overdue]
        elif status_filter in ('finished', 'no_data'):
            items = [item for item in items if item.dynamic_status in ('finished', 'no_data')]
        elif status_filter in status_keys:
            items = [item for item in items if item.dynamic_status == status_filter]

    # Metrics calculation (base on visible items of permitted parties)
    all_items = list(base_qs)
    hidden_count = sum(1 for item in all_items if item.is_hidden)
    visible_items = [item for item in all_items if not item.is_hidden]
    total_clients = len(visible_items)
    working_count = sum(1 for item in visible_items if item.dynamic_status == 'working')
    finished_no_data_count = sum(1 for item in visible_items if item.dynamic_status in ('finished', 'no_data'))
    no_data_count = finished_no_data_count
    finished_count = finished_no_data_count
    hold_count = sum(1 for item in visible_items if item.dynamic_status == 'hold')
    pending_count = sum(1 for item in visible_items if item.dynamic_status == 'pending')
    
    overdue_count = sum(1 for item in visible_items if item.is_overdue)
    total_pending = sum((item.pending_count or 0) for item in visible_items)
    total_ready = sum((item.ready_count or 0) for item in visible_items)

    # Status counts map for all statuses (visible items)
    status_counts = {}
    for s in all_statuses:
        status_counts[s.key] = sum(1 for item in visible_items if item.dynamic_status == s.key)

    # Header Column Configuration
    columns_map = TableColumnConfig.get_columns_map()
    all_columns = TableColumnConfig.objects.all().order_by('order_index', 'id')
    ordered_columns = TableColumnConfig.objects.filter(is_visible=True).order_by('order_index', 'id')

    # Filter columns based on user column visibility permissions
    if not profile.all_columns_access and not (profile.is_admin or request.user.is_superuser) and profile.allowed_columns:
        ordered_columns = [
            c for c in ordered_columns
            if c.key in profile.allowed_columns or c.key in ['col_counter', 'client_name', 'actions']
        ]

    # Status color & badge styling map
    status_colors = {}
    for s in all_statuses:
        status_colors[s.key] = {
            'key': s.key,
            'label': s.label,
            'badge_bg': s.badge_bg,
            'badge_color': s.badge_color,
            'hex_color': s.row_bg,
            'border_color': s.row_border,
            'is_enabled': s.is_row_highlight,
            'order_index': s.order_index,
            'is_system': s.is_system,
        }
    overdue_cfg = StatusColorConfig.objects.filter(status_key='overdue').first()
    if overdue_cfg:
        status_colors['overdue'] = {
            'key': 'overdue',
            'label': overdue_cfg.label,
            'badge_bg': '#f8d7da',
            'badge_color': '#842029',
            'hex_color': overdue_cfg.hex_color,
            'border_color': overdue_cfg.border_color,
            'is_enabled': overdue_cfg.is_enabled,
        }

    context = {
        'items': items,
        'today': today,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_clients': total_clients,
        'hidden_count': hidden_count,
        'visible_count': total_clients,
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
        'all_statuses': all_statuses,
        'status_counts': status_counts,
        # User Access Permissions
        'user_profile': profile,
        'can_view_party_details': profile.can_view_party_details or profile.is_admin or request.user.is_superuser,
        'can_edit_custom_tabs': profile.can_edit_custom_tabs or profile.is_admin or request.user.is_superuser,
        'can_edit_status': profile.can_edit_status or profile.is_admin or request.user.is_superuser,
        'can_edit_lot': profile.can_edit_lot or profile.is_admin or request.user.is_superuser,
        'can_edit_date': profile.can_edit_target_date or profile.is_admin or request.user.is_superuser,
        'can_edit_notes': profile.can_edit_notes or profile.is_admin or request.user.is_superuser,
        'can_add_party': profile.can_add_party or profile.is_admin or request.user.is_superuser,
        'can_delete_party': profile.can_delete_party or profile.is_admin or request.user.is_superuser,
        'can_hide_party': profile.can_hide_party or profile.is_admin or request.user.is_superuser,
        'can_export_excel': profile.can_export_excel or profile.is_admin or request.user.is_superuser,
        'can_import_excel': profile.can_import_excel or profile.is_admin or request.user.is_superuser,
        'can_manage_settings': profile.can_manage_settings or profile.is_admin or request.user.is_superuser,
        'can_view_history': profile.can_view_history or profile.is_admin or request.user.is_superuser,
        'can_view_problem_badge': profile.can_view_problem_badge or profile.is_admin or request.user.is_superuser,
        'can_view_party_data': profile.can_view_party_data or profile.is_admin or request.user.is_superuser,
        'can_access_main_app': profile.can_access_main_app or profile.is_admin or request.user.is_superuser,
        'is_admin': profile.is_admin or request.user.is_superuser,
    }
    return render(request, 'tracker/dashboard.html', context)



@login_required
def item_create(request):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_add_party:
        messages.error(request, "Permission denied: You do not have permission to add new clients.")
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        form = ProcessItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            if item.status:
                item.is_status_manual = True
            item.save()
            
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

            # Automatically sync to Main App Company Policy
            try:
                from main_app import db_manager
                db_manager.sync_client_to_company_policy(item.client_name)
            except Exception as e:
                print(f"Error syncing client '{item.client_name}' to Main App: {e}")

            messages.success(request, f"Added client '{item.client_name}' successfully!")
        else:
            messages.error(request, "Error adding item. Please check the form fields.")
    return redirect('tracker:dashboard')


@login_required
def item_update(request, pk):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied: Access to this client is restricted.")
        return redirect('tracker:dashboard')

    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        old_target_date = item.target_date
        old_status = item.status
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
            updated_item = form.save(commit=False)
            if updated_item.target_date != old_target_date:
                # Target date changed: clear manual status lock so dynamic status recalculates!
                updated_item.is_status_manual = False
            elif updated_item.status != old_status:
                # User selected a new status: keep manual status lock active!
                updated_item.is_status_manual = True
            updated_item.save()

            # Compare and build diff
            changes = []
            status_map = {s.key: s.label for s in StatusOption.get_all_statuses()}
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
                    old_disp = status_map.get(old_values[field], old_values[field]) if field == 'status' else old_values[field]
                    new_disp = status_map.get(new_val, new_val) if field == 'status' else new_val
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

            # If client_name was updated, sync to Main App
            if old_values.get('client_name') and old_values['client_name'].strip().lower() != updated_item.client_name.strip().lower():
                try:
                    from main_app import db_manager
                    conn = db_manager.get_db_connection()
                    cur = conn.cursor()
                    cur.execute("UPDATE business_policies SET company_name=? WHERE LOWER(company_name)=LOWER(?)", (updated_item.client_name.strip(), old_values['client_name'].strip()))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Error syncing renamed client to Main App: {e}")

            messages.success(request, f"Updated '{item.client_name}' successfully!")
        else:
            messages.error(request, "Error updating item. Please check the values.")
    return redirect('tracker:dashboard')


@login_required
def item_get_json(request, pk):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    item = get_object_or_404(ProcessItem, pk=pk)
    data = {
        'id': item.id,
        'client_name': item.client_name,
        'is_red_client': item.is_red_client,
        'status': item.status,
        'is_status_manual': item.is_status_manual,
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


@login_required
def item_quick_status(request, pk):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Access denied to this client'}, status=403)
    if not profile.can_edit_status:
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit status'}, status=403)

    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method == 'POST':
        import json
        try:
            body_data = json.loads(request.body)
            new_status = body_data.get('status')
        except Exception:
            new_status = request.POST.get('status')

        valid_statuses = {s.key: s.label for s in StatusOption.get_all_statuses()}
        if new_status in valid_statuses:
            old_status = item.status
            item.status = new_status
            item.is_status_manual = True
            item.row_highlight_color = ''
            item.save()

            # Record in history
            old_label = valid_statuses.get(old_status, old_status)
            new_label = valid_statuses.get(new_status, new_status)
            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=f"Status set to '{new_label}' (Manual selection)",
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
                'is_status_manual': item.is_status_manual,
                'status_display': item.dynamic_status_display,
                'dynamic_status': item.dynamic_status,
                'dynamic_status_display': item.dynamic_status_display,
                'is_overdue': item.is_overdue,
                'days_diff': item.days_diff,
                'client_name': item.client_name,
            })
        return JsonResponse({'success': False, 'error': 'Invalid status choice'}, status=400)
    return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)


@login_required
def item_inline_update(request, pk):
    """
    Inline double-click edit for LOT / ITEM and TARGET DATE.
    Automatically logs change in ProcessItemHistory and returns updated values.
    """
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Access denied to this client'}, status=403)

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
            if not profile.can_edit_lot:
                return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit LOT'}, status=403)
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
            if not profile.can_edit_target_date:
                return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit Target Date'}, status=403)
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
            item.is_status_manual = False  # Reset manual lock so status changes dynamically!
            item.save()

            new_date_display = item.target_date.strftime('%d/%m/%Y') if item.target_date else '-'
            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=f"Target Date updated from '{old_date_str}' to '{new_date_display}' (Dynamic status recalculated)",
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
                'is_status_manual': item.is_status_manual,
                'dynamic_status': item.dynamic_status,
                'dynamic_status_display': item.dynamic_status_display,
            })

        elif field == 'notes':
            if not profile.can_edit_notes:
                return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit Notes'}, status=403)
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

            return JsonResponse({
                'success': True,
                'field': 'notes',
                'raw_value': item.notes,
                'notes_is_red': item.notes_is_red,
            })

        elif field == 'status':
            if not profile.can_edit_status:
                return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit Status'}, status=403)
            status_map = {s.key: s.label for s in StatusOption.get_all_statuses()}
            new_status = str(value or '').strip()
            if new_status not in status_map:
                return JsonResponse({'success': False, 'error': f'Invalid status choice: {new_status}'}, status=400)

            old_status = item.status
            item.status = new_status
            item.is_status_manual = True  # User explicitly selected status: lock it until target date changes!
            item.row_highlight_color = ''
            item.save()

            old_label = status_map.get(old_status, old_status)
            new_label = status_map.get(new_status, new_status)
            ProcessItemHistory.objects.create(
                item=item,
                action_type='updated',
                summary=f"Status set to '{new_label}' (Manual selection)",
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
                'is_status_manual': item.is_status_manual,
                'status_display': item.dynamic_status_display,
                'dynamic_status': item.dynamic_status,
                'dynamic_status_display': item.dynamic_status_display,
                'row_highlight_color': item.row_highlight_color or '',
            })

        elif field == 'is_priority':
            if not (profile.can_edit_status or profile.can_manage_settings):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
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
            if not profile.can_edit_notes:
                return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit Notes / Milestones'}, status=403)
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


@login_required
def item_toggle_priority(request, pk):
    """
    Toggle High Priority on a ProcessItem (triggered via row long-press / context menu).
    """
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Access denied to this client'}, status=403)
    if not (profile.can_edit_status or profile.can_manage_settings):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

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


@login_required
def item_history_json(request, pk):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Access denied to this client'}, status=403)
    if not (profile.can_view_history or profile.is_admin or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied: Aapko history dekhne ki permission nahi hai.'}, status=403)

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


@login_required
def history_entry_delete(request, pk):
    """Delete a specific history revision entry"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        entry = get_object_or_404(ProcessItemHistory, pk=pk)
        item_id = entry.item_id
        entry.delete()
        remaining_count = ProcessItemHistory.objects.filter(item_id=item_id).count()
        return JsonResponse({
            'success': True,
            'message': 'History entry removed successfully.',
            'remaining_count': remaining_count
        })
    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)


@login_required
def item_history_clear(request, pk):
    """Clear all edit history logs for a specific client item"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        item = get_object_or_404(ProcessItem, pk=pk)
        deleted_count, _ = item.history_logs.all().delete()
        return JsonResponse({
            'success': True,
            'message': f'Cleared {deleted_count} history records for {item.client_name}.',
            'remaining_count': 0
        })
    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)


@login_required
def item_delete(request, pk):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_delete_party or not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied: You do not have permission to delete clients.")
        return redirect('tracker:dashboard')

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


@login_required
def item_toggle_hide(request, pk):
    """Toggle hidden status of a single process item"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_hide_party or not profile.is_party_allowed(pk):
        return JsonResponse({'error': 'Permission denied: Cannot hide clients'}, status=403)

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


@login_required
def items_bulk_delete(request):
    """Bulk delete multiple clients protected by password 8264"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_delete_party:
        messages.error(request, "Permission denied: You do not have permission to delete clients.")
        return redirect('tracker:dashboard')

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
            # Also filter by allowed parties if not admin/all_parties
            if not profile.is_admin and not profile.all_parties_access:
                ids = [i for i in ids if profile.is_party_allowed(i)]
            deleted_count, _ = ProcessItem.objects.filter(id__in=ids).delete()
            messages.success(request, f"Successfully deleted {deleted_count} client(s).")
        else:
            messages.warning(request, "No clients selected for deletion.")
            
    return redirect('tracker:dashboard')


@login_required
def items_bulk_hide(request):
    """Bulk hide or unhide multiple clients"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_hide_party:
        messages.error(request, "Permission denied: You do not have permission to hide clients.")
        return redirect('tracker:dashboard')

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
            if not profile.is_admin and not profile.all_parties_access:
                ids = [i for i in ids if profile.is_party_allowed(i)]
            updated_count = ProcessItem.objects.filter(id__in=ids).update(is_hidden=new_val)
            action_word = "hidden" if new_val else "restored"
            messages.success(request, f"Successfully {action_word} {updated_count} client(s).")
        else:
            messages.warning(request, "No clients selected.")
            
    return redirect('tracker:dashboard')


@login_required
def save_column_config(request):
    """Saves updated header labels, visibility toggles, ordering, and new custom columns"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        messages.error(request, "Permission denied: You cannot configure columns.")
        return redirect('tracker:dashboard')

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


@login_required
def delete_column_config(request, pk):
    """Deletes a custom column header"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        col = get_object_or_404(TableColumnConfig, pk=pk)
        if col.is_custom:
            name = col.label
            col.delete()
            messages.success(request, f"Removed custom header '{name}'.")
        else:
            messages.error(request, "Core system columns cannot be removed.")
    return redirect('tracker:dashboard')


@login_required
def reset_column_config(request):
    """Resets all header columns to original default labels"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    TableColumnConfig.reset_to_defaults()
    messages.success(request, "Header columns reset to default successfully!")
    return redirect('tracker:dashboard')


@login_required
def save_status_colors(request):
    """Saves customized status row highlight hex colors"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

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


@login_required
def reset_status_colors(request):
    """Resets status highlight hex colors back to system defaults"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    StatusColorConfig.reset_to_defaults()
    messages.success(request, "Status highlight colors reset to default hex colors!")
    return redirect('tracker:dashboard')


def status_list_api(request):
    """Returns JSON array of all status options for dynamic frontend consumption."""
    statuses = StatusOption.get_all_statuses()
    data = []
    for s in statuses:
        data.append({
            'key': s.key,
            'label': s.label,
            'badge_bg': s.badge_bg,
            'badge_color': s.badge_color,
            'row_bg': s.row_bg,
            'row_border': s.row_border,
            'is_row_highlight': s.is_row_highlight,
            'order_index': s.order_index,
            'is_system': s.is_system,
        })
    return JsonResponse({'success': True, 'statuses': data})


@login_required
def status_save(request):
    """
    Creates or updates a StatusOption.
    Accepts both JSON (AJAX) and standard form POST.
    """
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Permission denied: Cannot edit statuses'}, status=403)
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        import json, re
        data = {}
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except Exception:
                data = {}
        else:
            data = request.POST

        key = str(data.get('key') or '').strip().lower()
        label = str(data.get('label') or '').strip()
        badge_bg = str(data.get('badge_bg') or '#e2e3e5').strip()
        badge_color = str(data.get('badge_color') or '#333333').strip()
        row_bg = str(data.get('row_bg') or '#ffffff').strip()
        row_border = str(data.get('row_border') or '#84cc16').strip()
        is_row_highlight = bool(data.get('is_row_highlight') in [True, 'true', '1', 'on'])
        order_index_raw = data.get('order_index')
        try:
            order_index = int(order_index_raw) if order_index_raw is not None and str(order_index_raw).strip() != '' else (StatusOption.objects.count() + 1)
        except (ValueError, TypeError):
            order_index = StatusOption.objects.count() + 1

        if not label:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Status name/label is required.'}, status=400)
            messages.error(request, "Status name/label is required.")
            return redirect('tracker:dashboard')

        if not key:
            # Auto-generate slug key from label
            base_key = re.sub(r'[^a-zA-Z0-9_]', '_', label.lower()).strip('_')
            if not base_key:
                base_key = 'custom_status'
            key = base_key
            counter = 1
            while StatusOption.objects.filter(key=key).exists():
                key = f"{base_key}_{counter}"
                counter += 1

        obj, created = StatusOption.objects.update_or_create(
            key=key,
            defaults={
                'label': label,
                'badge_bg': badge_bg,
                'badge_color': badge_color,
                'row_bg': row_bg,
                'row_border': row_border,
                'is_row_highlight': is_row_highlight,
                'order_index': order_index,
            }
        )

        # Sync with StatusColorConfig for color highlights
        StatusColorConfig.objects.update_or_create(
            status_key=key,
            defaults={
                'label': label,
                'hex_color': row_bg,
                'border_color': row_border,
                'is_enabled': is_row_highlight,
            }
        )

        msg = f"Status '{label}' created successfully!" if created else f"Status '{label}' updated successfully!"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'created': created,
                'message': msg,
                'status': {
                    'key': obj.key,
                    'label': obj.label,
                    'badge_bg': obj.badge_bg,
                    'badge_color': obj.badge_color,
                    'row_bg': obj.row_bg,
                    'row_border': obj.row_border,
                    'is_row_highlight': obj.is_row_highlight,
                    'order_index': obj.order_index,
                    'is_system': obj.is_system,
                }
            })
        messages.success(request, msg)
        return redirect('tracker:dashboard')
    return redirect('tracker:dashboard')


@login_required
def status_delete(request, key):
    """
    Deletes a StatusOption. Reassigns existing items with this status to 'working'.
    """
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        if StatusOption.objects.count() <= 1:
            err = "Cannot delete the only remaining status."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': err}, status=400)
            messages.error(request, err)
            return redirect('tracker:dashboard')

        opt = StatusOption.objects.filter(key=key).first()
        if not opt:
            err = "Status not found."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': err}, status=404)
            messages.error(request, err)
            return redirect('tracker:dashboard')

        # Reassign items with deleted status to 'working' or first available status
        fallback = StatusOption.objects.exclude(key=key).first()
        fallback_key = fallback.key if fallback else 'working'
        ProcessItem.objects.filter(status=key).update(status=fallback_key)

        label = opt.label
        opt.delete()
        StatusColorConfig.objects.filter(status_key=key).delete()

        msg = f"Status '{label}' removed successfully! Associated clients updated to '{fallback.label if fallback else 'Working'}'."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg, 'fallback_key': fallback_key})
        messages.success(request, msg)
        return redirect('tracker:dashboard')
    return redirect('tracker:dashboard')


@login_required
def status_reset_defaults(request):
    """Resets all statuses back to system defaults"""
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_manage_settings:
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    if request.method == 'POST':
        StatusOption.reset_to_defaults()
        messages.success(request, "Statuses restored to system defaults!")
    return redirect('tracker:dashboard')


@login_required
def reset_demo_data(request):
    profile = get_user_access_profile(request.user)
    if not profile or not profile.is_admin:
        messages.error(request, "Permission denied: Only Admin can reset demo data.")
        return redirect('tracker:dashboard')

    from django.core.management import call_command
    call_command('seed_data')
    messages.success(request, "Demo process sheet data restored successfully from Excel screenshot!")
    return redirect('tracker:dashboard')


@login_required
def export_excel(request):
    """
    Exports the Process Sheet to an Excel (.xlsx) file matching the original screenshot style.
    Supports ?scope=visible (default), ?scope=hidden, or ?scope=all.
    """
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_export_excel:
        messages.error(request, "Permission denied: You do not have permission to export.")
        return redirect('tracker:dashboard')

    scope = request.GET.get('scope', 'visible').lower()
    if scope == 'hidden':
        items = ProcessItem.objects.filter(is_hidden=True)
        file_suffix = "Hidden"
        sheet_title = "Hidden Clients"
    elif scope == 'all':
        items = ProcessItem.objects.all()
        file_suffix = "All"
        sheet_title = "All Clients"
    else:
        items = ProcessItem.objects.filter(is_hidden=False)
        file_suffix = "Visible"
        sheet_title = "Visible Clients"

    if not profile.is_admin and not profile.all_parties_access:
        items = items.filter(id__in=profile.allowed_parties)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title

    # Styling definitions
    header_fill = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    green_fill = PatternFill(start_color="D1E7DD", end_color="D1E7DD", fill_type="solid")
    green_font = Font(name="Calibri", size=11, color="0F5132", bold=True)
    
    pink_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
    pink_font = Font(name="Calibri", size=11, color="842029", bold=True)
    red_font = Font(name="Calibri", size=11, color="DC3545", bold=True)
    
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
    if scope == 'all':
        headers.append("Hidden")

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_idx, item in enumerate(items, start=2):
        target_str = item.target_date.strftime("%d/%m/%Y") if item.target_date else ""
        days_diff_val = item.days_diff if item.days_diff is not None else ""

        # In exported excel if status is finished, display 'No data' instead of 'Finished'
        current_status = item.dynamic_status
        if current_status == 'finished' or item.status == 'finished':
            status_text = "No data"
            effective_status = "no_data"
        else:
            status_text = item.dynamic_status_display
            effective_status = current_status

        row_data = [
            item.client_name,
            status_text,
            item.formatted_lot or item.lot_progress,
            item.completed_count or 0,
            item.pending_count or 0,
            item.ready_count or 0,
            item.notes,
            target_str,
            days_diff_val,
            item.history_milestone
        ]
        if scope == 'all':
            row_data.append("Yes" if item.is_hidden else "No")

        ws.append(row_data)

        # Cell styling
        # Client Name
        c1 = ws.cell(row=row_idx, column=1)
        if item.is_red_client or current_status in ('finished', 'no_data') or item.status in ('finished', 'no_data'):
            c1.font = Font(name="Calibri", size=11, color="DC3545", bold=True)
        
        # Status
        c2 = ws.cell(row=row_idx, column=2)
        c2.alignment = Alignment(horizontal="center")
        if effective_status == 'working':
            c2.fill = green_fill
            c2.font = green_font
        elif effective_status == 'no_data':
            c2.fill = pink_fill
            c2.font = red_font
        elif effective_status == 'pending':
            c2.fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
            c2.font = Font(name="Calibri", size=11, color="664D03", bold=True)
        elif effective_status == 'hold':
            c2.fill = PatternFill(start_color="F7FEE7", end_color="F7FEE7", fill_type="solid")
            c2.font = Font(name="Calibri", size=11, color="3F6212", bold=True)
        else:
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

        # Scope 'all' Hidden column style
        if scope == 'all':
            c_hidden = ws.cell(row=row_idx, column=len(headers))
            c_hidden.alignment = Alignment(horizontal="center")
            if item.is_hidden:
                c_hidden.fill = gray_fill
                c_hidden.font = gray_font

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
    filename = f"Process_Dashboard_{file_suffix}_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
def import_excel(request):
    """
    Imports process data from uploaded Excel file (.xlsx)
    """
    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_import_excel:
        messages.error(request, "Permission denied: You do not have permission to import.")
        return redirect('tracker:dashboard')

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


@login_required
def database_export_bundle(request):
    """
    Exports a complete zip bundle containing:
    1. db.sqlite3 (Django Process Dashboard database)
    2. main_app/app_database.db (Main App engine database)
    3. backup_manifest.json (Metadata, timestamp, record counts)
    """
    profile = get_user_access_profile(request.user)
    if not (profile.is_admin or request.user.is_superuser or profile.can_manage_settings):
        messages.error(request, "Permission denied: Admin access required to export full database bundle.")
        return redirect('tracker:dashboard')

    import io, zipfile, json, os
    from datetime import datetime
    from django.conf import settings
    from django.http import HttpResponse
    from django.db import connections

    # Close DB connections to flush writes
    try:
        connections.close_all()
    except Exception:
        pass

    buf = io.BytesIO()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'exported_by': request.user.username,
        'client_count': ProcessItem.objects.count(),
        'files': []
    }

    try:
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Django DB
            db_sqlite = os.path.join(settings.BASE_DIR, 'db.sqlite3')
            if os.path.exists(db_sqlite):
                zf.write(db_sqlite, 'db.sqlite3')
                manifest['files'].append({'name': 'db.sqlite3', 'size': os.path.getsize(db_sqlite)})

            # 2. Main App DB
            main_db = os.path.join(settings.BASE_DIR, 'main_app', 'app_database.db')
            if os.path.exists(main_db):
                zf.write(main_db, 'main_app/app_database.db')
                manifest['files'].append({'name': 'main_app/app_database.db', 'size': os.path.getsize(main_db)})

            # 3. Manifest
            zf.writestr('backup_manifest.json', json.dumps(manifest, indent=2))

        buf.seek(0)
        filename = f"process_dashboard_complete_db_{timestamp}.zip"
        response = HttpResponse(buf.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        messages.error(request, f"Failed to export database bundle: {e}")
        return redirect('tracker:dashboard')


@login_required
def database_import_bundle(request):
    """
    Imports and restores database from an uploaded .zip bundle, .sqlite3 file, or .db file.
    Creates an automatic safety backup of existing databases before applying.
    """
    profile = get_user_access_profile(request.user)
    if not (profile.is_admin or request.user.is_superuser or profile.can_manage_settings):
        messages.error(request, "Permission denied: Admin access required to import database.")
        return redirect('tracker:dashboard')

    if request.method != 'POST' or not request.FILES.get('db_file'):
        messages.error(request, "Please choose a database bundle (.zip) or database (.db / .sqlite3) file to upload.")
        return redirect('tracker:dashboard')

    uploaded_file = request.FILES['db_file']
    filename = uploaded_file.name.lower()

    import os, io, zipfile, shutil
    from datetime import datetime
    from django.conf import settings
    from django.db import connections

    # Safety snapshot of current databases
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    db_sqlite = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    main_db = os.path.join(settings.BASE_DIR, 'main_app', 'app_database.db')

    try:
        connections.close_all()
    except Exception:
        pass

    if os.path.exists(db_sqlite):
        try:
            shutil.copy2(db_sqlite, os.path.join(backup_dir, f'pre_import_db_{timestamp}.sqlite3'))
        except Exception:
            pass
    if os.path.exists(main_db):
        try:
            shutil.copy2(main_db, os.path.join(backup_dir, f'pre_import_app_database_{timestamp}.db'))
        except Exception:
            pass

    restored_items = []

    try:
        if filename.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file, 'r') as zf:
                for member in zf.namelist():
                    member_clean = member.lower().replace('\\', '/')
                    if member_clean.endswith('db.sqlite3'):
                        extracted_bytes = zf.read(member)
                        connections.close_all()
                        with open(db_sqlite, 'wb') as f:
                            f.write(extracted_bytes)
                        restored_items.append('Process Dashboard (db.sqlite3)')
                    elif 'app_database.db' in member_clean or member_clean.endswith('.db'):
                        extracted_bytes = zf.read(member)
                        os.makedirs(os.path.dirname(main_db), exist_ok=True)
                        with open(main_db, 'wb') as f:
                            f.write(extracted_bytes)
                        restored_items.append('Main App Engine (app_database.db)')

        elif filename.endswith('.sqlite3'):
            connections.close_all()
            with open(db_sqlite, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            restored_items.append('Process Dashboard (db.sqlite3)')

        elif filename.endswith('.db'):
            with open(main_db, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            restored_items.append('Main App Engine (app_database.db)')

        else:
            messages.error(request, "Unsupported file format. Please upload a .zip database bundle or a .sqlite3 / .db file.")
            return redirect('tracker:dashboard')

        # Re-run schema migrations on main_app DB if restored
        try:
            from main_app import db_manager
            db_manager.init_db()
        except Exception:
            pass

        if restored_items:
            messages.success(request, f"Database restored successfully! Components updated: {', '.join(restored_items)}. All live data is now loaded.")
        else:
            messages.warning(request, "Archive was uploaded, but no valid database files (db.sqlite3 or app_database.db) were detected inside.")

    except Exception as e:
        messages.error(request, f"Error restoring database: {str(e)}")

    return redirect('tracker:dashboard')


# ==========================================
# PARTY DETAIL & CUSTOM TABS / TABLES SYSTEM
# ==========================================

@login_required
def party_detail(request, pk):
    """
    Detailed page for a specific Party / Client.
    Displays customizable tabs and dynamic tables.
    Checks party access rights and custom tabs editing permission.
    """
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied: Aapko is party ko dekhne ki access nahi hai.")
        return redirect('tracker:dashboard')

    if not profile.can_view_party_details and not (profile.is_admin or request.user.is_superuser):
        messages.error(request, "Permission denied: Party custom tabs dekhne ki access restricted hai.")
        return redirect('tracker:dashboard')

    item = get_object_or_404(ProcessItem, pk=pk)
    all_party_tabs = item.custom_tabs.prefetch_related('custom_tables').order_by('order_index', 'id')
    if not (profile.is_admin or profile.all_tabs_access or request.user.is_superuser):
        allowed_titles = [str(t).strip().lower() for t in (profile.allowed_tab_titles or []) if str(t).strip()]
        tabs = [t for t in all_party_tabs if str(t.title).strip().lower() in allowed_titles]
    else:
        tabs = all_party_tabs
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()

    return render(request, 'tracker/party_detail.html', {
        'item': item,
        'tabs': tabs,
        'today': today,
        'user_profile': profile,
        'can_edit_custom_tabs': profile.can_edit_custom_tabs or profile.is_admin or request.user.is_superuser,
    })



@login_required
@csrf_exempt
def party_tab_create(request, pk):
    """
    Create a new tab for this party.
    Optional flag: apply_to_all (boolean) -> if True, creates this tab across all parties!
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_edit_custom_tabs or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot modify tabs'}, status=403)

    item = get_object_or_404(ProcessItem, pk=pk)
    try:
        data = json.loads(request.body.decode('utf-8'))
        title = data.get('title', '').strip() or f"Tab {item.custom_tabs.count() + 1}"
        color = data.get('color', '').strip() or '#3b82f6'
        apply_to_all = bool(data.get('apply_to_all', False))

        max_order = item.custom_tabs.count()
        tab = PartyCustomTab.objects.create(
            item=item,
            title=title,
            color=color,
            order_index=max_order + 1
        )

        created_count = 1
        if apply_to_all:
            other_items = ProcessItem.objects.exclude(id=item.id)
            for other in other_items:
                other_order = other.custom_tabs.count() + 1
                PartyCustomTab.objects.create(
                    item=other,
                    title=title,
                    color=color,
                    order_index=other_order
                )
                created_count += 1

        return JsonResponse({
            'success': True,
            'apply_to_all': apply_to_all,
            'created_count': created_count,
            'tab': {
                'id': tab.id,
                'title': tab.title,
                'color': tab.color,
                'order_index': tab.order_index,
                'tables_count': 0
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_tab_update(request, tab_id):
    """Update tab title or color pattern"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    tab = get_object_or_404(PartyCustomTab, pk=tab_id)
    if not profile or not profile.can_edit_custom_tabs or not profile.is_party_allowed(tab.item_id):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot modify tabs'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        old_title = tab.title
        new_title = data.get('title', '').strip()
        new_color = data.get('color', '').strip()
        apply_to_all = bool(data.get('apply_to_all', False))

        if new_title:
            tab.title = new_title
        if new_color:
            tab.color = new_color
        if 'order_index' in data:
            try:
                tab.order_index = int(data['order_index'])
            except (ValueError, TypeError):
                pass
        tab.save()

        # If apply_to_all is True, sync tab rename / color to all matching tabs across parties
        synced_count = 1
        if apply_to_all:
            matching_tabs = PartyCustomTab.objects.filter(title__iexact=old_title).exclude(id=tab.id)
            for m_tab in matching_tabs:
                if new_title:
                    m_tab.title = new_title
                if new_color:
                    m_tab.color = new_color
                m_tab.save()
                synced_count += 1
        return JsonResponse({
            'success': True,
            'tab': {
                'id': tab.id,
                'title': tab.title,
                'color': tab.color,
                'order_index': tab.order_index
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_tab_delete(request, tab_id):
    """Delete a custom tab and its tables"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    tab = get_object_or_404(PartyCustomTab, pk=tab_id)
    if not profile or not profile.can_edit_custom_tabs or not profile.is_party_allowed(tab.item_id):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot modify tabs'}, status=403)

    try:
        tab_title = tab.title
        tab.delete()
        return JsonResponse({'success': True, 'message': f'Tab "{tab_title}" deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_tabs_reorder(request, pk):
    """
    Reorder custom tabs for a party.
    Payload: {"tab_ids": [3, 1, 2]}
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    if not profile or not profile.can_edit_custom_tabs or not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot modify tabs'}, status=403)

    item = get_object_or_404(ProcessItem, pk=pk)
    try:
        data = json.loads(request.body.decode('utf-8'))
        tab_ids = data.get('tab_ids', [])
        for index, tab_id in enumerate(tab_ids, 1):
            PartyCustomTab.objects.filter(id=tab_id, item=item).update(order_index=index)

        return JsonResponse({'success': True, 'message': 'Tabs reordered successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@login_required
@csrf_exempt
def party_table_save(request, tab_id):
    """
    Create or update a custom table within a tab.
    Payload:
      - table_id (optional, if updating existing table)
      - title
      - columns (array of string header names, e.g. ["Col 1", "Col 2"])
      - rows (array of arrays containing cell strings)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    tab = get_object_or_404(PartyCustomTab, pk=tab_id)
    if not profile or not profile.can_edit_custom_tabs or not profile.is_party_allowed(tab.item_id):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot modify tables'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        table_id = data.get('table_id')
        title = data.get('title', '').strip() or 'Custom Table'
        columns = data.get('columns', [])
        rows = data.get('rows', [])

        # Validate columns
        if not isinstance(columns, list) or len(columns) == 0:
            columns = ['Column 1', 'Column 2', 'Column 3']

        # Clean columns: each column can be a string name or a dict {'name': '...', 'type': 'text|date|checkbox', 'width': '...', 'alert_on_unchecked': bool}
        cleaned_columns = []
        for i, c in enumerate(columns):
            if isinstance(c, dict):
                col_name = str(c.get('name', '')).strip() or f"Col {i+1}"
                col_type = str(c.get('type', 'text')).strip().lower()
                if col_type not in ['text', 'date', 'checkbox']:
                    col_type = 'text'
                col_width = str(c.get('width', '')).strip()
                alert_on_unchecked = bool(c.get('alert_on_unchecked', False))
                cleaned_columns.append({
                    'name': col_name,
                    'type': col_type,
                    'width': col_width,
                    'alert_on_unchecked': alert_on_unchecked
                })
            else:
                col_name = str(c).strip() if str(c).strip() else f"Col {i+1}"
                cleaned_columns.append(col_name)

        # Clean rows
        cleaned_rows = []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, list):
                    # Pad or truncate to match columns length
                    cleaned_row = []
                    for c_idx in range(len(cleaned_columns)):
                        val = row[c_idx] if c_idx < len(row) else ''
                        cleaned_row.append(str(val))
                    cleaned_rows.append(cleaned_row)

        apply_to_all = bool(data.get('apply_to_all', False))

        if table_id:
            table = get_object_or_404(PartyCustomTable, pk=table_id, tab=tab)
            old_table_title = table.title
            table.title = title
            table.columns = cleaned_columns
            table.rows = cleaned_rows
            table.save()
            action = 'updated'

            # If user renamed table or modified columns, find matching tables across parties:
            # Match by old_table_title or new title
            matching_tabs = PartyCustomTab.objects.filter(title__iexact=tab.title).exclude(id=tab.id)
            for m_tab in matching_tabs:
                m_table = m_tab.custom_tables.filter(title__iexact=old_table_title).first()
                if not m_table and old_table_title != title:
                    m_table = m_tab.custom_tables.filter(title__iexact=title).first()
                if m_table:
                    # Sync title
                    m_table.title = title
                    # Update column definitions (width, types, order, alert_on_unchecked)
                    m_table.columns = cleaned_columns
                    # Ensure each existing row matches new column count
                    synced_rows = []
                    for m_r in m_table.rows or []:
                        if isinstance(m_r, list):
                            new_r = []
                            for c_idx, c_def in enumerate(cleaned_columns):
                                if c_idx < len(m_r):
                                    new_r.append(m_r[c_idx])
                                else:
                                    # New padded cell
                                    is_chk = isinstance(c_def, dict) and c_def.get('type') == 'checkbox'
                                    new_r.append('No' if is_chk else '')
                            synced_rows.append(new_r)
                    m_table.rows = synced_rows
                    m_table.save()
        else:
            max_order = tab.custom_tables.count()
            table = PartyCustomTable.objects.create(
                tab=tab,
                title=title,
                columns=cleaned_columns,
                rows=cleaned_rows,
                order_index=max_order + 1
            )
            action = 'created'

            # If user selected 'apply_to_all', create clean matching table across all other parties under tab with same name
            if apply_to_all:
                # Clean blank rows template (matching column structure but empty data)
                blank_rows = [['' for _ in cleaned_columns] for _ in range(len(cleaned_rows))] if cleaned_rows else []
                other_items = ProcessItem.objects.exclude(id=tab.item_id)
                for other in other_items:
                    # Find or create matching tab by title on other party
                    target_tab = other.custom_tabs.filter(title__iexact=tab.title).first()
                    if not target_tab:
                        target_tab = PartyCustomTab.objects.create(
                            item=other,
                            title=tab.title,
                            color=tab.color,
                            order_index=other.custom_tabs.count() + 1
                        )
                    # Check if table with this title already exists in target_tab
                    existing_tbl = target_tab.custom_tables.filter(title__iexact=title).first()
                    if not existing_tbl:
                        PartyCustomTable.objects.create(
                            tab=target_tab,
                            title=title,
                            columns=cleaned_columns,
                            rows=blank_rows,
                            order_index=target_tab.custom_tables.count() + 1
                        )

        return JsonResponse({
            'success': True,
            'action': action,
            'apply_to_all': apply_to_all,
            'table': {
                'id': table.id,
                'title': table.title,
                'columns': table.columns,
                'rows': table.rows,
                'order_index': table.order_index
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_table_delete(request, table_id):
    """Delete a table inside a tab"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    table = get_object_or_404(PartyCustomTable, pk=table_id)
    if not profile or not profile.can_edit_custom_tabs or (table.tab and not profile.is_party_allowed(table.tab.item_id)):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot delete table'}, status=403)

    try:
        title = table.title
        table.delete()
        return JsonResponse({'success': True, 'message': f'Table "{title}" deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_table_rename(request, table_id):
    """Rename a custom table, optionally syncing to all matching tables across parties."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    profile = get_user_access_profile(request.user)
    table = get_object_or_404(PartyCustomTable, pk=table_id)
    if not profile or not profile.can_edit_custom_tabs or (table.tab and not profile.is_party_allowed(table.tab.item_id)):
        return JsonResponse({'success': False, 'error': 'Permission denied: Cannot rename table'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
        new_title = data.get('title', '').strip()
        apply_to_all = bool(data.get('apply_to_all', True))
        if not new_title:
            return JsonResponse({'success': False, 'error': 'Table title cannot be empty'}, status=400)

        old_title = table.title
        table.title = new_title
        table.save()

        synced_count = 1
        if apply_to_all and table.tab:
            matching_tabs = PartyCustomTab.objects.filter(title__iexact=table.tab.title).exclude(id=table.tab.id)
            for m_tab in matching_tabs:
                m_tbl = m_tab.custom_tables.filter(title__iexact=old_title).first()
                if m_tbl:
                    m_tbl.title = new_title
                    m_tbl.save()
                    synced_count += 1

        return JsonResponse({'success': True, 'title': new_title, 'synced_count': synced_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==========================================
# PARTY CATALOG / PRODUCT DATA VIEWS
# ==========================================

def parse_catalog_file(uploaded_file):
    """
    Parses an uploaded .xlsx, .xls, or .csv file.
    Supports multi-sheet Excel files: iterates through each worksheet (e.g. RING, EARRINGS, PENDANT, BRACELET),
    tagging each record with its `sheet_name`.
    Returns a tuple of (records_list, all_extra_keys, detected_sheet_names).
    """
    filename = uploaded_file.name.lower()
    sheet_data_list = []
    detected_sheet_names = []

    if filename.endswith('.csv'):
        content = uploaded_file.read()
        rows = []
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                decoded_file = io.StringIO(content.decode(encoding))
                reader = csv.reader(decoded_file)
                rows = list(reader)
                break
            except Exception:
                continue
        if rows:
            sheet_data_list.append(('General', rows))
            detected_sheet_names.append('General')
    elif filename.endswith(('.xlsx', '.xls')):
        try:
            wb = openpyxl.load_workbook(uploaded_file, data_only=True)
            non_catalog_names = ['backend', 'config', 'settings', 'calculation', 'calculations', 'formula', 'formulas', 'lookup', 'lookups']
            for sheet_name in wb.sheetnames:
                clean_sname = sheet_name.strip()
                if clean_sname.lower() in non_catalog_names:
                    continue
                detected_sheet_names.append(clean_sname)
                ws = wb[sheet_name]
                s_rows = []
                for r in ws.iter_rows(values_only=True):
                    s_rows.append([str(cell) if cell is not None else '' for cell in r])
                if s_rows:
                    sheet_data_list.append((clean_sname, s_rows))
        except Exception:
            return [], [], []
    else:
        return [], [], []

    if not sheet_data_list:
        return [], [], []

    recognized_headers = [
        'sku', 'style', 'category', 'lot', 'selling_price_usd', 'cost_usd',
        'cost', 'selling', 'gold_kt', 'gold_weight', 'center_stone_shape',
        'gold_color', 'certified', 'diamond', 'setting'
    ]

    records = []
    all_extra_keys = []

    for sheet_name, rows in sheet_data_list:
        header_idx = -1
        for idx, row in enumerate(rows[:12]):
            clean_row = [str(c).strip().lower() for c in row if c]
            if any(h in clean_row for h in recognized_headers):
                header_idx = idx
                break

        if header_idx == -1:
            continue

        headers = [str(c).strip() for c in rows[header_idx]]

        for row in rows[header_idx + 1:]:
            if not any(row):
                continue

            row_dict = {}
            for col_idx, col_name in enumerate(headers):
                if col_idx < len(row):
                    val = str(row[col_idx]).strip() if row[col_idx] is not None else ''
                    if val.lower() == 'none':
                        val = ''
                    if col_name:
                        row_dict[col_name] = val

            clean_vals = [v.lower() for v in row_dict.values() if v]
            if not clean_vals:
                continue
            # Skip repeated header row
            if any(v in ['sku', 'category', 'selling_price_usd', 'cost_usd'] for v in clean_vals[:3]):
                continue

            mapped = {
                'sheet_name': sheet_name if sheet_name != 'General' else '',
                'lot': '',
                'category': '',
                'sku': '',
                'certified': '',
                'gold_kt': '',
                'gold_color': '',
                'gold_weight': '',
                'center_diamond_clarity': '',
                'center_diamond_color': '',
                'center_stone_shape': '',
                'center_stone_weight': '',
                'side_stone_shape': '',
                'side_stone_weight': '',
                'side_stone_color_clarity': '',
                'setting': '',
                'total_diamond_pcs': '',
                'cost_usd': '',
                'selling_price_usd': '',
                'extra_data': {}
            }

            for orig_key, val in row_dict.items():
                k_norm = orig_key.lower().replace(' ', '_').replace('-', '_').replace('#', '').strip()

                if k_norm in ['sku', 'style', 'style_code', 'item_code', 'design_no']:
                    mapped['sku'] = val
                elif k_norm in ['lot', 'lot_no', 'lot_num']:
                    mapped['lot'] = val
                elif k_norm in ['category', 'cat', 'item_type']:
                    mapped['category'] = val
                elif k_norm in ['certified', 'cert', 'certificate', 'lab']:
                    mapped['certified'] = val
                elif k_norm in ['gold_kt', 'gold_k', 'kt', 'karat', 'purity']:
                    mapped['gold_kt'] = val
                elif k_norm in ['gold_color', 'metal_color', 'color']:
                    mapped['gold_color'] = val
                elif k_norm in ['gold_weight', 'gold_wt', 'gross_wt', 'net_wt', 'weight']:
                    mapped['gold_weight'] = val
                elif k_norm in ['center_diamond_clarity', 'center_clarity', 'diamond_clarity']:
                    mapped['center_diamond_clarity'] = val
                elif k_norm in ['center_diamond_color', 'center_color']:
                    mapped['center_diamond_color'] = val
                elif k_norm in ['center_stone_shape', 'center_shape', 'stone_shape', 'shape']:
                    mapped['center_stone_shape'] = val
                elif k_norm in ['center_stone_weight', 'center_stone_wt', 'center_wt', 'center_weight']:
                    mapped['center_stone_weight'] = val
                elif k_norm in ['side_stone_shape', 'side_shape']:
                    mapped['side_stone_shape'] = val
                elif k_norm in ['side_stone_weight', 'side_stone_wt', 'side_wt']:
                    mapped['side_stone_weight'] = val
                elif k_norm in ['side_stone_color_clarity', 'side_stone_clarity', 'side_color_clarity', 'side_clarity']:
                    mapped['side_stone_color_clarity'] = val
                elif k_norm in ['setting', 'setting_type']:
                    mapped['setting'] = val
                elif k_norm in ['total_diamond_pcs', 'diamond_pcs', 'total_pcs', 'pcs']:
                    mapped['total_diamond_pcs'] = val
                elif k_norm in ['cost_usd', 'cost', 'cost_price', 'purchase_usd']:
                    mapped['cost_usd'] = val
                elif k_norm in ['selling_price_usd', 'selling_price', 'selling', 'price', 'sale_usd', 'retail_usd']:
                    mapped['selling_price_usd'] = val
                else:
                    if val and orig_key:
                        mapped['extra_data'][orig_key] = val
                        if orig_key not in all_extra_keys:
                            all_extra_keys.append(orig_key)

            # Auto-assign category from sheet name if category is empty
            if not mapped['category'] and mapped['sheet_name']:
                mapped['category'] = mapped['sheet_name'].title()

            if mapped['sku'] or mapped['category'] or mapped['lot'] or mapped['cost_usd'] or mapped['selling_price_usd']:
                records.append(mapped)

    return records, all_extra_keys, detected_sheet_names


@login_required
@xframe_options_exempt
def party_data_view(request, pk):
    """
    Dedicated Product / Catalog / SKU Data page for a specific Party.
    Displays tabular SKU data, summary statistics, separated sheet/category tabs (e.g. Ring, Earrings, Pendant),
    instant real-time SKU search, and handles multi-sheet Excel Import/Export.
    """
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_view_party_data or request.user.is_superuser):
        messages.error(request, "Permission denied: Catalog data dekhne ki permission admin dwara nahi di gayi hai.")
        return redirect('tracker:dashboard')
    if not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied: Aapko is party ka data dekhne ki access nahi hai.")
        return redirect('tracker:dashboard')

    item = get_object_or_404(ProcessItem, pk=pk)
    all_qs = item.data_records.all().order_by('order_index', 'id')
    all_records_count = all_qs.count()
    all_records = list(all_qs)

    # Attach tab_label to every record (sheet_name if present, else category, else 'General')
    for r in all_records:
        r.tab_label = (r.sheet_name.strip() if r.sheet_name else (r.category.strip() if r.category else 'General'))

    # Discover available tabs in preferred Excel sheet order
    detected_sheets = item.custom_fields.get('catalog_sheets', []) if isinstance(item.custom_fields, dict) else []
    tab_list = []
    seen_tabs = set()

    for s in detected_sheets:
        s_clean = s.strip()
        if s_clean and s_clean.upper() not in seen_tabs:
            seen_tabs.add(s_clean.upper())
            tab_list.append(s_clean)

    tab_counts = {}
    for r in all_records:
        t_label = r.tab_label
        t_upper = t_label.upper()
        if t_upper not in seen_tabs:
            seen_tabs.add(t_upper)
            tab_list.append(t_label)
        tab_counts[t_upper] = tab_counts.get(t_upper, 0) + 1

    # Active tab filter (from query param or defaults to All)
    active_tab = request.GET.get('tab', '').strip()
    filtered_records = all_records
    if active_tab and active_tab.lower() != 'all':
        filtered_records = [
            r for r in all_records
            if r.tab_label.lower() == active_tab.lower()
            or (r.category and r.category.lower() == active_tab.lower())
            or (r.sheet_name and r.sheet_name.lower() == active_tab.lower())
        ]

    # Additional text search & dropdown filters
    search_query = request.GET.get('q', '').strip().lower()
    category_filter = request.GET.get('category', '').strip().lower()
    color_filter = request.GET.get('color', '').strip().lower()
    shape_filter = request.GET.get('shape', '').strip().lower()

    if search_query:
        filtered_records = [
            r for r in filtered_records
            if search_query in r.sku.lower()
            or search_query in r.category.lower()
            or search_query in r.lot.lower()
            or search_query in r.center_stone_shape.lower()
            or search_query in r.certified.lower()
            or search_query in r.gold_color.lower()
            or search_query in r.sheet_name.lower()
        ]
    if category_filter:
        filtered_records = [r for r in filtered_records if r.category.lower() == category_filter]
    if color_filter:
        filtered_records = [r for r in filtered_records if r.gold_color.lower() == color_filter]
    if shape_filter:
        filtered_records = [r for r in filtered_records if r.center_stone_shape.lower() == shape_filter]

    records = filtered_records

    # Catalog tabs structure with counts for UI pills
    catalog_tabs = [{
        'name': 'All',
        'display': 'All Items',
        'count': all_records_count,
        'is_active': (not active_tab or active_tab.lower() == 'all')
    }]
    for t in tab_list:
        cnt = tab_counts.get(t.upper(), 0)
        catalog_tabs.append({
            'name': t,
            'display': t,
            'count': cnt,
            'is_active': (active_tab.lower() == t.lower())
        })

    # Compute metrics for currently visible active tab records
    scope_for_metrics = records if (active_tab and active_tab.lower() != 'all') else all_records
    total_cost = sum(r.cost_numeric for r in scope_for_metrics)
    total_selling = sum(r.selling_numeric for r in scope_for_metrics)
    total_gold_wt = sum(r.gold_weight_numeric for r in scope_for_metrics)
    total_diamonds = sum(r.diamond_pcs_numeric for r in scope_for_metrics)

    categories = sorted(list({r.category.strip() for r in all_records if r.category and r.category.strip()}))
    shapes = sorted(list({r.center_stone_shape.strip() for r in all_records if r.center_stone_shape and r.center_stone_shape.strip()}))
    gold_colors = sorted(list({r.gold_color.strip() for r in all_records if r.gold_color and r.gold_color.strip()}))

    # Discover unique extra column keys
    extra_keys = []
    for r in all_records:
        if isinstance(r.extra_data, dict):
            for k in r.extra_data.keys():
                if k not in extra_keys:
                    extra_keys.append(k)

    extra_keys = extra_keys[:6]
    for r in records:
        r.extra_values = [r.extra_data.get(k, '-') if isinstance(r.extra_data, dict) else '-' for k in extra_keys]

    can_import = profile.is_admin or profile.can_import_party_data or request.user.is_superuser
    can_edit = profile.is_admin or profile.can_edit_custom_tabs or request.user.is_superuser
    can_clear = profile.is_admin or profile.can_clear_party_data or request.user.is_superuser

    context = {
        'item': item,
        'records': records,
        'all_records_count': all_records_count,
        'filtered_count': len(records),
        'catalog_tabs': catalog_tabs,
        'active_tab': active_tab or 'All',
        'metrics': {
            'total_items': len(scope_for_metrics),
            'total_cost': total_cost,
            'total_selling': total_selling,
            'total_gold_wt': total_gold_wt,
            'total_diamonds': total_diamonds,
            'category_count': len(categories),
        },
        'categories': categories,
        'shapes': shapes,
        'gold_colors': gold_colors,
        'extra_keys': extra_keys[:6],
        'search_query': search_query,
        'category_filter': category_filter,
        'color_filter': color_filter,
        'shape_filter': shape_filter,
        'can_import': can_import,
        'can_edit': can_edit,
        'can_clear': can_clear,
        'user_profile': profile,
    }
    return render(request, 'tracker/party_data.html', context)


@login_required
@csrf_exempt
@xframe_options_exempt
def party_data_import(request, pk):
    """
    Import Excel (.xlsx/.xls) or CSV data into PartyDataRecord.
    Mode: 'append' (default) keeps existing records and adds new ones.
          Deduplication rule: If SKU is identical BUT Category is different, it APPENDS!
          Only skips/updates when BOTH SKU AND Category match identical existing data.
          'replace' removes existing records and imports fresh.
    """
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_view_party_data or request.user.is_superuser):
        messages.error(request, "Permission denied: Catalog data access restricted hai.")
        return redirect('tracker:dashboard')
    if not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    if not (profile.is_admin or profile.can_import_party_data or request.user.is_superuser):
        messages.error(request, "Permission denied: Data import access restricted hai.")
        return redirect('tracker:party_data', pk=pk)

    item = get_object_or_404(ProcessItem, pk=pk)

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        import_mode = request.POST.get('import_mode', 'append').strip().lower()

        try:
            records_data, _, detected_sheets = parse_catalog_file(uploaded_file)
            if not records_data:
                messages.error(request, "No valid data rows found in the uploaded file. Please check file format.")
                return redirect('tracker:party_data', pk=item.pk)

            # Store detected Excel sheets in party custom_fields for persistent tab ordering
            if detected_sheets:
                if not isinstance(item.custom_fields, dict):
                    item.custom_fields = {}
                item.custom_fields['catalog_sheets'] = detected_sheets
                item.save(update_fields=['custom_fields'])

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
                item.data_records.all().delete()
                start_order = 1
                existing_by_combo = {}
                existing_by_sig = {}
            else:
                last_record = item.data_records.order_by('-order_index').first()
                start_order = (last_record.order_index + 1) if last_record else 1
                # Build lookup maps for existing records: Key is (sku, category)
                existing_by_combo = {}
                existing_by_sig = {}
                for rec in item.data_records.all():
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

                # 1. Prevent duplicate rows within the uploaded file itself
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

                # 2. In append mode, check against existing DB records
                # If SKU matches BUT Category is different -> combo_key is different -> APPENDS as new!
                if import_mode != 'replace':
                    target_rec = None
                    if combo_key and combo_key in existing_by_combo:
                        target_rec = existing_by_combo[combo_key]
                    elif not combo_key and sig in existing_by_sig:
                        target_rec = existing_by_sig[sig]

                    if target_rec:
                        # Existing record with same SKU AND same Category found: check if all fields match
                        is_identical = True
                        for f in fields_to_compare:
                            old_val = str(getattr(target_rec, f, '') or '').strip()
                            new_val = str(r_data.get(f, '') or '').strip()
                            if old_val != new_val:
                                is_identical = False
                                break

                        if is_identical:
                            # Exact identical duplicate in same category: do not append!
                            skipped_duplicates += 1
                            continue
                        else:
                            # Same SKU & Category with updated attributes: update existing record
                            for f in fields_to_compare:
                                setattr(target_rec, f, r_data.get(f, ''))
                            if r_data.get('sheet_name'):
                                target_rec.sheet_name = r_data['sheet_name']
                            if r_data.get('extra_data'):
                                target_rec.extra_data = r_data['extra_data']
                            target_rec.save()
                            updated_count += 1
                            continue

                # 3. New record (different SKU or different Category)
                new_objs.append(PartyDataRecord(
                    party=item,
                    order_index=start_order + len(new_objs),
                    sheet_name=r_data.get('sheet_name', ''),
                    sku=raw_sku,
                    lot=r_data['lot'],
                    category=r_data['category'],
                    certified=r_data['certified'],
                    gold_kt=r_data['gold_kt'],
                    gold_color=r_data['gold_color'],
                    gold_weight=r_data['gold_weight'],
                    center_diamond_clarity=r_data['center_diamond_clarity'],
                    center_diamond_color=r_data['center_diamond_color'],
                    center_stone_shape=r_data['center_stone_shape'],
                    center_stone_weight=r_data['center_stone_weight'],
                    side_stone_shape=r_data['side_stone_shape'],
                    side_stone_weight=r_data['side_stone_weight'],
                    side_stone_color_clarity=r_data['side_stone_color_clarity'],
                    setting=r_data['setting'],
                    total_diamond_pcs=r_data['total_diamond_pcs'],
                    cost_usd=r_data['cost_usd'],
                    selling_price_usd=r_data['selling_price_usd'],
                    extra_data=r_data.get('extra_data', {}),
                ))

            if new_objs:
                PartyDataRecord.objects.bulk_create(new_objs)

            # Record Edit History entry
            history_summary = f"Imported data (Mode: {import_mode.title()}): {len(new_objs)} added"
            if updated_count:
                history_summary += f", {updated_count} updated"
            if skipped_duplicates:
                history_summary += f", {skipped_duplicates} duplicate skipped"

            ProcessItemHistory.objects.create(
                item=item,
                action_type='imported',
                summary=history_summary,
                changes=[{
                    'field': 'data_records',
                    'label': 'Catalog Data',
                    'old': f"{item.data_records.count() - len(new_objs)} items",
                    'new': f"{item.data_records.count()} items (+{len(new_objs)})",
                }]
            )

            msg_parts = []
            if new_objs:
                msg_parts.append(f"{len(new_objs)} naye items add hue")
            if updated_count:
                msg_parts.append(f"{updated_count} items update hue")
            if skipped_duplicates:
                msg_parts.append(f"{skipped_duplicates} duplicate items skip kar diye gaye (same category & data)")

            if not msg_parts:
                messages.info(request, "Uploaded file ka sara data already exist karta hai, koi duplicate record add nahi kiya gaya.")
            else:
                messages.success(request, f"Import report ({item.client_name}): " + ", ".join(msg_parts) + ".")
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")

    return redirect('tracker:party_data', pk=item.pk)


@login_required
@csrf_exempt
@xframe_options_exempt
def party_data_deduplicate(request, pk):
    """
    Scans all catalog records for this party and deletes any duplicate rows,
    keeping only the first instance of each (SKU, Category) combination.
    Records with different categories are strictly preserved.
    """
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_view_party_data or request.user.is_superuser):
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')
    if not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    if not (profile.is_admin or profile.can_import_party_data or request.user.is_superuser):
        messages.error(request, "Permission denied: Action not allowed.")
        return redirect('tracker:party_data', pk=pk)

    item = get_object_or_404(ProcessItem, pk=pk)
    records = list(item.data_records.all().order_by('order_index', 'id'))
    seen_combos = set()
    seen_sigs = set()
    duplicate_ids = []

    for r in records:
        sku_norm = r.sku.strip().upper() if r.sku else None
        cat_norm = (r.category or '').strip().upper()
        if sku_norm:
            combo_key = (sku_norm, cat_norm)
            if combo_key in seen_combos:
                duplicate_ids.append(r.id)
            else:
                seen_combos.add(combo_key)
        else:
            sig = (
                cat_norm,
                str(r.lot or '').strip().upper(),
                str(r.center_stone_shape or '').strip().upper(),
                str(r.gold_weight or '').strip(),
                str(r.cost_usd or '').strip(),
                str(r.selling_price_usd or '').strip(),
            )
            if sig in seen_sigs:
                duplicate_ids.append(r.id)
            else:
                seen_sigs.add(sig)

    if duplicate_ids:
        count = len(duplicate_ids)
        PartyDataRecord.objects.filter(id__in=duplicate_ids).delete()

        # Re-index cleanly
        for idx, rec in enumerate(item.data_records.all().order_by('order_index', 'id'), start=1):
            if rec.order_index != idx:
                rec.order_index = idx
                rec.save(update_fields=['order_index'])

        ProcessItemHistory.objects.create(
            item=item,
            action_type='edited',
            summary=f"Cleaned {count} duplicate catalog records",
            changes=[{'field': 'data_records', 'label': 'Clean Duplicates', 'old': f"{len(records)} items", 'new': f"{len(records) - count} items"}]
        )
        messages.success(request, f"Deduplication complete! {count} duplicate records successfully remove kar diye gaye.")
    else:
        messages.info(request, "Koi duplicate records nahi mile. Sabhi records already unique hain!")

    return redirect('tracker:party_data', pk=item.pk)


@login_required
def party_data_export(request, pk):
    """
    Export PartyDataRecords to formatted Excel (.xlsx) file.
    Creates separate worksheets for each sheet/category tab (e.g. RING, EARRINGS, PENDANT, BRACELET),
    matching the multi-sheet structure of the catalog!
    """
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_view_party_data or request.user.is_superuser):
        return HttpResponse("Permission denied", status=403)
    if not profile.is_party_allowed(pk):
        return HttpResponse("Permission denied", status=403)

    item = get_object_or_404(ProcessItem, pk=pk)
    records = list(item.data_records.all().order_by('order_index', 'id'))

    headers = [
        '#', 'LOT', 'CATEGORY', 'SKU', 'Certified', 'GOLD_KT', 'GOLD_COLOR',
        'GOLD_WEIGHT', 'CENTER_DIAMOND_CLARITY', 'CENTER_DIAMOND_COLOR',
        'CENTER_STONE_SHAPE', 'CENTER_STONE_WEIGHT', 'SIDE_STONE_SHAPE',
        'SIDE_STONE_WEIGHT', 'SIDE_STONE_COLOR_CLARITY', 'SETTING',
        'TOTAL_DIAMOND_PCS', 'COST_USD', 'SELLING_PRICE_USD'
    ]

    # Group records by sheet_name / category
    detected_sheets = item.custom_fields.get('catalog_sheets', []) if isinstance(item.custom_fields, dict) else []
    records_by_sheet = {}
    for r in records:
        sheet_key = (r.sheet_name.strip() if r.sheet_name else (r.category.strip() if r.category else 'General'))
        if sheet_key not in records_by_sheet:
            records_by_sheet[sheet_key] = []
        records_by_sheet[sheet_key].append(r)

    # Ensure detected sheets with 0 records also appear in export if appropriate
    for s in detected_sheets:
        if s not in records_by_sheet:
            records_by_sheet[s] = []

    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")

    if not records_by_sheet:
        ws = wb.create_sheet(title="Catalog Data")
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
    else:
        for s_title, s_records in records_by_sheet.items():
            clean_title = re.sub(r'[\\/*?:\[\]]', '_', s_title)[:31].strip() or 'Sheet'
            ws = wb.create_sheet(title=clean_title)
            ws.append(headers)
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            for idx, r in enumerate(s_records, start=1):
                ws.append([
                    idx, r.lot, r.category, r.sku, r.certified, r.gold_kt, r.gold_color,
                    r.gold_weight, r.center_diamond_clarity, r.center_diamond_color,
                    r.center_stone_shape, r.center_stone_weight, r.side_stone_shape,
                    r.side_stone_weight, r.side_stone_color_clarity, r.setting,
                    r.total_diamond_pcs, r.cost_usd, r.selling_price_usd
                ])

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    clean_name = "".join(c for c in item.client_name if c.isalnum() or c in (' ', '_', '-')).strip() or f"party_{item.id}"
    filename = f"{clean_name}_Catalog_Data_{date.today().strftime('%Y%m%d')}.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
@csrf_exempt
@xframe_options_exempt
def party_data_clear(request, pk):
    """Clear all catalog data records for a party with permission check and random CAPTCHA validation"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_clear_party_data or request.user.is_superuser):
        messages.error(request, "Permission denied: Catalog data delete / clear karne ki permission admin dwara nahi di gayi hai.")
        return redirect('tracker:party_data', pk=pk)
    if not profile.is_party_allowed(pk):
        messages.error(request, "Permission denied.")
        return redirect('tracker:dashboard')

    item = get_object_or_404(ProcessItem, pk=pk)

    if request.method == 'POST':
        captcha_input = request.POST.get('captcha_input', '').strip().upper()
        expected_captcha = request.POST.get('expected_captcha', '').strip().upper()

        if not captcha_input or not expected_captcha or captcha_input != expected_captcha:
            messages.error(request, "Security verification fail: Captcha code galat enter kiya gaya. Data clear nahi hua.")
            return redirect('tracker:party_data', pk=pk)

        count = item.data_records.count()
        item.data_records.all().delete()

        ProcessItemHistory.objects.create(
            item=item,
            action_type='edited',
            summary=f"Cleared all {count} catalog records",
            changes=[{'field': 'data_records', 'label': 'Clear Catalog Data', 'old': f"{count} items", 'new': "0 items"}]
        )
        messages.success(request, f"'{item.client_name}' ke sabhi {count} catalog records successfully delete kar diye gaye.")

    return redirect('tracker:party_data', pk=item.pk)


@login_required
@csrf_exempt
def party_data_add_record(request, pk):
    """Add a single PartyDataRecord manually"""
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_import_party_data or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    if not profile.is_party_allowed(pk):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    item = get_object_or_404(ProcessItem, pk=pk)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
        sku = data.get('sku', '').strip()
        category = data.get('category', '').strip()
        sheet_name = data.get('sheet_name', '').strip()
        if not sku:
            return JsonResponse({'success': False, 'error': 'SKU is required'}, status=400)

        existing = item.data_records.filter(sku__iexact=sku, category__iexact=category).first()
        if existing:
            return JsonResponse({'success': False, 'error': f"SKU '{sku}' category '{category}' me already exist karta hai! Same category me duplicate allowed nahi hai."}, status=400)

        last_record = item.data_records.order_by('-order_index').first()
        next_order = (last_record.order_index + 1) if last_record else 1

        record = PartyDataRecord.objects.create(
            party=item,
            order_index=next_order,
            sheet_name=sheet_name or (category.upper() if category else ''),
            sku=sku,
            lot=data.get('lot', '').strip(),
            category=category,
            certified=data.get('certified', '').strip(),
            gold_kt=data.get('gold_kt', '').strip(),
            gold_color=data.get('gold_color', '').strip(),
            gold_weight=data.get('gold_weight', '').strip(),
            center_diamond_clarity=data.get('center_diamond_clarity', '').strip(),
            center_diamond_color=data.get('center_diamond_color', '').strip(),
            center_stone_shape=data.get('center_stone_shape', '').strip(),
            center_stone_weight=data.get('center_stone_weight', '').strip(),
            side_stone_shape=data.get('side_stone_shape', '').strip(),
            side_stone_weight=data.get('side_stone_weight', '').strip(),
            side_stone_color_clarity=data.get('side_stone_color_clarity', '').strip(),
            setting=data.get('setting', '').strip(),
            total_diamond_pcs=data.get('total_diamond_pcs', '').strip(),
            cost_usd=data.get('cost_usd', '').strip(),
            selling_price_usd=data.get('selling_price_usd', '').strip(),
        )
        return JsonResponse({'success': True, 'record_id': record.id, 'sku': record.sku})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_data_update_record(request, record_id):
    """Update a single PartyDataRecord"""
    record = get_object_or_404(PartyDataRecord, pk=record_id)
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_import_party_data or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    if not profile.is_party_allowed(record.party_id):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
        fields = [
            'sheet_name', 'sku', 'lot', 'category', 'certified', 'gold_kt', 'gold_color',
            'gold_weight', 'center_diamond_clarity', 'center_diamond_color',
            'center_stone_shape', 'center_stone_weight', 'side_stone_shape',
            'side_stone_weight', 'side_stone_color_clarity', 'setting',
            'total_diamond_pcs', 'cost_usd', 'selling_price_usd'
        ]
        for f in fields:
            if f in data:
                setattr(record, f, str(data[f]).strip())
        record.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
def party_data_delete_record(request, record_id):
    """Delete a single PartyDataRecord"""
    record = get_object_or_404(PartyDataRecord, pk=record_id)
    profile = UserAccessProfile.get_or_create_for_user(request.user)
    if not (profile.is_admin or profile.can_clear_party_data or profile.can_import_party_data or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    if not profile.is_party_allowed(record.party_id):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    record.delete()
    return JsonResponse({'success': True})





