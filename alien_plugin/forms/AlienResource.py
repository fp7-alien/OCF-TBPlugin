
from django import forms
from alien_plugin.models.AlienResource import AlienResource as AlienResourceModel


class AlienResource(forms.models.ModelForm):

    connections = forms.ModelMultipleChoiceField(queryset = AlienResourceModel.objects.all().order_by("name"),
#                                                 widget = forms.SelectMultiple())
                                                 widget = forms.CheckboxSelectMultiple())

    class Meta:
        fields = ["name", "connections"]
        model = AlienResourceModel

    def __init__(self, *args, **kwargs):
        super(AlienResource, self).__init__(*args,**kwargs)
        try:
            # Do not allow links to self
            current_dpid = kwargs['instance'].dpid
            self.fields['connections'].queryset = AlienResourceModel.objects.exclude(dpid = current_dpid).order_by("dpid")
        except:
            pass

    def clean_name(self):
        #validate_resource_name(self.cleaned_data['name'])
        return self.cleaned_data['name']



