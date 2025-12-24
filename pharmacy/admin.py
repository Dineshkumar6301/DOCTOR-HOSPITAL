from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Doctor, Patient, Appointment, Clinic, Education, Experience,TimeSlot,Service
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model
from .models import ClinicListing, ClinicService,Award,Review, DoctorListing,Speciality, SubmitReview
from .models import Booking,ReportFile
from .models import (
    BloodBank, BloodInventory, BloodRequest,
    DonorRecord,BloodDispatch,TestCategory, DiagnosticTest
)


User = get_user_model()
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        'email', 'first_name', 'last_name',
        'is_clinic', 'is_doctor', 'is_patient', 'is_staff', 'is_superuser'
    )
    list_filter = (
        'is_clinic', 'is_doctor', 'is_patient', 'is_staff', 'is_superuser'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Role Flags', {'fields': ('is_clinic', 'is_doctor', 'is_patient')}),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'password1', 'password2',
                'is_clinic', 'is_doctor', 'is_patient', 'is_active', 'is_staff', 'is_superuser'
            )
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'specialization', 'mobile_number', 'city', 'created_at', 'get_clinics')
    search_fields = ('user__first_name', 'user__last_name', 'specialization', 'city')
    list_filter = ('specialization', 'city')

    def get_clinics(self, obj):
        from pharmacy.models import Clinic       
        owned = Clinic.objects.filter(doctor=obj)
        assigned = obj.clinics.all()
        all_clinics = set(owned) | set(assigned)

        if all_clinics:
            return ", ".join([clinic.name for clinic in all_clinics])
        return "-"
    get_clinics.short_description = 'Clinics'

class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'age', 'blood_group', 'mobile_number', 'doctor','profile_image_preview') 
    search_fields = ('full_name', 'mobile_number', 'email', 'doctor__username', 'date_of_birth')
    list_filter = ('gender', 'blood_group')
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="50" height="50" />')
        return "-"
    profile_image_preview.short_description = 'Profile Image'

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'appointment_datetime', 'appointment_type', 'status')
    list_filter = ('status', 'appointment_type')
    search_fields = ('doctor__user__first_name', 'patient__user__first_name')

class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_admin_name', 'address', 'get_doctors')
    search_fields = ('name', 'address', 'admin__first_name', 'admin__last_name')
    list_filter = ('admin',)
    autocomplete_fields = ['admin']

    def get_admin_name(self, obj):
        """Return admin name if set, else try matching clinic name to a superuser's full name."""
        if obj.admin:
            return obj.admin.get_full_name() or obj.admin.email

        clinic_name = obj.name.strip().lower()
        for user in User.objects.filter(is_superuser=True):
            full_name = f"{user.first_name} {user.last_name}".strip().lower()
            if clinic_name == full_name:
                return f"{user.first_name} {user.last_name}"
        return 'N/A'
    get_admin_name.short_description = 'Clinic Admin'

    @admin.display(description='Doctors Assigned')
    def get_doctors(self, obj):
        """Return all doctors assigned to this clinic."""
        doctors = obj.assigned_doctors.all()
        return ", ".join([d.user.get_full_name() for d in doctors if d.user])

class EducationAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'degree', 'institute', 'passing_year')
    search_fields = ('degree', 'institute')

class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'hospital_name', 'designation', 'from_date', 'to_date')
    search_fields = ('hospital_name', 'designation')

class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'doctor')
    search_fields = ('doctor__user__username',)

class DoctorListingAdmin(admin.ModelAdmin):
    list_display = ('get_doctor_name', 'treatment', 'price')
    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name()
    get_doctor_name.short_description = 'Doctor Name'  

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'name', 'price')
    search_fields = ('doctor__user__first_name', 'name')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'rating', 'created_at')

class AwardAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'name','year',)

class SpecialitiesAdmin(admin.ModelAdmin):
    list_display = ('name',)

class SubmitReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'doctor', 'rating', 'name', 'email', 'created_at')
    list_filter = ('doctor', 'rating', 'created_at')
    search_fields = ('title', 'name', 'email', 'message')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('doctor', 'rating', 'title', 'name', 'email', 'message', 'terms_accepted')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

class ClinicListingAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'treatment', 'price')
    search_fields = ('clinic__name', 'treatment')
    list_filter = ('clinic',)

class ClinicServiceAdmin(admin.ModelAdmin):
    list_display = ('clinic', 'name', 'price')
    search_fields = ('clinic__name', 'name')
    list_filter = ('clinic',)

class BloodBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'is_verified', 'is_active')
    search_fields = ('name', 'registration_number', 'city', 'state')
    list_filter = ('is_active', 'is_verified', 'city', 'state')
    readonly_fields = ('created_at', 'updated_at')

class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_bank', 'blood_group', 'component_type', 'quantity', 'stock_status')
    list_filter = ('blood_group', 'component_type', 'stock_status')
    search_fields = ('blood_bank__name', 'batch_number')

class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'blood_group', 'component_type', 'quantity_needed', 'urgency_level', 'required_date', 'status')
    list_filter = ('blood_group', 'component_type', 'urgency_level', 'status')
    search_fields = ('patient_name', 'hospital_name', 'doctor_name')
    ordering = ('-created_at',)

class DonorRecordAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'blood_group', 'age', 'donation_count', 'donor_status')
    search_fields = ('donor_name', 'donor_phone', 'blood_group')
    list_filter = ('blood_group', 'donor_status')

class BloodDispatchAdmin(admin.ModelAdmin):
    list_display = ('blood_group', 'quantity', 'recipient_name', 'dispatched_at')
    search_fields = ('blood_group', 'recipient_name')
    list_filter = ('blood_group', 'dispatched_at')


class TestCategoryAdmin(admin.ModelAdmin):
    list_display =('name',)

class DiagnosticTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'test_code', 'original_price', 'discounted_price', 'is_active', 'is_package')
    list_filter = ('category', 'is_active', 'is_package')
    search_fields = ('name', 'test_code')
    
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone",
        "preferred_date",
        "total_price",
        "tx_hash",
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "phone",
        "tx_hash",
        "user__username",
    )

    list_filter = (
        "status",
        "preferred_date",
        "created_at",
    )

    readonly_fields = (
        "tx_hash",
        "cart_data",
        "created_at",
    )

    ordering = ("-created_at",)
  


from django.conf import settings 
from .models import Booking, Refund 
from utils.refund import process_refund


@admin.action(description="Refund selected bookings")
def refund_booking(modeladmin, request, queryset):
    for booking in queryset.filter(status="PAID"):
        tx_hash = process_refund(booking, settings.ADMIN_PRIVATE_KEY)
        Refund.objects.create(
            booking=booking,
            tx_hash=tx_hash,
            amount=booking.crypto_amount
        )

class ReportFileAdmin(admin.ModelAdmin):
    list_display = ('booking', 'file', 'uploaded_at')
    search_fields = ('booking__patient__name',) 
    list_filter = ('uploaded_at',)

from .models import Product,MedicineCategory

@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'image', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'in_stock']
    list_filter = ['category', 'in_stock']
    search_fields = ['name']


admin.site.register(User, UserAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Clinic, ClinicAdmin)
admin.site.register(Education, EducationAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(DoctorListing, DoctorListingAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Award,  AwardAdmin)
admin.site.register(Speciality,SpecialitiesAdmin)
admin.site.register(SubmitReview,SubmitReviewAdmin)
admin.site.register(ClinicService, ClinicServiceAdmin)
admin.site.register(ClinicListing, ClinicListingAdmin)
admin.site.register(ReportFile,ReportFileAdmin)
admin.site.register(Booking,BookingAdmin)
admin.site.register(DiagnosticTest,DiagnosticTestAdmin)
admin.site.register(BloodBank,BloodBankAdmin)
admin.site.register(BloodDispatch,BloodDispatchAdmin)
admin.site.register(BloodInventory,BloodInventoryAdmin)
admin.site.register(BloodRequest,BloodRequestAdmin)
admin.site.register(DonorRecord,DonorRecordAdmin)
admin.site.register(TestCategory,TestCategoryAdmin)