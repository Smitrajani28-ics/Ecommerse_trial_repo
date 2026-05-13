from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, Shipment, ReturnRequest
from .utils import send_order_status_update_email


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'product_name', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    fields = ['status', 'notes', 'created_by', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'total_amount', 'coupon_code', 'total_items', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'updated_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'email']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'shipped_at', 'delivered_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'coupon_code', 'total_amount')
        }),
        ('Addresses', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        })
    )

    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'

    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        for order in queryset:
            send_order_status_update_email(order)
        self.message_user(request, f'{updated} orders marked as processing.')
    mark_as_processing.short_description = 'Mark selected orders as processing'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        for order in queryset:
            send_order_status_update_email(order)
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected orders as shipped'

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        for order in queryset:
            send_order_status_update_email(order)
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_as_delivered.short_description = 'Mark selected orders as delivered'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'unit_price', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name', 'product_name']
    readonly_fields = ['total_price', 'created_at']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'notes']
    readonly_fields = ['created_at']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'carrier', 'tracking_number', 'estimated_delivery', 'shipped_at', 'delivered_at')
    list_filter = ('carrier', 'shipped_at')
    search_fields = ('order__order_number', 'tracking_number')


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'reason', 'status', 'refund_amount', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('order__order_number', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_returns', 'process_refunds']

    def approve_returns(self, request, queryset):
        for ret in queryset.filter(status='pending'):
            ret.approve()
        self.message_user(request, 'Selected returns approved.')
    approve_returns.short_description = 'Approve selected returns'

    def process_refunds(self, request, queryset):
        for ret in queryset.filter(status='approved'):
            ret.process_refund()
        self.message_user(request, 'Refunds processed.')
    process_refunds.short_description = 'Process refunds for selected returns'
