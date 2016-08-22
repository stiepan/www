from django.core.management.base import BaseCommand, CommandError
from django.contrib.admin.models import LogEntry
from django.db import transaction
from django.db.utils import IntegrityError
from prezydent.models import CandidateResult, Municipality, MunicipalityType, Voivodeship, Candidate
from datetime import datetime


class Command(BaseCommand):
    help = 'Removes current data from basic models and sets some default as an example'

    def add_arguments(self, parser):
        parser.add_argument(
            '--municipalities',
            action='store_true',
            dest='example',
            default=False,
            help='Sets example municipalities with results',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        models = [LogEntry, CandidateResult, Municipality, MunicipalityType, Voivodeship, Candidate]
        try:
            for model in models:
                model.objects.all().delete()
        except Exception as e:
            raise CommandError("Could not remove current data from %s model" % str(model), e) from e
        for (fn, sn, dt) in [("Lech Aleksander", "Kaczyński", "18 06 1949"),
                             ("Donald Franciszek", "Tusk", "22 04 1957")]:
            candidate = Candidate(first_name=fn, surname=sn,
                               date_of_birth=datetime.strptime(dt, "%d %m %Y"))
            candidate.save()
        for type in ["wieś", "miasto", "statki", "zagranica"]:
            ntype = MunicipalityType(name=type)
            ntype.save()
        for (code, name) in [("PL-DS", "dolnośląskie"), ("PL-KP", "kujawsko-pomorskie"), ("PL-LU", "lubelskie"), ("PL-LB", "lubuskie"), ("PL-LD", "łódzkie"), ("PL-MA", "małopolskie"), ("PL-MZ", "mazowieckie"), ("PL-OP", "opolskie"), ("PL-PK", "podkarpackie"), ("PL-PD", "podlaskie"), ("PL-PM", "pomorskie"), ("PL-SL", "śląskie"), ("PL-SK", "świętokrzyskie"), ("PL-WN", "warmińsko-mazurskie"), ("PL-WP", "wielkopolskie"), ("PL-ZP", "zachodniopomorskie")]:
            voiv = Voivodeship(name=name, code=code)
            voiv.save()
        if options['example']:
            from prezydent.management.municipalities import municipalities
            candidates = Candidate.objects.all().order_by('surname')
            for (vcode, units) in municipalities:
                for (name, type, dwellers, entitled, issued_cards, votes, valid_votes, fst, snd) in units:
                    type = MunicipalityType.objects.get(name=type)
                    voivodeship = Voivodeship.objects.get(code=vcode)
                    try:
                        with transaction.atomic():
                            mun = Municipality(type=type, voivodeship=voivodeship, name=name, dwellers=dwellers,
                                       entitled=entitled, issued_cards=issued_cards, votes=votes, valid_votes=valid_votes)
                            print (mun)
                            mun.save()
                        res = CandidateResult(municipality=mun, candidate=candidates[0], votes=fst)
                        res.save()
                        res = CandidateResult(municipality=mun, candidate=candidates[1], votes=snd)
                        res.save()
                    except IntegrityError:
                        print ("Pomijam gminę %s o tej samej nazwie i type w tym samym województwie, "
                               "co już istniejąca gmina" % name)