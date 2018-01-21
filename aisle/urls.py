from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload),
    #path('upload/', views.upload),
    path('viewresult/', views.viewresult),
]