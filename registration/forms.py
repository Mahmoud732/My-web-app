# forms.py
from django import forms
from django.contrib.auth.models import User

class EditProfileForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='New Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    birthday = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Birthday'
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and new_password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data
