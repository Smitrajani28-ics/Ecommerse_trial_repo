from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Coupon


@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    if not code:
        messages.error(request, 'Please enter a coupon code.')
        return redirect('cart:cart_detail')

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        messages.error(request, 'Invalid coupon code.')
        return redirect('cart:cart_detail')

    if not coupon.is_valid:
        messages.error(request, 'This coupon is expired or no longer valid.')
        return redirect('cart:cart_detail')

    request.session['coupon_id'] = coupon.id
    messages.success(request, f'Coupon "{coupon.code}" applied!')
    return redirect('cart:cart_detail')


@require_POST
def remove_coupon(request):
    request.session.pop('coupon_id', None)
    messages.success(request, 'Coupon removed.')
    return redirect('cart:cart_detail')
