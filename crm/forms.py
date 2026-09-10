from django import forms

from .models import Company, Contact, Deal, Task

class CompanyForm(forms.ModelForm):
    """Form for creating and updating company records."""

    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. microsoft.com",
            }
        ),
    )

    class Meta:
        model = Company
        fields = [
            "name",
            "industry",
            "phone",
            "email",
            "website",
        ]

    def clean_website(self):
        """Add HTTPS to the website if the user omits the protocol."""

        website = self.cleaned_data.get("website")

        if website and not website.startswith(("http://", "https://")):
            website = f"https://{website}"

        return website


class ContactForm(forms.ModelForm):
    """Form for creating and updating contact records."""

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
    """Form for creating and updating deal records."""

    class Meta:
        model = Deal
        fields = [
            "title",
            "value",
            "stage",
            "company",
            "contact",
        ]


class TaskForm(forms.ModelForm):
    """Form for creating and updating task records."""

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "due_date",
            "company",
            "contact",
            "deal",
            "completed",
        ]