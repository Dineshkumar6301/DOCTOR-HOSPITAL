
import django_filters
from .models import BloodRequest

class BloodRequestFilter(django_filters.FilterSet):
    class Meta:
        model = BloodRequest
        fields = {
            'blood_group': ['exact'],
            'urgency_level': ['exact'],
            'status': ['exact'],
        }
