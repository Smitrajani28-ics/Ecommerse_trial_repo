from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, UserUpdateForm, UserProfileUpdateForm, AddressForm
from .models import Address


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Account created for {username}! You can now log in.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register'
        return context


class CustomLoginView(TemplateView):
    template_name = 'accounts/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Redirect to next page if specified, otherwise to home
                next_page = request.GET.get('next', '/')
                return redirect(next_page)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
        
        return self.get(request, *args, **kwargs)


class CustomLogoutView(TemplateView):
    template_name = 'accounts/logout.html'

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Logged Out'
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    login_url = 'accounts:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Profile'
        context['user_form'] = UserUpdateForm(instance=self.request.user)
        context['profile_form'] = UserProfileUpdateForm(instance=self.request.user.profile)
        context['addresses'] = Address.objects.filter(user=self.request.user, is_active=True)
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
            context = self.get_context_data(**kwargs)
            context['user_form'] = user_form
            context['profile_form'] = profile_form
            return self.render_to_response(context)


@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('accounts:profile')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/add_address.html', {
        'form': form,
        'title': 'Add Address'
    })


@login_required
def edit_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        messages.error(request, 'Address not found.')
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('accounts:profile')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'accounts/edit_address.html', {
        'form': form,
        'address': address,
        'title': 'Edit Address'
    })


@login_required
def delete_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    except Address.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('accounts:profile')
