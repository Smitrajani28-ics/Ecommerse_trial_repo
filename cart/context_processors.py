from decimal import Decimal
from .models import Cart


def cart_context(request):
    """Make cart and coupon info available in all templates."""
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(
            session_key=request.session.session_key, user__isnull=True
        ).first()

    coupon = None
    discount = Decimal('0.00')
    coupon_id = request.session.get('coupon_id')
    if coupon_id and cart:
        try:
            from coupons.models import Coupon
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid:
                discount = coupon.calculate_discount(cart.total_price)
            else:
                coupon = None
                del request.session['coupon_id']
        except Exception:
            pass

    return {'cart': cart, 'coupon': coupon, 'discount': discount}
