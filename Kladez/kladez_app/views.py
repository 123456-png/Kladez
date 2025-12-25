from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from django.contrib import messages
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory
from .forms import CompletedWorkForm, CarBrandForm, CarModelForm, RepairCategoryForm, RepairTypeForm, LoginForm, \
    RegisterForm, DecimalEncoder
import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

class ExportImportView(TemplateView):
    template_name = 'kladez_app/export_import.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Экспорт и импорт данных'
        return context

# Декоратор для проверки суперпользователя
def superuser_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='kladez_app:home'
    )(view_func)
    return decorated_view_func


# В views.py, в функции home, исправляем подсчет видов работ
@login_required
def home(request):
    """Главная страница с общей информацией"""
    last_30_days = datetime.now() - timedelta(days=30)
    last_30_days_date = last_30_days.date()

    recent_works = CompletedWork.objects.filter(user=request.user, work_date__gte=last_30_days)
    total_recent_works = recent_works.count()
    total_revenue = recent_works.aggregate(Sum('cost'))['cost__sum'] or 0

    context = {
        'total_brands': CarBrand.objects.count(),
        'total_models': CarModel.objects.count(),
        'total_repair_types': RepairType.objects.filter(user=request.user).count(),
        'total_recent_works': total_recent_works,
        'total_revenue': total_revenue,
        'recent_works': recent_works.order_by('-work_date')[:10],
        'last_30_days_date': last_30_days_date,
    }
    return render(request, 'kladez_app/home.html', context)


@login_required
def completed_works(request):
    """Список всех выполненных работ с аналитикой"""
    works = CompletedWork.objects.filter(user=request.user).select_related(
        'car_brand', 'car_model'
    ).prefetch_related('repair_types__category').order_by('-work_date')

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    show_analytics = request.GET.get('tab') == 'analytics'

    if date_from:
        works = works.filter(work_date__gte=date_from)
    if date_to:
        works = works.filter(work_date__lte=date_to)

    # Данные для аналитики
    analytics_data = {
        'by_category_count': [],
        'by_category_revenue': [],
        'by_category_avg': [],
        'table_data': [],
        'total_works': 0,
        'total_revenue': 0,
        'avg_revenue_per_work': 0,
    }

    # Если включена аналитика
    if show_analytics:
        # Собираем статистику по категориям
        category_stats = {}

        for work in works:
            analytics_data['total_works'] += 1
            analytics_data['total_revenue'] += float(work.cost)

            for repair in work.repair_types.all():
                category = repair.category
                if category.id not in category_stats:
                    category_stats[category.id] = {
                        'category': category,
                        'count': 0,
                        'revenue': 0,
                        'repair_types': {}
                    }

                category_stats[category.id]['count'] += 1
                category_stats[category.id]['revenue'] += float(work.cost)

                # Статистика по видам работ внутри категории
                if repair.id not in category_stats[category.id]['repair_types']:
                    category_stats[category.id]['repair_types'][repair.id] = {
                        'name': repair.name,
                        'count': 0,
                        'revenue': 0
                    }

                category_stats[category.id]['repair_types'][repair.id]['count'] += 1
                category_stats[category.id]['repair_types'][repair.id]['revenue'] += float(work.cost)

        # Преобразуем данные для таблицы и диаграмм
        for cat_id, stats in category_stats.items():
            category = stats['category']
            count = stats['count']
            revenue = stats['revenue']
            avg = revenue / count if count > 0 else 0

            # Данные для таблицы
            table_item = {
                'name': category.name,
                'color': category.color,
                'count': count,
                'revenue': revenue,
                'avg': avg,
                'share': (revenue / analytics_data['total_revenue'] * 100) if analytics_data[
                                                                                  'total_revenue'] > 0 else 0,
                'repair_types': list(stats['repair_types'].values())
            }
            analytics_data['table_data'].append(table_item)

            # Для диаграммы по количеству работ
            analytics_data['by_category_count'].append({
                'name': category.name,
                'color': category.color,
                'value': count,
                'repair_types': list(stats['repair_types'].values())
            })

            # Для диаграммы по выручке
            analytics_data['by_category_revenue'].append({
                'name': category.name,
                'color': category.color,
                'value': revenue,
                'repair_types': list(stats['repair_types'].values())
            })

            # Для диаграммы по среднему чеку
            analytics_data['by_category_avg'].append({
                'name': category.name,
                'color': category.color,
                'value': avg,
                'repair_types': list(stats['repair_types'].values())
            })

        # Сортируем по убыванию
        analytics_data['table_data'].sort(key=lambda x: x['revenue'], reverse=True)
        analytics_data['by_category_count'].sort(key=lambda x: x['value'], reverse=True)
        analytics_data['by_category_revenue'].sort(key=lambda x: x['value'], reverse=True)
        analytics_data['by_category_avg'].sort(key=lambda x: x['value'], reverse=True)

        # Рассчитываем среднюю выручку на работу
        if analytics_data['total_works'] > 0:
            analytics_data['avg_revenue_per_work'] = analytics_data['total_revenue'] / analytics_data['total_works']

    # Преобразуем в JSON для передачи в шаблон
    analytics_data_json = json.dumps(analytics_data, cls=DecimalEncoder)

    context = {
        'works': works,
        'total_count': works.count(),
        'total_cost': works.aggregate(Sum('cost'))['cost__sum'] or 0,
        'analytics_data': analytics_data,
        'analytics_data_json': analytics_data_json,
        'show_analytics': show_analytics,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'kladez_app/completed_works.html', context)


