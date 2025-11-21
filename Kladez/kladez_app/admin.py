from django.contrib import admin
from .models import CarBrand, CarModel, RepairCategory, RepairType, CompletedWork

@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    list_per_page = 20

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ['brand', 'name', 'production_years']
    list_filter = ['brand']
    search_fields = ['name', 'brand__name']
    list_per_page = 20

@admin.register(RepairCategory)
class RepairCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    list_per_page = 20

@admin.register(RepairType)
class RepairTypeAdmin(admin.ModelAdmin):
    list_display = ['category', 'name', 'typical_duration', 'complexity']
    list_filter = ['category']
    search_fields = ['name', 'category__name']
    list_per_page = 20

@admin.register(CompletedWork)
class CompletedWorkAdmin(admin.ModelAdmin):
    list_display = ['work_date', 'car_brand', 'car_model', 'repair_type', 'cost']
    list_filter = ['work_date', 'car_brand', 'repair_type__category']
    search_fields = ['car_brand__name', 'car_model__name', 'notes']
    date_hierarchy = 'work_date'
    list_per_page = 25