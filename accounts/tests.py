from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import UserProfile, Address


class UserProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123',
            first_name='Test', last_name='User', email='test@example.com'
        )

    def test_profile_auto_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_full_name(self):
        self.assertEqual(self.user.profile.full_name, 'Test User')

    def test_has_complete_profile(self):
        self.user.profile.phone = '+1234567890'
        self.user.profile.save()
        self.assertTrue(self.user.profile.has_complete_profile)


class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='authuser', password='testpass123')

    def test_register_page(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post('/accounts/login/', {
            'username': 'authuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post('/accounts/login/', {
            'username': 'authuser', 'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    def test_profile_requires_login(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)

    def test_profile_accessible_when_logged_in(self):
        self.client.login(username='authuser', password='testpass123')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username='authuser', password='testpass123')
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 200)