@login_required
def car_models_directory(request):
    """Справочник моделей автомобилей с пагинацией"""
    # Получаем все марки с моделями
    brands_list = CarBrand.objects.prefetch_related('carmodel_set').all()

    paginator = Paginator(brands_list, 5)
    page_number = request.GET.get('page')

    try:
        brands_page = paginator.page(page_number)
    except PageNotAnInteger:
        # Если страница не является целым числом, показываем первую страницу
        brands_page = paginator.page(1)
    except EmptyPage:
        # Если страница вне диапазона, показываем последнюю страницу
        brands_page = paginator.page(paginator.num_pages)

    # Общая статистика (для всех марок, а не только для текущей страницы)
    total_brands = CarBrand.objects.count()
    total_models = CarModel.objects.count()

    # Рассчитываем количество моделей для каждой марки на текущей странице
    for brand in brands_page:
        brand.model_count = brand.carmodel_set.count()

    context = {
        'brands_page': brands_page,
        'total_brands': total_brands,
        'total_models': total_models,
        'paginator': paginator,
    }
    return render(request, 'kladez_app/car_models_directory.html', context)

@login_required
def repair_types_directory(request):
    """Справочник видов работ для текущего пользователя"""
    categories_with_repairs = RepairCategory.objects.all()

    # Для каждой категории получаем только виды работ текущего пользователя
    for category in categories_with_repairs:
        category.user_repair_types = category.repairtype_set.filter(user=request.user)

    context = {
        'categories_with_repairs': categories_with_repairs
    }
    return render(request, 'kladez_app/repair_types_directory.html', context)


@login_required
def add_completed_work(request):
    if request.method == 'POST':
        form = CompletedWorkForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Работа успешно добавлена!')
            return redirect('kladez_app:add_completed_work')
    else:
        form = CompletedWorkForm(user=request.user)

    return render(request, 'kladez_app/add_completed_work.html', {'form': form})

def completed_work_detail(request, slug):
    """Детальная страница выполненной работы"""
    work = get_object_or_404(CompletedWork, slug=slug)
    return render(request, 'kladez_app/completed_work_detail.html', {'work': work})

@superuser_required
@login_required
def add_car_brand(request):
    """Добавление марки автомобиля - только для суперпользователей"""
    if request.method == 'POST':
        form = CarBrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Марка автомобиля успешно добавлена!')
            return redirect('kladez_app:add_car_brand')  # Остаемся на той же странице
    else:
        form = CarBrandForm()

    brands = CarBrand.objects.all().order_by('name')

    return render(request, 'kladez_app/add_car_brand.html', {
        'form': form,
        'brands': brands
    })


