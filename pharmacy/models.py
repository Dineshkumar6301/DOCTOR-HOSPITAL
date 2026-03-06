from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator,RegexValidator
from datetime import date, datetime
from PIL import Image

from cloudinary.models import CloudinaryField

GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    profile_image = CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    is_clinic = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email or f"User {self.id}"
    
    def save(self, *args, **kwargs):
        if self.is_doctor:
            self.is_staff = True  
        super().save(*args, **kwargs)

class Doctor(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id = models.CharField(max_length=10, unique=True, editable=False)
    qualification= models.CharField(max_length=255, default='')
    clinics = models.ManyToManyField('Clinic', related_name='assigned_doctors', blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=50, null=False, blank=False)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    biography = models.TextField(blank=True)
    specialities_description = models.TextField(blank=True)
    Address1 = models.CharField(max_length=255, null=True, blank=True)
    Address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, null=True ,blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    profile_image = CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    facebook_url = models.URLField(blank=True,null =True)
    twitter_url = models.URLField(blank=True,null=True)
    google_plus_url = models.URLField(blank=True,null=True)
    instagram_url = models.URLField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank = True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    review_count = models.IntegerField(default=0)
    location = models.CharField(max_length=255,blank = True,null =True)

    @property
    def availability_status(self):
        return "24/7 Available" if self.is_available else "Not Available"

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = 'DOC-' + get_random_string(6, '0123456789')
        super().save(*args, **kwargs)


    def get_full_name(self):
        if self.user:
            full_name = self.user.get_full_name()
            if full_name.strip():
                return full_name
            return self.user.email or self.user.username
        return f"Doctor {self.doctor_id}"

    def __str__(self):
        return self.get_full_name()
    @property
    def star_range(self):
        return range(round(self.average_rating or 0))


class Clinic(models.Model): 
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_clinics'
    )
    admin = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    null=True, 
    blank=True,
    limit_choices_to={'is_superuser': True},
    related_name='admin_clinics'
)
    doctor = models.ForeignKey(
    Doctor,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='owned_clinics'
)

    name = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fax = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    image = CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    gallery_images = models.JSONField(default=list, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    specifications = models.JSONField(default=list, blank=True,null =True)
    services = models.JSONField(default=list, blank=True,null =True)
    awards = models.JSONField(default=list, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)
    map_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    map_lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    map_marker =CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    google_plus = models.URLField(blank=True, null=True)
    
    class Meta:
        unique_together = ('name', 'city', 'admin')

    def __str__(self):
        return self.name or f"Clinic #{self.pk}"
    
class Branch(models.Model):
    clinic = models.ForeignKey(Clinic, related_name='branches', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    map_link = models.URLField(blank=True, null=True)

class GalleryImage(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='images')  
    image =CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.clinic.name}"


class Education(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    degree = models.CharField(max_length=100, blank=True, null=True)
    institute = models.CharField(max_length=100,blank=True,null=True)
    passing_year = models.IntegerField(blank=True,null=True)

class Experience(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    hospital_name = models.CharField(max_length=100,blank=True,null=True)
    designation = models.CharField(max_length=100,blank=True,null=True)
    from_date = models.DateField(max_length=100,blank=True,null=True)
    to_date = models.DateField(max_length=100,blank=True,null=True)

class Service(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        if self.doctor and self.doctor.user:
            return f"{self.name} - {self.doctor.user.get_full_name() or self.doctor.user.username}"
        return self.name

class DoctorSpeciality(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='speciality_entries')
    name = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)  
    def __str__(self):
        return f"{self.name} ({self.years_of_experience or 0} yrs)"
    
class Award(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='awards')
    name = models.CharField(max_length=200)
    year = models.PositiveIntegerField()

class Speciality(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='specialities', null=True, blank=True) 
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Patient(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'), ('Married', 'Married'),
        ('Divorced', 'Divorced'), ('Widowed', 'Widowed'),
    ]
    STATUS_CHOICES = [
        ('Online', 'Online'), ('Offline', 'Offline'),
        ('Away', 'Away'), ('Busy', 'Busy')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile', null=True, blank=True)
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='patients', null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    city = models.CharField(max_length=100,null=True,blank =True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(max_length=30,blank=True,null=True)
    last_name = models.CharField(max_length=30,blank =True,null=True)
    patient_id = models.CharField(max_length=10, editable=False, default='Temp')
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    doctor_note = models.TextField(blank=True)
    profile_image = CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Offline')
    favourites = models.ManyToManyField('Doctor', through='FavouriteDoctor', related_name='favoured_by')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=255, blank=True, null=True)
 
    def get_full_name(self):
        """Return the patient's full name"""
        first = self.first_name or ""
        last = self.last_name or ""
        full_name = f"{first} {last}".strip()
        return full_name if full_name else f"Patient #{self.pk}"
    

    def full_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip()
    
        return self.get_full_name()
   
    def calculate_age(self):
        if self.date_of_birth:
           
            if isinstance(self.date_of_birth, str):
                try:
                    self.date_of_birth = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
                except ValueError:
                    return None  

            today = date.today()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        return None

    def save(self, *args, **kwargs):
        
        if not self.patient_id or self.patient_id == 'Temp':
            self.patient_id = 'PAT-' + get_random_string(6, '0123456789')
    
        if self.date_of_birth:
            self.age = self.calculate_age()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else f"Patient {self.patient_id}"


class PatientSocialLinks(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='social_links')
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Social Links for {self.patient.get_full_name()}"

class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=100)  
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def get_days_list(self):
        return [day.strip() for day in self.day_of_week.split(',') if day.strip()]

class ScheduleTiming(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    title = models.CharField(max_length=255)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE) 
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date} ({self.start_datetime.time()} to {self.end_datetime.time()})"

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return self.title
 
class Appointment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    APPOINTMENT_TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
    ]

    APPOINTMENT_MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    VIDEO_PLATFORM_CHOICES = [
        ('jitsi', 'Jitsi'),
        ('zoom', 'Zoom'),
    ]

    patient = models.ForeignKey(
        "Patient",
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    doctor = models.ForeignKey(
        "Doctor",
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    schedule = models.ForeignKey(
        "ScheduleTiming",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    time_slot = models.ForeignKey(
        "TimeSlot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


    appointment_datetime = models.DateTimeField()
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)

   
    is_new_patient = models.BooleanField(null=True, blank=True)
    patient_name = models.CharField(max_length=255, blank=True, null=True)
    patient_email = models.EmailField(blank=True, null=True)
    patient_mobile_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(
        max_length=6,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        null=True,
        blank=True
    )
    age = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )

    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    purpose = models.TextField(blank=True, null=True)
    appointment_notes = models.TextField(blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)

    
    appointment_type = models.CharField(
        max_length=50,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='consultation'
    )
    appointment_mode = models.CharField(
        max_length=10,
        choices=APPOINTMENT_MODE_CHOICES,
        default='offline'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    blockchain_tx_hash = models.CharField(max_length=255, blank=True, null=True)
    blockchain_status = models.CharField(max_length=20, default="pending")
    user_wallet_address = models.CharField(max_length=42, null=True, blank=True)


    video_platform = models.CharField(
        max_length=20,
        choices=VIDEO_PLATFORM_CHOICES,
        default="jitsi"
    )
    video_link = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return (
            f"{self.patient_name or self.patient} "
            f"with Dr. {self.doctor} on "
            f"{self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}"
        )

    def generate_jitsi_link(self):
        return f"https://meet.jit.si/ClinicApp_{self.id}"

    def get_video_link(self):
        if self.appointment_mode == "online":
            if self.video_platform == "jitsi":
                return self.generate_jitsi_link()
            elif self.video_platform == "zoom" and self.video_link:
                return self.video_link
        return None

    def save(self, *args, **kwargs):
        if self.schedule and self.schedule.is_available:
            self.schedule.is_available = False
            self.schedule.save(update_fields=["is_available"])
        super().save(*args, **kwargs)

class ScheduleEvent(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return f"{self.title} - {self.start} to {self.end}"

class Schedule(models.Model):
    doctor = models.ForeignKey('pharmacy.Doctor', on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date_time} ({'Available' if self.is_available else 'Booked'})"

class FavouriteDoctor(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class DoctorListing(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    treatment = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.treatment} by Dr. {self.doctor.get_full_name()}"  


class Review(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_reviews')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_reviews', null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    message = models.TextField(max_length=1000, blank=True)
    comment = models.TextField(blank=True)
    terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    reply = models.TextField(blank=True, null=True)
    reply_created_at = models.DateTimeField(blank=True, null=True)
    is_new = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            doctor = self.doctor
            all_reviews = Review.objects.filter(doctor=doctor)
            doctor.total_reviews = all_reviews.count()
            doctor.average_rating = all_reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
            doctor.save()

    def __str__(self):
        return f"{self.title} by {self.name}"


class SubmitReview(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    message = models.TextField(max_length=1000)
    terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.name}"

    class Meta:
        ordering = ['-created_at']


class Conversation(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_conversations')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'doctor')

    def __str__(self):
        return f"Conversation between {self.patient.email} and {self.doctor.email}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True)
    sender_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        null=True,
        blank=True
    )
    sender_object_id = models.PositiveIntegerField(null=True, blank=True)
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')

    receiver_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='received_messages',
        null=True,
        blank=True
    )
    receiver_object_id = models.PositiveIntegerField(null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages',null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        sender_str = str(self.sender) if self.sender else "Unknown Sender"
        receiver_str = str(self.receiver) if self.receiver else "Unknown Receiver"
        return f"Message from {sender_str} to {receiver_str}"

    class Meta:
        ordering = ['-timestamp']



class Staff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='staff_members')
    role = models.CharField(max_length=50)



class ClinicListing(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    treatment = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)

class ClinicService(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)

class BloodBank(models.Model):
    name = models.CharField(max_length=200, verbose_name="Blood Bank Name")
    registration_number = models.CharField(max_length=50, unique=True, verbose_name="Registration/License Number")
    contact_person = models.CharField(max_length=100, verbose_name="Contact Person Name")
    designation = models.CharField(max_length=100, verbose_name="Designation")

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    primary_phone = models.CharField(validators=[phone_regex], max_length=17, verbose_name="Primary Phone")
    secondary_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name="Secondary Phone")
    emergency_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name="Emergency Phone")
    email = models.EmailField(verbose_name="Email Address")
    website = models.URLField(blank=True, verbose_name="Website URL")
    street_address = models.CharField(max_length=255, verbose_name="Street Address")
    city = models.CharField(max_length=100, verbose_name="City")
    state = models.CharField(max_length=100, verbose_name="State")
    pin_code = models.CharField(max_length=10, verbose_name="PIN/Zip Code")
    map_link = models.URLField(blank=True, verbose_name="Google Map Embed Link")
    operating_hours_weekday = models.CharField(max_length=50, default="9:00 AM - 5:00 PM", verbose_name="Weekday Hours")
    operating_hours_weekend = models.CharField(max_length=50, default="9:00 AM - 2:00 PM", verbose_name="Weekend Hours")
    is_24x7 = models.BooleanField(default=False, verbose_name="24x7 Service")
    emergency_service = models.BooleanField(default=False, verbose_name="Emergency Service Available")
    mobile_donation_camps = models.BooleanField(default=False, verbose_name="Mobile Donation Camps")
    home_collection = models.BooleanField(default=False, verbose_name="Home Collection Service")
    appointment_required = models.BooleanField(default=False, verbose_name="Appointment Required")
    
    SERVICES_CHOICES = [
        ('collection', 'Blood Collection'),
        ('testing', 'Blood Testing'),
        ('storage', 'Blood Storage'),
        ('distribution', 'Blood Distribution'),
        ('screening', 'Donor Screening'),
        ('components', 'Component Separation'),
    ]
    services = models.JSONField(default=list, verbose_name="Services Available")
    
    certifications = models.CharField(max_length=255, blank=True, null=True)
    affiliated_hospitals = models.CharField(max_length=255, blank=True, null=True)
    profile_image = CloudinaryField(
        'profile_image',
        folder='bloodbank_images/profile',
        blank=True,
        null=True
    )

    facility_images = CloudinaryField(
        'facility_images',
        folder='bloodbank_images/facility',
        blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    is_verified = models.BooleanField(default=False, verbose_name="Verified")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    special_instructions = models.TextField(blank=True, null=True, verbose_name="Special Instructions/Notes")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bloodbank_profile')
    
    class Meta:
        verbose_name = "Blood Bank"
        verbose_name_plural = "Blood Banks"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        return f"{self.street_address}, {self.city}, {self.state} - {self.pin_code}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_image:
            img = Image.open(self.profile_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_image.path)


class BloodInventory(models.Model):
    BLOOD_GROUPS = [
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
    ]
    
    COMPONENT_TYPES = [
        ('whole_blood', 'Whole Blood'),
        ('platelets', 'Platelets'),
        ('plasma', 'Plasma'),
        ('rbc', 'Red Blood Cells'),
        ('ffp', 'Fresh Frozen Plasma'),
        ('cryoprecipitate', 'Cryoprecipitate'),
    ]
    
    STOCK_STATUS = [
        ('available', 'Available'),
        ('low', 'Low Stock'),
        ('critical', 'Critical'),
        ('not_available', 'Not Available'),
    ]
    
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='inventory')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, verbose_name="Blood Group")
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES, verbose_name="Component Type")
    quantity = models.IntegerField(default=0, verbose_name="Quantity (Units)")
    collection_date = models.DateField(verbose_name="Collection Date")
    batch_number = models.CharField(max_length=50, verbose_name="Batch Number")
    testing_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('tested', 'Tested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending', verbose_name="Testing Status")
    stock_status = models.CharField(max_length=15, choices=STOCK_STATUS, default='available', verbose_name="Stock Status")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Blood Inventory"
        verbose_name_plural = "Blood Inventories"
        unique_together = ['blood_bank', 'blood_group', 'component_type', 'batch_number']
    
    def __str__(self):
        return f"{self.blood_bank.name} - {self.blood_group} {self.component_type} ({self.quantity} units)"
    
    def is_expired(self):
        return self.expiry_date < timezone.now().date()
    
    def days_to_expiry(self):
        return (self.expiry_date - timezone.now().date()).days


class BloodRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('fulfilled', 'Fulfilled'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    URGENCY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blood_requests',
        null=True,
        blank=True,
        verbose_name="Requested By"
    )
    
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='requests')
    hospital_name = models.CharField(max_length=200, verbose_name="Hospital Name")
    patient_name = models.CharField(max_length=100, verbose_name="Patient Name")
    blood_group = models.CharField(max_length=3, choices=BloodInventory.BLOOD_GROUPS, verbose_name="Blood Group")
    component_type = models.CharField(max_length=20, choices=BloodInventory.COMPONENT_TYPES, verbose_name="Component Type")
    quantity_needed = models.IntegerField(verbose_name="Quantity Needed (Units)")
    urgency_level = models.CharField(max_length=10, choices=URGENCY_LEVELS, verbose_name="Urgency Level")
    required_date = models.DateField(verbose_name="Required Date")
    medical_reason = models.CharField(max_length=255,verbose_name="Medical Reason")
    doctor_name = models.CharField(max_length=100, verbose_name="Doctor Name")
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='pending', verbose_name="Request Status")
    notes = models.TextField(blank=True,null=True, verbose_name="Additional Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Blood Request"
        verbose_name_plural = "Blood Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient_name} - {self.blood_group} {self.component_type} - {self.status}"


class DonorRecord(models.Model):
    DONOR_STATUS = [
        ('eligible', 'Eligible'),
        ('Uneligible','Uneligible'),
    ]
    
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='donors')
    donor_name = models.CharField(max_length=100, verbose_name="Donor Name")
    donor_phone = models.CharField(max_length=17, verbose_name="Donor Phone")
    donor_email = models.EmailField(blank=True, verbose_name="Donor Email")
    blood_group = models.CharField(max_length=3, choices=BloodInventory.BLOOD_GROUPS, verbose_name="Blood Group")
    age = models.IntegerField(verbose_name="Age")
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Weight (kg)")
    last_donation_date = models.DateField(blank=True, null=True, verbose_name="Last Donation Date")
    donation_count = models.IntegerField(default=0, verbose_name="Total Donations")
    donor_status = models.CharField(max_length=20, choices=DONOR_STATUS, default='eligible', verbose_name="Donor Status")
    medical_history = models.TextField(blank=True, verbose_name="Medical History")
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name="Emergency Contact")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    requested_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="donor_submissions",
    verbose_name="Submitted By"
)

    
    class Meta:
        verbose_name = "Donor Record"
        verbose_name_plural = "Donor Records"
        unique_together = []
    
    def __str__(self):
        return f"{self.donor_name} - {self.blood_group} - {self.donor_status}"
    
    def can_donate(self):
        if self.donor_status != 'eligible':
            return False
        if self.last_donation_date:
            days_since_last = (timezone.now().date() - self.last_donation_date).days
            return days_since_last >= 56
        return True


