from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, Address
from .forms import CustomUserCreationForm, UserUpdateForm, UserProfileUpdateForm, AddressForm


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_profile_creation(self):
        # Profile should be created automatically via signal
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_user_profile_str_representation(self):
        expected_str = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.user.profile), expected_str)

    def test_full_name_property(self):
        self.assertEqual(self.user.profile.full_name, "Test User")
        
        # Test with empty names
        user_no_name = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='testpass123'
        )
        self.assertEqual(user_no_name.profile.full_name, "noname")

    def test_has_complete_profile_property(self):
        # Initially incomplete (no phone)
        self.assertFalse(self.user.profile.has_complete_profile)
        
        # Add phone to complete profile
        self.user.profile.phone = '+1234567890'
        self.user.profile.save()
        self.assertTrue(self.user.profile.has_complete_profile)

    def test_phone_validation(self):
        profile = self.user.profile
        
        # Valid phone numbers
        valid_phones = ['+1234567890', '1234567890', '+123456789012345']
        for phone in valid_phones:
            profile.phone = phone
            profile.full_clean()  # Should not raise ValidationError
        
        # Invalid phone numbers
        invalid_phones = ['123', 'abc123', '+12345678901234567890']
        for phone in invalid_phones:
            profile.phone = phone
            with self.assertRaises(ValidationError):
                profile.full_clean()


class AddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.address = Address.objects.create(
            user=self.user,
            type='shipping',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='Anytown',
            state='CA',
            postal_code='12345',
            country='United States'
        )

    def test_address_creation(self):
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.address.type, 'shipping')
        self.assertEqual(self.address.first_name, 'John')
        self.assertEqual(self.address.last_name, 'Doe')

    def test_address_str_representation(self):
        expected_str = "Shipping - John Doe"
        self.assertEqual(str(self.address), expected_str)

    def test_full_name_property(self):
        self.assertEqual(self.address.full_name, "John Doe")

    def test_full_address_property(self):
        expected_address = "123 Main St\nAnytown, CA 12345\nUnited States"
        self.assertEqual(self.address.full_address, expected_address)

    def test_default_address_uniqueness(self):
        # Create first default address
        address1 = Address.objects.create(
            user=self.user,
            type='billing',
            first_name='Jane',
            last_name='Doe',
            address_line_1='456 Oak St',
            city='Otherville',
            state='NY',
            postal_code='67890',
            is_default=True
        )
        
        # Create second default address of same type
        address2 = Address.objects.create(
            user=self.user,
            type='billing',
            first_name='Bob',
            last_name='Smith',
            address_line_1='789 Pine St',
            city='Somewhere',
            state='TX',
            postal_code='54321',
            is_default=True
        )
        
        # First address should no longer be default
        address1.refresh_from_db()
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)


class CustomUserCreationFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_saves_user_with_profile(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(hasattr(user, 'profile'))

    def test_form_requires_email(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class AddressFormTest(TestCase):
    def test_valid_address_form(self):
        form_data = {
            'type': 'shipping',
            'first_name': 'John',
            'last_name': 'Doe',
            'address_line_1': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'postal_code': '12345',
            'country': 'United States',
            'phone': '+1234567890',
        }
        form = AddressForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form_data = {}
        form = AddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        required_fields = ['type', 'first_name', 'last_name', 'address_line_1', 'city', 'state', 'postal_code']
        for field in required_fields:
            self.assertIn(field, form.errors)


class AuthenticationViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_register_view_get(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, 'form')

    def test_register_view_post_valid(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        response = self.client.post('/accounts/register/', data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_post_invalid(self):
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'invalid-email',  # Invalid email
            'password1': 'complexpassword123',
            'password2': 'differentpassword',  # Passwords don't match
        }
        response = self.client.post('/accounts/register/', data=form_data)
        self.assertEqual(response.status_code, 200)  # Stay on same page
        # Check that user was not created due to form errors
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_login_view_get(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'username')
        self.assertContains(response, 'password')

    def test_login_view_post_valid(self):
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        
        # Check user is logged in
        user = User.objects.get(username='testuser')
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_view_post_invalid(self):
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Invalid username or password')

    def test_logout_view(self):
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Then logout
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'logged out successfully')

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile Information')
        self.assertContains(response, self.user.first_name)

    def test_profile_view_unauthenticated(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_update_post(self):
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'phone': '+1234567890',
            'bio': 'Updated bio',
            'newsletter_subscription': True,
            'email_notifications': False,
        }
        
        response = self.client.post('/accounts/profile/', data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Check user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.email, 'updated@example.com')


class AddressManagementViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_add_address_view_get(self):
        response = self.client.get('/accounts/address/add/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Address')

    def test_add_address_view_post_valid(self):
        form_data = {
            'type': 'shipping',
            'first_name': 'John',
            'last_name': 'Doe',
            'address_line_1': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'postal_code': '12345',
            'country': 'United States',
            'is_default': True,
        }
        
        response = self.client.post('/accounts/address/add/', data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check address was created
        self.assertTrue(Address.objects.filter(user=self.user, first_name='John').exists())

    def test_edit_address_view(self):
        address = Address.objects.create(
            user=self.user,
            type='shipping',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='Anytown',
            state='CA',
            postal_code='12345'
        )
        
        response = self.client.get(f'/accounts/address/edit/{address.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Address')
        self.assertContains(response, 'John')

    def test_delete_address_view(self):
        address = Address.objects.create(
            user=self.user,
            type='shipping',
            first_name='John',
            last_name='Doe',
            address_line_1='123 Main St',
            city='Anytown',
            state='CA',
            postal_code='12345'
        )
        
        response = self.client.get(f'/accounts/address/delete/{address.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Check address was deleted
        self.assertFalse(Address.objects.filter(id=address.id).exists())

    def test_address_access_control(self):
        # Create another user and their address
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_address = Address.objects.create(
            user=other_user,
            type='shipping',
            first_name='Jane',
            last_name='Smith',
            address_line_1='456 Oak St',
            city='Otherville',
            state='NY',
            postal_code='67890'
        )
        
        # Try to access other user's address
        response = self.client.get(f'/accounts/address/edit/{other_address.id}/')
        self.assertEqual(response.status_code, 302)  # Should redirect due to access denied