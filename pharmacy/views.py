import json
from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse ,reverse_lazy
from django.http import JsonResponse ,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, date, timedelta
import logging
from django.utils.timezone import now
from .models import User, Doctor, Patient, Appointment, Clinic, Education, Experience ,Message,ScheduleTiming,PatientSocialLinks,DoctorListing,Award,Speciality,SubmitReview,FavouriteDoctor,BloodDispatch
from .forms import DoctorProfileForm, ClinicForm, EducationForm, ExperienceForm,PatientForm,AppointmentForm,Service, AwardForm,SpecialityForm
from django.forms import  inlineformset_factory, modelformset_factory
from django.db.models import Value as V
from django.db.models.functions import Concat
from .models import  TimeSlot
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from. models import Conversation
from .forms import SocialLinksForm,SubmitReviewForm,TimeSlotForm,BranchForm,BloodBankForm,BloodRequestForm,BloodInventoryForm,DonorRecordForm,DispatchBloodForm
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_time
from dateutil.relativedelta import relativedelta
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode , urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from .models import Clinic, Branch,BloodBank ,BloodRequest, GalleryImage,BloodInventory, DonorRecord,Clinic, ClinicListing, ClinicService
from itertools import groupby
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.utils.http import urlencode
from django.utils.timezone import make_naive
from .filters import BloodRequestFilter
from django.contrib.admin.views.decorators import staff_member_required
from .models import TestCategory, DiagnosticTest,Booking, ReportFile,CartItem
from .forms import DiagnosticTestForm,TestCategoryForm
from collections import defaultdict
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import EmailMultiAlternatives
from pharmacy.models import Clinic
from .models import MedicineCategory ,Product,Cart, CartItem,Product, DiagnosticTest
from .forms import ProductForm ,MedicineCategoryForm
from urllib.parse import urlparse
import csv
from django.http import HttpResponse
from openpyxl import Workbook
from web3 import Web3


logger = logging.getLogger(__name__)
User = get_user_model() 
def is_ajax(request):
    """Helper function to check if the request is an AJAX request."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def home(request):
    doctor = None
    patient = None
    blood_bank = None
    clinics = None
    if request.user.is_authenticated:
        blood_bank = BloodBank.objects.filter(user=request.user).first()
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass
    if request.user.is_authenticated and request.user.is_clinic:
        try:
           clinics = Clinic.objects.filter(doctor__user=request.user)
        except Clinic.DoesNotExist:
            pass
    context = {
        'doctor': doctor,
        'patient': patient,  
        'blood_bank':blood_bank,
        'clinics':clinics
    }
    return render(request, 'base.html', context)

User = get_user_model()
def register_view(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None
        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None

    if request.method == 'GET':
        return render(request, 'register.html', {
            'doctor': doctor,
            'patient': patient,   
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            mobile_number = data.get('phone')
            user_type = data.get('user_type')

            if password != confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match'
                })

            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already exists'
                })

            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=mobile_number,
                )

                if user_type == 'doctor':
                    user.is_doctor = True
                    user.save()
                    Doctor.objects.create(
                        user=user,
                        specialization=data.get('specialization', '')
                    )
                else:
                    user.is_patient = True
                    user.save()
                    Patient.objects.create(user=user)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Registration successful',
                    'redirect': '/login/'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

@csrf_exempt
def login_view(request):
    doctor = None
    patient = None

    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None

    if request.method == 'GET':
        return render(request, 'login.html', {
            'doctor': doctor,
            'patient': patient,
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            user = authenticate(request, username=data.get('email'), password=data.get('password'))

            if user is not None:
                login(request, user)
                if hasattr(user, 'doctor') or user.is_doctor:
                    user_type = 'doctor'
                    redirect_url = '/doctors/dashboard/'

                elif hasattr(user, 'patient') or user.is_patient:
                    user_type = 'patient'
                    redirect_url = '/patients/dashboard/'

                elif user.is_clinic:
                    user_type = 'clinic'
                    redirect_url = '/clinics/dashboard/'

                else:
                    user_type = 'unknown'
                    redirect_url = '/'

                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful',
                    'redirect': redirect_url,
                    'user_type': user_type
                })

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid email or password'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

def logout_view(request):
    logout(request)
    return redirect('home')
                                                    
@login_required
def patient_dashboard_view(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return HttpResponse("Patient profile not found.", status=404)

    appointments = Appointment.objects.filter(patient=patient).select_related('doctor').order_by('-date')
    doctors = Doctor.objects.all()

    user_content_type = ContentType.objects.get_for_model(Patient)

    new_messages = Message.objects.filter(
        receiver_content_type=user_content_type,
        receiver_object_id=patient.id,
        is_read=False                                                                                                                                      
    ).count()

    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_datetime__gte=timezone.now()
    ).order_by('appointment_datetime')[:5]
    review_count = SubmitReview.objects.filter(patient=request.user).count()

    total_appointments = appointments.count()
    context = {
        'patient': patient,
        'total_appointments': total_appointments,
        'new_messages': new_messages,
        'review_count': review_count,
        'unread_messages_count': new_messages,
        'upcoming_appointments': upcoming_appointments,
        'appointments': appointments,
        'doctors': doctors,
    }
    return render(request, 'patient_dashboard.html', context)

@login_required
def doctor_dashboard_view(request): 
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
    else:
        form = DoctorProfileForm(instance=doctor)

    appointments = Appointment.objects.filter(doctor=doctor).select_related('patient').order_by('-appointment_datetime')[:]
    patient_ids = Appointment.objects.filter(doctor=doctor).values_list('patient_id', flat=True).distinct()
    total_patients = Patient.objects.filter(id__in=patient_ids).count()
    doctor.owned_clinics.all() 
    clinics = doctor.clinics.all()
    total_staffs = Doctor.objects.filter(clinics__in=clinics).distinct().count()
    appointment_count = Appointment.objects.filter(doctor=doctor).count()
    paginator = Paginator(appointments, 5)
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)
    context = {
        'doctor': doctor,
        'form': form,
        'appointments': appointments,
        'Total_patient': total_patients,
        'total_staffs': total_staffs,
        'appointment_count': appointment_count,   
        'clinic':clinic
    }
    return render(request, 'doctor_dashboard.html', context)

def appointment_detail_view(request, appointment_id):
    try:
        appointment = Appointment.objects.select_related('patient', 'doctor').get(id=appointment_id)
        return JsonResponse({
            'patient': appointment.patient.get_full_name(),
            'datetime': appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M'),
            'purpose' : appointment.purpose,
            'status': appointment.status,
            'appointment_mode': appointment.appointment_mode,
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found.'}, status=404)

@login_required
def doctor_appointment_list(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
    else:
        form = DoctorProfileForm(instance=doctor)

    all_appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_datetime')
    upcoming_appointments_qs = all_appointments.filter(appointment_datetime__gte=now()).order_by('appointment_datetime')
    past_appointments_qs = all_appointments.filter(appointment_datetime__lt=now()).order_by('-appointment_datetime')
    upcoming_page_number = request.GET.get('upcoming_page', 1)
    upcoming_paginator = Paginator(upcoming_appointments_qs, 5)
    upcoming_appointments = upcoming_paginator.get_page(upcoming_page_number)
    past_page_number = request.GET.get('past_page', 1)
    past_paginator = Paginator(past_appointments_qs, 5)
    past_appointments = past_paginator.get_page(past_page_number)

    context = {
        'form': form,
        'appointments': all_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'unread_messages': 0,
        'doctor': doctor, 
    }
    return render(request, 'appointment.html', context)

def add_appointment(request):
    if request.method == 'POST':
        doctor = Doctor.objects.get(user=request.user)
        patient_name = request.POST.get('patient_name')
        email = request.POST.get('email').strip().lower()
        phone = request.POST.get('phone')
        location = request.POST.get('location')  
        reason = request.POST.get('reason')
        appointment_date = request.POST.get('appointment_datetime')
        if not appointment_date:
            messages.error(request, "Please select a valid appointment date.")
            return redirect('add_appointment')
        try:
            appointment_datetime = datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M')
            appointment_datetime = make_aware(appointment_datetime)
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('add_appointment')
        appointment_end = appointment_datetime + timedelta(minutes=30)
        schedule = ScheduleTiming.objects.filter(
            doctor=doctor,
            start_datetime=appointment_datetime
        ).first()
        if not schedule:
            schedule = ScheduleTiming.objects.create(
                doctor=doctor,
                date=appointment_datetime.date(),
                start_datetime=appointment_datetime,
                end_datetime=appointment_end,
                is_available=False,
                title="Booked slot",
                description="Auto-created from appointment",
            )  
        user_obj, user_created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': patient_name.split()[0] if patient_name else '',
                'last_name': ' '.join(patient_name.split()[1:]) if patient_name and len(patient_name.split()) > 1 else '',
                'is_patient': True
            }
        )
        if not user_created:
            if not user_obj.first_name and patient_name:
                user_obj.first_name = patient_name.split()[0]
            if not user_obj.last_name and patient_name:
                user_obj.last_name = ' '.join(patient_name.split()[1:])
            user_obj.save()
        patient, patient_created = Patient.objects.get_or_create(
            user=user_obj,
            defaults={
                'email': email,
                'mobile_number': phone,
                'first_name': user_obj.first_name,
                'last_name': user_obj.last_name,
            }
        )
        if not patient_created and patient.mobile_number != phone:
            patient.mobile_number = phone
            patient.save()
        time_slot = TimeSlot.objects.first() 
        Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            time_slot=time_slot,
            appointment_datetime=appointment_datetime,
            location=location,
            purpose=reason,
            patient_name=patient_name,
            patient_email=email,
            patient_mobile_number=phone,
            status='Pending',
            payment_status='pending',
            schedule=schedule
        )
        messages.success(request, "Appointment successfully added.")
        return redirect('doctor_appointment_list')
    return render(request, 'appointment.html')

def video_call(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    room_name = f"doctor{appointment.doctor.id}-patient{appointment.patient.id}-appt{appointment.id}"
    return render(request, "video_call.html", {
        "appointment": appointment,
        "room_name":room_name
        })

@login_required
def accept_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor_profile)

    appointment.status = 'Accepted'
    appointment.save()

    subject = 'Your Appointment is Confirmed'

    message = f"""
Dear {appointment.patient.get_full_name()},

Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been accepted.

