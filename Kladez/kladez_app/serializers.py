# kladez_app/serializers.py
from rest_framework import serializers
from .models import CompletedWork, CarBrand, CarModel, RepairType, RepairCategory
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrand
        fields = '__all__'  # или ['id', 'name', 'description']


class CarModelSerializer(serializers.ModelSerializer):
    brand = CarBrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=CarBrand.objects.all(),
        source='brand',
        write_only=True
    )

    class Meta:
        model = CarModel
        fields = '__all__'


class RepairCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairCategory
        fields = '__all__'


class RepairTypeSerializer(serializers.ModelSerializer):
    category = RepairCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=RepairCategory.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = RepairType
        fields = '__all__'


class CompletedWorkSerializer(serializers.ModelSerializer):
    car_brand = CarBrandSerializer(read_only=True)
    car_brand_id = serializers.PrimaryKeyRelatedField(
        queryset=CarBrand.objects.all(),
        source='car_brand',
        write_only=True
    )

    car_model = CarModelSerializer(read_only=True)
    car_model_id = serializers.PrimaryKeyRelatedField(
        queryset=CarModel.objects.all(),
        source='car_model',
        write_only=True
    )

    repair_types = RepairTypeSerializer(many=True, read_only=True)
    repair_type_ids = serializers.PrimaryKeyRelatedField(
        queryset=RepairType.objects.all(),
        source='repair_types',
        many=True,
        write_only=True
    )

    user = UserSerializer(read_only=True)

    class Meta:
        model = CompletedWork
        fields = [
            'id', 'work_date', 'car_brand', 'car_brand_id',
            'car_model', 'car_model_id', 'repair_types', 'repair_type_ids',
            'cost', 'notes', 'parts_used', 'slug', 'user'  # УБРАЛИ created_at
        ]
        read_only_fields = ['slug', 'user']