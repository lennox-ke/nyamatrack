import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nyamatrack.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import MeatType, MeatCut, LowStockAlert

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@nyamatrack.com', 'admin123')
    print("✓ Superuser created: admin / admin123")

# Create default meat types and cuts
meat_data = {
    'Beef': ['Fillet', 'Sirloin', 'Rump', 'Chuck', 'Brisket', 'Ribs', 'Mince'],
    'Goat': ['Leg', 'Shoulder', 'Ribs', 'Mince'],
    'Chicken': ['Whole', 'Breast', 'Drumsticks', 'Wings', 'Mince'],
    'Lamb': ['Leg', 'Chops', 'Shoulder', 'Mince'],
    'Pork': ['Belly', 'Chops', 'Leg', 'Sausages', 'Mince']
}

for meat_name, cuts in meat_data.items():
    meat_type, created = MeatType.objects.get_or_create(name=meat_name)
    if created:
        print(f"✓ Created meat type: {meat_name}")
    
    for cut_name in cuts:
        cut, created = MeatCut.objects.get_or_create(
            meat_type=meat_type,
            name=cut_name
        )
        if created:
            print(f"  ✓ Created cut: {cut_name}")

# Create default low stock alerts
for cut in MeatCut.objects.all():
    LowStockAlert.objects.get_or_create(
        meat_cut=cut,
        defaults={'threshold_kg': 5.00}
    )

print("\n✓ Database initialized successfully!")
print("Login with: admin / admin123")