Appointment Details:
Date & Time: {appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M')}
Location: {appointment.location}
Reason: {appointment.purpose}
Appointment Mode: {appointment.appointment_mode.capitalize()}
"""
    message += """
Please arrive at least 10 minutes early (or join online 5 minutes before start).

Thank you,
Doctor Appointment Booking Team
"""
    recipient_email = appointment.patient_email or getattr(appointment.patient, 'email', None)

    if recipient_email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        messages.success(request, "Appointment accepted and confirmation email sent to the patient.")
    else:
        messages.warning(request, "Appointment accepted, but email not sent (email address missing).")
    return redirect('doctor_appointment_list')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor_profile)
    appointment.status = 'Cancelled'
    appointment.save()
    subject = 'Appointment Cancelled'
    message = f"""
    Dear {appointment.patient.get_full_name()},
    We regret to inform you that your appointment scheduled on
    {appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M')} with Dr. {appointment.doctor.user.get_full_name()}
    has been cancelled.

    If you have any questions, feel free to contact the clinic.

    Thank you,
    Doctor Appointment System
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [appointment.patient.user.email], 
        fail_silently=False,
    )
    return redirect('doctor_appointment_list')

@login_required
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        appointment.patient_name = request.POST.get('patient_name')
        appointment.patient_email = request.POST.get('email')
        appointment.patient_mobile_number = request.POST.get('phone')
        appointment.purpose = request.POST.get('purpose')
        appointment.location = request.POST.get('location')
        appointment_mode = request.POST.get('appointment_mode')
        appointment.appointment_mode = appointment_mode

        zoom_link_input = request.POST.get('video_link')
        if appointment_mode == 'online':
            appointment.video_link = zoom_link_input.strip() if zoom_link_input else ''
        else:
            appointment.video_link = ''  

        if appointment.patient:
            appointment.patient.location = appointment.location
            appointment.patient.save()

        dt_str = request.POST.get('appointment_datetime')
        try:
            appointment.appointment_datetime = make_aware(datetime.strptime(dt_str, '%Y-%m-%dT%H:%M'))
        except ValueError:
            messages.error(request, "Invalid appointment date and time format.")
            return redirect('edit_appointment', appointment_id=appointment.id)

        appointment.save()
        messages.success(request, "Appointment updated successfully.")
        return redirect('doctor_appointment_list')

    return render(request, 'edit_appointment.html', {
        'appointment': appointment,
    })

def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    return redirect('doctor_appointment_list')

@login_required
def my_profile(request):
    """Doctor profile management view"""
    ClinicFormSet = modelformset_factory(Clinic, form=ClinicForm, extra=1, can_delete=True)
    EducationFormSet = inlineformset_factory(
        Doctor, Education, form=EducationForm, extra=1, can_delete=True
    )
    ExperienceFormSet = inlineformset_factory(
        Doctor, Experience, form=ExperienceForm, extra=1, can_delete=True
    )
    AwardFormSet = inlineformset_factory(
        Doctor, Award, form=AwardForm, extra=1, can_delete=True
    )
    SpecialityFormSet = inlineformset_factory(
        Doctor, Speciality, form=SpecialityForm, extra=1, can_delete=True
    )

    if not hasattr(request.user, 'doctor_profile'):
        messages.error(request, "Access denied. Doctor account required.")
        return redirect('login')

    doctor_profile, _ = Doctor.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile_form = DoctorProfileForm(request.POST, request.FILES, instance=doctor_profile, user=request.user)
        clinic_formset = ClinicFormSet(request.POST, request.FILES,  queryset=doctor_profile.clinics.all())
        education_formset = EducationFormSet(request.POST, instance=doctor_profile)
        experience_formset = ExperienceFormSet(request.POST, instance=doctor_profile)
        award_formset = AwardFormSet(request.POST, instance=doctor_profile)
        speciality_formset = SpecialityFormSet(request.POST, instance=doctor_profile)

        if all([
            profile_form.is_valid(),
            clinic_formset.is_valid(),
            education_formset.is_valid(),
            experience_formset.is_valid(),
            award_formset.is_valid(),
            speciality_formset.is_valid()
        ]):
            try:
                with transaction.atomic():
                    doctor_profile = profile_form.save()
                    education_formset.instance = doctor_profile
                    experience_formset.instance = doctor_profile
                    award_formset.instance = doctor_profile
                    speciality_formset.instance = doctor_profile
                    education_formset.save()
                    experience_formset.save()
                    award_formset.save()
                    speciality_formset.save()
                    for form in clinic_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            name = form.cleaned_data.get('name')
                            address = form.cleaned_data.get('address')
                            if name:
                                name_cleaned = name.strip()
                                existing_clinic = Clinic.objects.filter(name__iexact=name_cleaned).first()

                                if existing_clinic:
                                    updated = False
                                    if address and existing_clinic.address != address:
                                        existing_clinic.address = address
                                        updated = True

                                    form.instance = existing_clinic
                                    form.save()

                                    if updated:
                                        messages.info(request, f"Updated details for existing clinic '{existing_clinic.name}'.")

                                    if not doctor_profile.clinics.filter(pk=existing_clinic.pk).exists():
                                        doctor_profile.clinics.add(existing_clinic)
                                        messages.info(request, f"Linked to existing clinic '{existing_clinic.name}'.")
                                else:
                                    new_clinic = form.save(commit=False)
                                    new_clinic.name = name_cleaned
                                    new_clinic.doctor = doctor_profile
                                    new_clinic.save()
                                    doctor_profile.clinics.add(new_clinic)
                                    messages.success(request, f"Created and linked new clinic '{new_clinic.name}'.")
                messages.success(request, "Profile updated successfully!")
                return redirect('my_profile')
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        profile_form = DoctorProfileForm(instance=doctor_profile, user=request.user)
        clinic_formset = ClinicFormSet(queryset=doctor_profile.clinics.all())
        education_formset = EducationFormSet(instance=doctor_profile)
        experience_formset = ExperienceFormSet(instance=doctor_profile)
        award_formset = AwardFormSet(instance=doctor_profile)
        speciality_formset = SpecialityFormSet(instance=doctor_profile)

    context = {
        'doctor': doctor_profile,
        'profile_form': profile_form,
        'clinic_formset': clinic_formset,
        'education_formset': education_formset,
        'experience_formset': experience_formset,
        'award_formset': award_formset,
        'speciality_formset': speciality_formset,
        'form': profile_form, 
    }
    return render(request, 'my-profile.html', context)

def group_time_slots(slots): 
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_to_index = {day: i for i, day in enumerate(days_order)}
    slot_list = []
    for slot in slots:
        for day in slot.day_of_week.split(','):
            slot_list.append((
                day.strip(),
                slot.start_time.strftime("%I:%M %p"),
                slot.end_time.strftime("%I:%M %p"),
                slot.is_available
            ))
    slot_list.sort(key=lambda x: day_to_index[x[0]])    
    grouped = []
    i = 0
    while i < len(slot_list):
        day_range = [slot_list[i][0]]
        start_time, end_time, available = slot_list[i][1], slot_list[i][2], slot_list[i][3]
        while (i + 1 < len(slot_list) and
               slot_list[i + 1][1] == start_time and
               slot_list[i + 1][2] == end_time and
               slot_list[i + 1][3] == available and
               day_to_index[slot_list[i + 1][0]] == day_to_index[slot_list[i][0]] + 1):
            i += 1
            day_range.append(slot_list[i][0])
        if len(day_range) == 1:
            day_str = day_range[0]
        else:
            day_str = f"{day_range[0]} to {day_range[-1]}"
        grouped.append({
            'day_range': day_str,
            'time_range': f"{start_time} - {end_time}",
            'available': available
        })
        i += 1
    return grouped

@login_required
def schedule_timing_view(request):
    doctor_user = request.user
    try:
        doctor = Doctor.objects.get(user=doctor_user)
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile_setup')
    
    time_slots = TimeSlot.objects.filter(doctor=doctor)
    DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    def compress_days(days_list):
        ordered = [day for day in DAY_ORDER if day in days_list]
        if len(ordered) == 1:
            return ordered[0]
        return f"{ordered[0]} - {ordered[-1]}"
    grouped_slots = group_time_slots(time_slots)
    time_slot_data = []
    for slot in time_slots:
        days_list = slot.get_days_list()
        time_slot_data.append({
            'id': slot.id,
            'days': compress_days(days_list),
            'day_of_week': slot.day_of_week, 
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'available': slot.is_available,
        })
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return render(request, 'schedule-timing.html', {
        'grouped_slots': grouped_slots,
        'time_slots': time_slot_data,
        'days': days,
        'doctor': doctor, 
    })

@login_required
def calendar_events(request):
    events = []
    try:
        doctor = Doctor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=["Accepted", "Pending", "Cancelled"],
            appointment_datetime__gte=date.today()
        )
        for appt in appointments:
            patient_name = (
                appt.patient.user.get_full_name()
                if appt.patient and appt.patient.user
                else appt.patient_name or "Unknown"
            )
            purpose = appt.purpose or "Checkup"
            appointment_mode = appt.appointment_mode.capitalize()
            status_color = {
                "Accepted": "green",
                "Cancelled": "red",
                "Pending": "orange"
            }.get(appt.status, "gray")
            description = f"Mode: {appointment_mode}\nPurpose: {purpose}"
            if appt.appointment_mode == "online" and appt.video_link:
                description += f"\nZoom Link: {appt.video_link}"
            events.append({
                "title": f"{patient_name} - {purpose} , {appointment_mode},{appt.video_link}",
                "start": appt.appointment_datetime.isoformat(),
                "end": appt.appointment_datetime.isoformat(),
                "color": status_color,
                "description": description, 
                "url": appt.video_link if appt.appointment_mode == "online" and appt.video_link else "",
            })

    except Doctor.DoesNotExist:
        pass
    return JsonResponse(events, safe=False)

@login_required
def add_or_edit_time_slot(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile_setup')
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        selected_days = request.POST.getlist('day_of_week')
        start_time = parse_time(request.POST.get('start_time'))
        end_time = parse_time(request.POST.get('end_time'))
        is_available = 'is_available' in request.POST
        if not selected_days:
            messages.error(request, "Please select at least one day.")
            return redirect('schedule_timing')
        if slot_id and slot_id.isdigit():  
            slot = get_object_or_404(TimeSlot, pk=int(slot_id), doctor=doctor)
            selected_days = request.POST.getlist('day_of_week')  
            day = ', '.join(selected_days) 
            slot.start_time = start_time
            slot.end_time = end_time
            slot.is_available = is_available
            slot.save()
            messages.success(request, 'Time slot updated successfully.')
        else: 
            for day in selected_days:
                TimeSlot.objects.create(
                    doctor=doctor,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=is_available
                )
            messages.success(request, 'Time slot(s) added successfully.')

        return redirect('schedule_timing')

    messages.error(request, "Invalid request method.")
    return redirect('schedule_timing')

@login_required
def delete_time_slot(request, slot_id):
    slot = get_object_or_404(TimeSlot, id=slot_id, doctor__user=request.user)
    slot.delete()
    messages.success(request, "Time slot deleted successfully.")
    return redirect('schedule_timing')

@login_required
def my_patients(request):  
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)
    
    patients_list = Patient.objects.filter(
        Q(doctor=request.user) | Q(appointments__doctor=doctor)
    ).distinct()

    search_query = request.GET.get('search', '').strip()
    full_name = Concat('first_name', V(' '), 'last_name')

    if search_query:
        patients_list = patients_list.annotate(full_name=full_name).filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )

    paginator = Paginator(patients_list, 10)  
    page_number = request.GET.get('page')
    patients = paginator.get_page(page_number)

    return render(request, 'my-patients.html', {
        'doctor': doctor,
        'patients': patients,
        'search_query': search_query,   
    })

@login_required
def add_patient(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.doctor = request.user  
            patient.save()
            messages.success(request, "Patient added successfully.")
            return redirect('my_patients')
        else:
            messages.error(request, "There was a problem with the form.")
    else:
        form = PatientForm()
    return render(request, 'patient_form.html', {
        'doctor': doctor,
        'form': form, 
        'action': 'Add'})

@login_required
def edit_patient(request, patient_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)
    patient = Patient.objects.filter(
    Q(id=patient_id) & (Q(doctor=request.user) | Q(appointments__doctor=doctor))
    ).distinct().first()
    if not patient:
        return HttpResponse("Patient not found.", status=404)
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient updated successfully.")
            return redirect('my_patients')
        else:
            messages.error(request, "There was a problem updating the patient.")
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patient_form.html', {
            'doctor': doctor,
            'patient': patient,
            'form': form,
            'action': 'Edit'
            })

@login_required
def delete_patient(request, patient_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)
    try:
        patient = Patient.objects.get(
            Q(id=patient_id) & (Q(doctor=request.user) | Q(appointments__doctor=doctor))
        )
    except Patient.DoesNotExist:
        return HttpResponse("You don't have permission to delete this patient.", status=403)
    patient.delete()
    messages.success(request, "Patient deleted successfully.")
    return redirect('my_patients')

@login_required
def add_listing(request):
    doctor = request.user.doctor_profile
    if request.method == 'POST':   
        DoctorListing.objects.filter(doctor=doctor).delete()
        Service.objects.filter(doctor=doctor).delete()  
        treatments = request.POST.getlist('treatment[]')
        prices = request.POST.getlist('price[]')
        for treatment, price in zip(treatments, prices):
            if treatment and price:    
                DoctorListing.objects.create(
                    doctor=doctor,
                    treatment=treatment,
                    price=price
                )
                Service.objects.create(
                    doctor=doctor,
                    name=treatment,
                    price=price,
                )

        return redirect('doctor_dashboard')
    else:
        pricing = DoctorListing.objects.filter(doctor=doctor)
        return render(request, 'add-listing.html', {
            'pricing': pricing,
            'doctor': doctor,   
        })

