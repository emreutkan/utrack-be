from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import date, time, timedelta
from .models import Supplement, UserSupplement, UserSupplementLog

User = get_user_model()


class SupplementTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test supplements
        self.supplement1 = Supplement.objects.create(
            name='Creatine Monohydrate',
            description='Best for strength and power',
            dosage_unit='g',
            default_dosage=5.0,
            bioavailability_score='High',
            is_active=True
        )
        self.supplement2 = Supplement.objects.create(
            name='Vitamin D3',
            description='Essential for bone health',
            dosage_unit='IU',
            default_dosage=2000,
            bioavailability_score='High',
            is_active=True
        )
        self.supplement3 = Supplement.objects.create(
            name='Inactive Supplement',
            description='This is inactive',
            is_active=False
        )

    def test_list_supplements(self):
        """Test listing all active supplements"""
        response = self.client.get('/api/supplements/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data or response.data)
        # Should only return active supplements
        if 'results' in response.data:
            supplement_names = [s['name'] for s in response.data['results']]
            self.assertIn('Creatine Monohydrate', supplement_names)
            self.assertIn('Vitamin D3', supplement_names)
            self.assertNotIn('Inactive Supplement', supplement_names)

    def test_search_supplements(self):
        """Test searching supplements by name"""
        response = self.client.get('/api/supplements/list/?search=creatine')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            supplement_names = [s['name'] for s in response.data['results']]
            self.assertIn('Creatine Monohydrate', supplement_names)

    def test_create_user_supplement(self):
        """Test creating a user supplement"""
        data = {
            'supplement_id': self.supplement1.id,
            'dosage': 5.0,
            'frequency': 'daily',
            'time_of_day': 'Morning'
        }
        response = self.client.post('/api/supplements/user/add/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserSupplement.objects.count(), 1)
        user_supplement = UserSupplement.objects.first()
        self.assertEqual(user_supplement.user, self.user)
        self.assertEqual(user_supplement.supplement, self.supplement1)
        self.assertEqual(user_supplement.dosage, 5.0)

    def test_list_user_supplements(self):
        """Test listing user's supplements"""
        UserSupplement.objects.create(
            user=self.user,
            supplement=self.supplement1,
            dosage=5.0,
            frequency='daily'
        )
        response = self.client.get('/api/supplements/user/list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)

    def test_validation_dosage_positive(self):
        """Test that dosage must be positive"""
        data = {
            'supplement_id': self.supplement1.id,
            'dosage': -5.0,
            'frequency': 'daily'
        }
        response = self.client.post('/api/supplements/user/add/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_dosage_max(self):
        """Test that dosage has maximum limit"""
        data = {
            'supplement_id': self.supplement1.id,
            'dosage': 50000.0,  # Exceeds max
            'frequency': 'daily'
        }
        response = self.client.post('/api/supplements/user/add/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_frequency(self):
        """Test frequency validation"""
        data = {
            'supplement_id': self.supplement1.id,
            'dosage': 5.0,
            'frequency': 'invalid'
        }
        response = self.client.post('/api/supplements/user/add/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserSupplementLogTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.supplement = Supplement.objects.create(
            name='Test Supplement',
            dosage_unit='g',
            default_dosage=5.0
        )
        self.user_supplement = UserSupplement.objects.create(
            user=self.user,
            supplement=self.supplement,
            dosage=5.0,
            frequency='daily'
        )

    def test_create_supplement_log(self):
        """Test creating a supplement log"""
        data = {
            'user_supplement_id': self.user_supplement.id,
            'date': timezone.now().date().isoformat(),
            'time': timezone.now().time().isoformat(),
            'dosage': 5.0
        }
        response = self.client.post('/api/supplements/user/log/add/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserSupplementLog.objects.count(), 1)

    def test_daily_log_limit(self):
        """Test that user can only log once per day"""
        today = timezone.now().date()
        UserSupplementLog.objects.create(
            user=self.user,
            user_supplement=self.user_supplement,
            date=today,
            time=timezone.now().time(),
            dosage=5.0
        )
        
        data = {
            'user_supplement_id': self.user_supplement.id,
            'date': today.isoformat(),
            'time': timezone.now().time().isoformat(),
            'dosage': 5.0
        }
        response = self.client.post('/api/supplements/user/log/add/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already logged', response.data.get('error', '').lower() or '')

    def test_list_supplement_logs(self):
        """Test listing supplement logs"""
        log1 = UserSupplementLog.objects.create(
            user=self.user,
            user_supplement=self.user_supplement,
            date=timezone.now().date(),
            time=time(10, 0),
            dosage=5.0
        )
        log2 = UserSupplementLog.objects.create(
            user=self.user,
            user_supplement=self.user_supplement,
            date=timezone.now().date() - timedelta(days=1),
            time=time(10, 0),
            dosage=5.0
        )
        
        response = self.client.get(
            f'/api/supplements/user/log/list/?user_supplement_id={self.user_supplement.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_today_logs(self):
        """Test getting today's supplement logs"""
        today = timezone.now().date()
        UserSupplementLog.objects.create(
            user=self.user,
            user_supplement=self.user_supplement,
            date=today,
            time=time(10, 0),
            dosage=5.0
        )
        UserSupplementLog.objects.create(
            user=self.user,
            user_supplement=self.user_supplement,
            date=today - timedelta(days=1),
            time=time(10, 0),
            dosage=5.0
        )
        
        response = self.client.get('/api/supplements/user/log/today/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['logs']), 1)

    def test_delete_supplement_log(self):
        """Test deleting a supplement log"""
        log = UserSupplementLog.objects.create(
            user=self.user,
            user_supplement=self.user_supplement,
            date=timezone.now().date(),
            time=timezone.now().time(),
            dosage=5.0
        )
        
        response = self.client.delete(f'/api/supplements/user/log/delete/{log.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserSupplementLog.objects.count(), 0)

    def test_validation_future_date(self):
        """Test that date cannot be in the future"""
        future_date = (timezone.now().date() + timezone.timedelta(days=1)).isoformat()
        data = {
            'user_supplement_id': self.user_supplement.id,
            'date': future_date,
            'time': timezone.now().time().isoformat(),
            'dosage': 5.0
        }
        response = self.client.post('/api/supplements/user/log/add/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_dosage_positive(self):
        """Test that log dosage must be positive"""
        data = {
            'user_supplement_id': self.user_supplement.id,
            'date': timezone.now().date().isoformat(),
            'time': timezone.now().time().isoformat(),
            'dosage': -5.0
        }
        response = self.client.post('/api/supplements/user/log/add/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
