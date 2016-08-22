from django.db import models
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Voivodeship(models.Model):
    class Meta:
        verbose_name = "Województwo"
        verbose_name_plural = "Województwa"
    name = models.CharField(max_length=30, verbose_name="Nazwa województwa")
    code = models.CharField(max_length=5, verbose_name="Kod według ISO 3166-2:PL", null=True, blank=True)

    @property
    def results(self):
        self.municipality_set.values('candidateresult__candidate').annotate()

    def __str__(self):
        return "Województwo " + self.name


class MunicipalityType(models.Model):
    class Meta:
        verbose_name = "Typ gminy"
        verbose_name_plural = "Typy gmin"
    name = models.CharField(max_length=30, verbose_name="Typ gminy")

    def __str__(self):
        return self.name


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

    def __str__(self):
        return "Gmina " + self.name

    @property
    def filled(self):
        return None not in [self.dwellers, self.entitled, self.issued_cards, self.votes, self.valid_votes] \
               and CandidateResult.objects.filter(municipality=self).count() == Candidate.objects.count()

    # TODO: Refactor underlying SQL
    @property
    def results(self):
        res = list()
        if self.filled:
            cands = Candidate.objects.all().order_by('surname')
            for cand in cands:
                cvotes = CandidateResult.objects.get(municipality=self, candidate=cand).votes
                res.append((cand, cvotes, round(cvotes/self.votes*100, 2)))
        return res



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


class CandidateResult(models.Model):
    class Meta:
        verbose_name = "Wynik kandydata"
        verbose_name_plural = "Wyniki kandydatów"
    municipality = models.ForeignKey(Municipality, null=True, verbose_name="Gmina")
    candidate = models.ForeignKey(Candidate, verbose_name="Kandydat")
    votes = models.PositiveIntegerField(verbose_name="Liczba głosów")

    def __str__(self):
        return "Wynik " + str(self.candidate) + " w gminie " + self.municipality.name + ": " + str(self.votes)