@login_required
def change_password(request):
    doctor = Doctor.objects.get(user=request.user)
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
        elif not new_password1 or not new_password2:
            messages.error(request, 'New password fields cannot be empty.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('doctor_dashboard')
    context = {
    'doctor': doctor
}
    return render(request, 'change_password.html',context)

@login_required
def profile(request):
    try:
        patient_profile, _ = Patient.objects.get_or_create(user=request.user)
        social_links, _ = PatientSocialLinks.objects.get_or_create(patient=patient_profile)

        if request.method == 'POST':
            form = PatientForm(request.POST, request.FILES, instance=patient_profile)
            social_form = SocialLinksForm(request.POST, instance=social_links)

            if form.is_valid() and social_form.is_valid():
                try:
                    with transaction.atomic():
                        request.user.first_name = form.cleaned_data['first_name']
                        request.user.last_name = form.cleaned_data['last_name']
                        request.user.email = form.cleaned_data['email']
                        request.user.save()
                        form.save()
                        social_form.save()
                        messages.success(request, 'Profile updated successfully!')
                        return redirect(reverse('profile') + '?success=true')
                except Exception as e:
                    messages.error(request, f'Error updating profile: {e}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                for field, errors in social_form.errors.items():
                    for error in errors:
                        messages.error(request, f'Social {field}: {error}')
        else:
            form = PatientForm(instance=patient_profile)
            social_form = SocialLinksForm(instance=social_links)
        unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return render(request, 'patient_profile.html', {
            'form': form,
            'social_form': social_form,
            'patient': patient_profile,
            'unread_messages_count': unread_messages_count,
            'user': request.user,
        })
    except Exception as e:
        raise e
    
@login_required
def change_password2(request):
    patient_profile, created = Patient.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')
        if not request.user.check_password(old):
            messages.error(request, 'Old password is incorrect.')
        elif new1 != new2:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new1)
            request.user.save()
            update_session_auth_hash(request, request.user)  
            messages.success(request, 'Password changed successfully.')
            return redirect('patient_dashboard')
    context = {
        'patient': patient_profile,
    }
    return render(request, 'change_password2.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def book_appointment(request, doctor_id): 
    doctor = get_object_or_404(Doctor, id=doctor_id)

    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, "You must be logged in as a patient to book an appointment.")
        return redirect('login') 

    if request.method == 'POST':
        selected_date = request.GET.get('date')
        selected_time = request.GET.get('time')

        if not selected_date or not selected_time:
            return HttpResponse("Missing date or time", status=400)

        appointment_datetime = timezone.make_aware(
            timezone.datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
        )

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_datetime=appointment_datetime,
            date=selected_date,
            time=selected_time,
            is_new_patient=(request.POST.get('is_new_patient') == 'yes'),
            gender=request.POST.get('gender'),
            patient_name=request.POST.get('patient_name'),
            patient_email=request.POST.get('patient_email'),
            patient_mobile_number=request.POST.get('patient_mobile_number'),
            purpose=request.POST.get('purpose'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip_code'),
            date_of_birth=request.POST.get('date_of_birth'),
            appointment_notes=request.POST.get('appointment_notes'),
            appointment_type=request.POST.get('appointment_type'),
            status=request.POST.get('status'),
            fee=request.POST.get('fee'),
            total_amount=request.POST.get('total_amount'),
            payment_status=request.POST.get('payment_status', 'pending'),
            appointment_mode=request.POST.get("appointment_mode", "offline"),
        )

        return redirect('confirm_appointment', appointment.id)

    selected_date = request.GET.get('date')
    selected_time = request.GET.get('time')
    selected_services_ids = request.GET.getlist('services')
    services = Service.objects.filter(id__in=selected_services_ids)
    total_amount = sum(service.price for service in services)

    return render(request, 'book_appointment.html', {
        'doctor': doctor,
        'patient': patient,
        'selected_date': selected_date,
        'selected_time': selected_time,
        'selected_services_info': services,
        'total_amount': total_amount,
        'doctor_profile': getattr(request.user, 'doctor_profile', None),
        'patient_profile': getattr(request.user, 'patient_profile', None),
    })


@login_required
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient__user=request.user
    )

    return render(
        request,
        "confirmation.html",
        {
            "appointment": appointment,
            "service_wallet_address": settings.SERVICE_WALLET_ADDRESS,
        }
    )


from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from web3 import Web3
from decimal import Decimal
import json

from .models import Appointment
from utils.crypto import inr_to_bnb


from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from web3 import Web3
from decimal import Decimal
import json

from .models import Appointment
from utils.crypto import inr_to_bnb


@login_required
def payment_success(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    appointment = None

    try:
        # 1️⃣ Parse request
        data = json.loads(request.body)
        tx_hash = data.get("tx_hash")
        appointment_id = data.get("appointment_id")

        if not tx_hash or not appointment_id:
            return JsonResponse({
                "status": "failed",
                "error": "Missing transaction data"
            })

        # 2️⃣ Fetch appointment
        appointment = Appointment.objects.get(id=appointment_id)

        # ✅ Idempotency (already paid)
        if appointment.payment_status == "paid":
            return JsonResponse({
                "status": "success",
                "redirect_url": reverse("home")
            })

        # 🔐 Replay attack protection
        if Appointment.objects.filter(
            blockchain_tx_hash=tx_hash
        ).exclude(id=appointment.id).exists():
            return JsonResponse({
                "status": "failed",
                "error": "Duplicate transaction"
            })

        # 3️⃣ Web3 setup
        w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
        if not w3.is_connected():
            raise Exception("Blockchain not connected")

        if w3.eth.chain_id != settings.CHAIN_ID:
            raise Exception("Wrong blockchain network")

        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt or receipt.status != 1:
            raise Exception("Transaction failed on blockchain")

        tx = w3.eth.get_transaction(tx_hash)

        if not tx.get("to"):
            raise Exception("Transaction has no recipient")

        # 4️⃣ Receiver validation
        if Web3.to_checksum_address(tx["to"]) != Web3.to_checksum_address(
            settings.SERVICE_WALLET_ADDRESS
        ):
            raise Exception("Payment sent to wrong wallet")

        # 5️⃣ Amount validation
        expected_inr = Decimal(appointment.total_amount)
        expected_crypto = inr_to_bnb(expected_inr)
        expected_wei = w3.to_wei(expected_crypto, "ether")
        paid_wei = tx["value"]

        # Skip strict amount check in LOCAL (Hardhat)
        if settings.BLOCKCHAIN_ENV != "LOCAL":
            if paid_wei < int(expected_wei * Decimal("0.99")):
                raise Exception("Insufficient payment amount")

        # 6️⃣ Mark appointment paid
        appointment.payment_status = "paid"
        appointment.status = "Confirmed"
        appointment.blockchain_status = "success"
        appointment.blockchain_tx_hash = tx_hash
        appointment.user_wallet_address = tx["from"]

        # Online appointment → video link
        if appointment.appointment_mode == "online":
            appointment.video_link = f"https://meet.jit.si/appointment-{appointment.id}"

        appointment.save()

        # 7️⃣ Emails
        appointment_time = appointment.appointment_datetime.strftime("%Y-%m-%d %H:%M")

        send_mail(
            subject="Appointment Confirmed ✅",
            message=(
                f"Dear {appointment.patient_name},\n\n"
                f"Your appointment has been successfully confirmed.\n\n"
                f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
                f"Date & Time: {appointment_time}\n"
                f"Mode: {appointment.appointment_mode.capitalize()}\n\n"
                f"Thank you for choosing our service."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient_email],
            fail_silently=True,
        )

        send_mail(
            subject="New Appointment Booked 📅",
            message=(
                f"Dear Dr. {appointment.doctor.user.first_name},\n\n"
                f"A new appointment has been booked.\n\n"
                f"Patient Name: {appointment.patient_name}\n"
                f"Date & Time: {appointment_time}\n"
                f"Mode: {appointment.appointment_mode.capitalize()}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.doctor.user.email],
            fail_silently=True,
        )

        # 8️⃣ SUCCESS → FRONTEND REDIRECTS TO HOME
        return JsonResponse({
            "status": "success",
            "redirect_url": reverse("home")
        })

    except Appointment.DoesNotExist:
        return JsonResponse({
            "status": "failed",
            "error": "Appointment not found"
        })

    except Exception as e:
        if appointment:
            appointment.payment_status = "failed"
            appointment.blockchain_status = "failed"
            appointment.save()

        return JsonResponse({
            "status": "failed",
            "error": str(e)
        })


@login_required
def manage_time_slots(request):
    doctor = request.user.doctor  
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            timeslot = form.save(commit=False)
            timeslot.doctor = doctor
            timeslot.save()
            return redirect('manage_time_slots')  
    else:
        form = TimeSlotForm()
    time_slots = TimeSlot.objects.filter(doctor=doctor)
    context = {
        'form': form,
        'time_slots': time_slots,
    }
    return render(request, 'schedule-timing.html', context)


def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', args=[uid, token])
            )
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_url': reset_url
            })
            send_mail(
                'Reset Your Password',
                message,
                'no-reply@yourdomain.com',
                [email],
                fail_silently=False
            )
            messages.success(request, 'Password reset link has been sent to your email.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email.')
        return redirect('login')
    return redirect('login')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = int(urlsafe_base64_decode(uidb64).decode())
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect(request.path)

            user.set_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset. You can now log in.')
            return redirect('login')

        return render(request, 'password_reset_confirm.html', {
            'validlink': True,
            'uid': uidb64,
            'token': token
        })
 
    messages.error(request, 'Reset link is invalid or expired.')
    return render(request, 'password_reset_confirm.html', {
        'validlink': False
    })

def doctor_list_view(request): 
    query = request.GET.get('q', '')
    specialization = request.GET.get('specialization', '')
    doctor = getattr(request.user, 'doctor_profile', None)
    patient = getattr(request.user, 'patient_profile', None)
    clinic = None
    if doctor and hasattr(doctor, 'clinic_name') and doctor.clinic_name:
        clinic = Clinic.objects.filter(
            name__iexact=doctor.clinic_name.strip(),
            admin__is_superuser=True
        ).first()  
        if clinic and doctor not in clinic.assigned_doctors.all():
            clinic.assigned_doctors.add(doctor)
    doctors = Doctor.objects.filter(user__is_active=True)
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) |
            Q(city__icontains=query)
        )
    if specialization:
        doctors = doctors.filter(specialization__iexact=specialization)
    specializations = Doctor.objects.values_list('specialization', flat=True).distinct()
    paginator = Paginator(doctors.order_by('-is_featured', '-average_rating'), 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'query': query,
        'specializations': specializations,
        'selected_specialization': specialization,
        'doctor': doctor,
        'patient': patient,
        'clinic': clinic,
    }
    return render(request, 'doctor_list.html', context)

def calculate_experience_years(from_date, to_date):
    if not to_date:
        to_date = date.today()
    delta = relativedelta(to_date, from_date)
    return f"{delta.years} years and {delta.months} months"

def group_schedule(schedule_timings):
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_to_index = {day: i for i, day in enumerate(day_order)}
    index_to_day = {i: day for i, day in enumerate(day_order)}
    schedule_timings = sorted(schedule_timings, key=lambda x: day_to_index[x.day_of_week])
    grouped = []
    for key, group in groupby(schedule_timings, key=lambda x: (x.start_time, x.end_time)):
        days = sorted([day_to_index[d.day_of_week] for d in group])
        ranges = []
        start = end = days[0]
        for i in days[1:]:
            if i == end + 1:
                end = i
            else:
                ranges.append((start, end))
                start = end = i
        ranges.append((start, end))
        grouped.append({
            'day_ranges': [(index_to_day[s], index_to_day[e]) for s, e in ranges],
            'start_time': key[0],
            'end_time': key[1],
        })
    return grouped

def doctor_detail_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    logged_in_doctor = None
    patient = None
    blood_bank = None
    clinics = None

    if request.user.is_authenticated:
        blood_bank = BloodBank.objects.filter(user=request.user).first()
        logged_in_doctor = Doctor.objects.filter(user=request.user).first()
        patient = Patient.objects.filter(user=request.user).first()

        if request.user.is_clinic:
            clinics = Clinic.objects.filter(doctor__user=request.user)

    services = Service.objects.filter(doctor=doctor)
    experiences = doctor.experience_set.all()

    reviews = SubmitReview.objects.filter(doctor=doctor).order_by('-created_at')

    time_slots = TimeSlot.objects.filter(
        doctor=doctor,
        is_available=True
    ).order_by('day_of_week', 'start_time')
    grouped_slots = group_schedule(time_slots)

    experience_data = [
        {
            'hospital_name': exp.hospital_name,
            'designation': exp.designation,
            'from_date': exp.from_date,
            'to_date': exp.to_date,
            'duration': calculate_experience_years(exp.from_date, exp.to_date)
        }
        for exp in experiences
    ]

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            if not patient:
                messages.error(request, "You must be logged in as a patient to book an appointment.")
                return redirect('login')

            appointment = form.save(commit=False)
            appointment.doctor = doctor
            appointment.patient = patient
            appointment.save()
            form.save_m2m()
            messages.success(request, "Appointment booked successfully!")
            return redirect('appointment_success')
    else:
        form = AppointmentForm()

    total_reviews = reviews.count()
    average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    return render(request, 'doctor_detail.html', {
        'doctor': doctor,
        'logged_in_doctor': logged_in_doctor,
        'services': services,
        'form': form,
        'experience_data': experience_data,
        'grouped_slots': grouped_slots,
        'patient': patient,
        'blood_bank': blood_bank,
        'clinics': clinics,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 2),
    })

