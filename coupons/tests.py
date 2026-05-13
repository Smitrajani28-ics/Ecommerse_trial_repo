from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Coupon


def make_coupon(**kwargs):
    """Helper: create a valid coupon with sensible defaults."""
    defaults = dict(
        code='TEST10',
        discount_type='percentage',
        discount_value=Decimal('10.00'),
        valid_from=timezone.now() - timedelta(days=1),
        valid_to=timezone.now() + timedelta(days=30),
        is_active=True,
        usage_limit=0,
        times_used=0,
        min_order_amount=Decimal('0.00'),
    )
    defaults.update(kwargs)
    return Coupon.objects.create(**defaults)


class CouponIsValidTest(TestCase):
    def test_valid_coupon(self):
        coupon = make_coupon()
        self.assertTrue(coupon.is_valid)

    def test_inactive_coupon_is_not_valid(self):
        coupon = make_coupon(is_active=False)
        self.assertFalse(coupon.is_valid)

    def test_expired_coupon_is_not_valid(self):
        coupon = make_coupon(
            valid_from=timezone.now() - timedelta(days=10),
            valid_to=timezone.now() - timedelta(days=1),
        )
        self.assertFalse(coupon.is_valid)

    def test_future_coupon_not_yet_valid(self):
        coupon = make_coupon(
            valid_from=timezone.now() + timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
        )
        self.assertFalse(coupon.is_valid)

    def test_usage_limit_exhausted_is_not_valid(self):
        coupon = make_coupon(usage_limit=5, times_used=5)
        self.assertFalse(coupon.is_valid)

    def test_usage_limit_not_yet_exhausted_is_valid(self):
        coupon = make_coupon(usage_limit=5, times_used=4)
        self.assertTrue(coupon.is_valid)

    def test_unlimited_usage_coupon_is_valid(self):
        # usage_limit=0 means unlimited
        coupon = make_coupon(usage_limit=0, times_used=9999)
        self.assertTrue(coupon.is_valid)

    def test_str_representation(self):
        coupon = make_coupon(code='HELLO20')
        self.assertEqual(str(coupon), 'HELLO20')


class CouponCalculateDiscountPercentageTest(TestCase):
    def test_percentage_discount_basic(self):
        coupon = make_coupon(discount_type='percentage', discount_value=Decimal('10.00'))
        # 10% of 100.00 = 10.00
        self.assertEqual(coupon.calculate_discount(Decimal('100.00')), Decimal('10.00'))

    def test_percentage_discount_with_max_cap(self):
        coupon = make_coupon(
            discount_type='percentage',
            discount_value=Decimal('50.00'),
            max_discount=Decimal('20.00'),
        )
        # 50% of 100 = 50, capped at 20
        self.assertEqual(coupon.calculate_discount(Decimal('100.00')), Decimal('20.00'))

    def test_percentage_discount_below_cap(self):
        coupon = make_coupon(
            code='TESTBELOW',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            max_discount=Decimal('50.00'),
        )
        # 10% of 100 = 10, below cap of 50
        self.assertEqual(coupon.calculate_discount(Decimal('100.00')), Decimal('10.00'))

    def test_percentage_discount_below_min_order(self):
        coupon = make_coupon(
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('200.00'),
        )
        # Order total 100 < min 200, so discount = 0
        self.assertEqual(coupon.calculate_discount(Decimal('100.00')), Decimal('0.00'))

    def test_percentage_discount_exactly_at_min_order(self):
        coupon = make_coupon(
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('100.00'),
        )
        self.assertEqual(coupon.calculate_discount(Decimal('100.00')), Decimal('10.00'))

    def test_percentage_result_quantized_to_two_decimals(self):
        coupon = make_coupon(discount_type='percentage', discount_value=Decimal('33.00'))
        result = coupon.calculate_discount(Decimal('100.00'))
        self.assertEqual(result, result.quantize(Decimal('0.01')))


class CouponCalculateDiscountFixedTest(TestCase):
    def test_fixed_discount_basic(self):
        coupon = make_coupon(discount_type='fixed', discount_value=Decimal('15.00'))
        self.assertEqual(coupon.calculate_discount(Decimal('100.00')), Decimal('15.00'))

    def test_fixed_discount_capped_at_order_total(self):
        # Fixed discount cannot exceed the order total
        coupon = make_coupon(discount_type='fixed', discount_value=Decimal('200.00'))
        self.assertEqual(coupon.calculate_discount(Decimal('50.00')), Decimal('50.00'))

    def test_fixed_discount_below_min_order(self):
        coupon = make_coupon(
            discount_type='fixed',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('100.00'),
        )
        self.assertEqual(coupon.calculate_discount(Decimal('50.00')), Decimal('0.00'))

    def test_fixed_discount_quantized_to_two_decimals(self):
        coupon = make_coupon(discount_type='fixed', discount_value=Decimal('5.00'))
        result = coupon.calculate_discount(Decimal('100.00'))
        self.assertEqual(result, result.quantize(Decimal('0.01')))


class ApplyCouponViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='couponuser', password='testpass123')
        self.coupon = make_coupon(code='SAVE10')

    def test_apply_coupon_requires_post(self):
        response = self.client.get('/coupons/apply/')
        self.assertEqual(response.status_code, 405)

    def test_apply_valid_coupon_sets_session(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'SAVE10'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['coupon_id'], self.coupon.id)

    def test_apply_coupon_case_insensitive(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'save10'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['coupon_id'], self.coupon.id)

    def test_apply_nonexistent_coupon_does_not_set_session(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'INVALID'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_empty_code_does_not_set_session(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': ''})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_expired_coupon_does_not_set_session(self):
        make_coupon(
            code='EXPIRED',
            valid_from=timezone.now() - timedelta(days=10),
            valid_to=timezone.now() - timedelta(days=1),
        )
        response = self.client.post('/coupons/apply/', {'coupon_code': 'EXPIRED'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_inactive_coupon_does_not_set_session(self):
        make_coupon(code='INACTIVE', is_active=False)
        response = self.client.post('/coupons/apply/', {'coupon_code': 'INACTIVE'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_apply_redirects_to_cart(self):
        response = self.client.post('/coupons/apply/', {'coupon_code': 'SAVE10'})
        self.assertRedirects(response, '/cart/', fetch_redirect_response=False)

    def test_apply_usage_limit_exhausted_does_not_set_session(self):
        make_coupon(code='MAXED', usage_limit=1, times_used=1)
        response = self.client.post('/coupons/apply/', {'coupon_code': 'MAXED'})
        self.assertNotIn('coupon_id', self.client.session)


class RemoveCouponViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.coupon = make_coupon(code='REMOVE10')

    def test_remove_coupon_requires_post(self):
        response = self.client.get('/coupons/remove/')
        self.assertEqual(response.status_code, 405)

    def test_remove_coupon_clears_session(self):
        # First apply
        self.client.post('/coupons/apply/', {'coupon_code': 'REMOVE10'})
        self.assertIn('coupon_id', self.client.session)
        # Then remove
        response = self.client.post('/coupons/remove/')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('coupon_id', self.client.session)

    def test_remove_coupon_when_none_applied_is_safe(self):
        # Should not raise an error even when no coupon is in session
        response = self.client.post('/coupons/remove/')
        self.assertEqual(response.status_code, 302)

    def test_remove_redirects_to_cart(self):
        response = self.client.post('/coupons/remove/')
        self.assertRedirects(response, '/cart/', fetch_redirect_response=False)
