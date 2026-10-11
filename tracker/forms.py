from django import forms
from .models import ProcessItem

class ProcessItemForm(forms.ModelForm):
    class Meta:
        model = ProcessItem
        fields = [
            'client_name',
            'is_red_client',
            'status',
            'lot_progress',
            'current_lot',
            'total_lot',
            'completed_count',
            'pending_count',
            'ready_count',
            'notes',
            'notes_is_red',
            'target_date',
            'history_milestone',
            'row_highlight_color',
            'is_priority',
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Solitaire Diamond / Mauni'}),
            'is_red_client': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_priority': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'lot_progress': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 24|75 or Finished'}),
            'current_lot': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 24'}),
            'total_lot': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 75'}),
            'completed_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'pending_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'ready_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks / Notes (English or Gujarati)'}),
            'notes_is_red': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'history_milestone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 23-05-2026 (Till lot 19)'}),
            'row_highlight_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#f7fee7'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import StatusOption
        choices = StatusOption.get_status_choices()
        self.fields['status'].choices = choices