def doctor_reviews(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    sort_option = request.GET.get('sort', 'any')
    if sort_option == 'latest':
        reviews_qs = SubmitReview.objects.filter(doctor=doctor).order_by('-created_at')
    elif sort_option == 'oldest':
        reviews_qs = SubmitReview.objects.filter(doctor=doctor).order_by('created_at')
    else:
        reviews_qs = SubmitReview.objects.filter(doctor=doctor).order_by('-created_at')
    if request.method == 'POST' and request.user == doctor.user:
        review_id = request.POST.get('review_id')
        reply = request.POST.get('reply')
        if review_id and reply:
            review = SubmitReview.objects.get(id=review_id)
            review.reply = reply
            review.reply_created_at = timezone.now()
            review.save()
            return redirect('doctor_reviews', doctor_id=doctor_id)
    paginator = Paginator(reviews_qs, 5)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    context = {
        'doctor': doctor,
        'reviews': reviews,
    }
    return render(request, 'review.html', context)

@login_required
def submit_review(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['rating'] = request.POST.get('rating') 
        form = SubmitReviewForm(post_data)
        if form.is_valid():
            review = form.save(commit=False)
            review.patient = request.user
            review.doctor = form.cleaned_data['doctor']  
            review.save()
            doctor_reviews = SubmitReview.objects.filter(doctor=review.doctor)
            review.doctor.total_reviews = doctor_reviews.count()
            review.doctor.average_rating = round(
                doctor_reviews.aggregate(Avg('rating'))['rating__avg'] or 0, 2
            )
            review.doctor.save()
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect('submit_review')
        else:
            messages.error(request, "Please fix the errors in your submission.")
    else:
        form = SubmitReviewForm()

    return render(request, 'submit_review.html', {
        'form': form,
        'available_doctors': Doctor.objects.all(),
        'patient': getattr(request.user, 'patient_profile', None),
        'logged_in_doctor': getattr(request.user, 'doctor_profile', None),
    })

def contact_us(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None
        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None

    return render(request, 'contact.html', {
        'doctor': doctor,
        'patient': patient, 
    })

def about_us(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None
        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None 
            
    return render(request, 'about.html', {
        'doctor': doctor,
        'patient': patient,
    })

def clinic(request, clinic_id):
    doctor = None
    patient = None
    clinic = Clinic.objects.all()
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None
    clinic = get_object_or_404(Clinic, id=clinic_id)
    doctors = clinic.assigned_doctors.all()
    if clinic.doctor and clinic.doctor not in doctors:
        doctors = list(doctors) + [clinic.doctor]
    paginator = Paginator(doctors, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    can_edit_clinic = False
    if request.user.is_authenticated and request.user == clinic.admin:
        can_edit_clinic = True

    raw = clinic.specifications or ''
    if isinstance(raw, str):
        raw = raw.replace("'", "").replace('"', '')
        specifications = [s.strip() for s in raw.split(',') if s.strip()]
    else:
        specifications = raw  
    half = len(specifications) // 2 + len(specifications) % 2
    specs_left = specifications[:half]
    specs_right = specifications[half:]
    awards = []

    if isinstance(clinic.awards, str):
        awards = [a.strip() for a in clinic.awards.split(',') if a.strip()]
    elif isinstance(clinic.awards, list):
        awards = clinic.awards

    services = ClinicService.objects.filter(clinic=clinic)
    gallery_images = clinic.images.all() if hasattr(clinic, 'images') else []
    
    return render(request, 'clinic.html', {
        "clinic": clinic,
        "form": ClinicForm(instance=clinic),
        "doctor": doctor,
        "patient": patient,
        "page_obj": page_obj,
        "specifications": specifications,
        "services": services,
        "awards": awards,
        "gallery_images": gallery_images,
        "specs_left" :specs_left,
        "specs_right":specs_right,
        "can_edit_clinic": can_edit_clinic,
    })

@login_required
def edit_clinic(request):
    user = request.user
    clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        clinic = Clinic.objects.filter(doctor=doctor).first()
        if not clinic:
            clinic = Clinic.objects.filter(assigned_doctors=doctor).first()

    if not clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        clinic = Clinic.objects.filter(admin=user).first() 
    if not clinic:
        return JsonResponse({'success': False, 'error': 'Clinic not found or permission denied.'}, status=403)
    if request.method == 'POST':
        form = ClinicForm(request.POST, request.FILES, instance=clinic)
        if form.is_valid():
            clinic = form.save()
            data = {
                'name': clinic.name,
                'tagline': clinic.tagline,
                'description': clinic.description,
                'address': clinic.address,
                'phone': clinic.phone,
                'image_url': clinic.image.url if clinic.image else '',
            }
            return JsonResponse({'success': True, 'clinic': data})
        else:
            print("Form errors:", form.errors)
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def add_branch(request, clinic_id):
    user = request.user
    clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        clinic = Clinic.objects.filter(doctor=doctor).first()
        if not clinic:
            clinic = Clinic.objects.filter(assigned_doctors=doctor).first()
    if not clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        clinic = Clinic.objects.filter(admin=user).first()  
    if not clinic:
        return JsonResponse({'success': False, 'error': 'Clinic not found or permission denied.'}, status=403)
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.clinic = clinic
            branch.save()
            return redirect('clinic', clinic_id=clinic.id)
    return redirect('clinic', clinic_id=clinic.id)

@login_required
def edit_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    user = request.user
    clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        clinic = Clinic.objects.filter(doctor=doctor).first()
        if not clinic:
            clinic = Clinic.objects.filter(assigned_doctors=doctor).first()
    if not clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        clinic = Clinic.objects.filter(admin=user).first() 
    if not clinic:
        return JsonResponse({'success': False, 'error': 'Clinic not found or permission denied.'}, status=403)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
    return redirect('clinic', clinic_id=branch.clinic.id)

@login_required
def delete_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    user = request.user
    clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        clinic = Clinic.objects.filter(doctor=doctor).first()
        if not clinic:
            clinic = Clinic.objects.filter(assigned_doctors=doctor).first()
    if not clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        clinic = Clinic.objects.filter(admin=user).first()  
    if not clinic:
        return JsonResponse({'success': False, 'error': 'Clinic not found or permission denied.'}, status=403)
    clinic_id = branch.clinic.id
    branch.delete()
    return redirect('clinic', clinic_id=clinic_id)

@login_required
def edit_clinic_overview(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    user = request.user
    clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        clinic = Clinic.objects.filter(doctor=doctor).first()
        if not clinic:
            clinic = Clinic.objects.filter(assigned_doctors=doctor).first()
    if not clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        clinic = Clinic.objects.filter(admin=user).first()
    if not clinic:
        return JsonResponse({'success': False, 'error': 'Clinic not found or permission denied.'}, status=403)
    if request.method == "POST":
        clinic.about = request.POST.get("about", "").strip()
        raw_specs = request.POST.get("specifications", "")
        if raw_specs.startswith("[") and raw_specs.endswith("]"):
            try:
                import ast
                parsed = ast.literal_eval(raw_specs)
                if isinstance(parsed, list):
                    clinic.specifications = parsed
                else:
                    clinic.specifications = []
            except:
                clinic.specifications = []
        else:
            import re
            clinic.specifications = [s.strip() for s in re.split(r'\d+\.', raw_specs) if s.strip()]
        raw_awards = request.POST.get("awards", "")
        clinic.awards = [a.strip() for a in raw_awards.split(',') if a.strip()]
        raw_services = request.POST.get("services", "")
        services = []
        for item in raw_services.split('|'):
            parts = item.split('-')
            name = parts[0].strip() if len(parts) > 0 else ''
            price = parts[1].strip() if len(parts) > 1 else '0'
            services.append({"name": name, "price": price, "description": ""})
        clinic.services = services
        if request.FILES.getlist('gallery_images'):
            for img in request.FILES.getlist('gallery_images'):
                clinic.images.create(image=img)
        clinic.save()
        return redirect('clinic', clinic_id=clinic.id)
    return redirect('clinic', clinic_id=clinic.id)

@login_required
def delete_gallery_image(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    user = request.user
    user_clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        user_clinic = Clinic.objects.filter(doctor=doctor).first()
        if not user_clinic:
            user_clinic = Clinic.objects.filter(assigned_doctors=doctor).first()
    if not user_clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        user_clinic = Clinic.objects.filter(admin=user).first()
    if not user_clinic or user_clinic != image.clinic:
        return JsonResponse({'success': False, 'error': 'Permission denied or clinic mismatch.'}, status=403)
    image.delete()
    return redirect('clinic', clinic_id=user_clinic.id)

@login_required
def update_clinic_contact(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)
    user = request.user
    clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        clinic = Clinic.objects.filter(doctor=doctor).first()
        if not clinic:
            clinic = Clinic.objects.filter(assigned_doctors=doctor).first()

    if not clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        clinic = Clinic.objects.filter(admin=user).first() 

    if not clinic:
        return JsonResponse({'success': False, 'error': 'Clinic not found or permission denied.'}, status=403)
    
    if request.method == 'POST':
        clinic.working_hours = request.POST.get('working_hours', '')
        clinic.address = request.POST.get('address', '')
        clinic.phone = request.POST.get('phone', '')
        clinic.fax = request.POST.get('fax', '')
        clinic.email = request.POST.get('email', '')
        clinic.website = request.POST.get('website', '')
        clinic.facebook = request.POST.get('facebook', '')
        clinic.instagram = request.POST.get('instagram', '')
        clinic.twitter = request.POST.get('twitter', '')
        clinic.google_plus = request.POST.get('google_plus', '')
        clinic.save()
        return redirect('clinic', clinic_id=clinic.id)
    return redirect('clinic', clinic_id=clinic.id)

def Clinic_list(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass  

    category_id = request.GET.get('category_id')
    query = request.GET.get('q', '').strip()
    clinics = Clinic.objects.all()
    if category_id:
        clinics = clinics.filter(category_id=category_id)
    if query:
        clinics = clinics.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query)
        )
    context = {
        'clinics': clinics,
        'doctor': doctor,
        'patient': patient,
        'query': query,  
    }
    return render(request, 'Clinic_list.html', context)

def search_results(request):
    if request.method == 'POST':
        query = request.POST.get('name', '').strip()
        filter_type = request.POST.get('filter_type', 'all')
        doctors = Doctor.objects.none()
        clinics = Clinic.objects.none()    
        doctor_filter = (
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query)
        )
        clinic_filter = (
            Q(name__icontains=query) |
            Q(city__icontains=query)
        )
        if filter_type == 'all':
            doctors = Doctor.objects.filter(doctor_filter).distinct()
            clinics = Clinic.objects.filter(clinic_filter).distinct()
        elif filter_type == 'doctor':
            doctors = Doctor.objects.filter(doctor_filter).distinct()
        elif filter_type == 'clinic':
            clinics = Clinic.objects.filter(clinic_filter).distinct()
        if doctors.exists() and not clinics.exists():
            query_string = urlencode({'q': query})
            return redirect(f"{reverse('doctor_list')}?{query_string}")
        elif clinics.exists() and not doctors.exists():
            query_string = urlencode({'q': query})
            return redirect(f"{reverse('Clinic_list')}?{query_string}")
        return render(request, 'base.html', {
            'query': query,
            'doctors': doctors,
            'clinics': clinics,
        })
    return redirect('home')

@login_required
def messages_view(request):
    doctor = request.user.doctor_profile 
    doctor_type = ContentType.objects.get_for_model(doctor)
    messages = Message.objects.filter(
        sender_content_type=doctor_type,
        sender_object_id=doctor.id
    )
    context = {
        'doctor':doctor,
        'messages': messages
    }
    return render(request, 'message.html', context)

@login_required
def favourite_doctors(request):
    patient = get_object_or_404(Patient, user=request.user)
    favourite_list = patient.favourites.all()
    paginator = Paginator(favourite_list, 6) 
    page = request.GET.get('page')
    doctors = paginator.get_page(page)

    return render(request, 'favourite_doctors.html', {
        'doctors': doctors,
        'patient': patient,
        'unread_messages': 0, 
    })

@login_required
def toggle_favourite(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    favourite, created = FavouriteDoctor.objects.get_or_create(user=request.user, doctor=doctor)
    if not created:
        favourite.delete()  
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def message_dashboard(request):
    conversations = Conversation.objects.filter(
        Q(doctor=request.user) | Q(patient=request.user)
    ).order_by('-created_at')
    contacts = []
    for conv in conversations:
        contact = conv.doctor if conv.patient == request.user else conv.patient
        last_message = conv.messages.order_by('-timestamp').first()
        unread_count = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        contacts.append({
            'user': contact,
            'conversation_id': conv.id,
            'last_message': last_message.content if last_message else '',
            'timestamp': last_message.timestamp if last_message else conv.created_at,
            'unread_count': unread_count,
            'status': 'online' if contact.is_active else 'away',
        })
    selected_conversation_id = request.GET.get('conversation_id')
    selected_conversation = None
    messages = []
    selected_contact = None
    if selected_conversation_id:
        try:
            selected_conversation = Conversation.objects.get(id=selected_conversation_id)
            if selected_conversation.patient == request.user or selected_conversation.doctor == request.user:
                messages = selected_conversation.messages.order_by('timestamp')
                selected_contact = selected_conversation.doctor if selected_conversation.patient == request.user else selected_conversation.patient
                selected_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        except Conversation.DoesNotExist:
            pass

    context = {
        'contacts': contacts,
        'selected_conversation': selected_conversation,
        'messages': messages,
        'selected_contact': selected_contact,
        'doctor_or_patient': 'doctor' if hasattr(request.user, 'doctor_profile') else 'patient'
    }
    return render(request, 'message.html', context)

@login_required
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conversation_id = data.get('conversation_id')
            content = data.get('content')
            replace_messages = data.get('replace', False)  
            if not content or not conversation_id:
                return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
            conversation = Conversation.objects.get(id=conversation_id)
            if conversation.patient != request.user and conversation.doctor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            if replace_messages:
                conversation.messages.all().delete()
            new_messages = Message.objects.for_receiver(request.user).filter(is_read=False).count()
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': new_messages.id,
                    'content': new_messages.content,
                    'timestamp': new_messages.timestamp.strftime('%I:%M %p'),
                    'sender': new_messages.sender.username,
                }
            })
        except Conversation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
def clinic_dashboard(request):
    user = request.user
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    clinics = Clinic.objects.filter(admin=user)
    clinic_id = request.GET.get('clinic_id')
    clinic = clinics.filter(id=clinic_id).first() if clinic_id else clinics.first()
    if not isinstance(clinic, Clinic):
        return render(request, 'clinic/dashboard.html', {
            'error': 'No clinic found or access denied.',
            'clinics': clinics
        })
    doctor_list = Doctor.objects.filter(clinics=clinic).distinct()
    total_doctors = doctor_list.count()
    appointments = Appointment.objects.filter(
        doctor__in=doctor_list,
        doctor__clinics=clinic
    ).distinct()
    appointment_count = appointments.count()
    total_appointments = appointments.count()
    upcoming_appointments = appointments.filter(
        appointment_datetime__gte=timezone.now()
    ).count()
    Approved = appointments.filter(status__iexact='accepted').count()
    pending = appointments.filter(status__iexact='pending').count()
    total_patients = Patient.objects.filter(
        appointments__in=appointments
    ).distinct().count()
    reviews_count = SubmitReview.objects.filter(
        doctor__in=doctor_list,
        doctor__clinics=clinic
    ).count()
    context = {
        'clinic': clinic,
        'blood_bank':blood_bank,
        'clinics': clinics,
        'doctor_list': doctor_list,
        'total_doctors': total_doctors,
        'appointment_count': appointment_count,
        'total_patients': total_patients,
        'upcoming_appointments': upcoming_appointments,
        'total_appointments': total_appointments,
        'reviews_count': reviews_count,
        'Approved': Approved,
        'pending': pending,
        'is_clinic_owner': True,
    }
    return render(request, 'clinic/dashboard.html', context)

@login_required
def clinic_appointment_list(request):
    user = request.user
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    clinics = Clinic.objects.filter(admin=user)

    if not clinics.exists():
        messages.error(request, "You are not assigned to any clinic.")
        return redirect('home')
    clinic_id = request.GET.get('clinic_id')
    clinic = clinics.filter(id=clinic_id).first() if clinic_id else clinics.first()
    if not clinic:
        messages.error(request, "Invalid clinic selection.")
        return redirect('home')
    doctors_in_clinic = Doctor.objects.filter(clinics=clinic).distinct()
    now = timezone.now()
    all_appointments = Appointment.objects.filter(
        doctor__in=doctors_in_clinic,
        doctor__clinics=clinic
    ).distinct()
    past_appointments = []
    upcoming_appointments = []
    for appt in all_appointments:
        if timezone.is_naive(appt.appointment_datetime):   
            appt.appointment_datetime = timezone.make_aware(appt.appointment_datetime)
        if appt.appointment_datetime < now:
            past_appointments.append(appt)
        else:
            upcoming_appointments.append(appt)
    upcoming_appointments.sort(key=lambda x: x.appointment_datetime)
    past_appointments.sort(key=lambda x: x.appointment_datetime, reverse=True)
    paginator_upcoming = Paginator(upcoming_appointments, 10)
    paginator_past = Paginator(past_appointments, 10)
    upcoming_page = request.GET.get('upcoming_page')
    past_page = request.GET.get('past_page')
    upcoming_page_obj = paginator_upcoming.get_page(upcoming_page)
    past_page_obj = paginator_past.get_page(past_page)

    return render(request, 'clinic/clinic_appointments.html', {
        'clinic': clinic,
        'clinics': clinics,
        'upcoming_page_obj': upcoming_page_obj,
        'past_page_obj': past_page_obj,
        'doctor': getattr(user, 'doctor_profile', None),
        'blood_bank':blood_bank,
    })

@login_required
def clinic_listing(request):
    user = request.user
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    clinics = Clinic.objects.filter(admin=user)
    clinic_id = request.GET.get('clinic_id')
    clinic = clinics.filter(id=clinic_id).first() if clinic_id else clinics.first()

    if not clinic:
        return redirect('some_error_page')

    if request.method == 'POST':
        ClinicListing.objects.filter(clinic=clinic).delete()
        ClinicService.objects.filter(clinic=clinic).delete()

        treatments = request.POST.getlist('treatment[]')
        prices = request.POST.getlist('price[]')

        for treatment, price in zip(treatments, prices):
            if treatment and price:
                ClinicListing.objects.create(clinic=clinic, treatment=treatment, price=price)
                ClinicService.objects.create(clinic=clinic, name=treatment, price=price)
        return redirect(f"{request.path}?clinic_id={clinic.id}")
    pricing = ClinicListing.objects.filter(clinic=clinic)
    print("Pricing in template:", pricing)
    return render(request, 'clinic/clinic_listing.html', {
        'pricing': pricing,
        'clinic': clinic,
        'clinics': clinics,
        'blood_bank':blood_bank,
    })

class BloodBankListView(ListView):
    model = BloodBank
    template_name = 'bloodbank/bloodbank_list.html'
    context_object_name = 'bloodbanks'
    queryset = BloodBank.objects.filter(is_active=True)
    ordering = ['name']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['doctor'] = None
        context['patient'] = None
        context['blood_bank'] = None
        context['clinics'] = None
        if user.is_authenticated:
            context['blood_bank'] = BloodBank.objects.filter(user=user).first()
            try:
                context['doctor'] = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                try:
                    context['patient'] = Patient.objects.get(user=user)
                except Patient.DoesNotExist:
                    pass
            if user.is_clinic:
                context['clinics'] = Clinic.objects.filter(doctor__user=user)

        return context

class BloodBankDetailView(DetailView):
    model = BloodBank
    template_name = 'bloodbank/bloodbank_detail.html'
    context_object_name = 'bloodbank'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bloodbank = self.object
        user = self.request.user
        today = timezone.now().date()
        blood_group_summary = (
            BloodInventory.objects
            .filter(blood_bank=bloodbank)
            .values('blood_group')
            .annotate(total_units=Sum('quantity'))
            .order_by('blood_group')
        )
        context['blood_bank'] = bloodbank  
        context['blood_group_summary'] = blood_group_summary
        context['can_edit'] = user == bloodbank.user or user.is_staff
        context['clinic'] = Clinic.objects.filter(admin=self.request.user).first()
        context['doctor'] = None
        context['patient'] = None
        if user.is_authenticated:
            try:
                context['doctor'] = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                pass
            try:
                context['patient'] = Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                pass
        return context

class BloodBankCreateView(LoginRequiredMixin, CreateView):
    model = BloodBank
    form_class = BloodBankForm
    template_name = 'bloodbank/bloodbank_form.html'
    success_url = reverse_lazy('clinic_dashboard')

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "❌ You must be logged in to submit this form.")
            return redirect('login') 
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['doctor'] = None
        context['patient'] = None
        if user.is_authenticated:
            try:
                context['doctor'] = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                pass
            try:
                context['patient'] = Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                pass

        return context

class BloodBankUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BloodBank
    form_class = BloodBankForm
    template_name = 'bloodbank/bloodbank_form.html'
    success_url = reverse_lazy('bloodbank-list')
    def test_func(self):
        bloodbank = self.get_object()
        return self.request.user == bloodbank.user or self.request.user.is_staff

def blood_donation_dashboard(request, bank_id):
    clinic= Clinic.objects.filter(admin=request.user).first()
    blood_bank = get_object_or_404(BloodBank, id=bank_id)
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    inventory_data = []  
    for group in blood_groups:
        inventory_items = BloodInventory.objects.filter(
            blood_bank=blood_bank,
            blood_group=group,
        )
        total_units = sum(i.quantity for i in inventory_items)
        stock_status = (
            'Not Available' if total_units == 0 else
            'Critical' if total_units < 5 else
            'Low' if total_units < 10 else
            'Available'
        )
        blood_requests = BloodRequest.objects.filter(
            blood_group=group,
            status='pending'
        )
        donor_requests = DonorRecord.objects.filter(
            blood_group=group,
            donor_status='eligible'
        )
        inventory_data.append({
            'group': group,
            'units': total_units,
            'status': stock_status,
            'blood_requests': blood_requests,
            'donor_requests': donor_requests,
        })
    blood_paginator = Paginator(BloodRequest.objects.all(), 10)
    donor_paginator = Paginator(DonorRecord.objects.all(), 10)
    blood_page_number = request.GET.get('page')
    donor_page_number = request.GET.get('donor_page')
    
    return render(request, 'bloodbank/blood_donation_dashboard.html', {
        'blood_bank': blood_bank,
        'inventory_data': inventory_data,
        'blood_requests_page': blood_paginator.get_page(blood_page_number),
        'donor_requests_page': donor_paginator.get_page(donor_page_number),
        'all_blood_requests': BloodRequest.objects.all(),
        'all_donor_requests': DonorRecord.objects.all(),
        'clinic':clinic,
    })

@login_required
def manage_inventory(request):
    doctor = None
    patient = None
    blood_bank = None
    clinics = None
    if request.user.is_authenticated:
        blood_bank = BloodBank.objects.filter(user=request.user).first()
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass
    if request.user.is_authenticated and request.user.is_clinic:
        try:
           clinics = Clinic.objects.filter(doctor__user=request.user)
        except Clinic.DoesNotExist:
            pass
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    if not blood_bank:
        messages.error(request, "No associated Blood Bank found.")
        return redirect('home')

    clinic = Clinic.objects.filter(admin=request.user).first()
    create_form = BloodInventoryForm()
    dispatch_form = DispatchBloodForm()

    if request.method == "POST":
        if 'create-submit' in request.POST:
            create_form = BloodInventoryForm(request.POST)
            if create_form.is_valid():
                blood_group = create_form.cleaned_data['blood_group']
                quantity = create_form.cleaned_data['quantity']

                existing_inventory = BloodInventory.objects.filter(
                    blood_bank=blood_bank,
                    blood_group=blood_group
                ).first()

                if existing_inventory:
                    existing_inventory.quantity += quantity
                    existing_inventory.save()
                    messages.success(request, f"{quantity} units added to existing {blood_group} inventory.")
                else:
                    new_item = create_form.save(commit=False)
                    new_item.blood_bank = blood_bank
                    new_item.save()
                    messages.success(request, f"New entry for {blood_group} created with {quantity} units.")

                return redirect('manage_inventory')
            else:
                messages.error(request, "Failed to add inventory. Please check the form.")

        elif 'dispatch-submit' in request.POST:
            dispatch_form = DispatchBloodForm(request.POST)
            if dispatch_form.is_valid():
                blood_group = dispatch_form.cleaned_data['blood_group']
                quantity = dispatch_form.cleaned_data['quantity']
                recipient_name = dispatch_form.cleaned_data.get('recipient_name')
                purpose = dispatch_form.cleaned_data.get('purpose')

                try:
                    inventory = BloodInventory.objects.get(
                        blood_bank=blood_bank,
                        blood_group=blood_group
                    )
                    if inventory.quantity >= quantity:
                        inventory.quantity -= quantity
                        inventory.save()

                        BloodDispatch.objects.create(
                            blood_bank=blood_bank,
                            blood_group=blood_group,
                            quantity=quantity,
                            recipient_name=recipient_name,
                            purpose=purpose,
                        )

                        messages.success(request, f"{quantity} units of {blood_group} dispatched successfully.")
                    else:
                        messages.error(request, f"Only {inventory.quantity} units of {blood_group} available.")
                except BloodInventory.DoesNotExist:
                    messages.error(request, "Blood group not available in inventory.")

                return redirect('manage_inventory')
            else:
                messages.error(request, "Failed to dispatch blood. Please check the form.")

        elif 'edit-submit' in request.POST:
            inventory_id = request.POST.get('inventory_id')
            inventory = get_object_or_404(BloodInventory, id=inventory_id, blood_bank=blood_bank)
            edit_form = BloodInventoryForm(request.POST, instance=inventory)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, f"Inventory for {inventory.blood_group} updated successfully.")
            else:
                messages.error(request, "Failed to update inventory. Please check the form.")

            return redirect('manage_inventory')

    inventory_qs = BloodInventory.objects.filter(blood_bank=blood_bank)
    inventory_paginator = Paginator(inventory_qs, 8)
    inventory_page_number = request.GET.get('inventory_page')
    inventory_page = inventory_paginator.get_page(inventory_page_number)

    for item in inventory_page:
        item.edit_form = BloodInventoryForm(instance=item)

    dispatch_qs = BloodDispatch.objects.filter(blood_bank=blood_bank).order_by('-dispatched_at')
    dispatch_paginator = Paginator(dispatch_qs, 8)
    dispatch_page_number = request.GET.get('dispatch_page')
    dispatch_page = dispatch_paginator.get_page(dispatch_page_number)

    context = {
        'create_form': create_form,
        'dispatch_form': dispatch_form,
        'inventory_items': inventory_page,
        'Dispatch_items': dispatch_page,
        'inventory_page': inventory_page,
        'dispatch_page': dispatch_page,
        'blood_bank': blood_bank,
        'clinic': clinic,
    }
    return render(request, 'bloodbank/blood_inventory_form.html', context)

@login_required
def edit_inventory(request, inventory_id):
    inventory = get_object_or_404(BloodInventory, id=inventory_id)
    if inventory.blood_bank.user != request.user:
        return redirect('manage_inventory') 
    if request.method == "POST":
        form = BloodInventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, f"Inventory for {inventory.blood_group} updated successfully.")
        else:
            messages.error(request, "Failed to update inventory. Please check the form.")
    return redirect('manage_inventory')

