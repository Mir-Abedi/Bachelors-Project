from django import forms
from webpages.models import WebPage

class WebPageForm(forms.ModelForm):
    class Meta:
        model = WebPage
        fields = ['url']
