"""
API Views for NyamaTrack
"""

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Q
from inventory.models import (
    MeatType, MeatCut, Stock, Sale, 
    LowStockAlert, SystemLog
)
from .serializers import (
    MeatTypeSerializer, MeatCutSerializer, StockSerializer,
    SaleSerializer, SystemLogSerializer
)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint that returns a token for API authentication.
    Token is required for cross-domain requests (Netlify -> Render).
    """
    if request.method == 'GET':
        return Response({'detail': 'Login endpoint. Send POST request with username and password.'})
    
    # Debug logging
    print(f"=== LOGIN ATTEMPT ===")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.headers.get('Content-Type', 'Not set')}")
    print(f"Request data type: {type(request.data)}")
    print(f"Request data: {request.data}")
    print(f"Request body: {request.body}")
    print(f"====================")
    
    try:
        username = request.data.get('username')
        password = request.data.get('password')
    except Exception as e:
        print(f"Error reading request data: {e}")
        return Response({
            'success': False, 
            'error': f'Invalid request format: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not username or not password:
        return Response({
            'success': False, 
            'error': 'Please provide username and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        
        # Get or create authentication token for API access
        token, created = Token.objects.get_or_create(user=user)
        
        # Log the login
        try:
            SystemLog.objects.create(
                user=user, 
                action='LOGIN', 
                description=f'User {username} logged in'
            )
        except Exception as e:
            print(f"Log error: {e}")
        
        return Response({
            'success': True,
            'token': token.key,  # CRITICAL: Frontend stores this for subsequent requests
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff
            }
        })
    
    return Response({
        'success': False, 
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def register_view(request):
    """
    User registration endpoint.
    Creates user and returns token immediately for auto-login.
    """
    if request.method == 'GET':
        return Response({'detail': 'Register endpoint. Send POST with username, password, email'})
    
    print(f"=== REGISTER ATTEMPT ===")
    print(f"Request data: {request.data}")
    print(f"========================")
    
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
    except Exception as e:
        print(f"Error reading request data: {e}")
        return Response({
            'success': False, 
            'error': f'Invalid request format: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not username or not password:
        return Response({
            'success': False, 
            'error': 'Please provide username and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(password) < 6:
        return Response({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Case-insensitive username check
    if User.objects.filter(username__iexact=username).exists():
        return Response({
            'success': False,
            'error': 'Username already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create user with properly hashed password
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create token for immediate API access
        token = Token.objects.create(user=user)
        
        # Log the user in (for session-based admin access)
        login(request, user)
        
        # Log the registration
        try:
            SystemLog.objects.create(
                user=user,
                action='REGISTER',
                description=f'New user {username} registered'
            )
        except Exception as e:
            print(f"Log error: {e}")
        
        return Response({
            'success': True,
            'token': token.key,  # CRITICAL: Return token for immediate API access
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff
            }
        })
    except Exception as e:
        print(f"Registration error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout endpoint - invalidates token on frontend, session on backend."""
    try:
        # Delete token to invalidate API access
        Token.objects.filter(user=request.user).delete()
        
        # Log the logout
        try:
            SystemLog.objects.create(
                user=request.user, 
                action='LOGOUT', 
                description=f'User {request.user.username} logged out'
            )
        except Exception as e:
            print(f"Log error: {e}")
    except Exception as e:
        print(f"Token deletion error: {e}")
    
    logout(request)
    return Response({'success': True, 'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user details."""
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """Dashboard data with accurate alert counting."""
    # Current stock totals by meat type
    stock_data = []
    for meat_type in MeatType.objects.all():
        total_weight = Decimal('0')
        items = []
        for cut in meat_type.cuts.all():
            cut_stock = Stock.objects.filter(meat_cut=cut, is_active=True)
            weight = sum((s.weight_kg for s in cut_stock), Decimal('0'))
            if weight > 0:
                total_weight += weight
                items.append({
                    'cut_name': cut.name,
                    'weight': float(weight),
                    'items': cut_stock.count()
                })
        
        if total_weight > 0:
            stock_data.append({
                'meat_type': meat_type.name,
                'total_weight': float(total_weight),
                'cuts': items
            })
    
    # Today's sales
    today = timezone.now().date()
    today_sales = Sale.objects.filter(sold_at__date=today)
    total_revenue = sum((s.total_price for s in today_sales), Decimal('0'))
    total_weight_sold = sum((s.weight_sold for s in today_sales), Decimal('0'))
    
    # Alert counting
    alerts = []
    
    # Low stock alerts
    for alert in LowStockAlert.objects.filter(is_active=True):
        current_stock = Stock.objects.filter(meat_cut=alert.meat_cut, is_active=True)
        total_weight = sum((s.weight_kg for s in current_stock), Decimal('0'))
        if total_weight < alert.threshold_kg:
            alerts.append({
                'type': 'low_stock',
                'message': f"{alert.meat_cut.name} is running low ({float(total_weight)}kg remaining)",
                'severity': 'warning'
            })
    
    # Expiring soon
    expiring = Stock.objects.filter(
        is_active=True,
        expiry_date__lte=timezone.now() + timedelta(days=2)
    )
    for item in expiring:
        days_left = item.days_until_expiry
        alerts.append({
            'type': 'expiring',
            'message': f"{item.meat_cut.name} expires in {days_left} days",
            'severity': 'danger' if days_left <= 0 else 'warning'
        })
    
    return Response({
        'stock_summary': stock_data,
        'today_sales': {
            'count': today_sales.count(),
            'revenue': float(total_revenue),
            'weight': float(total_weight_sold)
        },
        'alerts': alerts
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def stock_list_create(request):
    """List all stock or create new stock entry."""
    if request.method == 'GET':
        stock = Stock.objects.filter(is_active=True).order_by('-received_date')
        serializer = StockSerializer(stock, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        try:
            data = request.data
            print(f"Received data: {data}")
            
            # Validate required fields
            if 'meat_cut_id' not in data or 'weight_kg' not in data:
                return Response(
                    {'error': 'Missing required fields: meat_cut_id and weight_kg'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate meat_cut_id exists
            try:
                meat_cut = MeatCut.objects.get(id=int(data['meat_cut_id']))
            except MeatCut.DoesNotExist:
                return Response(
                    {'error': 'Invalid meat_cut_id. Meat cut does not exist.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate weight is positive
            weight_kg = float(data['weight_kg'])
            if weight_kg <= 0:
                return Response(
                    {'error': 'Weight must be greater than 0'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate expiry (3 days from receive date for fresh meat)
            received_date = timezone.now()
            expiry_date = received_date + timedelta(days=3)
            
            stock = Stock.objects.create(
                meat_cut=meat_cut,
                weight_kg=weight_kg,
                received_date=received_date,
                expiry_date=expiry_date,
                recorded_by=request.user,
                notes=data.get('notes', '')
            )
            
            # Log the action
            try:
                SystemLog.objects.create(
                    user=request.user,
                    action='STOCK_ADD',
                    description=f"Added {weight_kg}kg of {stock.meat_cut.name}"
                )
            except Exception as e:
                print(f"Log error: {e}")
            
            return Response(StockSerializer(stock).data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': f'Invalid number format: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"Stock creation error: {str(e)}")
            return Response(
                {'error': f'Failed to create stock: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def stock_detail(request, pk):
    """Get, update or delete specific stock item."""
    try:
        stock = Stock.objects.get(pk=pk)
    except Stock.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        return Response(StockSerializer(stock).data)
    
    elif request.method == 'PUT':
        try:
            weight_kg = request.data.get('weight_kg')
            if weight_kg is not None:
                weight_kg = float(weight_kg)
                if weight_kg <= 0:
                    return Response(
                        {'error': 'Weight must be greater than 0'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                stock.weight_kg = weight_kg
            
            stock.notes = request.data.get('notes', stock.notes)
            stock.save()
            return Response(StockSerializer(stock).data)
        except ValueError:
            return Response(
                {'error': 'Invalid weight format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    elif request.method == 'DELETE':
        stock.is_active = False
        stock.save()
        return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_by_freshness(request):
    """Separate fresh stock (≤3 days) from expired (>3 days)."""
    now = timezone.now()
    three_days_ago = now - timedelta(days=3)
    
    # Fresh: received within last 3 days AND not expired
    fresh = Stock.objects.filter(
        is_active=True,
        received_date__gte=three_days_ago,
        expiry_date__gt=now
    ).order_by('-received_date')
    
    # Expired/Old: received more than 3 days ago OR past expiry
    expired = Stock.objects.filter(
        is_active=True
    ).filter(
        Q(received_date__lt=three_days_ago) | 
        Q(expiry_date__lte=now)
    ).order_by('expiry_date')
    
    return Response({
        'fresh': StockSerializer(fresh, many=True).data,
        'expired_or_old': StockSerializer(expired, many=True).data,
        'fresh_count': fresh.count(),
        'expired_count': expired.count(),
        'fresh_total_weight': float(sum((s.weight_kg for s in fresh), Decimal('0'))),
        'expired_total_weight': float(sum((s.weight_kg for s in expired), Decimal('0')))
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expiring_stock(request):
    """Get stock expiring within 2 days."""
    expiring = Stock.objects.filter(
        is_active=True,
        expiry_date__lte=timezone.now() + timedelta(days=2)
    ).order_by('expiry_date')
    return Response(StockSerializer(expiring, many=True).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sales_list_create(request):
    """List recent sales or create new sale."""
    if request.method == 'GET':
        sales = Sale.objects.select_related(
            'stock_item', 
            'stock_item__meat_cut', 
            'sold_by'
        ).all().order_by('-sold_at')[:50]
        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        
        # Validate required fields exist
        required_fields = ['stock_id', 'weight_sold', 'price_per_kg']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return Response(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Safely convert to Decimal with error handling
            try:
                stock_id = int(data['stock_id'])
                weight_sold = Decimal(str(data['weight_sold']))
                price_per_kg = Decimal(str(data['price_per_kg']))
            except (ValueError, TypeError, InvalidOperation) as e:
                return Response(
                    {'error': f'Invalid number format: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate positive numbers
            if weight_sold <= 0:
                return Response(
                    {'error': 'Weight sold must be greater than 0'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if price_per_kg <= 0:
                return Response(
                    {'error': 'Price per kg must be greater than 0'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                stock = Stock.objects.select_related('meat_cut').get(
                    id=stock_id, 
                    is_active=True
                )
            except Stock.DoesNotExist:
                return Response(
                    {'error': 'Stock not found or inactive'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if stock.weight_kg < weight_sold:
                return Response(
                    {'error': f'Insufficient stock. Available: {stock.weight_kg}kg, Requested: {weight_sold}kg'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create sale with customer_name
            sale = Sale.objects.create(
                stock_item=stock,
                weight_sold=weight_sold,
                price_per_kg=price_per_kg,
                sold_by=request.user,
                customer_name=data.get('customer_name', '')
            )
            
            # Update stock
            stock.weight_kg -= weight_sold
            if stock.weight_kg <= 0:
                stock.is_active = False
            stock.save()
            
            # Log the sale
            try:
                SystemLog.objects.create(
                    user=request.user,
                    action='SALE',
                    description=f"Sold {weight_sold}kg of {stock.meat_cut.name} for KES {sale.total_price}"
                )
            except Exception as e:
                print(f"Log error: {e}")
            
            # Return serialized sale data
            serializer = SaleSerializer(sale)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Sale creation error: {str(e)}")
            return Response(
                {'error': f'Failed to create sale: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_sales(request):
    """Get today's sales with proper date filtering."""
    today = timezone.now().date()
    
    sales = Sale.objects.select_related(
        'stock_item', 
        'stock_item__meat_cut',
        'sold_by'
    ).filter(
        sold_at__date=today
    ).order_by('-sold_at')
    
    serializer = SaleSerializer(sales, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_by_date(request, year, month, day):
    """Get sales for specific date."""
    try:
        target_date = datetime(year, month, day).date()
    except ValueError:
        return Response({'error': 'Invalid date'}, status=status.HTTP_400_BAD_REQUEST)
    
    sales = Sale.objects.filter(
        sold_at__date=target_date
    ).select_related('stock_item', 'stock_item__meat_cut', 'sold_by')
    
    total_revenue = sum((s.total_price for s in sales), Decimal('0'))
    total_weight = sum((s.weight_sold for s in sales), Decimal('0'))
    
    # Group by meat cut for summary
    cut_summary = {}
    for sale in sales:
        cut_name = sale.meat_cut_name
        if cut_name not in cut_summary:
            cut_summary[cut_name] = {'weight': 0, 'revenue': 0, 'count': 0}
        cut_summary[cut_name]['weight'] += float(sale.weight_sold)
        cut_summary[cut_name]['revenue'] += float(sale.total_price)
        cut_summary[cut_name]['count'] += 1
    
    return Response({
        'date': target_date.isoformat(),
        'sales': SaleSerializer(sales, many=True).data,
        'summary': {
            'count': sales.count(),
            'total_revenue': float(total_revenue),
            'total_weight': float(total_weight)
        },
        'by_cut': cut_summary
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_by_date_range(request):
    """Get sales between start_date and end_date."""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return Response(
            {'error': 'start_date and end_date required (YYYY-MM-DD)'}, 
            status=400
        )
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
            status=400
        )
    
    sales = Sale.objects.filter(
        sold_at__date__gte=start_date,
        sold_at__date__lte=end_date
    ).select_related(
        'stock_item', 
        'stock_item__meat_cut', 
        'sold_by'
    ).order_by('-sold_at')
    
    # Group by date
    daily_data = {}
    for sale in sales:
        date_key = sale.sold_at.strftime('%Y-%m-%d')
        if date_key not in daily_data:
            daily_data[date_key] = {'revenue': 0, 'weight': 0, 'count': 0}
        daily_data[date_key]['revenue'] += float(sale.total_price)
        daily_data[date_key]['weight'] += float(sale.weight_sold)
        daily_data[date_key]['count'] += 1
    
    return Response({
        'start_date': start_date_str,
        'end_date': end_date_str,
        'sales': SaleSerializer(sales, many=True).data,
        'daily_breakdown': daily_data,
        'total_revenue': sum(d['revenue'] for d in daily_data.values()),
        'total_weight': sum(d['weight'] for d in daily_data.values()),
        'total_transactions': sum(d['count'] for d in daily_data.values())
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request):
    """Generate sales report for last N days."""
    try:
        days = int(request.GET.get('days', 7))
        if days <= 0 or days > 365:
            return Response(
                {'error': 'Days must be between 1 and 365'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError:
        return Response(
            {'error': 'Invalid days parameter'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from_date = timezone.now() - timedelta(days=days)
    
    sales = Sale.objects.filter(sold_at__gte=from_date)
    
    # Group by date
    daily_data = {}
    for sale in sales:
        date_key = sale.sold_at.strftime('%Y-%m-%d')
        if date_key not in daily_data:
            daily_data[date_key] = {'revenue': 0, 'weight': 0, 'count': 0}
        daily_data[date_key]['revenue'] += float(sale.total_price)
        daily_data[date_key]['weight'] += float(sale.weight_sold)
        daily_data[date_key]['count'] += 1
    
    return Response({
        'period': f'Last {days} days',
        'daily_breakdown': daily_data,
        'total_revenue': sum(d['revenue'] for d in daily_data.values()),
        'total_weight': sum(d['weight'] for d in daily_data.values()),
        'total_transactions': sum(d['count'] for d in daily_data.values())
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meat_types_list(request):
    """List all meat types."""
    types = MeatType.objects.all()
    serializer = MeatTypeSerializer(types, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meat_cuts_list(request):
    """List all meat cuts."""
    cuts = MeatCut.objects.select_related('meat_type').all()
    serializer = MeatCutSerializer(cuts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meat_cuts_by_type(request, meat_type_id):
    """Get meat cuts for specific meat type."""
    try:
        meat_type = MeatType.objects.get(id=meat_type_id)
    except MeatType.DoesNotExist:
        return Response(
            {'error': 'Meat type not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    cuts = MeatCut.objects.filter(meat_type=meat_type)
    serializer = MeatCutSerializer(cuts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alerts_list(request):
    """Get all active alerts with accurate counting."""
    alerts = []
    
    # Low stock alerts
    for alert in LowStockAlert.objects.filter(is_active=True):
        current_stock = Stock.objects.filter(meat_cut=alert.meat_cut, is_active=True)
        total_weight = sum((s.weight_kg for s in current_stock), Decimal('0'))
        if total_weight < alert.threshold_kg:
            alerts.append({
                'id': f"low_{alert.id}",
                'type': 'low_stock',
                'title': 'Low Stock Alert',
                'message': f"{alert.meat_cut.name} is below threshold ({float(total_weight)}kg < {float(alert.threshold_kg)}kg)",
                'created_at': alert.created_at,
                'severity': 'warning'
            })
    
    # Expiring stock
    expiring = Stock.objects.filter(
        is_active=True,
        expiry_date__lte=timezone.now() + timedelta(days=2)
    )
    for item in expiring:
        days_left = item.days_until_expiry
        alerts.append({
            'id': f"exp_{item.id}",
            'type': 'expiring',
            'title': 'Spoilage Warning',
            'message': f"{item.meat_cut.name} ({item.weight_kg}kg) expires in {days_left} days",
            'created_at': item.received_date,
            'severity': 'danger' if days_left <= 0 else 'warning'
        })
    
    return Response(sorted(alerts, key=lambda x: x['created_at'], reverse=True))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def low_stock_alerts(request):
    """Get low stock alerts only."""
    alerts = []
    for alert in LowStockAlert.objects.filter(is_active=True):
        current_stock = Stock.objects.filter(meat_cut=alert.meat_cut, is_active=True)
        total_weight = sum((s.weight_kg for s in current_stock), Decimal('0'))
        if total_weight < alert.threshold_kg:
            alerts.append({
                'meat_cut': alert.meat_cut.name,
                'current_weight': float(total_weight),
                'threshold': float(alert.threshold_kg)
            })
    return Response(alerts)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_historical(request):
    """View stock status as it was on a specific date."""
    date_str = request.GET.get('date')
    if not date_str:
        return Response(
            {'error': 'Date parameter required (YYYY-MM-DD)'}, 
            status=400
        )
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
            status=400
        )
    
    # Stock that was added on or before that date
    stock_added = Stock.objects.filter(
        received_date__date__lte=target_date
    ).select_related('meat_cut', 'meat_cut__meat_type')
    
    historical_stock = []
    
    for item in stock_added:
        # Calculate how much was sold from this stock before the target date
        sold_before = Sale.objects.filter(
            stock_item=item,
            sold_at__date__lte=target_date
        ).aggregate(total=Sum('weight_sold'))['total'] or Decimal('0')
        
        # Calculate remaining as of target date
        original_weight = item.weight_kg + sold_before
        remaining_on_date = original_weight - sold_before
        
        # Only include if there was still stock remaining on that date
        if remaining_on_date > 0:
            days_since_received = (target_date - item.received_date.date()).days
            status = 'fresh' if days_since_received <= 3 else 'aged'
            is_expired = days_since_received > 3
            
            historical_stock.append({
                'id': item.id,
                'meat_cut_name': item.meat_cut_name,
                'meat_type_name': item.meat_type_name,
                'original_weight': float(original_weight),
                'remaining_on_date': float(remaining_on_date),
                'received_date': item.received_date.isoformat(),
                'days_since_received': days_since_received,
                'status': status,
                'is_expired': is_expired,
                'added_by': item.recorded_by.username if item.recorded_by else 'Unknown'
            })
    
    # Group by status
    fresh_stock = [s for s in historical_stock if s['status'] == 'fresh']
    aged_stock = [s for s in historical_stock if s['status'] == 'aged']
    
    return Response({
        'date': date_str,
        'total_items': len(historical_stock),
        'fresh_count': len(fresh_stock),
        'aged_count': len(aged_stock),
        'total_weight': sum(s['remaining_on_date'] for s in historical_stock),
        'fresh_weight': sum(s['remaining_on_date'] for s in fresh_stock),
        'aged_weight': sum(s['remaining_on_date'] for s in aged_stock),
        'stock_items': historical_stock
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_logs(request):
    """Get system logs (admin only)."""
    if not request.user.is_staff:
        return Response(
            {'error': 'Unauthorized'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    logs = SystemLog.objects.all().order_by('-timestamp')[:100]
    serializer = SystemLogSerializer(logs, many=True)
    return Response(serializer.data)