@login_required
def create_blood_request(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            pass
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            pass

    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.requested_by = request.user 
            blood_request.save()
            messages.success(request, "✅ Blood request submitted successfully.")
            return redirect('create_blood_request')
    else:
        form = BloodRequestForm()

    return render(request, 'bloodbank/blood_request_form.html', {
        'form': form,
        'doctor': doctor,
        'patient': patient,
    })

@login_required
@require_POST
def update_blood_request_status(request, pk):
    request_obj = get_object_or_404(BloodRequest, pk=pk)
    new_status = request.POST.get('status')

    if new_status in dict(BloodRequest.REQUEST_STATUS):
        request_obj.status = new_status
        request_obj.save()

        if request_obj.requested_by and request_obj.requested_by.email:
            subject = "Blood Request Status Update"
            message = (
                f"Dear {request_obj.requested_by.get_full_name() or request_obj.patient_name},\n\n"
                f"The status of your blood request has been updated to '{new_status}'.\n\n"
                f"Blood Group: {request_obj.blood_group}\n"
                f"Component: {request_obj.component_type}\n"
                f"Quantity: {request_obj.quantity_needed} units\n"
                "\nThank you,\nBlood Bank Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [request_obj.requested_by.email],
                fail_silently=False,
            )
        messages.success(request, f"Request status updated to '{new_status}' and email sent.")
    else:
        messages.error(request, "Invalid status value.")

    return redirect('blood_requests_list')

@login_required
def list_blood_requests(request):
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    clinic = Clinic.objects.filter(admin=request.user).first()
    
    queryset = BloodRequest.objects.filter(blood_bank=blood_bank).order_by('-created_at')
    filterset = BloodRequestFilter(request.GET, queryset=queryset)
    paginator = Paginator(filterset.qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bloodbank/blood_request_list.html', {
        'blood_requests': page_obj,
        'filter': filterset,
        'page_obj': page_obj,
        'blood_bank': blood_bank,
        'clinic': clinic,
    })

