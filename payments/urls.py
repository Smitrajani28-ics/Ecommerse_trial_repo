from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<int:order_id>/', views.PaymentProcessView.as_view(), name='process'),
    path('success/<int:order_id>/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancel/<int:order_id>/', views.PaymentCancelView.as_view(), name='cancel'),
]
