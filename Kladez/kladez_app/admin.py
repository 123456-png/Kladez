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
    list_display = ['name', 'color', 'description']
    search_fields = ['name']
    list_per_page = 20

@admin.register(RepairType)
class RepairTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'user', 'complexity', 'typical_duration']
    list_filter = ['category', 'user', 'complexity']
    search_fields = ['name', 'category__name', 'description']
    list_per_page = 20

@admin.register
class RepairTypeInline(admin.TabularInline):
    """Inline для отображения видов работ в выполненной работе"""
    model = CompletedWork.repair_types.through
    extra = 1
    verbose_name = "Вид работ"
    verbose_name_plural = "Виды работ"

@admin.register
class CompletedWorkAdmin(admin.ModelAdmin):
    list_display = ['work_date', 'car_brand', 'car_model', 'display_repair_types', 'cost', 'user']
    list_filter = ['work_date', 'car_brand', 'car_model', 'user']
    search_fields = ['car_brand__name', 'car_model__name', 'notes', 'parts_used']
    readonly_fields = ['slug']
    list_per_page = 20
    inlines = [RepairTypeInline]

    def display_repair_types(self, obj):
        """Отображает список видов работ в админке"""
        return ", ".join([rt.name for rt in obj.repair_types.all()])

    display_repair_types.short_description = 'Виды работ'