def donor_submit_view(request):
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            pass
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            pass
    if request.method == 'POST':
        form = DonorRecordForm(request.POST)
        if form.is_valid():
            blood_bank_name = form.cleaned_data.get('blood_bank_name')
            donor_phone = form.cleaned_data.get('donor_phone')
            last_donation_date = form.cleaned_data.get('last_donation_date')

            try:
                blood_bank = BloodBank.objects.get(name__iexact=blood_bank_name)
                existing_donor = DonorRecord.objects.filter(
                    blood_bank=blood_bank,
                    donor_phone=donor_phone
                ).order_by('-last_donation_date').first()

                if existing_donor:
                    last_donation = existing_donor.last_donation_date
                    if hasattr(last_donation, 'tzinfo'):
                        last_donation = make_naive(last_donation)

                    days_since_last_donation = (date.today() - last_donation).days

                    if days_since_last_donation < 90:
                        form.add_error('donor_phone', f"You have already submitted a record. You can donate again after {90 - days_since_last_donation} days.")
                    else:
                        donor = form.save(commit=False)
                        donor.blood_bank = blood_bank
                        donor.save()
                        messages.success(request, "✅ Donor information submitted successfully.")
                        return redirect('home')
                else:
                    if last_donation_date and (date.today() - last_donation_date).days < 90:
                        form.add_error('last_donation_date', 'You can donate again only after 3 months from your last donation.')
                    else:
                        donor = form.save(commit=False)
                        donor.blood_bank = blood_bank
                        donor.requested_by = request.user  
                        donor.save()
                        messages.success(request, "✅ Donor information submitted successfully.")
                        return redirect('donor_submit')

            except BloodBank.DoesNotExist:
                form.add_error('blood_bank_name', '❌ Blood Bank not found. Please check the name.')
    else:
        form = DonorRecordForm()
    return render(request, 'bloodbank/public_donor_form.html', {
        'form': form,
        'doctor':doctor,
        'patient':patient,
        'blood_bank':blood_bank,
        })

class DonorRecordListView(LoginRequiredMixin, ListView):
    model = DonorRecord
    template_name = 'bloodbank/admin_donor_list.html'
    context_object_name = 'donors'
    paginate_by = 10

    def get_queryset(self):
        return DonorRecord.objects.filter(blood_bank__user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blood_bank'] = BloodBank.objects.filter(user=self.request.user).first()
        context['clinic'] = Clinic.objects.filter(admin=self.request.user).first()
        return context

@staff_member_required
def update_donor_status(request, donor_id):
    donor = get_object_or_404(DonorRecord, id=donor_id)
    if request.method == 'POST':
        new_status = request.POST.get('donor_status')
        if new_status in ['available', 'unavailable']:
            donor.donor_status = new_status
            donor.save()

            subject = "Donor Availability Status Update"
            message = (
                f"Dear {donor.donor_name},\n\n"
                f"Your donor record status is now marked as '{new_status}'.\n"
                "Thank you for your contribution."
            )
            recipients = []
            if donor.donor_email:
                recipients.append(donor.donor_email)
            if donor.requested_by and donor.requested_by.email:  
                recipients.append(donor.requested_by.email)

            if recipients:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=False,
                )
    
    return redirect('admin_donor_list')

BLOOD_GROUP_ORDER = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
def bloodbank_dashboard(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:                
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
                pass
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
                pass
   
    inventory_data = [{'group': bg, 'units': 0} for bg in BLOOD_GROUP_ORDER]
    group_index_map = {item['group']: idx for idx, item in enumerate(inventory_data)}
    inventory = BloodInventory.objects.all()
    for item in inventory:
        if item.blood_group in group_index_map:
            inventory_data[group_index_map[item.blood_group]]['units'] = item.quantity

    return render(request, 'bloodbank/bloodbank_dashboard.html', {
        'inventory_data': inventory_data,
        'doctor': doctor,
        'patient': patient,
        })

@login_required
def test_list(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None
    test_categories = TestCategory.objects.filter(type='test')
    package_categories = TestCategory.objects.filter(type='package')

    test_category_tests = {
        category: DiagnosticTest.objects.filter(category=category, is_active=True)
        for category in test_categories
    }

    package_category_tests = {
        category: DiagnosticTest.objects.filter(category=category, is_active=True,is_package=True)
        for category in package_categories
    }
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_price = 0
    for item in cart_items:
        obj = item.content_object
        model_name = item.content_type.model

        if model_name == 'diagnostictest':
            total_price += item.quantity * getattr(obj, 'discounted_price', 0)
        elif model_name == 'product':
            price = getattr(obj, 'discount_price', obj.price)
            total_price += item.quantity * price
    return render(request, 'diagnosis/test_list.html', {
        'test_category_tests': test_category_tests,
        'package_category_tests': package_category_tests,
        'cart_tests': cart_items,
        'cart_total': total_price,
        'doctor':doctor,
        'patient':patient,
    })

@login_required
def add_to_cart(request, model_name, object_id):
    content_type = get_object_or_404(ContentType, model=model_name)
    model_class = content_type.model_class()
    product = get_object_or_404(model_class, id=object_id)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, defaults={'session_key': session_key})
    else:
        cart, created = Cart.objects.get_or_create(session_key=session_key)

    is_test = content_type.model == 'diagnostictest'

    preferred_date = request.POST.get('preferred_date')
    preferred_time = request.POST.get('preferred_time')
    notes = request.POST.get('notes')

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        content_type=content_type,
        object_id=object_id,
    )

    if created:
        cart_item.quantity = 1
    else:
        if is_test:
            cart_item.quantity = 1
        else:
            cart_item.quantity += 1 

    if is_test:
        if preferred_date:
            try:
                cart_item.preferred_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
            except ValueError:
                cart_item.preferred_date = None
        cart_item.preferred_time = preferred_time or None
        cart_item.notes = notes or None

    cart_item.save()

    messages.success(request, "Item added to cart!")

    referer = request.META.get('HTTP_REFERER', '/')
    if urlparse(referer).path.startswith('/add-to-cart'):
        return redirect('/')
    return redirect(referer)

