from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import ContactMessage, ContactReply
from .serializers import ContactMessageSerializer, ContactReplySerializer


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def messages_view(request):
    if request.method == "POST":
        name = request.data.get("name") or ""
        email = request.data.get("email") or ""
        subject = request.data.get("subject") or ""
        message_text = request.data.get("message") or ""
        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        obj = ContactMessage.objects.create(user=user, name=name, email=email, subject=subject, message=message_text, status="open")
        ser = ContactMessageSerializer(obj)
        return Response(ser.data, status=status.HTTP_201_CREATED)
    if not getattr(request, "user", None) or not request.user.is_staff:
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    qs = ContactMessage.objects.order_by("-created_at")
    ser = ContactMessageSerializer(qs, many=True)
    return Response(ser.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def message_detail_view(request, pk: int):
    msg = ContactMessage.objects.filter(id=pk).first()
    if not msg:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        if not getattr(request, "user", None) or not request.user.is_staff:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        ser = ContactMessageSerializer(msg)
        return Response(ser.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def reply_view(request, pk: int):
    msg = ContactMessage.objects.filter(id=pk).first()
    if not msg:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if not getattr(request, "user", None) or not request.user.is_staff:
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    text = request.data.get("text") or request.data.get("message") or ""
    if not text.strip():
        return Response({"detail": "Reply text required"}, status=status.HTTP_400_BAD_REQUEST)
    rep = ContactReply.objects.create(message=msg, sender=request.user, sender_type="admin", text=text.strip())
    ser = ContactReplySerializer(rep)
    msg.status = "open"
    msg.save(update_fields=["status"])
    return Response(ser.data, status=status.HTTP_201_CREATED)
