from django import forms

from .models import Company, Contact, Deal, Invitation, Membership, Task


class CompanyForm(forms.ModelForm):
    """Form used to create and edit companies."""

    class Meta:
        model = Company
        fields = [
            "name",
            "industry",
            "phone",
            "email",
            "website",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Company name",
                    "autocomplete": "organization",
                }
            ),
            "industry": forms.TextInput(
                attrs={
                    "placeholder": "Industry",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Phone number",
                    "autocomplete": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Email address",
                    "autocomplete": "email",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "placeholder": "https://example.com",
                    "autocomplete": "url",
                }
            ),
        }


class ContactForm(forms.ModelForm):
    """Form used to create and edit contacts."""

    class Meta:
        model = Contact
        fields = [
            "company",
            "first_name",
            "last_name",
            "job_title",
            "email",
            "phone",
        ]


class DealForm(forms.ModelForm):
    """Form used to create and edit deals.

    The ``owner`` field (who on the team this deal belongs to) is only
    included when the view passes ``allow_owner_assignment=True``.
    """

    class Meta:
        model = Deal
        fields = [
            "company",
            "contact",
            "title",
            "value",
            "stage",
            "owner",
        ]

    def __init__(self, *args, allow_owner_assignment=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].required = False

        if not allow_owner_assignment:
            del self.fields["owner"]


class TaskForm(forms.ModelForm):
    """Form used to create and edit CRM tasks."""

    class Meta:
        model = Task
        fields = [
            "company",
            "contact",
            "deal",
            "title",
            "description",
            "due_date",
            "due_time",
            "completed",
        ]

        widgets = {
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "due_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
        }


class InvitationForm(forms.ModelForm):
    """Form used by business administrators to invite new users."""

    class Meta:
        model = Invitation
        fields = [
            "email",
            "role",
        ]

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "placeholder": "Enter email address",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Limit invitation roles to non-administrative roles."""

        super().__init__(*args, **kwargs)

        self.fields["role"].choices = [
            (
                Membership.SALES,
                "Sales",
            ),
            (
                Membership.MEMBER,
                "Member",
            ),
        ]

    def clean_email(self):
        """Return the invitation email address in lowercase."""

        return self.cleaned_data["email"].lower()