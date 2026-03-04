from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('api/auth/login/', views.login_view, name='login'),
    path('api/auth/register/', views.register_view, name='register'),
    path('api/auth/logout/', views.logout_view, name='logout'),
    path('api/auth/user/', views.current_user, name='current_user'),
    
    # Dashboard
    path('api/dashboard/', views.dashboard_data, name='dashboard'),
    
    # Stock
    path('api/stock/', views.stock_list_create, name='stock_list_create'),
    path('api/stock/<int:pk>/', views.stock_detail, name='stock_detail'),
    path('api/stock/expiring/', views.expiring_stock, name='expiring_stock'),
    path('api/stock/by-freshness/', views.stock_by_freshness, name='stock-by-freshness'),
    path('api/stock/historical/', views.stock_historical, name='stock-historical'),
    
    # Sales
    path('api/sales/', views.sales_list_create, name='sales_list_create'),
    path('api/sales/today/', views.today_sales, name='today_sales'),
    path('api/sales/report/', views.sales_report, name='sales_report'),
    path('api/sales/date/<int:year>/<int:month>/<int:day>/', views.sales_by_date, name='sales-by-date'),
    path('api/sales/date-range/', views.sales_by_date_range, name='sales-by-date-range'),
    
    # Meat Types & Cuts
    path('api/meat-types/', views.meat_types_list, name='meat_types'),
    path('api/meat-cuts/', views.meat_cuts_list, name='meat_cuts'),
    path('api/meat-cuts/<int:meat_type_id>/', views.meat_cuts_by_type, name='meat_cuts_by_type'),
    
    # Alerts
    path('api/alerts/', views.alerts_list, name='alerts'),
    path('api/alerts/low-stock/', views.low_stock_alerts, name='low_stock_alerts'),
    
    # Logs
    path('api/logs/', views.system_logs, name='logs'),
]