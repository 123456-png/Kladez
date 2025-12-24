from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory


class CompletedWorkForm(forms.ModelForm):
    class Meta:
        model = CompletedWork
        fields = ['work_date', 'car_brand', 'car_model', 'repair_type', 'cost', 'notes', 'parts_used']
        widgets = {
            'work_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'parts_used': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'work_date': 'Дата выполнения',
            'car_brand': 'Марка автомобиля',
            'car_model': 'Модель автомобиля',
            'repair_type': 'Вид работ',
            'cost': 'Стоимость работы (руб)',
            'notes': 'Заметки',
            'parts_used': 'Использованные запчасти',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Фильтруем виды работ по текущему пользователю
        if self.user:
            self.fields['repair_type'].queryset = RepairType.objects.filter(user=self.user)

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
        fields = ['name', 'description']


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