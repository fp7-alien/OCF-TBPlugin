
from django import forms
from alien_plugin.models import AlienResourceAggregate as AlienResourceAggregateModel

class AlienResourceAggregate(forms.ModelForm):
    '''
    A form to create and edit AlienResource Aggregates.
    '''

    sync_resources = forms.BooleanField(label = "Sync resources?", initial = True, required = False)

    class Meta:
        model = AlienResourceAggregateModel
        exclude = ['client', 'owner', 'users', 'available']