@superuser_required
@login_required
def add_car_model(request):
    """Добавление модели автомобиля - только для суперпользователей"""
    if request.method == 'POST':
        form = CarModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Модель автомобиля успешно добавлена!')
            return redirect('kladez_app:add_car_model')  # Остаемся на той же странице
    else:
        form = CarModelForm()

    brands = CarBrand.objects.all().order_by('name')
    car_models = CarModel.objects.all().select_related('brand').order_by('brand__name', 'name')

    return render(request, 'kladez_app/add_car_model.html', {
        'form': form,
        'brands': brands,
        'car_models': car_models
    })


@superuser_required
@login_required
def add_repair_category(request):
    """Добавление категории работ - только для суперпользователей"""
    if request.method == 'POST':
        form = RepairCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория работ успешно добавлена!')
            return redirect('kladez_app:add_repair_category')  # Остаемся на той же странице
    else:
        form = RepairCategoryForm()

    categories = RepairCategory.objects.all().order_by('name')

    return render(request, 'kladez_app/add_repair_category.html', {
        'form': form,
        'categories': categories
    })


@login_required
def add_repair_type(request):
    """Добавление вида работ - для всех пользователей"""
    if request.method == 'POST':
        form = RepairTypeForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вид работ успешно добавлен!')
            return redirect('kladez_app:add_repair_type')  # Остаемся на той же странице
    else:
        form = RepairTypeForm(user=request.user)

    repair_types = RepairType.objects.filter(user=request.user).select_related('category').order_by('category__name', 'name')

    return render(request, 'kladez_app/add_repair_type.html', {
        'form': form,
        'repair_types': repair_types
    })

def load_car_models(request):
    """AJAX-загрузка моделей автомобилей по марке"""
    brand_id = request.GET.get('brand_id')
    if brand_id:
        try:
            car_models = CarModel.objects.filter(brand_id=brand_id).order_by('name')
            return render(request, 'kladez_app/car_models_dropdown.html', {'car_models': car_models})
        except (ValueError, TypeError):
            pass

    return render(request, 'kladez_app/car_models_dropdown.html', {'car_models': []})


def logout_user(request):
    """Выход пользователя из системы"""
    logout(request)
    return redirect('kladez_app:login')


class RegisterUser(CreateView):
    form_class = RegisterForm
    template_name = 'kladez_app/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('kladez_app:home')


class LoginUser(LoginView):
    form_class = LoginForm
    template_name = 'kladez_app/login.html'

    def get_success_url(self):
        return reverse_lazy('kladez_app:home')


@login_required
def delete_completed_work(request, slug):
    """Удаление выполненной работы"""
    work = get_object_or_404(CompletedWork, slug=slug, user=request.user)

    if request.method == 'POST':
        work.delete()
        messages.success(request, 'Работа успешно удалена!')
        return redirect('kladez_app:completed_works')  # Перенаправляем на список работ

    # Если запрос GET (просто перешли по ссылке), спрашиваем подтверждение
    return render(request, 'kladez_app/confirm_delete.html', {
        'object': work,
        'object_name': 'выполненную работу',
        'cancel_url': reverse_lazy('kladez_app:completed_works')
    })

@login_required
def delete_repair_type(request, pk):
    """Удаление вида работ"""
    repair_type = get_object_or_404(RepairType, pk=pk, user=request.user)

    if request.method == 'POST':
        # Проверяем, используется ли этот вид работ в каких-либо работах
        used_in_works = CompletedWork.objects.filter(repair_types=repair_type).exists()

        if used_in_works:
            messages.error(request, 'Невозможно удалить вид работ, так как он используется в выполненных работах!')
            return redirect('kladez_app:repair_types_directory')

        repair_type.delete()
        messages.success(request, 'Вид работ успешно удален!')
        return redirect('kladez_app:repair_types_directory')

    # Если запрос не POST, показываем страницу подтверждения
    return render(request, 'kladez_app/confirm_delete.html', {
        'object': repair_type,
        'object_name': 'вид работ',
        'cancel_url': reverse_lazy('kladez_app:repair_types_directory')
    })