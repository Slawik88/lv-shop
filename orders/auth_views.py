"""
Customer authentication views.
Separate from the manager panel — regular users can register and login
to track their orders and save preferences.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django import forms

from .models import Order


class CustomerRegistrationForm(UserCreationForm):
    """Extended registration form with email."""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=100, required=False, label='Имя')
    last_name = forms.CharField(max_length=100, required=False, label='Фамилия')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Translate field labels to Russian
        self.fields['username'].label = 'Логин'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повторите пароль'
        # Remove help texts for cleaner UI
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = 'Минимум 8 символов'
        self.fields['password2'].help_text = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


def customer_register(request):
    """Registration page for customers."""
    if request.user.is_authenticated:
        return redirect('products:home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Аккаунт создан.')
            return redirect('products:home')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'orders/auth/register.html', {'form': form})


def customer_login(request):
    """Login page for customers."""
    if request.user.is_authenticated:
        return redirect('products:home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or ''
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('products:home')
        else:
            error = 'Неверный логин или пароль.'

    return render(request, 'orders/auth/login.html', {
        'error': error,
        'next': request.GET.get('next', ''),
    })


def customer_logout(request):
    """Log out and redirect to home."""
    auth_logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('products:home')


@login_required
def customer_profile(request):
    """Customer profile page with order history."""
    orders = Order.objects.filter(customer_email=request.user.email).order_by('-created_at')
    return render(request, 'orders/auth/profile.html', {
        'orders': orders,
    })
