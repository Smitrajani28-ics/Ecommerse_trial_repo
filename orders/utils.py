import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    try:
        subject = f'Order Confirmation - #{order.order_number}'
        message = (
            f'Thank you for your order!\n\n'
            f'Order Number: {order.order_number}\n'
            f'Total: ${order.total_amount}\n'
            f'Status: {order.get_status_display()}\n\n'
            f'We will notify you when your order ships.'
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
        logger.info(f'Order confirmation email sent for order {order.order_number}')
    except Exception as e:
        logger.error(f'Failed to send order confirmation email: {e}')


def send_order_status_update_email(order):
    try:
        subject = f'Order Update - #{order.order_number}'
        message = (
            f'Your order #{order.order_number} has been updated.\n\n'
            f'New Status: {order.get_status_display()}\n\n'
            f'Thank you for shopping with us!'
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
    except Exception as e:
        logger.error(f'Failed to send status update email: {e}')


def send_shipping_notification_email(order, shipment):
    try:
        subject = f'Your Order #{order.order_number} Has Shipped!'
        message = (
            f'Great news! Your order has been shipped.\n\n'
            f'Order Number: {order.order_number}\n'
            f'Carrier: {shipment.get_carrier_display()}\n'
            f'Tracking Number: {shipment.tracking_number}\n'
        )
        if shipment.tracking_url:
            message += f'Track your package: {shipment.tracking_url}\n'
        if shipment.estimated_delivery:
            message += f'Estimated Delivery: {shipment.estimated_delivery}\n'
        message += '\nThank you for shopping with us!'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
        logger.info(f'Shipping notification sent for order {order.order_number}')
    except Exception as e:
        logger.error(f'Failed to send shipping notification: {e}')


def send_return_status_email(return_request):
    try:
        order = return_request.order
        subject = f'Return Request Update - Order #{order.order_number}'
        message = (
            f'Your return request for order #{order.order_number} has been updated.\n\n'
            f'Status: {return_request.get_status_display()}\n'
            f'Item: {return_request.order_item.product_name}\n'
        )
        if return_request.refund_amount:
            message += f'Refund Amount: ${return_request.refund_amount}\n'
        message += '\nThank you for your patience.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
        logger.info(f'Return status email sent for return #{return_request.id}')
    except Exception as e:
        logger.error(f'Failed to send return status email: {e}')
