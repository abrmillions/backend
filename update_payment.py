import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from payments.models import Payment

try:
    # Get the first pending payment
    payment = Payment.objects.filter(status__iexact='pending').first()
    if payment:
        print(f"Updating payment ID {payment.id} from {payment.status} to 'success'...")
        payment.status = 'success'
        payment.save()
        print(f"Successfully updated payment ID {payment.id}.")
        
        # Verify the update
        updated_payment = Payment.objects.get(id=payment.id)
        print(f"Verification: Payment ID {updated_payment.id} status is now {updated_payment.status}")
    else:
        print("No pending payments found to update.")

except Exception as e:
    print(f"Error: {e}")
