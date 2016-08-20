from django.shortcuts import render


def prezydent(request):
    return render(request, 'prezydent.html')


#def handle_500(request):
#    template = loader.get_template('500.html')
#    back = request.META['HTTP_REFERER']
#    return HttpResponseServerError(template.render(Context({'prev': back})))