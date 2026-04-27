import uuid
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from payments.models import Payment
from payments.services.chapa_service import ChapaService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment(request):

    user = request.user

    tx_ref = f"license-{uuid.uuid4()}"

    amount = request.data.get("amount")
    metadata = request.data.get("metadata")

    payment = Payment.objects.create(
        payer=user,
        tx_ref=tx_ref,
        amount=amount,
        email=user.email,
        description="Construction License Payment",
        metadata=metadata
    )

    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": user.email,
        "first_name": user.first_name or user.username or "User",
        "last_name": user.last_name or "Applicant",
        "tx_ref": tx_ref,
        "callback_url": f"{settings.FRONTEND_URL}/payment/callback",
        "return_url": f"{settings.FRONTEND_URL}/payment/success"
    }

    try:
        chapa = ChapaService.initialize_payment(payload)
        
        # Save checkout_url from Chapa response
        if chapa.get("status") == "success" and "data" in chapa:
            checkout_url = chapa["data"].get("checkout_url")
            if checkout_url:
                payment.checkout_url = checkout_url
                payment.save()
            chapa["data"]["tx_ref"] = tx_ref

        return JsonResponse(chapa)
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Chapa Initialization Error: {error_msg}")
        print(traceback.format_exc())
        
        # Friendly message for connection issues
        friendly_message = "Failed to initialize payment. Please check your internet connection."
        if "Failed to resolve" in error_msg or "getaddrinfo failed" in error_msg or "ConnectionError" in error_msg:
            error_msg = friendly_message

        return JsonResponse({
            "status": "error",
            "message": error_msg if error_msg else "Unable to process payment. Please try again."
        }, status=500)
