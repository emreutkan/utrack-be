from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class AuthTests(APITestCase):
    def setUp(self):
        # Create a test user for login tests
        self.user_data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        self.user = User.objects.create_user(**self.user_data)
        
        # URLs
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

    def test_register_user(self):
        """
        Ensure we can register a new user.
        """
        data = {
            'email': 'newuser@example.com',
            'password': 'newpassword456'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(User.objects.count(), 2) # 1 setup user + 1 new user
        self.assertEqual(User.objects.get(email='newuser@example.com').email, 'newuser@example.com')

    def test_register_user_existing_email(self):
        """
        Ensure we cannot register with an existing email.
        """
        data = {
            'email': 'test@example.com', # Already exists from setUp
            'password': 'somepassword'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user(self):
        """
        Ensure we can login with valid credentials.
        """
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_password(self):
        """
        Ensure login fails with wrong password.
        """
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
