from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    """Form used to create a ConnectCRM user account."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, invitation_email=None, **kwargs):
        """Optionally bind registration to a specific invitation email."""

        super().__init__(*args, **kwargs)
        self.invitation_email = (
            invitation_email.lower() if invitation_email else None
        )

        if self.invitation_email:
            self.fields["email"].initial = self.invitation_email
            self.fields["email"].widget.attrs["readonly"] = "readonly"

    def clean_email(self):
        """Validate and normalise the account email address."""

        email = self.cleaned_data["email"].lower()

        if self.invitation_email and email != self.invitation_email:
            raise forms.ValidationError(
                "This account must use the email address from the invitation."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists. "
                "Please log in instead."
            )

        return email
