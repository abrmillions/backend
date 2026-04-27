import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from payments.models import Payment
from django.db.models import Sum, Q

try:
    print(f"Total Payments: {Payment.objects.count()}")
    
    # Check all statuses
    statuses = list(Payment.objects.values_list('status', flat=True).distinct())
    print(f"Unique Statuses: {statuses}")
    
    # Check all currencies
    currencies = list(Payment.objects.values_list('currency', flat=True).distinct())
    print(f"Unique Currencies: {currencies}")
    
    # Check specific filtering
    success_count = Payment.objects.filter(status__iexact='success').count()
    active_count = Payment.objects.filter(status__iexact='active').count()
    paid_count = Payment.objects.filter(status__iexact='paid').count()
    print(f"Counts - Success: {success_count}, Active: {active_count}, Paid: {paid_count}")
    
    # Calculate revenue
    total_rev = Payment.objects.filter(
        Q(status__iexact='success') | Q(status__iexact='active') | Q(status__iexact='paid')
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    print(f"Total Revenue (all currencies): {total_rev}")
    
    # ETB Revenue
    etb_rev = Payment.objects.filter(
        (Q(status__iexact='success') | Q(status__iexact='active') | Q(status__iexact='paid')),
        currency__iexact='ETB'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    print(f"Total ETB Revenue: {etb_rev}")

    # Sample pending payments
    print("\nSample Pending Payments:")
    pending_samples = Payment.objects.filter(status__iexact='pending')[:5]
    for p in pending_samples:
        print(f"ID: {p.id}, Amount: {p.amount}, Currency: {p.currency}, Status: {p.status}")

except Exception as e:
    print(f"Error: {e}")
