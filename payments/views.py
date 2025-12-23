from django.shortcuts import render
from django.views.generic import TemplateView

class PaymentProcessView(TemplateView):
    template_name = 'payments/process.html'

class PaymentSuccessView(TemplateView):
    template_name = 'payments/success.html'

class PaymentCancelView(TemplateView):
    template_name = 'payments/cancel.html'
