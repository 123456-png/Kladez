from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory

import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class GroupedRepairTypesWidget(forms.CheckboxSelectMultiple):
    """Кастомный виджет для группировки видов работ по категориям"""

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)

    def optgroups(self, name, value, attrs=None):
        """Группируем опции по категориям"""
        groups = []
        has_selected = False

        # Получаем категории с видами работ для текущего пользователя
        from .models import RepairCategory
        categories = RepairCategory.objects.all()

        for category in categories:
            category_choices = []
            repair_types = RepairType.objects.filter(category=category, user=self.user)

            for repair in repair_types:
                option_value = str(repair.id)
                option_label = repair.name

                selected = (
                        str(option_value) in value and
                        (has_selected is False or self.allow_multiple_selected)
                )
                if selected is True and has_selected is False:
                    has_selected = True

                category_choices.append({
                    'name': name,
                    'value': option_value,
                    'label': option_label,
                    'selected': selected,
                    'index': len(groups),
                    'attrs': self.build_attrs(
                        self.attrs,
                        attrs,
                    ),
                    'type': self.input_type,
                })

            if category_choices:
                groups.append((category.name, category_choices, category.id))

        return groups

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        """Создаем опцию с цветом категории"""
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        # Добавляем цвет категории как data-атрибут
        if hasattr(self, 'category_colors'):
            for category_name, choices, category_id in self.groups:
                if category_name == label.split(' - ')[0] if ' - ' in label else '':
                    option['attrs']['data-category-color'] = self.category_colors.get(category_id, '#e67e22')
                    break

        return option


class CompletedWorkForm(forms.ModelForm):
    class Meta:
        model = CompletedWork
        fields = ['work_date', 'car_brand', 'car_model', 'repair_types', 'cost', 'notes', 'parts_used']
        widgets = {
            'work_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'parts_used': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'work_date': 'Дата выполнения',
            'car_brand': 'Марка автомобиля',
            'car_model': 'Модель автомобиля',
            'repair_types': 'Виды работ',
            'cost': 'Стоимость работы (руб)',
            'notes': 'Заметки',
            'parts_used': 'Использованные запчасти',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Фильтруем виды работ по текущему пользователю с select_related
        if self.user:
            repair_types_qs = RepairType.objects.filter(user=self.user).select_related('category').order_by(
                'category__name', 'name')
            self.fields['repair_types'].queryset = repair_types_qs

        # Логика для динамической загрузки моделей
        if 'car_brand' in self.data:
            try:
                brand_id = int(self.data.get('car_brand'))
                self.fields['car_model'].queryset = CarModel.objects.filter(brand_id=brand_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['car_model'].queryset = CarModel.objects.none()

        elif self.instance.pk:
            if self.instance.car_brand:
                self.fields['car_model'].queryset = self.instance.car_brand.carmodel_set.all().order_by('name')
            else:
                self.fields['car_model'].queryset = CarModel.objects.none()

        else:
            self.fields['car_model'].queryset = CarModel.objects.none()

    def save(self, commit=True):
        """Сохраняем форму с привязкой к пользователю"""
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
            self.save_m2m()  # Сохраняем связи ManyToMany
        return instance

class CarBrandForm(forms.ModelForm):
    """Форма для добавления марки автомобиля"""

    class Meta:
        model = CarBrand
        fields = ['name', 'description']


class CarModelForm(forms.ModelForm):
    """Форма для добавления модели автомобиля"""

    class Meta:
        model = CarModel
        fields = ['brand', 'name', 'production_years', 'engine_options', 'notes']


class RepairCategoryForm(forms.ModelForm):
    """Форма для добавления категории работ"""

    class Meta:
        model = RepairCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class RepairTypeForm(forms.ModelForm):
    """Форма для добавления вида работ"""

    class Meta:
        model = RepairType
        fields = ['category', 'name', 'description', 'typical_duration', 'complexity']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Сохраняем форму с привязкой к пользователю"""
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)