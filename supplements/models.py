from django.db import models
from core.models import TimestampedModel
from user.models import CustomUser

class Supplement(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    DOSAGE_UNIT_CHOICES = [
        ('mg', 'mg'),
        ('g', 'g'),
        ('mcg', 'mcg'),
        ('IU', 'IU'),
        ('ml', 'ml'),
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('scoop', 'Scoop'),
        ('other', 'Other'),
    ]
    dosage_unit = models.CharField(max_length=50, choices=DOSAGE_UNIT_CHOICES, default='mg')
    default_dosage = models.FloatField(blank=True, null=True)
    
    # New field for bioavailability score/description
    bioavailability_score = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. High, Low, Poor")
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class UserSupplement(TimestampedModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_supplements')
    supplement = models.ForeignKey(Supplement, on_delete=models.CASCADE)
    
    dosage = models.FloatField(help_text="Amount taken per serving") 
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom'),
    ]
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES, default='daily')
    
    time_of_day = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Morning, Before Bed")
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.supplement.name}"

class UserSupplementLog(TimestampedModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_supplement_logs')
    user_supplement = models.ForeignKey(UserSupplement, on_delete=models.CASCADE, related_name='user_supplement_logs')

    date = models.DateField()
    time = models.TimeField()
    dosage = models.FloatField(help_text="Amount taken")
    
    def __str__(self):
        return f"{self.user.email} - {self.user_supplement.supplement.name} - {self.date} - {self.time}"