@login_required
def view_cart(request):
    doctor = None
    patient = None
    blood_bank = None
    clinics = None
    if request.user.is_authenticated:
        blood_bank = BloodBank.objects.filter(user=request.user).first()
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass
    if request.user.is_authenticated and request.user.is_clinic:
        try:
           clinics = Clinic.objects.filter(doctor__user=request.user)
        except Clinic.DoesNotExist:
            pass
    cart, created = Cart.objects.get_or_create(user=request.user)
    total_price = 0

    for item in cart.items.all():
        content_object = item.content_object
        quantity = item.quantity

        if item.content_type.model == 'product':
            price = content_object.discount_price if content_object.discount_price else content_object.price
        elif item.content_type.model == 'diagnostictest':
            price = content_object.discounted_price
        else:
            price = 0

        total_price += price * quantity

    return render(request, 'medicine/view_cart.html', {
        'cart': cart,
        'total_price': total_price,
        'doctor': doctor,
        'patient': patient,
        'blood_bank': blood_bank,
        'clinics': clinics,
    })

@require_POST
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        item.quantity = quantity
        item.save()
    return redirect('view_cart')


def remove_from_cart(request, item_id):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(session_key=session_key).first()

    if not cart:
        return redirect('view_cart') 

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()

    return redirect('view_cart')

@login_required
def book_tests(request):
    if request.method == 'POST':
        test_ids = CartItem.objects.filter(user=request.user).values_list('test_id', flat=True)
        if test_ids:
            booking = Booking.objects.create(user=request.user)
            booking.tests.set(test_ids)
            booking.save()
            CartItem.objects.filter(user=request.user).delete()
            return redirect('booking_success')
    return redirect('test_list')

def manage_tests(request):
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    clinic = Clinic.objects.filter(admin=request.user).first()
    if request.method == 'POST' and 'add_test' in request.POST:
        form = DiagnosticTestForm(request.POST)

        if form.is_valid():
            selected_category = form.cleaned_data.get('category')
            print("✅ Saving test with category:", selected_category)
            form.save()
            messages.success(request, "Diagnostic test added successfully.")
            return redirect('manage_tests')
        else:
            print("❌ Form submission failed.")
            print("Form Errors:", form.errors)
            print("POST Data:", request.POST)
    else:
        form = DiagnosticTestForm()

    all_tests = DiagnosticTest.objects.select_related('category').all()

    for test in all_tests:
        test.edit_form = DiagnosticTestForm(instance=test, prefix=str(test.id))

    grouped_tests = defaultdict(list)
    for test in all_tests:
        grouped_tests[test.category].append(test)

    return render(request, 'diagnosis/manage_tests.html', {
        'form': form,
        'grouped_tests': grouped_tests.items(),
        'all_tests': all_tests,
        'clinic':clinic,
        'blood_bank':blood_bank,
    })

def edit_test(request, test_id):
    test = get_object_or_404(DiagnosticTest, id=test_id)
    if request.method == 'POST':
        form = DiagnosticTestForm(request.POST, instance=test, prefix=str(test.id))
        if form.is_valid():
            form.save()
            messages.success(request, f"Test '{test.name}' updated successfully.")
        else:
            messages.error(request, f"Error updating test '{test.name}'. Please correct the errors.")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('manage_tests')


def delete_test(request, test_id):
    test = get_object_or_404(DiagnosticTest, id=test_id)
    test.delete()
    return redirect('manage_tests')

def add_category(request):
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    clinic = Clinic.objects.filter(admin=request.user).first()
    if request.method == 'POST':
        form = TestCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_category') 
    else:
        form = TestCategoryForm()

    all_categories = TestCategory.objects.all()
    return render(request, 'diagnosis/add_category.html', {
        'form': form,
        'categories': all_categories,
        'clinic':clinic,
        'blood_bank': blood_bank,
    })

def update_category(request, pk):
    category = get_object_or_404(TestCategory, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.type = request.POST.get('type')
        category.save()
        messages.success(request, 'Category updated successfully.')
    return redirect('add_category')  

def delete_category(request, pk):
    category = get_object_or_404(TestCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    return redirect('add_category')


from utils.crypto import inr_to_bnb
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json

@login_required
def checkout_view(request):
    doctor = Doctor.objects.filter(user=request.user).first()
    patient = Patient.objects.filter(user=request.user).first()

    cart_items = CartItem.objects.filter(cart__user=request.user)

    has_tests = any(i.content_type.model == "diagnostictest" for i in cart_items)
    has_medicines = any(i.content_type.model == "product" for i in cart_items)

    total_price = 0
    cart_items_json = []

    for item in cart_items:
        obj = item.content_object
        if not obj:
            continue

        if item.content_type.model == "product":
            price = getattr(obj, "discount_price", None) or obj.price
        elif item.content_type.model == "diagnostictest":
            price = obj.discounted_price
        else:
            price = 0

        total_price += price * (item.quantity or 1)

        cart_items_json.append({
            "name": obj.name,
            "quantity": item.quantity,
            "model": item.content_type.model,
        })

    crypto_amount = inr_to_bnb(total_price)

    return render(request, "diagnosis/checkout.html", {
        "cart_items": cart_items,
        "cart_items_json": cart_items_json,          # ✅ NOT json.dumps
        "total_price": total_price,
        "crypto_amount": crypto_amount,
        "chain_id": settings.CHAIN_ID,
        "service_wallet_address": settings.SERVICE_WALLET_ADDRESS,
        "ENVIRONMENT": settings.BLOCKCHAIN_ENV,      # ✅ NEW
        "doctor": doctor,
        "patient": patient,
        "has_tests": has_tests,
        "has_medicines": has_medicines,
    })


from django.http import JsonResponse
from django.urls import reverse
from web3 import Web3
from decimal import Decimal
import json

@login_required
def place_order_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    tx_hash = request.POST.get("tx_hash")
    if not tx_hash:
        return JsonResponse({"error": "Missing transaction hash"}, status=400)

    # 🔒 Anti-replay
    if Booking.objects.filter(tx_hash=tx_hash).exists():
        return JsonResponse({"error": "Duplicate transaction"}, status=400)

    w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))

    if not w3.is_connected():
        return JsonResponse({"error": "Blockchain unavailable"}, status=500)

    # ✅ Correct network check
    if int(w3.eth.chain_id) != int(settings.CHAIN_ID):
        return JsonResponse({"error": "Wrong network"}, status=400)

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        return JsonResponse({"error": "Transaction not found"}, status=400)

    if receipt.status != 1:
        return JsonResponse({"error": "Transaction failed"}, status=400)

    tx = w3.eth.get_transaction(tx_hash)

    # ✅ Receiver verification (checksum safe)
    if Web3.to_checksum_address(tx["to"]) != Web3.to_checksum_address(
        settings.SERVICE_WALLET_ADDRESS
    ):
        return JsonResponse({"error": "Invalid receiver"}, status=400)

    total_price = Decimal(request.POST.get("total_price"))
    expected_bnb = inr_to_bnb(total_price)
    paid_bnb = Decimal(Web3.from_wei(tx["value"], "ether"))

    # ✅ 1% tolerance (industry standard)
    if paid_bnb < expected_bnb * Decimal("0.99"):
        return JsonResponse({"error": "Insufficient payment"}, status=400)

    clinic = Clinic.objects.first()
    if not clinic:
        return JsonResponse({"error": "Clinic not configured"}, status=500)

    booking = Booking.objects.create(
        user=request.user,
        clinic=clinic,
        name=request.POST.get("name"),
        phone=request.POST.get("phone"),
        email=request.POST.get("email"),
        total_price=total_price,
        crypto_amount=paid_bnb,
        tx_hash=tx_hash,
        user_wallet_address=request.POST.get("user_wallet_address"),
        cart_data=json.loads(request.POST.get("cart_data")),
        status="Booked",
    )

    CartItem.objects.filter(cart__user=request.user).delete()

    return JsonResponse({
        "status": "success",
        "redirect_url": reverse("booking_success_page", args=[booking.id]),
    })


@login_required
def booking_success_page(request, booking_id):
    doctor = Doctor.objects.filter(user=request.user).first()
    patient = Patient.objects.filter(user=request.user).first()

    booking = get_object_or_404(Booking, id=booking_id)

    # ✅ ALWAYS define cart_items first
    cart_items = booking.cart_data or []

    # ✅ Update status once (idempotent)
    if booking.status != "Booked":
        booking.status = "Booked"
        booking.save()

        # Reduce product stock only once
        product_lookup = {
            p.name.lower(): p for p in Product.objects.all()
        }

        for item in cart_items:
            name = item.get("name", "").strip().lower()
            quantity = int(item.get("quantity", 1))

            product = product_lookup.get(name)
            if product and product.stock_quantity >= quantity:
                product.stock_quantity -= quantity
                product.save()

    # --- Classification ---
    product_names = set(
        Product.objects.values_list("name", flat=True)
    )
    test_names = set(
        DiagnosticTest.objects.values_list("name", flat=True)
    )

    lab_tests = []
    medicines = []

    for item in cart_items:
        name = item.get("name", "").strip().lower()

        if name in (t.lower() for t in test_names):
            item["type"] = "lab"
            lab_tests.append(item)

        elif name in (p.lower() for p in product_names):
            item["type"] = "medicine"
            medicines.append(item)

        else:
            model_name = (
                item.get("model", "")
                .lower()
                .replace(" ", "")
            )

            if "test" in model_name:
                item["type"] = "lab"
                lab_tests.append(item)
            else:
                item["type"] = "medicine"
                medicines.append(item)

    return render(
        request,
        "diagnosis/booking_success.html",
        {
            "booking": booking,
            "lab_tests": lab_tests,
            "medicines": medicines,
            "doctor": doctor,
            "patient": patient,
        },
    )


from utils.blockchain import confirm_transaction
def verify_pending_payments():
    pending = Booking.objects.filter(status="PENDING")

    for booking in pending:
        if confirm_transaction(booking.tx_hash):
            booking.status = "PAID"
            booking.save()


