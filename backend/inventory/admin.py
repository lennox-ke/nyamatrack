from django.contrib import admin
from .models import MeatType, MeatCut, Stock, Sale, LowStockAlert, SystemLog

admin.site.register(MeatType)
admin.site.register(MeatCut)
admin.site.register(Stock)
admin.site.register(Sale)
admin.site.register(LowStockAlert)
admin.site.register(SystemLog)