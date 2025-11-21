from django.urls import path
from . import views

app_name = 'kladez_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('works/', views.completed_works, name='completed_works'),
    path('car-models/', views.car_models_directory, name='car_models_directory'),
    path('repair-types/', views.repair_types_directory, name='repair_types_directory'),
]