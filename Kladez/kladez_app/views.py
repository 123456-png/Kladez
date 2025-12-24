from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from django.contrib import messages
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory
from .forms import CompletedWorkForm, CarBrandForm, CarModelForm, RepairCategoryForm, RepairTypeForm, LoginForm, \
    RegisterForm


# Декоратор для проверки суперпользователя
def superuser_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='kladez_app:home'
    )(view_func)
    return decorated_view_func


@login_required
def home(request):
    """Главная страница с общей информацией"""
    last_30_days = datetime.now() - timedelta(days=30)
    last_30_days_date = last_30_days.date()  # Для передачи в ссылку

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
        'last_30_days_date': last_30_days_date,  # Передаем дату для фильтра
    }
    return render(request, 'kladez_app/home.html', context)


@login_required
def completed_works(request):
    """Список всех выполненных работ"""
    works = CompletedWork.objects.filter(user=request.user).select_related(
        'car_brand', 'car_model', 'repair_type'
    ).order_by('-work_date')

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


@login_required
def car_models_directory(request):
    """Справочник моделей автомобилей"""
    brands_with_models = CarBrand.objects.prefetch_related('carmodel_set').all()

    context = {
        'brands_with_models': brands_with_models
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
            return redirect('kladez_app:add_completed_work')  # Остаемся на той же странице
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