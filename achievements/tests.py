from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from exercise.models import Exercise
from workout.models import Workout
from .models import Achievement, UserAchievement, PersonalRecord

User = get_user_model()


class AchievementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.achievement = Achievement.objects.create(
            name='First Workout',
            category='workout_count',
            requirement_value=1,
            is_active=True
        )
        self.exercise = Exercise.objects.create(
            name='Bench Press',
            primary_muscle='chest',
            equipment_type='barbell'
        )

    def test_list_achievements(self):
        """Test listing achievements"""
        response = self.client.get('/api/achievements/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_achievements(self):
        """Test getting user's earned achievements"""
        UserAchievement.objects.create(
            user=self.user,
            achievement=self.achievement,
            earned_value=1
        )
        response = self.client.get('/api/achievements/earned/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_personal_records(self):
        """Test getting personal records"""
        PersonalRecord.objects.create(
            user=self.user,
            exercise=self.exercise,
            best_weight=100.0,
            best_one_rep_max=120.0
        )
        response = self.client.get('/api/achievements/prs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
