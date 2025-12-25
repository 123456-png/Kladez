from django.urls import path, include
from .views import ExportImportView
from . import views

app_name = 'kladez_app'
urlpatterns = [
    path('', views.home, name='home'),
    path('works/', views.completed_works, name='completed_works'),
    path('car-models/', views.car_models_directory, name='car_models_directory'),
    path('repair-types/', views.repair_types_directory, name='repair_types_directory'),
    path('add-work/', views.add_completed_work, name='add_completed_work'),
    path('work/<slug:slug>/', views.completed_work_detail, name='completed_work_detail'),
    path('add-brand/', views.add_car_brand, name='add_car_brand'),
    path('add-car-model/', views.add_car_model, name='add_car_model'),
    path('add-repair-category/', views.add_repair_category, name='add_repair_category'),
    path('add-repair-type/', views.add_repair_type, name='add_repair_type'),
    path('load-car-models/', views.load_car_models, name='load_car_models'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('api/', include('kladez_app.api_urls')),
    path('data-export/', ExportImportView.as_view(), name='data_export'),
    path('work/<slug:slug>/delete/', views.delete_completed_work, name='delete_completed_work'),
path('repair-type/<int:pk>/delete/', views.delete_repair_type, name='delete_repair_type'),
]