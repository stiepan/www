from django.contrib import admin
from django.db import transaction
from django import forms
from .models import Voivodeship, Municipality, MunicipalityType, Candidate, CandidateResult
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.contrib.messages import constants as message_constants
from django.shortcuts import HttpResponseRedirect
from django.db.models import Count, Max, F

admin.site.register(Voivodeship)
admin.site.register(MunicipalityType)


class MultiThreadRaceSave(Exception):
    pass


class MunicipalityForm(forms.ModelForm):

    class Meta:
        model = Municipality
        exclude = []

    _candidates_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._candidates_fields.clear()
        candidates = Candidate.objects.all().order_by('surname')
        for candidate in candidates:
            field_name =  "candidate_" + str(candidate.id)
            verbose_name = str(candidate)
            self.fields[field_name] = forms.IntegerField(label=verbose_name, min_value=0, required=False)
            instance = kwargs.get('instance')
            if instance:
                candidateresult = candidate.candidateresult_set.filter(municipality=instance)
                if candidateresult.count():
                    self.fields[field_name].initial = candidateresult.first().votes
            self._candidates_fields.append(field_name)

    def clean(self):
        if self.is_valid():
            name = self.cleaned_data['name']
            statistics_set = ['dwellers', 'entitled', 'issued_cards', 'votes', 'valid_votes']
            filled = list(map(lambda x : self.cleaned_data.get(x) is not None, statistics_set))
            if any(filled):
                if not all(filled):
                    raise forms.ValidationError("Sekcja nie może być częściowo pusta.")
                if sorted(statistics_set, key=lambda name : self.cleaned_data[name], reverse=True) != statistics_set:
                    raise forms.ValidationError("Wprowadzone statystyki są niepoprawne")
            filled_candidates = 0
            candidates_votes = 0
            for candidate_name in self._candidates_fields:
                candidate_votes = self.cleaned_data.get(candidate_name)
                if candidate_votes is not None:
                    filled_candidates += 1
                    candidates_votes += candidate_votes
            if filled_candidates == len(self._candidates_fields):
                valid_votes = self.cleaned_data.get('valid_votes')
                if valid_votes is None or candidates_votes != valid_votes:
                    raise forms.ValidationError("Głosy ważne powinny być sumą głosów oddanych na kandydatów.")
            # Don't really bother multi-thread environment as model enforces uniqueness of the name
            # in case of the race user would simply see 500 server error
            existing = Municipality.objects.filter(name=name, type=self.cleaned_data['type'],
                                                   voivodeship=self.cleaned_data['voivodeship'])
            if self.instance is not None:
                existing = existing.exclude(id=self.instance.id)
            if existing.count():
                raise forms.ValidationError("Gmina o takiej nazwie już istnieje. Edytuj ją lub usuń.")

    def save(self, commit=True):
        municipality = super().save(commit)
        for candidate_name in self._candidates_fields:
            candidate_id = candidate_name.split('_')[1]
            candidate_votes = self.cleaned_data.get(candidate_name)
            if candidate_votes is not None:
                municipality.save()
                result, created = CandidateResult.objects.get_or_create(municipality=municipality,
                                                                        candidate_id=candidate_id,
                                                                        defaults={'votes': candidate_votes})
                if not created:
                    result.votes = candidate_votes
                    result.save()
        return municipality


