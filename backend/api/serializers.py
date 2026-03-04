from rest_framework import serializers
from inventory.models import MeatType, MeatCut, Stock, Sale, SystemLog


class MeatTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeatType
        fields = '__all__'


class MeatCutSerializer(serializers.ModelSerializer):
    meat_type_name = serializers.CharField(source='meat_type.name', read_only=True)
    
    class Meta:
        model = MeatCut
        fields = ['id', 'name', 'description', 'meat_type', 'meat_type_name']


class StockSerializer(serializers.ModelSerializer):
    # These come from model properties
    meat_cut_name = serializers.CharField(read_only=True)
    meat_type_name = serializers.CharField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'meat_cut', 'meat_cut_name', 'meat_type_name',
            'weight_kg', 'received_date', 'expiry_date',
            'days_until_expiry', 'is_active', 'notes', 'recorded_by'
        ]
        read_only_fields = ['recorded_by', 'received_date', 'expiry_date']


class SaleSerializer(serializers.ModelSerializer):
    # These come from model properties
    meat_cut_name = serializers.CharField(read_only=True)
    meat_type_name = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    sold_by_username = serializers.CharField(source='sold_by.username', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'stock_item', 'meat_cut_name', 'meat_type_name',
            'weight_sold', 'price_per_kg', 'total_price', 'sold_at',
            'sold_by', 'sold_by_username', 'customer_name'
        ]
        read_only_fields = ['sold_by', 'sold_at', 'total_price', 'meat_cut_name', 'meat_type_name']


class SystemLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SystemLog
        fields = ['id', 'action', 'description', 'timestamp', 'username']