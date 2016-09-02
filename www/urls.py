"""www URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from prezydent import views

#handler500 = 'prezydent.views.handle_500'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.Main.as_view()),
    url(r'^results/$', views.Results.as_view()),
    url(r'^results/detailed/(\w+),([0-9]+)_([0-9]+)$', views.Detailed.as_view()),
    url(r'^results/detailed/(\w+),([0-9, \w, \-]+)$', views.Detailed.as_view(), name='details'),
    url(r'^login/$', views.Login.as_view()),
    url(r'^municipality/$', views.Muni.as_view()),
    url(r'^municipality/([0-9]+)$', views.Muni.as_view(), name='muni')
]