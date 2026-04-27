from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
import re
from datetime import date
from licenses.models import License

@require_GET
def verify_by_number(request):
    num = (request.GET.get('licenseNumber') or request.GET.get('license_number') or '').strip()
    if not num:
        return JsonResponse({"valid": False, "detail": "License number is required."}, status=400)
    s = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]", "-", num)
    lic = (
        License.objects.filter(Q(license_number__iexact=s)).first()
        or License.objects.filter(
            Q(data__licenseNumber__iexact=s)
            | Q(data__license_number__iexact=s)
            | Q(data__registrationNumber__iexact=s)
            | Q(data__registration_number__iexact=s)
        ).first()
    )
    if not lic:
        return JsonResponse({"valid": False, "detail": "The license number you entered was not found in the database."}, status=404)
    not_expired = True
    try:
        if lic.expiry_date:
            not_expired = lic.expiry_date >= date.today()
    except Exception:
        not_expired = True

    # Get holder name from various possible locations
    holder_name = ""
    if lic.owner:
        holder_name = lic.owner.get_full_name() or lic.owner.username
    if not holder_name and isinstance(lic.data, dict):
        holder_name = lic.data.get("full_name") or lic.data.get("fullName") or lic.data.get("applicant_name")

    # Find the effective photo using the full inheritance chain
    effective_photo = None

    # 1. Try current license photo
    if not effective_photo:
        photo = getattr(lic, 'license_photo', None)
        if photo:
            try:
                if photo.name:
                    effective_photo = photo
            except Exception:
                pass

    # 2. Look back at previous licenses (renewal chain)
    if not effective_photo:
        curr = lic
        seen = {curr.id}
        while True:
            prev = getattr(curr, 'previous_license', None) or getattr(curr, 'replaces_license', None)
            if not prev or not hasattr(prev, 'id') or prev.id in seen:
                break
            seen.add(prev.id)
            prev_photo = getattr(prev, 'license_photo', None)
            if prev_photo:
                try:
                    if prev_photo.name:
                        effective_photo = prev_photo
                        break
                except Exception:
                    pass
            curr = prev

    # 3. Linked application photo
    if not effective_photo:
        try:
            from applications.models import Application
            app_id = None
            if isinstance(lic.data, dict):
                app_id = lic.data.get('application_id')

            app = None
            if app_id:
                app = Application.objects.filter(id=app_id).first()

            # Helper to extract photo from an application
            def get_app_photo(a):
                if not a: return None
                lt = getattr(a, 'license_type', None) or getattr(lic, 'license_type', None)
                if lt == "Contractor License":
                    preferred = ('profile_photo', 'professional_photo', 'company_representative_photo')
                elif lt == "Professional License":
                    preferred = ('professional_photo', 'profile_photo', 'company_representative_photo')
                elif lt == "Import/Export License":
                    preferred = ('company_representative_photo', 'profile_photo', 'professional_photo')
                else:
                    preferred = ('profile_photo', 'professional_photo', 'company_representative_photo')

                for fld in preferred:
                    af = getattr(a, fld, None)
                    if af and hasattr(af, 'name') and af.name:
                        return af
                
                # Check data dictionary for photos
                if isinstance(a.data, dict):
                    # Check for photo URLs or base64 in data
                    for key in ('profile_photo', 'professional_photo', 'company_representative_photo', 'photo', 'photo_url'):
                        val = a.data.get(key)
                        if val and isinstance(val, str):
                            return val

                # Check linked Document images
                try:
                    docs = getattr(a, 'documents', None)
                    if docs:
                        for doc in docs.all():
                            try:
                                f = getattr(doc, 'file', None)
                                name = getattr(f, 'name', '')
                                if isinstance(name, str) and name.lower().split('.')[-1] in ('jpg','jpeg','png','gif','webp'):
                                    if f and f.name:
                                        return f
                            except Exception:
                                continue
                except Exception:
                    pass
                return None

            # Try the explicitly linked application first
            effective_photo = get_app_photo(app)
            
            # If no photo in linked app, search ALL applications for this owner
            if not effective_photo:
                other_apps = Application.objects.filter(
                    applicant=lic.owner
                ).filter(
                    Q(profile_photo__isnull=False) |
                    Q(professional_photo__isnull=False) |
                    Q(company_representative_photo__isnull=False)
                ).order_by('-created_at')

                for oa in other_apps:
                    effective_photo = get_app_photo(oa)
                    if effective_photo:
                        break
        except Exception:
            pass

    # 4. Owner profile photo
    if not effective_photo and lic.owner:
        try:
            pf = getattr(lic.owner, 'profile_photo', None)
            if pf:
                try:
                    if pf.name:
                        effective_photo = pf
                except Exception:
                    pass
        except Exception:
            pass

    # 5. data dictionary fallback
    if not effective_photo and isinstance(lic.data, dict):
        effective_photo = lic.data.get("photo_url") or lic.data.get("photo") or lic.data.get("license_photo_url")

    # Derive photo_url and photo_base64 from effective_photo
    photo_url = ""
    photo_base64 = ""

    if effective_photo:
        if isinstance(effective_photo, str):
            # If it's a string, it could be a URL or a base64 string
            if effective_photo.startswith('data:'):
                photo_url = "" # Can't use data URL as photo_url easily in some contexts
                photo_base64 = effective_photo
            elif effective_photo.startswith('http'):
                photo_url = effective_photo
                # Try to fetch and convert to base64 to avoid CORS issues in frontend
                try:
                    import requests, base64, mimetypes
                    resp = requests.get(effective_photo, timeout=5)
                    if resp.status_code == 200:
                        b64 = base64.b64encode(resp.content).decode('ascii')
                        mime = resp.headers.get('Content-Type') or mimetypes.guess_type(effective_photo)[0] or 'image/jpeg'
                        photo_base64 = f"data:{mime};base64,{b64}"
                    else:
                        photo_base64 = effective_photo
                except Exception:
                    photo_base64 = effective_photo
            else:
                # Assume relative URL
                try:
                    photo_url = request.build_absolute_uri(effective_photo)
                    # Try to read from disk if it's a media file to avoid CORS
                    if '/media/' in photo_url or effective_photo.startswith('/media/'):
                        try:
                            import os
                            from django.conf import settings
                            # Extract relative path from media root
                            if 'media/' in effective_photo:
                                rel_path = effective_photo.split('media/')[-1]
                            else:
                                rel_path = effective_photo
                            
                            full_path = os.path.join(settings.MEDIA_ROOT, rel_path.lstrip('/'))
                            if os.path.exists(full_path):
                                import base64, mimetypes
                                with open(full_path, 'rb') as f:
                                    b64 = base64.b64encode(f.read()).decode('ascii')
                                    mime = mimetypes.guess_type(full_path)[0] or 'image/jpeg'
                                    photo_base64 = f"data:{mime};base64,{b64}"
                            else:
                                photo_base64 = photo_url
                        except Exception:
                            photo_base64 = photo_url
                    else:
                        photo_base64 = photo_url
                except Exception:
                    photo_url = effective_photo
                    photo_base64 = effective_photo
        else:
            try:
                photo_url = request.build_absolute_uri(effective_photo.url)
            except Exception:
                pass
            try:
                import base64, mimetypes
                effective_photo.open('rb')
                content = effective_photo.read()
                b64 = base64.b64encode(content).decode('ascii')
                mime = mimetypes.guess_type(getattr(effective_photo, 'name', ''), strict=False)[0] or 'image/jpeg'
                photo_base64 = f"data:{mime};base64,{b64}"
                effective_photo.close()
            except Exception:
                pass

    data = {
        "id": lic.id,
        "license_number": lic.license_number or s,
        "license_type": lic.license_type,
        "holder_name": holder_name,
        "photo_url": photo_url,
        "license_photo_url": photo_url,
        "license_photo_base64": photo_base64,
        "status": lic.status,
        "issued_date": getattr(lic, "issued_date", None),
        "expiry_date": getattr(lic, "expiry_date", None),
        "company_name": (isinstance(lic.data, dict) and (lic.data.get("company_name") or lic.data.get("companyName"))) or "",
        "valid": (str(lic.status or "").lower() in ("approved", "active", "expired", "renewed")),
        "is_expired": not not_expired,
        "data": lic.data,
    }
    return JsonResponse(data, status=200)
