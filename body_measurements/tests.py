from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import BodyMeasurement

User = get_user_model()


class BodyMeasurementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            gender='male'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_measurement(self):
        """Test creating a body measurement"""
        data = {
            'height': 180.0,
            'weight': 75.0,
            'waist': 80.0,
            'neck': 40.0
        }
        response = self.client.post('/api/measurements/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BodyMeasurement.objects.count(), 1)

    def test_create_measurement_female_requires_hips(self):
        """Test that female measurements require hips"""
        self.user.gender = 'female'
        self.user.save()
        data = {
            'height': 165.0,
            'weight': 60.0,
            'waist': 70.0,
            'neck': 35.0
            # Missing hips
        }
        response = self.client.post('/api/measurements/create/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_measurements(self):
        """Test listing body measurements"""
        BodyMeasurement.objects.create(
            user=self.user,
            height=180.0,
            weight=75.0,
            waist=80.0,
            neck=40.0,
            gender='male'
        )
        response = self.client.get('/api/measurements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validation_height_range(self):
        """Test height validation range"""
        data = {
            'height': 10.0,  # Too small
            'weight': 75.0,
            'waist': 80.0,
            'neck': 40.0
        }
        response = self.client.post('/api/measurements/create/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calculate_body_fat_men(self):
        """Test body fat calculation for men"""
        data = {
            'height': 180.0,
            'weight': 75.0,
            'waist': 80.0,
            'neck': 40.0,
            'gender': 'male'
        }
        response = self.client.post('/api/measurements/calculate-body-fat/men/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('body_fat_percentage', response.data)

    def test_calculate_body_fat_women(self):
        """Test body fat calculation for women"""
        data = {
            'height': 165.0,
            'weight': 60.0,
            'waist': 70.0,
            'neck': 35.0,
            'hips': 95.0,
            'gender': 'female'
        }
        response = self.client.post('/api/measurements/calculate-body-fat/women/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('body_fat_percentage', response.data)
