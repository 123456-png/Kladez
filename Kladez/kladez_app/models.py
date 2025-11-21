from django.db import models
from django.utils import timezone


class CarBrand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Марка автомобиля")
    description = models.TextField(blank=True, verbose_name="Описание марки")

    class Meta:
        verbose_name = "Марка автомобиля"
        verbose_name_plural = "Марки автомобилей"

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, verbose_name="Марка")
    name = models.CharField(max_length=100, verbose_name="Модель")
    production_years = models.CharField(max_length=50, blank=True, verbose_name="Годы выпуска")
    engine_options = models.TextField(blank=True, verbose_name="Двигатели")
    notes = models.TextField(blank=True, verbose_name="Особенности")

    class Meta:
        verbose_name = "Модель автомобиля"
        verbose_name_plural = "Модели автомобилей"

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class RepairCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Категория работ")
    description = models.TextField(blank=True, verbose_name="Описание категории")

    class Meta:
        verbose_name = "Категория работ"
        verbose_name_plural = "Категории работ"

    def __str__(self):
        return self.name


class RepairType(models.Model):
    category = models.ForeignKey(RepairCategory, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Вид работ")
    description = models.TextField(blank=True, verbose_name="Описание работ")
    typical_duration = models.CharField(max_length=50, blank=True, verbose_name="Типовая длительность")
    complexity = models.CharField(max_length=50, blank=True, verbose_name="Сложность")

    class Meta:
        verbose_name = "Вид работ"
        verbose_name_plural = "Виды работ"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class CompletedWork(models.Model):
    work_date = models.DateField(default=timezone.now, verbose_name="Дата выполнения")
    car_brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, verbose_name="Марка")
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, verbose_name="Модель")
    repair_type = models.ForeignKey(RepairType, on_delete=models.CASCADE, verbose_name="Вид работ")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость работы")
    notes = models.TextField(blank=True, verbose_name="Заметки")
    parts_used = models.TextField(blank=True, verbose_name="Использованные запчасти")

    class Meta:
        verbose_name = "Выполненная работа"
        verbose_name_plural = "Выполненные работы"
        ordering = ['-work_date']

    def __str__(self):
        return f"{self.work_date} - {self.car_brand} {self.car_model} - {self.repair_type}"