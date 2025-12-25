# kladez_app/api_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
from django.http import HttpResponse
import pandas as pd
from openpyxl import Workbook
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction


from django.db.models import Sum, Count
from datetime import datetime, timedelta
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory
from .serializers import (
    CompletedWorkSerializer, CarBrandSerializer,
    CarModelSerializer, RepairTypeSerializer, RepairCategorySerializer
)


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompletedWorkViewSet(viewsets.ModelViewSet):
    serializer_class = CompletedWorkSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  # Только встроенные фильтры

    search_fields = ['notes', 'parts_used']
    ordering_fields = ['work_date', 'cost']
    ordering = ['-work_date']  # Сортировка по умолчанию

    def get_queryset(self):
        """Возвращаем только работы текущего пользователя"""
        queryset = CompletedWork.objects.filter(user=self.request.user)

        # Ручная фильтрация по параметрам
        work_date = self.request.query_params.get('work_date')
        car_brand_id = self.request.query_params.get('car_brand_id')
        car_model_id = self.request.query_params.get('car_model_id')

        if work_date:
            queryset = queryset.filter(work_date=work_date)
        if car_brand_id:
            queryset = queryset.filter(car_brand_id=car_brand_id)
        if car_model_id:
            queryset = queryset.filter(car_model_id=car_model_id)

        return queryset

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Экспорт работ в CSV"""
        queryset = self.get_queryset()

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="works_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'

        writer = csv.writer(response)

        # Заголовки
        writer.writerow([
            'Дата', 'Марка', 'Модель', 'Категории работ',
            'Виды работ', 'Стоимость (руб)', 'Заметки', 'Запчасти'
        ])

        # Данные
        for work in queryset:
            categories = set()
            repair_names = []

            for repair in work.repair_types.all():
                categories.add(repair.category.name)
                repair_names.append(repair.name)

            writer.writerow([
                work.work_date.strftime('%d.%m.%Y'),
                work.car_brand.name,
                work.car_model.name,
                ', '.join(categories),
                ', '.join(repair_names[:5]),  # Ограничиваем количество
                str(work.cost),
                work.notes[:100] if work.notes else '',  # Ограничиваем длину
                work.parts_used[:100] if work.parts_used else ''
            ])

        return response

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Экспорт работ в Excel"""
        queryset = self.get_queryset()

        # Создаем DataFrame
        data = []
        for work in queryset:
            categories = set()
            repair_names = []

            for repair in work.repair_types.all():
                categories.add(repair.category.name)
                repair_names.append(repair.name)

            data.append({
                'Дата': work.work_date,
                'Марка': work.car_brand.name,
                'Модель': work.car_model.name,
                'Категории': ', '.join(categories),
                'Виды работ': ', '.join(repair_names),
                'Стоимость (руб)': float(work.cost),
                'Заметки': work.notes,
                'Запчасти': work.parts_used
            })

        df = pd.DataFrame(data)

        # Создаем Excel файл
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Работы', index=False)

            # Добавляем лист со сводной таблицей
            if not df.empty:
                summary = df.groupby('Марка').agg({
                    'Стоимость (руб)': ['sum', 'count', 'mean']
                }).round(2)
                summary.columns = ['Общая сумма', 'Количество работ', 'Средняя стоимость']
                summary.to_excel(writer, sheet_name='Статистика')

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="works_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx"'

        return response

    @action(detail=False, methods=['get'])
    def export_json(self, request):
        """Экспорт работ в JSON"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        response = HttpResponse(
            json.dumps(serializer.data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="works_{datetime.now().strftime("%Y%m%d_%H%M")}.json"'

        return response

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_excel(self, request):
        """Импорт работ из Excel файла"""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Файл не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']

        try:
            # Читаем Excel
            if file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                return Response(
                    {'error': 'Поддерживаются только .xlsx и .csv файлы'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            required_columns = ['Дата', 'Марка', 'Модель', 'Виды работ', 'Стоимость (руб)']
            for col in required_columns:
                if col not in df.columns:
                    return Response(
                        {'error': f'Отсутствует обязательная колонка: {col}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            imported_count = 0
            errors = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Ищем или создаем марку авто
                        brand, _ = CarBrand.objects.get_or_create(
                            name=str(row['Марка']).strip()
                        )

                        # Ищем или создаем модель
                        model, _ = CarModel.objects.get_or_create(
                            brand=brand,
                            name=str(row['Модель']).strip()
                        )

                        # Создаем работу
                        work = CompletedWork(
                            work_date=pd.to_datetime(row['Дата']).date(),
                            car_brand=brand,
                            car_model=model,
                            cost=float(row['Стоимость (руб)']),
                            notes=str(row.get('Заметки', '')).strip(),
                            parts_used=str(row.get('Запчасти', '')).strip(),
                            user=request.user
                        )
                        work.save()

                        # Обрабатываем виды работ
                        if pd.notna(row['Виды работ']):
                            repair_names = str(row['Виды работ']).split(',')
                            for repair_name in repair_names:
                                repair_name = repair_name.strip()
                                if repair_name:
                                    # Ищем или создаем вид работ
                                    repair_type, _ = RepairType.objects.get_or_create(
                                        name=repair_name,
                                        defaults={
                                            'category': RepairCategory.objects.first() or RepairCategory.objects.create(
                                                name='Общие'),
                                            'user': request.user
                                        }
                                    )
                                    work.repair_types.add(repair_type)

                        imported_count += 1

                    except Exception as e:
                        errors.append(f"Строка {index + 2}: {str(e)}")

            return Response({
                'message': f'Успешно импортировано {imported_count} записей',
                'imported_count': imported_count,
                'errors': errors if errors else None
            })

        except Exception as e:
            return Response(
                {'error': f'Ошибка при обработке файла: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
# 2. API для справочников (доступно всем)
class CarBrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer
    permission_classes = [permissions.AllowAny]


class CarModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Фильтрация моделей по марке"""
        queryset = CarModel.objects.all()
        brand_id = self.request.query_params.get('brand_id')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
        return queryset


class RepairTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RepairTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Возвращаем только виды работ текущего пользователя"""
        return RepairType.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Автоматически привязываем вид работ к пользователю"""
        serializer.save(user=self.request.user)


class RepairCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RepairCategory.objects.all()
    serializer_class = RepairCategorySerializer
    permission_classes = [permissions.IsAuthenticated]