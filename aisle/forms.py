from django import forms
from .models import Input

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Input
        fields = ('description', 'fc_code', 'user_id', 'log_file', 'aisle_file', 'bay_to_aisle_file')