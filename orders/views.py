from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView
from decimal import Decimal
from cart.views import get_or_create_cart
from .models import Order, OrderItem, OrderStatusHistory
from .forms import CheckoutForm


class OrderCreateView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        cart = get_or_create_cart(request)
        if cart.is_empty:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart_detail')

        form = CheckoutForm(initial={
            'shipping_first_name': request.user.first_name,
            'shipping_last_name': request.user.last_name,
            'shipping_email': request.user.email,
        })
        # Pre-fill from default shipping address if available
        default_addr = request.user.addresses.filter(type='shipping', is_default=True).first()
        if default_addr:
            form = CheckoutForm(initial={
                'shipping_first_name': default_addr.first_name,
                'shipping_last_name': default_addr.last_name,
                'shipping_email': request.user.email,
                'shipping_phone': default_addr.phone,
                'shipping_address_1': default_addr.address_line_1,
                'shipping_address_2': default_addr.address_line_2,
                'shipping_city': default_addr.city,
                'shipping_state': default_addr.state,
                'shipping_postal_code': default_addr.postal_code,
                'shipping_country': default_addr.country,
            })

        cart_items = cart.items.select_related('product').all()
        return render(request, 'orders/checkout.html', {
            'form': form, 'cart': cart, 'cart_items': cart_items
        })

    def post(self, request):
        cart = get_or_create_cart(request)
        if cart.is_empty:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart:cart_detail')

        form = CheckoutForm(request.POST)
        cart_items = cart.items.select_related('product').all()

        if form.is_valid():
            cd = form.cleaned_data
            shipping_address = (
                f"{cd['shipping_first_name']} {cd['shipping_last_name']}\n"
                f"{cd['shipping_address_1']}\n"
            )
            if cd.get('shipping_address_2'):
                shipping_address += f"{cd['shipping_address_2']}\n"
            shipping_address += (
                f"{cd['shipping_city']}, {cd['shipping_state']} {cd['shipping_postal_code']}\n"
                f"{cd['shipping_country']}"
            )

            billing_address = shipping_address if cd.get('billing_same_as_shipping') else shipping_address

            subtotal = cart.total_price
            tax = subtotal * Decimal('0.08')  # 8% tax
            total = subtotal + tax

            order = Order.objects.create(
                user=request.user,
                subtotal=subtotal,
                tax_amount=tax,
                total_amount=total,
                shipping_address=shipping_address,
                billing_address=billing_address,
                email=cd['shipping_email'],
                phone=cd.get('shipping_phone', ''),
                notes=cd.get('notes', ''),
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_sku=item.product.sku,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                    total_price=item.quantity * item.product.price,
                )
                item.product.reduce_stock(item.quantity)

            OrderStatusHistory.objects.create(
                order=order, status='pending', notes='Order placed', created_by=request.user
            )

            cart.clear()
            return redirect('payments:process', order_id=order.id)

        return render(request, 'orders/checkout.html', {
            'form': form, 'cart': cart, 'cart_items': cart_items
        })


class OrderHistoryView(LoginRequiredMixin, ListView):
    template_name = 'orders/order_history.html'
    context_object_name = 'orders'
    login_url = '/accounts/login/'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    login_url = '/accounts/login/'

    def get_object(self):
        return get_object_or_404(
            Order, id=self.kwargs['order_id'], user=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = self.object.items.select_related('product').all()
        context['status_history'] = self.object.status_history.all()
        return context
