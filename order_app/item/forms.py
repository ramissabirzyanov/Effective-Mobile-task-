from django.forms import ModelForm
from .models import Item


class ItemCreateForm(ModelForm):

    class Meta:
        model = Item
        fields = ['name', 'price']