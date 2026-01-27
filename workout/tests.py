from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from exercise.models import Exercise
from .models import Workout, WorkoutExercise, ExerciseSet

User = get_user_model()


class WorkoutTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.exercise = Exercise.objects.create(
            name='Bench Press',
            primary_muscle='chest',
            equipment_type='barbell',
            category='compound'
        )

    def test_create_workout(self):
        """Test creating a workout"""
        data = {'title': 'Test Workout'}
        response = self.client.post('/api/workout/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workout.objects.count(), 1)

    def test_get_workout(self):
        """Test getting a workout"""
        workout = Workout.objects.create(
            user=self.user,
            title='Test Workout',
            datetime=timezone.now()
        )
        response = self.client.get(f'/api/workout/list/{workout.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_exercise_to_workout(self):
        """Test adding exercise to workout"""
        workout = Workout.objects.create(
            user=self.user,
            title='Test Workout',
            datetime=timezone.now()
        )
        data = {'exercise_id': self.exercise.id}
        response = self.client.post(f'/api/workout/{workout.id}/add_exercise/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WorkoutExercise.objects.count(), 1)

    def test_complete_workout(self):
        """Test completing a workout"""
        workout = Workout.objects.create(
            user=self.user,
            title='Test Workout',
            datetime=timezone.now()
        )
        data = {'duration': 60}
        response = self.client.post(f'/api/workout/{workout.id}/complete/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        workout.refresh_from_db()
        self.assertTrue(workout.is_done)
