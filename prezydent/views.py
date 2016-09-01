from django.views.generic import TemplateView, View
from django.contrib.auth import logout, authenticate, login
from prezydent.models import Candidate, Voivodeship, MunicipalityType, Municipality, CandidateResult
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from prezydent.admin import MultiThreadRaceSave
from django.http import JsonResponse
from prezydent.forms import MunicipalityForm
import json
from collections import OrderedDict
import dateutil.parser

infinity = 100000000
exter = ['statki', 'zagranica']
within_country = ['wieś', 'miasto']

STATUS_OK = 'OK'
STATUS_ERROR = 'ERROR'


class Main(TemplateView):
    template_name = 'prezydent.html'


class Results(View):

    def get(self, request):
        types = MunicipalityType.objects.all()
        voivs = Voivodeship.objects.all()
        cands = Candidate.objects.all()
        voivs = [{'name': voiv.name, 'id': voiv.code, 'results': voiv.results} for voiv in voivs]
        candidates = [{'first_name': cand.first_name, 'surname': cand.surname, 'results': cand.results}
                      for cand in cands]
        types = [{'name': type.name, 'results': type.results, 'id': type.id} for type in types]
        thresholds = [5000, 10000, 20000, 50000, 100000, 200000, 500000, infinity]
        quantile = []
        end = 0
        for i, step in enumerate(thresholds):
            st = end
            end = step
            if i == 0:
                name = "do " + str(end)
            elif i == len(thresholds) - 1:
                name = "pow. " + str(st)
            else:
                name = "od " + str(st) + " do " + str(end)
            quantile.append({'name': name, 'id': str(st) + '_' + str(end),
                             'results': MunicipalityType.results_in_range(st + 1, end, within_country)})
        return JsonResponse({'types': types, 'quantile': quantile, 'candidates': candidates, 'voivs': voivs})

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        return super(Results, self).dispatch(request, *args, *kwargs)


class Detailed(View):

    def get(self, request, type, typepar, optpar=None):
        accepted = {
            'voiv': lambda : Municipality.objects.filter(voivodeship__code=typepar),
            'type': lambda : Municipality.objects.filter(type__id=typepar),
            'quant': lambda : Municipality.objects.filter(dwellers__gte=typepar, dwellers__lte=optpar)
        }
        lst = accepted.get(type)
        if lst is None:
            return JsonResponse({'status': 'Incorrect type passed'})
        ms = [{'name': m.name, 'results': m.results, 'id': m.id} for m in lst() if m.filled]
        return JsonResponse({'status': 'OK', 'muni': ms})


class Login(View):

    def get(self, request):
        if request.user.is_authenticated():
            return JsonResponse({'status': 'loggedin','username': request.user.username})
        else:
            return JsonResponse({'status': 'anonymous'})

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        if data.get('logout'):
            logout(request)
        else:
            username = data.get('username')
            password = data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
            else:
                return JsonResponse({'status': 'unrecognized'})
        return self.get(request)

class Muni(View):
    
    def get(self, request, id=None):
        muni = Municipality.objects.filter(id=id)
        if len(muni) != 1:
            return JsonResponse({'status': 'Dla wybranej gminy nie ma żadnych danych.'})
        muni = muni.first()
        if not muni.filled:
            return JsonResponse({'status': 'Wybrana gmina jest nieaktywna.'})
        else:
            attrs = [(attr, {'val': getattr(muni, attr), 'name': Municipality._meta.get_field(attr)
              .verbose_name.title()}) for attr in ['dwellers', 'entitled', 'issued_cards', 'votes',
                                                   'valid_votes', 'last_modification', 'counter']]
            cands = CandidateResult.objects.filter(municipality=muni)\
                .values_list('candidate__surname', 'candidate__first_name', 'candidate__id', 'votes')
            for cand in cands:
                attrs.append(('candidate_' + str(cand[2]), {'val': str(cand[3]), 'name': cand[0] + ' ' + cand[1]}))
            return JsonResponse({'status': 'OK', 'attrs': OrderedDict(attrs)})

    def post(self, request):
        if not request.user.is_authenticated():
            return JsonResponse({"status": "Nie masz uprawnień do wykonania tej czynności"})
        data = json.loads(request.body.decode('utf-8'))
        if data.get('last_modification'):
            data['last_modification'] = dateutil.parser.parse(data.get('last_modification'))
        mun = Municipality.objects.filter(id=data['id'])
        if (len(mun)) != 1:
            return JsonResponse({"status": "Wybrana gmina nie istnieje"})
        mun = mun.first()
        form = MunicipalityForm(data=data)
        if not form.is_valid():
            return JsonResponse({"status": "Nieprawidłowe dane."})
        try:
            form.save(mun)
        except MultiThreadRaceSave:
            return JsonResponse({"status": "Wystąpił błąd. Sprawdź czy dane nie zostały zmodyfikowane "
                                           "przez innego użytkownika."})
        return JsonResponse({'status': 'OK'})

# def handle_500(request):
#    template = loader.get_template('500.html')
#    back = request.META['HTTP_REFERER']
#    return HttpResponseServerError(template.render(Context({'prev': back})))
