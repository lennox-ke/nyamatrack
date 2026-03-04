from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.current_user, name='current_user'),
    
    # Dashboard
    path('dashboard/', views.dashboard_data, name='dashboard'),
    
    # Stock
    path('stock/', views.stock_list_create, name='stock_list_create'),
    path('stock/<int:pk>/', views.stock_detail, name='stock_detail'),
    path('stock/expiring/', views.expiring_stock, name='expiring_stock'),
    
    # NEW FEATURE 1: Fresh vs Expired Stock Separation
    path('stock/by-freshness/', views.stock_by_freshness, name='stock-by-freshness'),
    
    # NEW FEATURE 3: Historical Stock Tracking
    path('stock/historical/', views.stock_historical, name='stock-historical'),
    
    # Sales
    path('sales/', views.sales_list_create, name='sales_list_create'),
    path('sales/today/', views.today_sales, name='today_sales'),
    path('sales/report/', views.sales_report, name='sales_report'),
    
    # NEW FEATURE 2: Date-based Sales Reports
    path('sales/date/<int:year>/<int:month>/<int:day>/', views.sales_by_date, name='sales-by-date'),
    path('sales/date-range/', views.sales_by_date_range, name='sales-by-date-range'),
    
    # Meat Types & Cuts
    path('meat-types/', views.meat_types_list, name='meat_types'),
    path('meat-cuts/', views.meat_cuts_list, name='meat_cuts'),
    path('meat-cuts/<int:meat_type_id>/', views.meat_cuts_by_type, name='meat_cuts_by_type'),
    
    # Alerts
    path('alerts/', views.alerts_list, name='alerts'),
    path('alerts/low-stock/', views.low_stock_alerts, name='low_stock_alerts'),
    
    # Logs
    path('logs/', views.system_logs, name='logs'),
]