class Filled(admin.SimpleListFilter):
    title = "Wypełniona i uwzględniana"
    parameter_name = 'filled'

    def lookups(self, request, model_admin):
        return (
            ('True', 'tak'),
            ('False', 'nie'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        candsn = Candidate.objects.all().count()
        first = queryset.annotate(cands = Count('candidateresult'))
        if self.value() == 'True':
            return first.filter(cands=candsn, dwellers__isnull=False, entitled__isnull=False, issued_cards__isnull=False,
                                votes__isnull=False, valid_votes__isnull=False)
        return first.exclude(cands=candsn, dwellers__isnull=False, entitled__isnull=False, issued_cards__isnull=False,
                            votes__isnull=False, valid_votes__isnull=False)


class Winner(admin.SimpleListFilter):
    title = "Zwycięzca"
    parameter_name = 'winner'

    def lookups(self, request, model_admin):
        opts = list()
        cands = Candidate.objects.all().order_by('surname')
        for cand in cands:
            opts.append((cand.id, str(cand)))
        return opts

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.annotate(winner_vts=Max('candidateresult__votes'))\
            .filter(candidateresult__candidate__id=self.value(), candidateresult__votes=F('winner_vts'),)


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    form = MunicipalityForm
    _error_message = ""
    list_display = ('name', 'type', 'voivodeship', 'filled')
    list_filter = [Filled, Winner, 'type', 'voivodeship']
    search_fields = ['name']

    fieldsets = (
        ('Dane gminy',
         {'fields': ('type', 'voivodeship', 'name')}
         ),
        ('Statystyki głosowania:',
         {'fields': ('dwellers', 'entitled', 'issued_cards', 'votes', 'valid_votes'),
          'description': 'Możesz uzupełnić tę sekcję później'}
         ),
        ('Liczba głosów na poszczególnych kandydatów',
         {'fields': form._candidates_fields,
          'description': 'Możesz uzupełnić tę sekcję później'})
    )

    def has_add_permission(self, request):
        return Candidate.objects.all().count() == 2 and super().has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return Candidate.objects.all().count() == 2 and super().has_module_permission(request)

    def get_form(self, request, obj=None, **kwargs):
        kwargs['exclude'] = self.form._candidates_fields
        return super().get_form(request, obj, **kwargs)

    def filled(self, obj):
        return obj.filled
    filled.short_description = "Wypełniona i uwzględniana"
    filled.boolean = True


class CandidateForm(forms.ModelForm):

    class Meta:
        model = Candidate
        exclude = ['_version']

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        first_name = first_name.title()
        return first_name

    def clean_surname(self):
        surname = self.cleaned_data['surname']
        surname = surname.title()
        return surname

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data['date_of_birth']
        if datetime.now().date() - relativedelta(years=35) < date_of_birth:
            raise forms.ValidationError("Kandydat nie spełnia kryterium wieku")
        return date_of_birth


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    form = CandidateForm
    _error_message = ""

    def has_add_permission(self, request):
        return Candidate.objects.all().count() < 2 and super().has_add_permission(request)

    @transaction.atomic
    def safe_save_model(self, request, obj, form, change):
        n_candidates = Candidate.objects.all().count()
        version = 0
        if n_candidates > 0:
            version = Candidate.objects.all().first()._version
        obj._version = version
        super().save_model(request, obj, form, change)
        # If adding new Candidate
        if not change:
            updated = Candidate.objects.filter(_version=version).update(_version=version + 1)
            if updated != Candidate.objects.all().count() or updated > 2:
                # As just a few steps before it was stated there is less than two Candidates
                raise MultiThreadRaceSave

    # It's not actually idiomatic for django to deny to save data in save model method
    # but it's virtually only way to prevent multiple save in multi thread environment
    # using no more than transactions on methods.
    def save_model(self, request, obj, form, change):
        n_candidates = Candidate.objects.all().count()
        if not change and n_candidates >= 2:
            self._error_message = "Istnieją już dwaj kandydaci"
        else:
            try:
                self.safe_save_model(request, obj, form, change)
            except MultiThreadRaceSave:
                self._error_message = "Operacja nie powiodła się, ponieważ inny użytkownik próbował jednocześnie " \
                                      "dodać kandydata, co mogło doprowadzić do przekroczenia liczby kandydatów."

    def response_add(self, request, obj, post_url_continue=None):
        if self._error_message == "":
            if Candidate.objects.all().count() >= 2:
                self.message_user(request, "Pomyślnie dodano kandydata. Osiągnięto maksymalną liczbę kandydatów.",
                                  message_constants.SUCCESS)
                return self.response_post_save_add(request, obj)
            return super().response_add(request, obj, post_url_continue)
        else:
            self.message_user(request, self._error_message, level=message_constants.ERROR)
            return HttpResponseRedirect(request.path)