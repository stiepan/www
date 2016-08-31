from django import forms
from prezydent.models import Candidate, Municipality, CandidateResult
from django.db import transaction
from prezydent.admin import MultiThreadRaceSave
from django.utils import timezone


class MunicipalityForm(forms.Form):

    _candidates_fields = []

    dwellers = forms.IntegerField()
    entitled = forms.IntegerField()
    issued_cards = forms.IntegerField()
    votes = forms.IntegerField()
    valid_votes = forms.IntegerField()
    last_modification = forms.DateTimeField()


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
        mun = Municipality.objects.filter(id=inst.id, last_modification=self.cleaned_data['last_modification'])
        if len(mun) != 1:
            raise MultiThreadRaceSave
        for candidate_name in self._candidates_fields:
            print ("xDD")
            candidate_id = candidate_name.split('_')[1]
            candidate_votes = self.cleaned_data[candidate_name]
            CandidateResult.objects.filter(candidate__id=candidate_id, municipality=mun.first()).update(votes=candidate_votes)
        upds = mun.update(dwellers=self.cleaned_data['dwellers'], entitled=self.cleaned_data['entitled'],
                   issued_cards=self.cleaned_data['issued_cards'], votes=self.cleaned_data['votes'],
                   valid_votes=self.cleaned_data['valid_votes'], last_modification=timezone.now())
        if upds != 1:
            raise MultiThreadRaceSave

