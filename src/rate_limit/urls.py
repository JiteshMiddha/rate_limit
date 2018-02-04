from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^status/$', views.get_status, name='status'),
    url(r'^pay/$', views.initiate_payment, name='pay'),
]
