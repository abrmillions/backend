from rest_framework import serializers
from .models import License
from datetime import date


class LicenseSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    can_download = serializers.SerializerMethodField()
    license_photo_url = serializers.SerializerMethodField()
    license_photo_base64 = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()
    holder_full_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    downloaded = serializers.SerializerMethodField()

    class Meta:
        model = License
        # expose system-generated license_number and key dates for frontend
        fields = (
            "id",
            "owner",
            "holder_full_name",
            "company_name",
            "license_type",
            "license_number",
            "issued_date",
            "expiry_date",
            "qr_code_data",
            "data",
            "license_photo_url",
            "license_photo_base64",
            "application_status",
            "status",
            "created_at",
            "can_download",
            "grade",
            "downloaded",
        )
        read_only_fields = ("id", "owner", "created_at", "license_number", "issued_date", "expiry_date", "qr_code_data", "can_download")

    def get_downloaded(self, obj):
        if obj.data and isinstance(obj.data, dict):
            return obj.data.get('downloaded', False)
        return False

    def get_can_download(self, obj):
        """Return whether the current request user may download this license.

        Rules: only owner or staff may download, and license must be approved/active
        and not expired.
        """
        request = self.context.get('request') if isinstance(self.context, dict) else None
        user = getattr(request, 'user', None)
        # Only owner or staff can download
        if not user:
            return False
        if not (user == obj.owner or getattr(user, 'is_staff', False)):
            return False

        # Status must be approved or active
        if obj.status not in ('approved', 'active'):
            return False

        # Must not be expired
        if getattr(obj, 'expiry_date', None) and obj.expiry_date < date.today():
            return False

        return True

    def _get_effective_photo(self, obj):
        """
        Helper to find the best available photo for a license.
        Checks current license, then looks back at previous licenses (renewals/replacements),
        then linked application fields, then application documents, then owner profile.
        """
        # 1. Try current license photo
        photo = getattr(obj, 'license_photo', None)
        if photo:
            try:
                if photo.name:
                    return photo
            except Exception:
                pass

        # 2. Look back at previous licenses (inheritance)
        curr = obj
        seen = {curr.id}
        # Iterate back through previous_license or replaces_license chain
        while True:
            prev = getattr(curr, 'previous_license', None) or getattr(curr, 'replaces_license', None)
            if not prev or not hasattr(prev, 'id') or prev.id in seen:
                break
            seen.add(prev.id)
            if getattr(prev, 'license_photo', None):
                try:
                    if prev.license_photo.name:
                        return prev.license_photo
                except Exception:
                    pass
            curr = prev

        # 3. Fallback to linked application photo if available
        try:
            from applications.models import Application
            from django.db.models import Q
            
            app_id = None
            if isinstance(obj.data, dict):
                app_id = obj.data.get('application_id')
            
            app = None
            if app_id:
                app = Application.objects.filter(id=app_id).first()
            
            # Helper to extract photo from an application
            def get_app_photo(a):
                if not a: return None
                lt = getattr(a, 'license_type', None) or getattr(obj, 'license_type', None)
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
                
                # Check linked Document images
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
                return None

            # Try the explicitly linked application first
            photo = get_app_photo(app)
            if photo:
                return photo
            
            # If no photo in linked app, search ALL applications for this owner/type
            other_apps = Application.objects.filter(
                applicant=obj.owner, 
                license_type=obj.license_type
            ).filter(
                Q(profile_photo__isnull=False) | 
                Q(professional_photo__isnull=False) | 
                Q(company_representative_photo__isnull=False)
            ).order_by('-created_at')
            
            for oa in other_apps:
                photo = get_app_photo(oa)
                if photo:
                    return photo

        except Exception:
            pass

        # 4. Fallback to owner's profile photo
        try:
            owner = getattr(obj, 'owner', None)
            if owner:
                pf = getattr(owner, 'profile_photo', None)
                if pf:
                    try:
                        if pf.name:
                            return pf
                    except Exception:
                        pass
        except Exception:
            pass

        return None

    def get_license_photo_url(self, obj):
        request = self.context.get('request') if isinstance(self.context, dict) else None
        photo = self._get_effective_photo(obj)
        if photo:
            try:
                url = photo.url
                if request:
                    return request.build_absolute_uri(url)
                return url
            except Exception:
                pass
        return None
    
    def get_license_photo_base64(self, obj):
        try:
            def to_b64(p):
                import base64
                import mimetypes
                if not p or not hasattr(p, 'open'):
                    return None
                try:
                    p.open('rb')
                    content = p.read()
                    b64 = base64.b64encode(content).decode('ascii')
                    mime = None
                    try:
                        mime = mimetypes.guess_type(getattr(p, 'name', ''), strict=False)[0]
                    except Exception:
                        mime = None
                    if not mime:
                        mime = 'image/jpeg'
                    return f"data:{mime};base64,{b64}"
                finally:
                    try:
                        p.close()
                    except Exception:
                        pass

            photo = self._get_effective_photo(obj)
            return to_b64(photo)
        except Exception:
            pass
        return None


    def get_application_status(self, obj):
        # Try to find linked application id in license data and return its status
        try:
            app_id = None
            if isinstance(obj.data, dict):
                app_id = obj.data.get('application_id')
            if app_id:
                from applications.models import Application
                app = Application.objects.filter(id=app_id).first()
                if app:
                    return app.status
        except Exception:
            pass
        return None

    def get_holder_full_name(self, obj):
        try:
            owner = getattr(obj, 'owner', None)
            if owner:
                fn = getattr(owner, 'get_full_name', None)
                if callable(fn):
                    name = fn()
                    if name and str(name).strip():
                        return str(name).strip()
                return getattr(owner, 'email', getattr(owner, 'username', None))
        except Exception:
            return None

    def get_company_name(self, obj):
        try:
            # Prefer explicit company_name/companyName in license data
            if isinstance(obj.data, dict):
                val = obj.data.get('company_name') or obj.data.get('companyName')
                if val and str(val).strip():
                    return str(val).strip()
                # Fallback: pull from linked application, if present
                app_id = obj.data.get('application_id')
                if app_id:
                    from applications.models import Application
                    app = Application.objects.filter(id=app_id).first()
                    if app and isinstance(app.data, dict):
                        val2 = app.data.get('company_name') or app.data.get('companyName')
                        if val2 and str(val2).strip():
                            return str(val2).strip()
            return None
        except Exception:
            return None

    def get_grade(self, obj):
        try:
            lt = getattr(obj, 'license_type', '') or ''
            if 'contractor' not in str(lt).lower():
                return None
            d = obj.data if isinstance(obj.data, dict) else {}
            raw = d.get('grade') or d.get('licenseType') or d.get('category')
            if not raw:
                return None
            s = str(raw).strip().lower()
            if 'grade-a' in s or s == 'a' or 'grade a' in s:
                return 'Grade A'
            if 'grade-b' in s or s == 'b' or 'grade b' in s:
                return 'Grade B'
            if 'grade-c' in s or s == 'c' or 'grade c' in s:
                return 'Grade C'
            if 'specialized' in s:
                return 'Specialized Contractor'
            return str(raw)
        except Exception:
            return None
