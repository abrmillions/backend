from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.text import slugify
import io
import zipfile

from .models import Application, ApplicationLog
from documents.models import Document, DocumentAccessLog


class DocumentInline(admin.TabularInline):
    model = Document
    fields = ("name", "file_link", "uploaded_at")
    readonly_fields = ("file_link", "uploaded_at")
    extra = 0

    def file_link(self, obj):
        try:
            storage = obj.file.storage
            if not storage.exists(obj.file.name):
                return format_html('<span style="color: #c00;">Missing file</span>')
            return format_html('<a href="{}" target="_blank" rel="noopener">Download</a>', obj.file.url)
        except Exception:
            return "-"


class ApplicationLogInline(admin.TabularInline):
    model = ApplicationLog
    readonly_fields = ("actor", "action", "details", "timestamp")
    extra = 0
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "applicant", "license_type", "status", "created_at")
    list_filter = ("license_type", "status")
    search_fields = ("applicant__email",)
    inlines = (DocumentInline, ApplicationLogInline)
    actions = ("download_documents_zip",)
    exclude = ("profile_photo", "professional_photo", "company_representative_photo")
    readonly_fields = ("preview_certificate_photo",)
    fields = (
        "applicant",
        "license_type",
        "subtype",
        "status",
        "data",
        "preview_certificate_photo",
    )

    def save_model(self, request, obj, form, change):
        prev_status = None
        if obj.pk:
            try:
                prev = Application.objects.get(pk=obj.pk)
                prev_status = prev.status
            except Application.DoesNotExist:
                prev_status = None
        super().save_model(request, obj, form, change)
        try:
            if obj.status == "approved":
                from datetime import date
                from licenses.models import License
                today = date.today()
                year = today.year
                prefix = "LIC"
                license_qs = License.objects.filter(owner=obj.applicant, license_type=obj.license_type)
                lic = None
                if license_qs.exists():
                    lic = license_qs.first()
                    license_number = lic.license_number or ""
                else:
                    seq = License.objects.count() + 1
                    while True:
                        candidate = f"{prefix}-{year:04d}-{seq:06d}"
                        if not License.objects.filter(license_number=candidate).exists():
                            license_number = candidate
                            break
                        seq += 1
                expiry = date(today.year + 5, today.month, today.day)
                base_data = obj.data if isinstance(obj.data, dict) else {}
                company_name = None
                if isinstance(base_data, dict):
                    cn = base_data.get("companyName") or base_data.get("company_name") or base_data.get("company")
                    if cn and isinstance(cn, str):
                        company_name = cn.strip()
                merged_data = {
                    **(base_data or {}),
                    "subtype": obj.subtype,
                    "licenseNumber": license_number,
                    "issueDate": today.isoformat(),
                    "expiryDate": expiry.isoformat(),
                    "application_id": obj.id,
                }
                if company_name and not merged_data.get("companyName"):
                    merged_data["companyName"] = company_name
                if lic is None:
                    lic = License.objects.create(
                        owner=obj.applicant,
                        license_type=obj.license_type,
                        license_number=license_number,
                        issued_by=request.user,
                        issued_date=today,
                        expiry_date=expiry,
                        data=merged_data,
                        status="active",
                    )
                else:
                    lic.issued_by = lic.issued_by or request.user
                    lic.issued_date = lic.issued_date or today
                    lic.expiry_date = lic.expiry_date or expiry
                    new_data = lic.data if isinstance(lic.data, dict) else {}
                    new_data.update(merged_data)
                    lic.data = new_data
                    if lic.status in ("pending", "approved"):
                        lic.status = "active"
                    lic.save()
                    candidates = []
                    if obj.license_type == "Contractor License":
                        candidates.append(obj.profile_photo)
                    elif obj.license_type == "Professional License":
                        candidates.append(obj.professional_photo)
                    elif obj.license_type == "Import/Export License":
                        candidates.append(obj.company_representative_photo)
                    candidates.extend([obj.profile_photo, obj.professional_photo, obj.company_representative_photo])
                    photo_field = next((f for f in candidates if f), None)
                    if photo_field and getattr(photo_field, "name", None):
                        from django.core.files.base import ContentFile
                        import os
                        try:
                            photo_field.open("rb")
                            try:
                                name = os.path.basename(photo_field.name)
                                content = photo_field.read()
                                lic.license_photo.save(name, ContentFile(content))
                            finally:
                                try:
                                    photo_field.close()
                                except Exception:
                                    pass
                        except Exception:
                            try:
                                lic.license_photo = photo_field
                            except Exception:
                                pass
                        lic.save(update_fields=["license_photo"])
                    else:
                        try:
                            docs = getattr(obj, "documents", None)
                            chosen = None
                            if docs:
                                for doc in docs.all():
                                    f = getattr(doc, "file", None)
                                    name = getattr(f, "name", "")
                                    if isinstance(name, str) and name.lower().split(".")[-1] in ("jpg", "jpeg", "png", "gif", "webp"):
                                        chosen = f
                                        break
                            if chosen:
                                from django.core.files.base import ContentFile
                                import os
                                storage = chosen.storage
                                fh = None
                                try:
                                    fh = storage.open(chosen.name, "rb")
                                    content = fh.read()
                                    basename = os.path.basename(chosen.name)
                                    lic.license_photo.save(basename, ContentFile(content))
                                    lic.save(update_fields=["license_photo"])
                                finally:
                                    try:
                                        if fh:
                                            fh.close()
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    try:
                        app_data = obj.data if isinstance(obj.data, dict) else {}
                        app_data["licenseNumber"] = license_number
                        app_data["license_number"] = license_number
                        obj.data = app_data
                        obj.save(update_fields=["data"])
                    except Exception:
                        pass
                    try:
                        if prev_status != "approved":
                            ApplicationLog.objects.create(
                                application=obj,
                                actor=request.user,
                                action="approved",
                                details="Approved via admin",
                            )
                    except Exception:
                        pass
        except Exception:
            pass

    def preview_certificate_photo(self, obj):
        try:
            candidates = []
            if obj.license_type == "Contractor License":
                candidates.append(obj.profile_photo)
            elif obj.license_type == "Professional License":
                candidates.append(obj.professional_photo)
            elif obj.license_type == "Import/Export License":
                candidates.append(obj.company_representative_photo)
            candidates.extend([obj.profile_photo, obj.professional_photo, obj.company_representative_photo])
            for f in candidates:
                if f:
                    url = getattr(f, "url", None)
                    if url:
                        return format_html('<img src="{}" style="max-width:200px; height:auto; border:1px solid #ddd;"/>', url)
        except Exception:
            pass
        return "-"

    preview_certificate_photo.short_description = "Certificate Photo"

    def download_documents_zip(self, request, queryset):
        """Admin action: create a zip of all documents for selected applications and return it as a response."""
        buffer = io.BytesIO()
        z = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)
        files_added = 0

        for app in queryset.select_related("applicant").prefetch_related("documents"):
            applicant_email = app.applicant.email if app.applicant else f"app_{app.id}"
            folder = slugify(applicant_email)
            for doc in app.documents.all():
                try:
                    # ensure file exists
                    storage = doc.file.storage
                    if not storage.exists(doc.file.name):
                        continue
                    with storage.open(doc.file.name, "rb") as fh:
                        data = fh.read()
                    arcname = f"{folder}/{doc.name or doc.file.name}"
                    z.writestr(arcname, data)
                    files_added += 1
                    # Log access
                    try:
                        DocumentAccessLog.objects.create(
                            user=request.user if request.user.is_authenticated else None,
                            document=doc,
                            application=app,
                            action="download",
                            details=f"Downloaded as part of admin zip for application {app.id}",
                        )
                    except Exception:
                        pass
                except Exception:
                    # skip any unreadable files
                    continue

        z.close()
        if files_added == 0:
            self.message_user(request, "No documents available to download for selected applications.")
            return None

        buffer.seek(0)
        resp = HttpResponse(buffer.getvalue(), content_type="application/zip")
        resp["Content-Disposition"] = "attachment; filename=applications_documents.zip"
        return resp

    download_documents_zip.short_description = "Download documents for selected applications (zip)"
