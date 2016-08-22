from django.shortcuts import render
from prezydent.models import Voivodeship, Candidate, MunicipalityType
from django.db.models import Sum


def prezydent(request):
    infinity = 100000000
    exter = ['statki', 'zagranica']
    candidates = []
    cands = Candidate.objects.all().order_by('surname').values('first_name', 'surname')
    for cand in cands:
        candidates.append(list(cand.values()))
    ships_and_abroad = ('statki i zagranica', MunicipalityType.results_in_range(0, infinity, exter))
    thresholds = [5000, 10000, 20000, 50000, 100000, 200000, 500000, infinity]
    quantile = [ships_and_abroad]
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
        quantile.append((name, MunicipalityType.results_in_range(st, end, ['wieś', 'miasto'])))
    overall = MunicipalityType.results_in_range(0, infinity,
                                                MunicipalityType.objects.all().values_list('name', flat=True))
    overall_pl = MunicipalityType.results_in_range(0, infinity, MunicipalityType.objects.exclude(name__in=exter)
                                                   .values_list('name', flat=True))
    density = None
    if overall_pl.get('dwellers'):
        density = round(overall_pl.get('dwellers') / 312685)
    return render(request, 'prezydent.html', {
        'voivodeships': Voivodeship.objects.all(),
        'overall': overall,
        'voiv_overall': overall_pl,
        'density': density,
        'candidates': candidates,
        'types': MunicipalityType.objects.filter(municipality__isnull=False,
                                                 municipality__candidateresult__isnull=False).distinct(),
        'quantile': quantile

    })


#def handle_500(request):
#    template = loader.get_template('500.html')
#    back = request.META['HTTP_REFERER']
#    return HttpResponseServerError(template.render(Context({'prev': back})))