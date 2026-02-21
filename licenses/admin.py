from django.contrib import admin
from django.utils.html import format_html
from .models import License
from applications.models import Application


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "license_type", "status", "created_at")
    list_filter = ("license_type", "status")
    search_fields = ("owner__username", "data")
    exclude = ("license_photo",)
    readonly_fields = ("preview_license_photo",)
    fields = (
        "owner",
        "license_type",
        "license_number",
        "issued_by",
        "issued_date",
        "expiry_date",
        "status",
        "data",
        "preview_license_photo",
    )

    def preview_license_photo(self, obj):
        try:
            f = getattr(obj, "license_photo", None)
            url = getattr(f, "url", None)
            if url:
                return format_html('<img src="{}" style="max-width:200px; height:auto; border:1px solid #ddd;"/>', url)
        except Exception:
            pass
        try:
            app_id = None
            if isinstance(obj.data, dict):
                app_id = obj.data.get("application_id")
            app = None
            if app_id:
                app = Application.objects.filter(id=app_id).first()
            if not app:
                app = Application.objects.filter(applicant=obj.owner, license_type=obj.license_type).order_by("-created_at").first()
            if app:
                for fld in ("profile_photo", "professional_photo", "company_representative_photo"):
                    af = getattr(app, fld, None)
                    if af:
                        url = getattr(af, "url", None)
                        if url:
                            return format_html('<img src="{}" style="max-width:200px; height:auto; border:1px solid #ddd;"/>', url)
        except Exception:
            pass
        return "-"
