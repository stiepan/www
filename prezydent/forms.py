from django import forms
from prezydent.models import Candidate, Municipality, CandidateResult
from django.db import transaction
from prezydent.admin import MultiThreadRaceSave
from datetime import datetime
from django.db.models import F

class MunicipalityForm(forms.Form):

    _candidates_fields = []

    dwellers = forms.IntegerField()
    entitled = forms.IntegerField()
    issued_cards = forms.IntegerField()
    votes = forms.IntegerField()
    valid_votes = forms.IntegerField()
    last_modification = forms.DateTimeField(input_formats=['%c'])
    counter = forms.IntegerField()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._candidates_fields.clear()
        candidates = Candidate.objects.all().order_by('surname')
        for candidate in candidates:
            field_name =  "candidate_" + str(candidate.id)
            verbose_name = str(candidate)
            self.fields[field_name] = forms.IntegerField(label=verbose_name, min_value=0, required=True)
            self._candidates_fields.append(field_name)

    @transaction.atomic
    def save(self, inst):
        for candidate_name in self._candidates_fields:
            candidate_id = candidate_name.split('_')[1]
            candidate_votes = self.cleaned_data[candidate_name]
            CandidateResult.objects.filter(candidate__id=candidate_id, municipality=inst).update(votes=candidate_votes)
        if self.cleaned_data['last_modification'].replace(microsecond=0)\
            != inst.last_modification.replace(microsecond=0):
            raise MultiThreadRaceSave
        upds = Municipality.objects.filter(id=inst.id, counter=self.cleaned_data['counter'])\
            .update(dwellers=self.cleaned_data['dwellers'], entitled=self.cleaned_data['entitled'],
                   issued_cards=self.cleaned_data['issued_cards'], votes=self.cleaned_data['votes'],
                   valid_votes=self.cleaned_data['valid_votes'], last_modification=datetime.now(),
                    counter = F('counter') + 1)
        if upds != 1:
            raise MultiThreadRaceSave

