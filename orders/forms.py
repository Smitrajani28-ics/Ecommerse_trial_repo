from django import forms


class CheckoutForm(forms.Form):
    # Shipping info
    shipping_first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    shipping_phone = forms.CharField(max_length=17, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_address_1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_address_2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_postal_code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    shipping_country = forms.CharField(max_length=100, initial='United States', widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Billing same as shipping
    billing_same_as_shipping = forms.BooleanField(required=False, initial=True)

    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    def clean_shipping_first_name(self):
        value = self.cleaned_data['shipping_first_name'].strip()
        if not value:
            raise forms.ValidationError('First name is required.')
        return value

    def clean_shipping_last_name(self):
        value = self.cleaned_data['shipping_last_name'].strip()
        if not value:
            raise forms.ValidationError('Last name is required.')
        return value

    def clean_shipping_postal_code(self):
        value = self.cleaned_data['shipping_postal_code'].strip()
        if not value:
            raise forms.ValidationError('Postal code is required.')
        return value
