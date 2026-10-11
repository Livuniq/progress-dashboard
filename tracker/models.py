from django.db import models
from django.utils import timezone
from datetime import date

class ProcessItem(models.Model):
    STATUS_CHOICES = [
        ('working', 'Working'),
        ('no_data', 'No data'),
        ('finished', 'Finished'),
        ('pending', 'Pending'),
        ('hold', 'On Hold'),
    ]

    client_name = models.CharField(max_length=255, verbose_name="Client / Account Name")
    is_red_client = models.BooleanField(default=False, verbose_name="Highlight Client Name in Red")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='working', verbose_name="Status")
    
    lot_progress = models.CharField(max_length=50, blank=True, default='', verbose_name="LOT (e.g. 24|75 or Finished)")
    current_lot = models.IntegerField(null=True, blank=True, verbose_name="Current LOT")
    total_lot = models.IntegerField(null=True, blank=True, verbose_name="Total LOT")
    
    completed_count = models.IntegerField(null=True, blank=True, default=0, verbose_name="Completed Count")
    pending_count = models.IntegerField(null=True, blank=True, default=0, verbose_name="Pending Count")
    ready_count = models.IntegerField(null=True, blank=True, default=0, verbose_name="Ready / In Pipeline")
    
    notes = models.TextField(blank=True, default='', verbose_name="Process Notes / Remarks")
    notes_is_red = models.BooleanField(default=False, verbose_name="Highlight Notes in Red")
    
    target_date = models.DateField(null=True, blank=True, verbose_name="Target / Finish Date")
    history_milestone = models.CharField(max_length=150, blank=True, default='', verbose_name="History / Milestone")
    
    row_highlight_color = models.CharField(max_length=25, blank=True, default='', verbose_name="Row Highlight Color (Hex)")
    is_priority = models.BooleanField(default=False, verbose_name="High Priority (Neon Border)")
    is_hidden = models.BooleanField(default=False, verbose_name="Hidden from Main View")
    is_status_manual = models.BooleanField(default=False, verbose_name="Is Status Manually Selected")
    custom_fields = models.JSONField(default=dict, blank=True, verbose_name="Custom Fields")
    
    order_index = models.IntegerField(default=0, verbose_name="Sort Order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index', 'id']
        verbose_name = "Process Item"
        verbose_name_plural = "Process Items"

    def __str__(self):
        return f"{self.client_name} ({self.get_status_display()})"

    @property
    def days_diff(self):
        """
        Calculates difference in days between current date and target date:
        today - target_date
        Positive value means overdue (e.g. +54).
        Negative value means remaining until target date (e.g. -7).
        """
        if not self.target_date:
            return None
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        diff = (today - self.target_date).days
        return diff

    @property
    def is_overdue(self):
        if self.is_status_manual and self.status != 'finished':
            return False
        if self.status in ['hold', 'pending']:
            return False
        diff = self.days_diff
        return diff is not None and diff > 0

    @property
    def dynamic_status(self):
        """
        If user manually selected the status (is_status_manual is True),
        show that selected status until target date is changed!
        When target date changes, is_status_manual is reset to False and
        dynamic calculation takes effect.
        """
        if self.is_status_manual:
            return self.status
        if self.status in ['hold', 'pending']:
            return self.status
        if self.days_diff is not None and self.days_diff > 0:
            return 'finished'
        return self.status

    @property
    def dynamic_status_display(self):
        opt = StatusOption.objects.filter(key=self.dynamic_status).first()
        if opt:
            return opt.label
        if self.dynamic_status == 'hold':
            return 'On Hold'
        if self.dynamic_status == 'pending':
            return 'Pending'
        if self.dynamic_status == 'finished':
            return 'Finished'
        return self.get_status_display()

    @property
    def formatted_lot(self):
        """
        Formats '24|75' or '24/75' as '#LOT=24, ITEM 75'.
        Handles 'Finished' and custom text cleanly.
        """
        if not self.lot_progress:
            return ""
        val = self.lot_progress.strip()
        if val.lower() == 'finished':
            return 'Finished'
        if '|' in val:
            parts = val.split('|')
            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                return f"#LOT={parts[0].strip()}, ITEM {parts[1].strip()}"
        elif '/' in val and not val.startswith('#'):
            parts = val.split('/')
            if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                return f"#LOT={parts[0].strip()}, ITEM {parts[1].strip()}"
        return val


class ProcessItemHistory(models.Model):
    item = models.ForeignKey(ProcessItem, on_delete=models.CASCADE, related_name='history_logs')
    edited_at = models.DateTimeField(default=timezone.now, verbose_name="Edited Date & Time")
    action_type = models.CharField(max_length=50, default='updated', verbose_name="Action Type") # 'created', 'updated'
    summary = models.CharField(max_length=255, blank=True, default='', verbose_name="Edit Summary")
    changes = models.JSONField(default=dict, blank=True, verbose_name="Field Changes")

    class Meta:
        ordering = ['-edited_at', '-id']
        verbose_name = "Process Item History"
        verbose_name_plural = "Process Item Histories"

    def __str__(self):
        return f"{self.item.client_name} - {self.action_type} at {self.edited_at.strftime('%d/%m/%Y %H:%M')}"


DEFAULT_COLUMNS = [
    {'key': 'col_counter', 'label': '#', 'order_index': 1, 'is_system': True},
    {'key': 'client_name', 'label': 'CLIENT / ACCOUNT', 'order_index': 2, 'is_system': True},
    {'key': 'status', 'label': 'STATUS', 'order_index': 3, 'is_system': False},
    {'key': 'lot_progress', 'label': 'LOT / ITEM', 'order_index': 4, 'is_system': False},
    {'key': 'completed_count', 'label': 'DONE', 'order_index': 5, 'is_system': False},
    {'key': 'pending_count', 'label': 'PENDING', 'order_index': 6, 'is_system': False},
    {'key': 'ready_count', 'label': 'READY', 'order_index': 7, 'is_system': False},
    {'key': 'notes', 'label': 'PROCESS NOTES / REMARKS', 'order_index': 8, 'is_system': False},
    {'key': 'target_date', 'label': 'TARGET DATE', 'order_index': 9, 'is_system': False},
    {'key': 'days_diff', 'label': 'DAYS DIFF', 'order_index': 10, 'is_system': False},
    {'key': 'history_milestone', 'label': 'HISTORY / MILESTONE', 'order_index': 11, 'is_system': False},
    {'key': 'actions', 'label': 'ACTIONS', 'order_index': 12, 'is_system': True},
]


class TableColumnConfig(models.Model):
    key = models.CharField(max_length=100, unique=True, verbose_name="Column Key")
    label = models.CharField(max_length=150, verbose_name="Header Name")
    is_visible = models.BooleanField(default=True, verbose_name="Is Visible")
    order_index = models.IntegerField(default=0, verbose_name="Order")
    is_custom = models.BooleanField(default=False, verbose_name="Is Custom Column")
    is_system = models.BooleanField(default=False, verbose_name="Is Core System Column")

    class Meta:
        ordering = ['order_index', 'id']
        verbose_name = "Table Column Configuration"
        verbose_name_plural = "Table Column Configurations"

    def __str__(self):
        return f"{self.label} ({self.key}) - {'Visible' if self.is_visible else 'Hidden'}"

    @classmethod
    def get_columns_map(cls):
        """
        Returns a dict of all columns keyed by their key.
        Creates default columns if table is empty.
        """
        if not cls.objects.exists():
            cls.reset_to_defaults()
        return {col.key: col for col in cls.objects.all().order_by('order_index')}

    @classmethod
    def reset_to_defaults(cls):
        """Resets all standard columns to their default headers."""
        cls.objects.filter(is_custom=False).delete()
        for col_data in DEFAULT_COLUMNS:
            cls.objects.update_or_create(
                key=col_data['key'],
                defaults={
                    'label': col_data['label'],
                    'order_index': col_data['order_index'],
                    'is_system': col_data.get('is_system', False),
                    'is_visible': True,
                    'is_custom': False,
                }
            )


class StatusColorConfig(models.Model):
    status_key = models.CharField(max_length=50, unique=True, verbose_name="Status Key")
    label = models.CharField(max_length=100, verbose_name="Status Label")
    hex_color = models.CharField(max_length=25, default='#ffffff', verbose_name="Row Background Hex Color")
    border_color = models.CharField(max_length=25, default='#84cc16', verbose_name="Border Edge Hex Color")
    is_enabled = models.BooleanField(default=True, verbose_name="Enable Row Highlight")

    class Meta:
        verbose_name = "Status Color Configuration"
        verbose_name_plural = "Status Color Configurations"

    def __str__(self):
        return f"{self.label}: {self.hex_color}"

    DEFAULT_CONFIGS = {
        'working': {
            'label': 'Working',
            'hex_color': '#f0fdf4',
            'border_color': '#22c55e',
            'is_enabled': False,
        },
        'no_data': {
            'label': 'No data',
            'hex_color': '#fff1f2',
            'border_color': '#f43f5e',
            'is_enabled': True,
        },
        'finished': {
            'label': 'Finished',
            'hex_color': '#f8fafc',
            'border_color': '#94a3b8',
            'is_enabled': False,
        },
        'pending': {
            'label': 'Pending',
            'hex_color': '#fefce8',
            'border_color': '#eab308',
            'is_enabled': True,
        },
        'hold': {
            'label': 'On Hold',
            'hex_color': '#f7fee7',
            'border_color': '#84cc16',
            'is_enabled': True,
        },
        'overdue': {
            'label': 'Overdue (Target Date Passed)',
            'hex_color': '#fff1f2',
            'border_color': '#f43f5e',
            'is_enabled': True,
        },
    }

    @classmethod
    def get_colors_map(cls):
        for key, conf in cls.DEFAULT_CONFIGS.items():
            cls.objects.get_or_create(
                status_key=key,
                defaults={
                    'label': conf['label'],
                    'hex_color': conf['hex_color'],
                    'border_color': conf['border_color'],
                    'is_enabled': conf['is_enabled'],
                }
            )
        existing = {item.status_key: item for item in cls.objects.all()}
        result = {}
        for key in cls.DEFAULT_CONFIGS.keys():
            if key in existing:
                result[key] = existing[key]
        for key, val in existing.items():
            if key not in result:
                result[key] = val
        return result

    @classmethod
    def reset_to_defaults(cls):
        for key, conf in cls.DEFAULT_CONFIGS.items():
            cls.objects.update_or_create(
                status_key=key,
                defaults={
                    'label': conf['label'],
                    'hex_color': conf['hex_color'],
                    'border_color': conf['border_color'],
                    'is_enabled': conf['is_enabled'],
                }
            )


class StatusOption(models.Model):
    key = models.CharField(max_length=50, unique=True, verbose_name="Status Key / ID")
    label = models.CharField(max_length=100, verbose_name="Status Name / Label")
    badge_bg = models.CharField(max_length=25, default='#e2e3e5', verbose_name="Badge Background Color")
    badge_color = models.CharField(max_length=25, default='#333333', verbose_name="Badge Text Color")
    row_bg = models.CharField(max_length=25, default='#ffffff', verbose_name="Row Highlight Color")
    row_border = models.CharField(max_length=25, default='#84cc16', verbose_name="Row Border Color")
    is_row_highlight = models.BooleanField(default=False, verbose_name="Enable Row Highlight")
    order_index = models.IntegerField(default=0, verbose_name="Order")
    is_system = models.BooleanField(default=False, verbose_name="Is Core System Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index', 'id']
        verbose_name = "Status Option"
        verbose_name_plural = "Status Options"

    def __str__(self):
        return f"{self.label} ({self.key})"

    DEFAULT_STATUSES = [
        {
            'key': 'working',
            'label': 'Working',
            'badge_bg': '#d1e7dd',
            'badge_color': '#0f5132',
            'row_bg': '#f0fdf4',
            'row_border': '#22c55e',
            'is_row_highlight': False,
            'order_index': 1,
            'is_system': True,
        },
        {
            'key': 'pending',
            'label': 'Pending',
            'badge_bg': '#fff3cd',
            'badge_color': '#664d03',
            'row_bg': '#fefce8',
            'row_border': '#eab308',
            'is_row_highlight': True,
            'order_index': 2,
            'is_system': True,
        },
        {
            'key': 'hold',
            'label': 'On Hold',
            'badge_bg': '#f7fee7',
            'badge_color': '#3f6212',
            'row_bg': '#f7fee7',
            'row_border': '#84cc16',
            'is_row_highlight': True,
            'order_index': 3,
            'is_system': True,
        },
        {
            'key': 'finished',
            'label': 'Finished',
            'badge_bg': '#e2e3e5',
            'badge_color': '#41464b',
            'row_bg': '#f8fafc',
            'row_border': '#94a3b8',
            'is_row_highlight': False,
            'order_index': 4,
            'is_system': True,
        },
        {
            'key': 'no_data',
            'label': 'No data',
            'badge_bg': '#f8d7da',
            'badge_color': '#842029',
            'row_bg': '#fff1f2',
            'row_border': '#f43f5e',
            'is_row_highlight': True,
            'order_index': 5,
            'is_system': True,
        },
    ]

    @classmethod
    def get_all_statuses(cls):
        if not cls.objects.exists():
            cls.reset_to_defaults()
        return list(cls.objects.all().order_by('order_index', 'id'))

    @classmethod
    def get_status_choices(cls):
        statuses = cls.get_all_statuses()
        return [(s.key, s.label) for s in statuses]

    @classmethod
    def reset_to_defaults(cls):
        for data in cls.DEFAULT_STATUSES:
            cls.objects.update_or_create(
                key=data['key'],
                defaults=data
            )
        # Also sync StatusColorConfig for colors modal
        for data in cls.DEFAULT_STATUSES:
            StatusColorConfig.objects.update_or_create(
                status_key=data['key'],
                defaults={
                    'label': data['label'],
                    'hex_color': data['row_bg'],
                    'border_color': data['row_border'],
                    'is_enabled': data['is_row_highlight'],
                }
            )

