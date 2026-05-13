from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from .models import Coupon


def make_coupon(**kwargs):
    now = timezone.now()
    defaults = {
        'code': 'TESTCODE',
        'discount_type': 'percentage',
        'discount_value': Decimal('10.00'),
        'valid_from': now - timedelta(days=1),
        'valid_to': now + timedelta(days=30),
        'is_active': True,
        'usage_limit': 0,
        'times_used': 0,
        'min_order_amount': Decimal('0.00'),
    }
    defaults.update(kwargs)
    return Coupon.objects.create(**defaults)


class CouponModelStrTest(TestCase):
    def test_str_returns_code(self):
        coupon = make_coupon(code='WELCOME20')
        self.assertEqual(str(coupon), 'WELCOME20')


class CouponIsValidTest(TestCase):
    def test_valid_coupon_is_valid(self):
        coupon = make_coupon()
        self.assertTrue(coupon.is_valid)

    def test_inactive_coupon_is_not_valid(self):
        coupon = make_coupon(is_active=False)
        self.assertFalse(coupon.is_valid)

    def test_before_valid_from_is_not_valid(self):
        now = timezone.now()
        coupon = make_coupon(
            valid_from=now + timedelta(days=1),
            valid_to=now + timedelta(days=30),
        )
        self.assertFalse(coupon.is_valid)

    def test_after_valid_to_is_not_valid(self):
        now = timezone.now()
        coupon = make_coupon(
            valid_from=now - timedelta(days=30),
            valid_to=now - timedelta(days=1),
        )
        self.assertFalse(coupon.is_valid)

    def test_usage_limit_not_exceeded_is_valid(self):
        coupon = make_coupon(usage_limit=5, times_used=4)
        self.assertTrue(coupon.is_valid)

    def test_usage_limit_exactly_reached_is_not_valid(self):
        coupon = make_coupon(usage_limit=5, times_used=5)
        self.assertFalse(coupon.is_valid)

    def test_usage_limit_exceeded_is_not_valid(self):
        coupon = make_coupon(usage_limit=3, times_used=10)
        self.assertFalse(coupon.is_valid)

    def test_unlimited_usage_zero_limit_is_valid(self):
        # usage_limit=0 means unlimited
        coupon = make_coupon(usage_limit=0, times_used=9999)
        self.assertTrue(coupon.is_valid)


class CouponCalculateDiscountTest(TestCase):
    def test_percentage_discount(self):
        coupon = make_coupon(discount_type='percentage', discount_value=Decimal('10.00'))
        discount = coupon.calculate_discount(Decimal('100.00'))
        self.assertEqual(discount, Decimal('10.00'))

    def test_percentage_discount_with_max_discount_cap(self):
        coupon = make_coupon(
            discount_type='percentage',
            discount_value=Decimal('50.00'),
            max_discount=Decimal('20.00'),
        )
        # 50% of 100 = 50, but max is 20
        discount = coupon.calculate_discount(Decimal('100.00'))
        self.assertEqual(discount, Decimal('20.00'))

    def test_percentage_discount_below_max_discount_not_capped(self):
        coupon = make_coupon(
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_discount=Decimal('50.00'),
        )
        # 10% of 100 = 10, which is below max 50
        discount = coupon.calculate_discount(Decimal('100.00'))
        self.assertEqual(discount, Decimal('10.00'))

    def test_fixed_discount(self):
        coupon = make_coupon(discount_type='fixed', discount_value=Decimal('15.00'))
        discount = coupon.calculate_discount(Decimal('100.00'))
        self.assertEqual(discount, Decimal('15.00'))

    def test_fixed_discount_capped_at_order_total(self):
        coupon = make_coupon(discount_type='fixed', discount_value=Decimal('200.00'))
        # Discount cannot exceed order total
        discount = coupon.calculate_discount(Decimal('50.00'))
        self.assertEqual(discount, Decimal('50.00'))

    def test_min_order_amount_not_met_returns_zero(self):
        coupon = make_coupon(
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('100.00'),
        )
        discount = coupon.calculate_discount(Decimal('50.00'))
        self.assertEqual(discount, Decimal('0.00'))

    def test_min_order_amount_exactly_met(self):
        coupon = make_coupon(
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('50.00'),
        )
        discount = coupon.calculate_discount(Decimal('50.00'))
        self.assertEqual(discount, Decimal('10.00'))

    def test_discount_rounded_to_two_decimal_places(self):
        coupon = make_coupon(discount_type='percentage', discount_value=Decimal('10.00'))
        # 10% of 33.33 = 3.333 -> should round to 3.33
        discount = coupon.calculate_discount(Decimal('33.33'))
        self.assertEqual(discount, Decimal('3.33'))

    def test_percentage_no_max_discount_field(self):
        coupon = make_coupon(discount_type='percentage', discount_value=Decimal('20.00'), max_discount=None)
        discount = coupon.calculate_discount(Decimal('150.00'))
        self.assertEqual(discount, Decimal('30.00'))

    def test_zero_order_total_fixed_discount(self):
        coupon = make_coupon(discount_type='fixed', discount_value=Decimal('10.00'))
        discount = coupon.calculate_discount(Decimal('0.00'))
        self.assertEqual(discount, Decimal('0.00'))


class ApplyCouponViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        now = timezone.now()
        self.valid_coupon = make_coupon(
            code='SAVE10',
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
        )
        self.expired_coupon = make_coupon(
            code='OLD10',
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            valid_from=now - timedelta(days=60),
            valid_to=now - timedelta(days=1),
        )

    def test_apply_valid_coupon_stores_in_session(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'SAVE10'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['coupon_id'], self.valid_coupon.id)

    def test_apply_coupon_case_insensitive(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'save10'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('coupon_id'), self.valid_coupon.id)

    def test_apply_empty_code_redirects_with_no_coupon_stored(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': ''})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_nonexistent_code_redirects(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'NOTREAL'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_expired_coupon_redirects(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'OLD10'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_coupon_get_not_allowed(self):
        response = self.client.get('/coupons/apply/')
        self.assertEqual(response.status_code, 405)

    def test_apply_coupon_redirects_to_cart(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'SAVE10'})
        self.assertRedirects(response, '/cart/', fetch_redirect_response=False)

    def test_apply_inactive_coupon_not_stored(self):
        inactive = make_coupon(code='INACTIVE', is_active=False)
        response = self.client.post('/coupons/apply/', {'coupon_code': 'INACTIVE'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)


class RemoveCouponViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        now = timezone.now()
        self.coupon = make_coupon(
            code='REMOVE10',
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
        )

    def test_remove_coupon_clears_session(self):
        # First apply
        self.client.post('/coupons/apply/', {'coupon_code': 'REMOVE10'})
        self.assertIn('coupon_id', self.client.session)

        # Then remove
        response = self.client.post('/coupons/remove/')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_remove_coupon_without_session_is_safe(self):
        # No coupon in session, should still succeed
        response = self.client.post('/coupons/remove/')
        self.assertEqual(response.status_code, 302)

    def test_remove_coupon_get_not_allowed(self):
        response = self.client.get('/coupons/remove/')
        self.assertEqual(response.status_code, 405)

    def test_remove_coupon_redirects_to_cart(self):
        response = self.client.post('/coupons/remove/')
        self.assertRedirects(response, '/cart/', fetch_redirect_response=False)
