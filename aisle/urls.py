from django.urls import path
from . import views

urlpatterns = [
	path('', views.browse),
	path('browse/', views.browse),
	path('upload/', views.upload),
	path('result/<int:input_id>', views.result),    
]