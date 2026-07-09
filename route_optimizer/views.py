import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import RoutePlanningError, plan_fuel_stops


def index(request):
    return render(request, 'index.html')


@require_http_methods(['GET', 'POST'])
def route_api(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    else:
        payload = request.GET.dict()

    start = payload.get('start')
    finish = payload.get('finish')
    if not start or not finish:
        return JsonResponse({'error': 'Both start and finish parameters are required.'}, status=400)

    max_range_miles = float(payload.get('max_range_miles', 500))
    fuel_efficiency_mpg = float(payload.get('fuel_efficiency_mpg', 10))

    try:
        result = plan_fuel_stops(
            start=start,
            finish=finish,
            max_range_miles=max_range_miles,
            fuel_efficiency_mpg=fuel_efficiency_mpg,
        )
    except RoutePlanningError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except Exception as exc:  # pragma: no cover - defensive guard
        return JsonResponse({'error': f'Unexpected server error: {exc}'}, status=500)

    return JsonResponse(result)


def health_view(request):
    return JsonResponse({'status': 'ok'})
