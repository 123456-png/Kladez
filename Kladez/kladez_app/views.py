from django.shortcuts import render
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory
from django.db.models import Count, Sum
from datetime import datetime, timedelta


def home(request):
    """Главная страница с общей информацией"""
    # Статистика за последние 30 дней
    last_30_days = datetime.now() - timedelta(days=30)

    recent_works = CompletedWork.objects.filter(work_date__gte=last_30_days)
    total_recent_works = recent_works.count()
    total_revenue = recent_works.aggregate(Sum('cost'))['cost__sum'] or 0

    context = {
        'total_brands': CarBrand.objects.count(),
        'total_models': CarModel.objects.count(),
        'total_repair_types': RepairType.objects.count(),
        'total_recent_works': total_recent_works,
        'total_revenue': total_revenue,
        'recent_works': recent_works.order_by('-work_date')[:10]  # последние 10 работ
    }
    return render(request, 'kladez_app/home.html', context)


def completed_works(request):
    """Список всех выполненных работ"""
    works = CompletedWork.objects.all().select_related(
        'car_brand', 'car_model', 'repair_type'
    ).order_by('-work_date')

    # Простая фильтрация по дате (можно будет улучшить)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        works = works.filter(work_date__gte=date_from)
    if date_to:
        works = works.filter(work_date__lte=date_to)

    context = {
        'works': works,
        'total_count': works.count(),
        'total_cost': works.aggregate(Sum('cost'))['cost__sum'] or 0
    }
    return render(request, 'kladez_app/completed_works.html', context)


def car_models_directory(request):
    """Справочник моделей автомобилей"""
    brands_with_models = CarBrand.objects.prefetch_related('carmodel_set').all()

    context = {
        'brands_with_models': brands_with_models
    }
    return render(request, 'kladez_app/car_models_directory.html', context)


def repair_types_directory(request):
    """Справочник видов работ"""
    categories_with_repairs = RepairCategory.objects.prefetch_related('repairtype_set').all()

    context = {
        'categories_with_repairs': categories_with_repairs
    }
    return render(request, 'kladez_app/repair_types_directory.html', context)