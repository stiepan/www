from django.db import models
from django.utils import timezone as datetime
from dateutil.relativedelta import relativedelta


class Voivodeship(models.Model):
    class Meta:
        verbose_name = "Województwo"
        verbose_name_plural = "Województwa"
    name = models.CharField(max_length=30, verbose_name="Nazwa województwa")
    code = models.CharField(max_length=5, verbose_name="Kod według ISO 3166-2:PL", null=True, blank=True)

    @property
    def results(self):
        cands = self.municipality_set.values('candidateresult__candidate',
                                             'candidateresult__candidate__first_name',
                                             'candidateresult__candidate__surname')\
            .annotate(models.Sum('candidateresult__votes'))\
            .order_by('candidateresult__candidate__surname')
        all = self.municipality_set.aggregate(models.Sum('valid_votes'))
        valid = all['valid_votes__sum']
        res = list()
        for cand in cands:
            if cand['candidateresult__candidate'] is not None and valid is not None:
                res.append({
                    'id': cand['candidateresult__candidate'],
                    'first_name': cand['candidateresult__candidate__first_name'],
                    'surname': cand['candidateresult__candidate__surname'],
                    'votes': cand['candidateresult__votes__sum'],
                    'percentage': round(cand['candidateresult__votes__sum'] / valid * 100, 2)
                })
        return {'valid_votes': valid, 'candidates': res}

    def __str__(self):
        return "Województwo " + self.name


class MunicipalityType(models.Model):
    class Meta:
        verbose_name = "Typ gminy"
        verbose_name_plural = "Typy gmin"
    name = models.CharField(max_length=30, verbose_name="Typ gminy")

    def __str__(self):
        return self.name

    @staticmethod
    def results_in_range(atleast, atmost, types=None):
        municipalities = Municipality.objects.filter(type__name__in=types)\
            .filter(dwellers__gte=atleast, dwellers__lte=atmost)
        cands = municipalities.values('candidateresult__candidate', 'candidateresult__candidate__first_name',
                                      'candidateresult__candidate__surname')\
            .annotate(models.Sum('candidateresult__votes'))\
            .order_by('candidateresult__candidate__surname')
        all = municipalities.aggregate(models.Sum('valid_votes'), models.Sum('dwellers'), models.Sum('entitled'),
                                       models.Sum('issued_cards'), models.Sum('votes'))
        valid = all['valid_votes__sum']
        res = list()
        for cand in cands:
            if cand['candidateresult__candidate'] is not None:
                res.append({
                    'id': cand['candidateresult__candidate'],
                    'first_name': cand['candidateresult__candidate__first_name'],
                    'surname': cand['candidateresult__candidate__surname'],
                    'votes': cand['candidateresult__votes__sum'],
                    'percentage': round(cand['candidateresult__votes__sum'] / valid * 100, 2)
                })
        return {'valid_votes': valid, 'dwellers': all['dwellers__sum'], 'entitled': all['entitled__sum'],
                'issued_cards': all['issued_cards__sum'], 'votes': all['votes__sum'], 'candidates': res}

    @property
    def results(self):
        return MunicipalityType.results_in_range(0, 100000000, [self.name])


class Municipality(models.Model):
    class Meta:
        verbose_name = "Gmina"
        verbose_name_plural = "Gminy"
        unique_together = ('type', 'name', 'voivodeship')
    type = models.ForeignKey(MunicipalityType, on_delete=models.PROTECT, verbose_name="Typ gminy")
    voivodeship = models.ForeignKey(Voivodeship, on_delete=models.PROTECT, null=True, blank=True,
                                    verbose_name="Województwo")
    name = models.CharField(max_length=100, verbose_name="Nazwa gminy")
    dwellers = models.PositiveIntegerField(verbose_name="Liczba mieszkańców", null=True, blank=True)
    entitled = models.PositiveIntegerField(verbose_name="Liczba uprawnionych do głosowania", null=True, blank=True)
    issued_cards = models.PositiveIntegerField(verbose_name="Liczba wydanych kart do głosowania", null=True, blank=True)
    votes = models.PositiveIntegerField(verbose_name="Liczba oddanych głosów", null=True, blank=True)
    valid_votes = models.PositiveIntegerField(verbose_name="Liczba ważnych głosów", null=True, blank=True)
    last_modification = models.DateTimeField(default=datetime.now, blank=True,
                                             verbose_name="Ostatnio modyfikowany")

    def __str__(self):
        return "Gmina " + self.name

    @property
    def filled(self):
        return None not in [self.dwellers, self.entitled, self.issued_cards, self.votes, self.valid_votes] \
               and CandidateResult.objects.filter(municipality=self).count() == Candidate.objects.count()

    @property
    def results(self):
        res = list()
        if self.filled:
            cands = self.candidateresult_set.values('candidate', 'candidate__first_name', 'candidate__surname')\
                .annotate(models.Sum('votes')).order_by('candidate__surname')
            valid = self.valid_votes
            for cand in cands:
                if cand['candidate'] is not None:
                    res.append({
                        'id': cand['candidate'],
                        'votes': cand['votes__sum'],
                        'percentage': round(cand['votes__sum'] / valid * 100, 2)
                    })
            return {'valid_votes': valid, 'candidates': res}



class Candidate(models.Model):
    class Meta:
        verbose_name = "Kandydat"
        verbose_name_plural = "Kandydaci"
    first_name = models.CharField(max_length=100, verbose_name="Imiona")
    surname = models.CharField(max_length=100, verbose_name="Nazwisko")
    date_of_birth = models.DateField(verbose_name="Data urodzenia")
    _version = models.IntegerField(default=0)

    def __str__(self):
        return self.first_name + " " + self.surname

    @property
    def age(self):
        return relativedelta(datetime.now().date(), self.date_of_birth).years

    @property
    def results(self):
        candv = self.candidateresult_set.aggregate(models.Sum('votes'))
        all = Municipality.objects.all().aggregate(models.Sum('valid_votes'))
        if candv is None:
            candv = 0;
        if all is None or all['valid_votes__sum'] is None:
            return None
        return {
            'for_all': all['valid_votes__sum'],
            'votes': candv['votes__sum'],
            'percentage': round(candv['votes__sum'] / all['valid_votes__sum'] * 100, 2),
        }


class CandidateResult(models.Model):
    class Meta:
        verbose_name = "Wynik kandydata"
        verbose_name_plural = "Wyniki kandydatów"
    municipality = models.ForeignKey(Municipality, null=True, verbose_name="Gmina")
    candidate = models.ForeignKey(Candidate, verbose_name="Kandydat")
    votes = models.PositiveIntegerField(verbose_name="Liczba głosów")

    def __str__(self):
        return "Wynik " + str(self.candidate) + " w gminie " + self.municipality.name + ": " + str(self.votes)
