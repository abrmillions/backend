from rest_framework import serializers
from .models import Application, ApplicationLog, Notification
import json


class NotificationSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'user', 'application', 'title', 'message', 'is_read', 'created_at', 'type']
        read_only_fields = ['id', 'user', 'created_at']

    def get_type(self, obj):
        if obj.application:
            return "application"
        if "Registration" in obj.title or "User" in obj.title:
            return "registration"
        if "Contact" in obj.title or "Message" in obj.title:
            return "contact"
        return "general"


class ApplicationLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.ReadOnlyField(source='actor.get_full_name')
    actor_email = serializers.ReadOnlyField(source='actor.email')

    class Meta:
        model = ApplicationLog
        fields = ['id', 'actor', 'actor_name', 'actor_email', 'action', 'details', 'timestamp']


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = serializers.ReadOnlyField(source="applicant.email")
    applicant_name = serializers.ReadOnlyField(source="applicant.get_full_name")
    previous_license_id = serializers.ReadOnlyField(source="previous_license.id")
    data = serializers.JSONField(required=False, allow_null=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    professional_photo = serializers.ImageField(required=False, allow_null=True)
    company_representative_photo = serializers.ImageField(required=False, allow_null=True)
    effective_photo_url = serializers.SerializerMethodField()
    logs = ApplicationLogSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "applicant",
            "applicant_name",
            "license_type",
            "subtype",
            "status",
            "data",
            "profile_photo",
            "professional_photo",
            "company_representative_photo",
            "effective_photo_url",
            "created_at",
            "updated_at",
            "logs",
            "previous_license_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "logs"]

    def get_effective_photo_url(self, obj):
        """
        Robustly find the best available photo for this application.
        Useful for admin review of renewals where the applicant didn't upload a new photo.
        """
        request = self.context.get('request')
        
        # 1. Try application's own photos first (explicitly uploaded)
        mapping = {
            "Contractor License": "profile_photo",
            "Professional License": "professional_photo",
            "Import/Export License": "company_representative_photo",
        }
        preferred_field = mapping.get(obj.license_type)
        if preferred_field:
            photo = getattr(obj, preferred_field, None)
            if photo and hasattr(photo, 'name') and photo.name:
                return request.build_absolute_uri(photo.url) if request else photo.url

        # Fallback to other application photos
        for fld in ["profile_photo", "professional_photo", "company_representative_photo"]:
            photo = getattr(obj, fld, None)
            if photo and hasattr(photo, 'name') and photo.name:
                return request.build_absolute_uri(photo.url) if request else photo.url

        # 2. If it's a renewal, look back at the previous license's photo
        if obj.is_renewal and obj.previous_license:
            try:
                from licenses.serializers import LicenseSerializer
                ls = LicenseSerializer(context=self.context)
                url = ls.get_license_photo_url(obj.previous_license)
                if url:
                    return url
            except Exception:
                pass

        # 3. Fallback to owner's profile photo
        if obj.applicant:
            profile_photo = getattr(obj.applicant, 'profile_photo', None)
            if profile_photo and hasattr(profile_photo, 'name') and profile_photo.name:
                try:
                    return request.build_absolute_uri(profile_photo.url) if request else profile_photo.url
                except Exception:
                    pass

        return None

    def to_internal_value(self, data):
        try:
            d = dict(data)
            if "data" in d:
                val = d["data"]
                if isinstance(val, (list, tuple)) and val:
                    val = val[0]
                if isinstance(val, str):
                    try:
                        d["data"] = json.loads(val)
                    except Exception:
                        d["data"] = val
            return super().to_internal_value(d)
        except Exception:
            return super().to_internal_value(data)

    def validate(self, attrs):
        request = self.context.get("request")
        method = getattr(request, "method", None) if request else None
        license_type = attrs.get("license_type") or (self.instance.license_type if self.instance else None)
        mapping = {
            "profile_photo": "profile_photo",
            "professional_photo": "professional_photo",
            "company_representative_photo": "company_representative_photo",
        }
        required_field = mapping.get(license_type)
        if required_field:
            provided = attrs.get(required_field) or (self.instance and getattr(self.instance, required_field))
            if not provided:
                if method in ("PUT", "PATCH"):
                    raise serializers.ValidationError({required_field: "This photo is required for the selected license type."})

        # Reject non-image uploads (ImageField handles basic validation but be explicit)
        for fld in ("profile_photo", "professional_photo", "company_representative_photo"):
            fval = attrs.get(fld)
            if fval is not None and hasattr(fval, "content_type"):
                if not fval.content_type.startswith("image/"):
                    raise serializers.ValidationError({fld: "Uploaded file must be an image."})

        return super().validate(attrs)
