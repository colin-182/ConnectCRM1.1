from django import forms

from .models import Company, Contact, Deal


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