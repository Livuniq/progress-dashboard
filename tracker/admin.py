from django.contrib import admin
from .models import ProcessItem, PartyCustomTab, PartyCustomTable

@admin.register(ProcessItem)
class ProcessItemAdmin(admin.ModelAdmin):
    list_display = (
        'client_name',
        'status',
        'lot_progress',
        'completed_count',
        'pending_count',
        'ready_count',
        'target_date',
        'days_diff',
        'order_index',
    )
    list_filter = ('status', 'is_red_client', 'target_date')
    search_fields = ('client_name', 'notes', 'lot_progress', 'history_milestone')
    list_editable = ('status', 'lot_progress', 'pending_count', 'target_date')
    ordering = ('order_index', 'id')

@admin.register(PartyCustomTab)
class PartyCustomTabAdmin(admin.ModelAdmin):
    list_display = ('item', 'title', 'color', 'order_index', 'created_at')
    list_filter = ('item',)
    search_fields = ('title', 'item__client_name')

@admin.register(PartyCustomTable)
class PartyCustomTableAdmin(admin.ModelAdmin):
    list_display = ('tab', 'title', 'order_index', 'created_at')
    search_fields = ('title', 'tab__title', 'tab__item__client_name')