class BloodDispatch(models.Model):
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=3, choices=BloodInventory.BLOOD_GROUPS)
    quantity = models.PositiveIntegerField()
    recipient_name = models.CharField(max_length=100, blank=True)
    purpose = models.TextField(blank=True)
    dispatched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blood_group} - {self.quantity} units to {self.recipient_name or 'Unknown'}"


class TestCategory(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('test', 'Test'),
        ('package', 'Package'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPE_CHOICES, default='test')

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    

from multiselectfield import MultiSelectField

SAMPLE_TYPE_CHOICES = [
   ('Blood'," Blood"),
   ('Urine', " Urine"),
   ('Saliva', " Saliva"),
   ('Stool', " Stool (Feces)"),
   ('Sputum', " Sputum (Mucus from lungs)"),
   ('Tissue', " Tissue / Biopsy"),
   ('Sweat', " Sweat"),
   ('Cerebrospinal Fluid', " Cerebrospinal Fluid (CSF)"),
   ('Amniotic Fluid', " Amniotic Fluid"),
   ('Semen', " Semen"),
   ('Nasal / Throat Swab', " Nasal / Throat Swab"),
   ('Hair / Nail', " Hair / Nail"),
   ('Not Specified', " Not Specified")
]
FASTING_CHOICES = (
    ('yes', 'Yes'),
    ('no', 'No'),
    ('optional', 'Not Specified'),
)


class DiagnosticTest(models.Model):
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    test_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    parameters_included = models.TextField(blank=True, null=True)
    sample_type = MultiSelectField(choices=SAMPLE_TYPE_CHOICES)
    fasting_required = models.CharField(max_length=10, choices=FASTING_CHOICES, default='optional')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = models.PositiveIntegerField(default=24)
    is_active = models.BooleanField(default=True)
    is_package = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


MEDICINE_STATUS_CHOICES = [
    ('Placed', 'Placed'),
    ('Packed', 'Packed'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled')
]
STATUS_CHOICES = [
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
class Booking(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Booked", "Booked"),
        ("Cancelled", "Cancelled"),
        ("Completed", "Completed"),
        ("Refunded", "Refunded"),
    ]

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True)
    user_wallet_address = models.CharField(
        max_length=42,
        blank=True,
        null=True
    )

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    tx_hash = models.CharField(
        max_length=66,
        blank=True,
        null=True,
        unique=True
    )

    crypto_amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        blank=True,
        null=True
    )

    cart_data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    lab_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Booked"
    )

    medicine_status = models.CharField(
        max_length=50,
        choices=MEDICINE_STATUS_CHOICES,
        default="Placed"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return f"Booking by {self.name} on {self.preferred_date}"

class Refund(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    tx_hash = models.CharField(max_length=66)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)

class ReportFile(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reports')
    file = models.FileField(upload_to='test_reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_cart', condition=~models.Q(user=None)),
        ]

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    
from django.utils.text import slugify
class MedicineCategory(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='medicine_categories', null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = CloudinaryField(
        'profile_image',
        folder='Hospital_images',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name 
     


class Product(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE,null=True, blank=True)
    category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = CloudinaryField(
        'products',
        folder='Hospital_images',
        blank=True,
        null=True
    )
    stock_quantity = models.PositiveIntegerField(default=0,null=True,blank=True)

    in_stock = models.BooleanField(default=True)
    created_at =models.DateTimeField(auto_now_add =True)
    updated_at  = models.DateTimeField(auto_now = True)


    def save(self, *args, **kwargs):
        self.stock_quantity = self.stock_quantity or 0 
        self.in_stock = self.stock_quantity > 0
        super().save(*args, **kwargs)