LAB_STATUS_CHOICES = [
    ('Booked', 'Booked'),
    ('Phlebo Assigned', 'Phlebo Assigned'),
    ('Sample Collected', 'Sample Collected'),
    ('In Transit', 'In Transit to Lab'),
    ('Received at Lab', 'Received at Lab'),
    ('Under Analysis', 'Under Analysis'),
    ('Report Ready', 'Report Ready'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
]

MEDICINE_STATUS_CHOICES = [
    ('Placed', 'Placed'),
    ('Packed', 'Packed'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
]

def is_clinic_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_clinic_admin)
@login_required
def clinic_bookings_view(request):
    clinic = Clinic.objects.filter(admin=request.user).first()
    today = timezone.now().date()
    filter_type = request.GET.get('filter', 'upcoming')
    active_tab = request.GET.get('tab', 'tests')
    page_number = request.GET.get('page', 1)

    if not clinic:
        messages.error(request, "No clinic found for this admin.")
        return redirect('dashboard')

    context = {
        'active_tab': active_tab,
        'filter_type': filter_type,
        'clinic': clinic,
        'today': today,
    }

    medicine_names = set(Product.objects.values_list('name', flat=True))
    diagnostic_names = set(DiagnosticTest.objects.values_list('name', flat=True))

    if active_tab == 'medicines':
        orders_qs = Booking.objects.filter(clinic=clinic)
        context['medicine_status_choices'] = MEDICINE_STATUS_CHOICES

        if filter_type == 'past':
            orders_qs = orders_qs.filter(medicine_status__in=['Delivered', 'Cancelled'])
        else:
            orders_qs = orders_qs.exclude(medicine_status__in=['Delivered', 'Cancelled'])

        orders_qs = orders_qs.order_by('created_at')

        valid_orders = []
        for order in orders_qs:
            med_items = []
            for item in order.cart_data:
                name = item.get("name", "").strip().lower()
                if name in (n.lower() for n in medicine_names):
                    item["type"] = "medicine"
                    med_items.append(item)

            if med_items:
                order.filtered_cart_data = med_items
                order.filtered_total_price = sum(
                    float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in med_items
                )
                valid_orders.append(order)

        paginator = Paginator(valid_orders, 10)
        context['medicine_orders'] = paginator.get_page(page_number)
        context['bookings'] = None

    else:  
        bookings_qs = Booking.objects.filter(clinic=clinic)
        context['lab_status_choices'] = LAB_STATUS_CHOICES

        if filter_type == 'past':
            bookings_qs = bookings_qs.filter(lab_status__in=['Completed', 'Cancelled'])
        else:
            bookings_qs = bookings_qs.exclude(lab_status__in=['Completed', 'Cancelled'])

        bookings_qs = bookings_qs.order_by('created_at')

        valid_bookings = []
        for booking in bookings_qs:
            lab_items = []
            for item in booking.cart_data:
                name = item.get("name", "").strip().lower()
                if name in (n.lower() for n in diagnostic_names):
                    item["type"] = "lab"
                    lab_items.append(item)

            if lab_items:
                booking.filtered_cart_data = lab_items
                booking.filtered_total_price = sum(
                    float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in lab_items
                )
                valid_bookings.append(booking)
        paginator = Paginator(valid_bookings, 10)
        context['bookings'] = paginator.get_page(page_number)
        context['medicine_orders'] = None
        
    return render(request, 'clinic/bookings.html', context)

@user_passes_test(is_clinic_admin)
@login_required
@require_POST
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('lab_status')

    valid_statuses = dict(LAB_STATUS_CHOICES).keys()
    notify_statuses = ['Booked', 'Sample Collected', 'Report Ready', 'Completed']

    if new_status not in valid_statuses:
        messages.error(request, "Invalid status selected.")
    elif new_status == booking.lab_status:
        messages.warning(request, "This status is already set.")
    else:
        booking.lab_status = new_status
        booking.save()

        if new_status in notify_statuses:
            booking_with_reports = Booking.objects.prefetch_related('reports').get(id=booking.id)

            context = {
                'name': booking.name,
                'lab_status': new_status,
                'preferred_date': booking.preferred_date,
                'booking_id': booking.id,
                'total_price': booking.total_price,
                'booking': booking_with_reports,
                'now': timezone.now(),
            }

            subject = f"Your Lab Test Booking Status: {new_status}"
            from_email = 'Dineshkumar630186@gmail.com'
            to_email = booking.email
            text_content = f"Dear {booking.name}, your lab test status is now: {new_status}."
            html_content = render_to_string('clinic/status_update_email.html', context)

            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            try:
                email.send()
            except Exception as e:
                messages.warning(request, f"Status updated but email failed: {e}")

        messages.success(request, f"Lab status updated to '{new_status}'.")

    return redirect('clinic_bookings')

@user_passes_test(is_clinic_admin)
@login_required
@require_POST
def update_medicine_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('medicine_status')
    valid_statuses = dict(MEDICINE_STATUS_CHOICES).keys()
    notify_statuses = ['Placed','Packed','Shipped','Delivered']

    if new_status not in valid_statuses:
        messages.error(request, "Invalid status selected.")
    elif new_status == 'Delivered' and booking.medicine_status != 'Packed':
        messages.error(request, "Cannot mark as Delivered unless status is Packed.")
    elif new_status == booking.medicine_status:
        messages.warning(request, "This status is already set.")
    else:
        booking.medicine_status = new_status
        booking.save()

        if new_status in notify_statuses:
            booking_with_reports = Booking.objects.prefetch_related('reports').get(id=booking.id)

            context = {
                'name': booking.name,
                'medicine_status': new_status,
                'preferred_date': booking.preferred_date,
                'booking_id': booking.id,
                'total_price': booking.total_price,
                'booking': booking_with_reports,
                'now': timezone.now(),
            }

            subject = f"Your Medicine Booking Status: {new_status}"
            from_email = 'Dineshkumar630186@gmail.com'
            to_email = booking.email
            text_content = f"Dear {booking.name}, your medicine status is now: {new_status}."
            html_content = render_to_string('medicine/status_update_email.html', context)

            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            try:
                email.send()
            except Exception as e:
                messages.warning(request, f"Status updated but email failed: {e}")

        messages.success(request, f"medicine status updated to '{new_status}'.")

    return redirect(request.META.get('HTTP_REFERER', 'clinic_bookings'))


@user_passes_test(is_clinic_admin)
@login_required
def upload_report(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        files = request.FILES.getlist('report_files')
        for f in files:
            ReportFile.objects.create(booking=booking, file=f)
        messages.success(request, "Report(s) uploaded successfully.")
    return redirect('clinic_bookings')


@user_passes_test(is_clinic_admin)
@login_required
def edit_report(request, report_id):
    report = get_object_or_404(ReportFile, id=report_id)
    if request.method == 'POST':
        new_file = request.FILES.get('new_file')
        if new_file:
            report.file.delete(save=False)
            report.file = new_file
            report.save()
            messages.success(request, "Report updated successfully.")
    return redirect('clinic_bookings')

@user_passes_test(is_clinic_admin)
@login_required
def delete_report(request, report_id):
    report = get_object_or_404(ReportFile, id=report_id)
    report.delete()
    messages.success(request, "Report deleted successfully.")
    return redirect('clinic_bookings')


@login_required
def my_bookings_view(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    medicine_names = set(Product.objects.values_list('name', flat=True))
    diagnostic_names = set(DiagnosticTest.objects.values_list('name', flat=True))

    bookings_qs = Booking.objects.filter(user=request.user).order_by('-preferred_date')
    paginator = Paginator(bookings_qs, 4)
    page_number = request.GET.get('page')
    bookings_page = paginator.get_page(page_number)

    for booking in bookings_page:
        lab_items = []
        medicine_items = []
        for item in booking.cart_data:
            name = item.get("name", "").strip().lower()
            if name in (n.lower() for n in diagnostic_names):
                item["type"] = "lab"
                lab_items.append(item)
            elif name in (n.lower() for n in medicine_names):
                item["type"] = "medicine"
                medicine_items.append(item)

        booking.lab_tests = lab_items
        booking.medicines = medicine_items
        booking.lab_total_price = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in lab_items)
        booking.medicine_total_price = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in medicine_items)
        booking.lab_status = booking.lab_status if lab_items else None
        booking.medicine_status = booking.medicine_status if medicine_items else None

    return render(request, 'diagnosis/my_bookings.html', {
        'doctor': doctor,
        'patient': patient,
        'bookings': bookings_page,
        'blood_bank': blood_bank,
    })

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status in ['Booked', 'Phlebo Assigned']:
        booking.status = 'Cancelled'
        booking.save()
        messages.success(request, "Your booking has been cancelled successfully.")
    else:
        messages.error(request, "This booking cannot be cancelled at this stage.")
    return redirect('my_bookings')

@login_required
def add_medicine_category(request):
    clinic = Clinic.objects.filter(admin=request.user).first()
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = MedicineCategoryForm(request.POST, request.FILES)  
        if form.is_valid():
            category = form.save(commit=False)
            category.clinic = clinic  
            category.save()
            return redirect('add_medicine_category')
    else:
        form = MedicineCategoryForm() 

    all_categories = MedicineCategory.objects.all()
    return render(request, 'medicine/medicine_category.html', {
        'form': form,
        'categories': all_categories,
        'clinic': clinic,
        'blood_bank': blood_bank,
    })

@login_required
def update_medicine_category(request, pk):
    category = get_object_or_404(MedicineCategory, pk=pk)
    if request.method == "POST":
        form = MedicineCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
        else:
            messages.error(request, 'There was an error updating the category.')
    return redirect('add_medicine_category')

def delete_medicine_category(request,pk):
    category = get_object_or_404(MedicineCategory,pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request,'Category Deleted Successfully.')
    return redirect("add_mediciene_category")

def manage_medicine(request):
    doctor =None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None
    clinic = Clinic.objects.filter(admin=request.user).first()
    blood_bank = BloodBank.objects.filter(user=request.user).first()
    form = ProductForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('manage_medicine')
    categories = MedicineCategory.objects.all()
    grouped_products = defaultdict(list)
    for product in Product.objects.select_related('category'):
        grouped_products[product.category.name].append(product)

    return render(request, 'medicine/manage_medicine.html', {
        'form': form,
        'categories': categories,
        'grouped_products': dict(grouped_products),
        'blood_bank': blood_bank,
        'clinic': clinic,
        'doctor': doctor,
        'patient': patient,
    })

@require_POST
def edit_medicine(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.name = request.POST.get('name')
    product.description = request.POST.get('description')
    product.price = request.POST.get('price')
    product.discount_price = request.POST.get('discount_price')
    stock_quantity = request.POST.get('stock_quantity')
    if stock_quantity != "" and stock_quantity is not None:
        product.stock_quantity = int(stock_quantity)

    if 'image' in request.FILES:
        product.image = request.FILES['image']
    product.save()
    return redirect('manage_medicine')

@require_POST
def delete_medicine(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('manage_medicine')

def medicine_list(request):
    doctor = None
    patient = None
    blood_bank = None
    clinics = None
    if request.user.is_authenticated:
        blood_bank = BloodBank.objects.filter(user=request.user).first()
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass
    if request.user.is_authenticated and request.user.is_clinic:
        try:
           clinics = Clinic.objects.filter(doctor__user=request.user)
        except Clinic.DoesNotExist:
            pass
    categories = MedicineCategory.objects.all()
    return render(request, 'medicine/medicine_list.html', {
        'categories': categories,
        'doctor': doctor,
        'patient': patient,
        'blood_bank': blood_bank,
        'clinics': clinics,
    })

def category_products(request, slug):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None
    category = get_object_or_404(MedicineCategory, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'medicine/category_product.html', {
        'category': category,
        'products': products,
        'doctor': doctor,
        'patient': patient,
    })

def get_filtered_bookings(request, tab, filter_type):
    clinic = Clinic.objects.filter(admin=request.user).first()
    if not clinic:
        return []
    medicine_names = set(Product.objects.values_list('name', flat=True))
    diagnostic_names = set(DiagnosticTest.objects.values_list('name', flat=True))
    if tab == 'medicines':
        qs = Booking.objects.filter(clinic=clinic)
        if filter_type == 'past':
            qs = qs.filter(medicine_status__in=['Delivered', 'Cancelled'])
        else:
            qs = qs.exclude(medicine_status__in=['Delivered', 'Cancelled'])
        qs = qs.order_by('created_at')
        valid_orders = []
        for order in qs:
            med_items = []
            for item in order.cart_data:
                name = item.get("name", "").strip().lower()
                if name in (n.lower() for n in medicine_names):
                    item["type"] = "medicine"
                    med_items.append(item)
            if med_items:
                order.filtered_cart_data = med_items
                order.filtered_total_price = sum(
                    float(i.get("price", 0)) * int(i.get("quantity", 1))
                    for i in med_items
                )
                valid_orders.append(order)
        return valid_orders
    else:
        qs = Booking.objects.filter(clinic=clinic)
        if filter_type == 'past':
            qs = qs.filter(lab_status__in=['Completed', 'Cancelled'])
        else:
            qs = qs.exclude(lab_status__in=['Completed', 'Cancelled'])
        qs = qs.order_by('created_at')
        valid_bookings = []
        for booking in qs:
            lab_items = []
            for item in booking.cart_data:
                name = item.get("name", "").strip().lower()
                if name in (n.lower() for n in diagnostic_names):
                    item["type"] = "lab"
                    lab_items.append(item)
            if lab_items:
                booking.filtered_cart_data = lab_items
                booking.filtered_total_price = sum(
                    float(i.get("price", 0)) * int(i.get("quantity", 1))
                    for i in lab_items
                )
                valid_bookings.append(booking)
        return valid_bookings
    
    
def export_bookings_csv(request, tab, filter_type):
    bookings = get_filtered_bookings(request, tab, filter_type)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{tab}_{filter_type}_bookings.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Patient", "Items", "Date", "Status", "Address", "Total"])
    for booking in bookings:
        items = ", ".join([f"{item['name']} x{item['quantity']}" for item in booking.filtered_cart_data])
        status = booking.lab_status if tab == "tests" else booking.medicine_status
        writer.writerow([
            booking.id, booking.name, items, booking.preferred_date,
            status, booking.address, booking.filtered_total_price
        ])
    return response

def export_bookings_excel(request, tab, filter_type):
    bookings = get_filtered_bookings(request, tab, filter_type)
    wb = Workbook()
    ws = wb.active
    ws.title = "Bookings"
    ws.append(["ID", "Patient", "Items", "Date", "Status", "Address", "Total"])

    for booking in bookings:
        items = ", ".join([f"{item['name']} x{item['quantity']}" for item in booking.filtered_cart_data])
        status = booking.lab_status if tab == "tests" else booking.medicine_status
        ws.append([
            booking.id, booking.name, items, str(booking.preferred_date),
            status, booking.address, booking.filtered_total_price
        ])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{tab}_{filter_type}_bookings.xlsx"'
    wb.save(response)
    return response
