from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from core.models import TimestampedModel

## Basic info about the models

## Model.model = default django model class
## TimestampedModel = Model.model + created_at and updated_at fields

class CustomUserManager(BaseUserManager):
    """
    Custom user manager that overrides the create_user and create_superuser methods to use the email field for authentication.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email) ## This is the normalize_email() method from Django's BaseUserManager. It normalizes the email address by converting it to lowercase and removing whitespace.
        user = self.model(email=email, **extra_fields)
        user.set_password(password) ## That set_password() method is from Django's AbstractUser. It automatically hashes the password using Django's default password hasher (PBKDF2 with SHA256 by default).
        user.save(using=self._db) ## This is the save() method from Django's Model. It saves the user to the database.
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True) ## This is the is_staff field from Django's AbstractUser. It is a boolean field that indicates whether the user is a staff member.
        extra_fields.setdefault('is_superuser', True) ## This is the is_superuser field from Django's AbstractUser. It is a boolean field that indicates whether the user is a superuser.
        return self.create_user(email, password, **extra_fields) 

## AbstractUser = User model template that includes username, password, first_name, last_name, email, is_active, is_staff, is_superuser, last_login, date_joined fields
class CustomUser(AbstractUser, TimestampedModel):
    """
    Custom user with email login and basic verification state.
    Inherits Django auth fields plus timestamp fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True) ## abstract user already has an email field, but we need to make it unique so we override it
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'  ## this tells Django that the email field is used for authentication instead of the username field
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager() ## This is the custom user manager that we created above. It is used to create and manage users.

class UserProfile(TimestampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

class SecurityStatus(TimestampedModel):
    """
    Security status for user including login attempt tracking and lockout functionality.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

class Preferences(TimestampedModel):
    """
    User preferences including auto warmup settings and rest time. Rest time is the time in seconds between sets.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    auto_warmup_set = models.BooleanField(default=False)
    rest_time = models.PositiveIntegerField(default=90)
    units = models.CharField(max_length=10, choices=[('metric', 'Metric'), ('imperial', 'Imperial')], default='metric')