from django import forms
from django.contrib.auth.forms import UserCreationForm 
from .models import User
from django.conf import settings

class loginForm(forms.Form):
    ''' Form to authenticate current users '''
    email = forms.EmailField(max_length=100, label='Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    email.widget.attrs.update({"class": "form-control"})
    password.widget.attrs.update({"class": "form-control"})

    class Meta:
        fields = ['email', 'password']


class signupForm(UserCreationForm):
    ''' Sign up form to create users '''

    email = forms.EmailField(label="Email Address")
    username = forms.CharField(max_length=15, label="Username", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(max_length=100, label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(max_length=100, label="Confirm Password", widget=forms.PasswordInput(attrs={'class': 'form-control'})) # Two fields to confirm password
    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    email.widget.attrs.update({"class": "form-control"})
    username.widget.attrs.update({"class": "form-control"})
    password1.widget.attrs.update({"class": "form-control"})
    password2.widget.attrs.update({"class": "form-control"}) # Apply the form-control class to all fields