from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class MeatType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class MeatCut(models.Model):
    meat_type = models.ForeignKey(MeatType, on_delete=models.CASCADE, related_name='cuts')
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.meat_type.name} - {self.name}"


class Stock(models.Model):
    meat_cut = models.ForeignKey(MeatCut, on_delete=models.CASCADE, related_name='stock_items')
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Stock"
        ordering = ['-received_date']  # ADDED: Default ordering
    
    def __str__(self):
        return f"{self.meat_cut} - {self.weight_kg}kg"
    
    @property  # CHANGED: Made this a property so it's accessible in serializers
    def days_until_expiry(self):
        if not self.expiry_date:
            return 0
        days = (self.expiry_date.date() - timezone.now().date()).days
        return max(0, days)  # ADDED: Ensure non-negative
    
    @property  # ADDED: Property for meat_cut_name
    def meat_cut_name(self):
        return self.meat_cut.name if self.meat_cut else 'Unknown'
    
    @property  # ADDED: Property for meat_type_name
    def meat_type_name(self):
        if self.meat_cut and self.meat_cut.meat_type:
            return self.meat_cut.meat_type.name
        return 'Unknown'
    
    def is_expiring_soon(self):
        return self.days_until_expiry <= 2  # CHANGED: Use property access


class Sale(models.Model):
    stock_item = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sales')
    weight_sold = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # CHANGED: Made editable=False
    sold_at = models.DateTimeField(default=timezone.now)
    sold_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-sold_at']  # ADDED: Default ordering by most recent first
    
    def save(self, *args, **kwargs):
        # FIXED: Ensure proper Decimal calculation
        if isinstance(self.weight_sold, (int, float)):
            self.weight_sold = Decimal(str(self.weight_sold))
        if isinstance(self.price_per_kg, (int, float)):
            self.price_per_kg = Decimal(str(self.price_per_kg))
        
        self.total_price = self.weight_sold * self.price_per_kg
        super().save(*args, **kwargs)
    
    @property  # ADDED: Property for easy access to meat cut name
    def meat_cut_name(self):
        if self.stock_item and self.stock_item.meat_cut:
            return self.stock_item.meat_cut.name
        return 'Unknown'
    
    @property  # ADDED: Property for easy access to meat type name
    def meat_type_name(self):
        if self.stock_item and self.stock_item.meat_cut and self.stock_item.meat_cut.meat_type:
            return self.stock_item.meat_cut.meat_type.name
        return 'Unknown'
    
    def __str__(self):
        return f"Sale: {self.weight_sold}kg of {self.meat_cut_name} for KES {self.total_price}"  # CHANGED: Use property


class LowStockAlert(models.Model):
    meat_cut = models.ForeignKey(MeatCut, on_delete=models.CASCADE)
    threshold_kg = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # ADDED: Default ordering
    
    def __str__(self):
        return f"Alert for {self.meat_cut} below {self.threshold_kg}kg"


class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('STOCK_ADD', 'Stock Added'),
        ('SALE', 'Sale Recorded'),
        ('ALERT', 'Alert Triggered'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']  # ADDED: Default ordering
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Unknown'
        return f"{self.action} by {user_str} at {self.timestamp}"