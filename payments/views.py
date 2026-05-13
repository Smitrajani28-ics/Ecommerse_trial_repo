import stripe
import logging
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from orders.models import Order
from orders.utils import send_order_confirmation_email
from .models import Payment

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentProcessView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.is_paid:
            messages.info(request, 'This order has already been paid.')
            return redirect('orders:order_detail', order_id=order.id)

        # Create or get payment record
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'user': request.user,
                'amount': order.total_amount,
            }
        )

        client_secret = ''
        if settings.STRIPE_SECRET_KEY:
            try:
                if not payment.stripe_payment_intent_id:
                    intent = stripe.PaymentIntent.create(
                        amount=int(order.total_amount * 100),
                        currency='usd',
                        metadata={'order_id': order.id},
                    )
                    payment.stripe_payment_intent_id = intent.id
                    payment.stripe_client_secret = intent.client_secret
                    payment.save()
                client_secret = payment.stripe_client_secret
            except Exception as e:
                logger.error(f'Stripe error: {e}')
                messages.error(request, 'Payment service unavailable. Please try again.')

        return render(request, 'payments/process.html', {
            'order': order,
            'payment': payment,
            'client_secret': client_secret,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        })


class PaymentSuccessView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment = get_object_or_404(Payment, order=order)

        if payment.status != 'completed':
            # Verify with Stripe if configured
            if settings.STRIPE_SECRET_KEY and payment.stripe_payment_intent_id:
                try:
                    intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                    if intent.status == 'succeeded':
                        payment.mark_completed()
                except Exception as e:
                    logger.error(f'Stripe verification error: {e}')
            else:
                # For demo/dev without Stripe, mark as completed
                payment.mark_completed()

        if payment.status == 'completed':
            send_order_confirmation_email(order)

        messages.success(request, f'Payment successful! Order #{order.order_number} confirmed.')
        return render(request, 'payments/success.html', {'order': order})


class PaymentCancelView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        messages.warning(request, 'Payment was cancelled. You can try again.')
        return render(request, 'payments/cancel.html', {'order': order})
