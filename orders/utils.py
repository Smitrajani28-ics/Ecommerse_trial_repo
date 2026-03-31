import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """Send order confirmation email to customer."""
    try:
        subject = f'Order Confirmation - #{order.order_number}'
        message = (
            f'Thank you for your order!\n\n'
            f'Order Number: {order.order_number}\n'
            f'Total: ${order.total_amount}\n'
            f'Status: {order.get_status_display()}\n\n'
            f'We will notify you when your order ships.'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )
        logger.info(f'Order confirmation email sent for order {order.order_number}')
    except Exception as e:
        logger.error(f'Failed to send order confirmation email: {e}')


def send_order_status_update_email(order):
    """Send order status update email to customer."""
    try:
        subject = f'Order Update - #{order.order_number}'
        message = (
            f'Your order #{order.order_number} has been updated.\n\n'
            f'New Status: {order.get_status_display()}\n\n'
            f'Thank you for shopping with us!'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f'Failed to send status update email: {e}')
