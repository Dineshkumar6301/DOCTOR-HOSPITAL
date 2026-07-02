from .models import Clinic, Doctor, Patient
def clinic_context(request):
    clinic = None
    doctor = None
    patient = None

    if request.user.is_authenticated:
        try:
            doctor = request.user.doctor_profile
            clinic = Clinic.objects.filter(doctor=doctor).first()
        except:
            doctor = None
        try:
            patient = request.user.patient
        except:
            patient = None

    return {
        'clinic': clinic,
        'doctor': doctor,
        'patient': patient,
    }
