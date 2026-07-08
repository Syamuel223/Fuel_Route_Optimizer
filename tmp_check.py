import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuel_route_app.settings')
import django
django.setup()
from route_optimizer.models import FuelStation
out = f"count={FuelStation.objects.count()}\nwith_coords={FuelStation.objects.filter(latitude__isnull=False, longitude__isnull=False).count()}"
with open('tmp_check.txt', 'w', encoding='utf-8') as f:
    f.write(out)
