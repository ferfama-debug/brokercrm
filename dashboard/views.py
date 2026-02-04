from django.shortcuts import render
from alerts.models import Alert
from policies.models import Policy
from datetime import date, timedelta

def dashboard_view(request):
    alerts = Alert.objects.filter(resolved=False).order_by('-created_at')[:10]

    today = date.today()
    limit_date = today + timedelta(days=30)

    upcoming_policies = Policy.objects.filter(
        end_date__gte=today,
        end_date__lte=limit_date
    ).order_by('end_date')

    return render(request, 'dashboard/dashboard.html', {
        'alerts': alerts,
        'upcoming_policies': upcoming_policies
    })
