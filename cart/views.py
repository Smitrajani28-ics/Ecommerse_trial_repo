from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Product
from .models import Cart, CartItem


def get_or_create_cart(request):
    """Get existing cart or create a new one for the user/session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Merge session cart if exists
        if created and request.session.session_key:
            session_cart = Cart.objects.filter(
                session_key=request.session.session_key, user__isnull=True
            ).first()
            if session_cart:
                for item in session_cart.items.all():
                    existing = cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(
            session_key=request.session.session_key, user__isnull=True
        )
        return cart


class CartDetailView(TemplateView):
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_or_create_cart(self.request)
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('product').all()
        return context


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity

    # Check stock
    if cart_item.quantity > product.stock_quantity:
        cart_item.quantity = product.stock_quantity
        messages.warning(request, f'Only {product.stock_quantity} of "{product.name}" available.')

    cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'cart_total_items': cart.total_items,
            'message': f'"{product.name}" added to cart.'
        })

    messages.success(request, f'"{product.name}" added to cart.')
    return redirect('cart:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        cart_item.delete()
        msg = 'Item removed from cart.'
    elif quantity > cart_item.product.stock_quantity:
        cart_item.quantity = cart_item.product.stock_quantity
        cart_item.save()
        msg = f'Quantity set to max available ({cart_item.product.stock_quantity}).'
    else:
        cart_item.quantity = quantity
        cart_item.save()
        msg = 'Cart updated.'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'item_total': str(cart_item.total_price) if quantity > 0 else '0',
            'message': msg
        })

    messages.success(request, msg)
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    product_name = cart_item.product.name
    cart_item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'message': f'"{product_name}" removed from cart.'
        })

    messages.success(request, f'"{product_name}" removed from cart.')
    return redirect('cart:cart_detail')
