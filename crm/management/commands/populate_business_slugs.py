from django.core.management.base import BaseCommand

from crm.models import Business
from crm.tenancy import generate_unique_slug


class Command(BaseCommand):
    """Populate unique workspace slugs for existing businesses."""

    help = "Populate unique slugs for existing businesses."

    def handle(self, *args, **options):
        businesses = Business.objects.all().order_by("id")

        for business in businesses:
            business.slug = generate_unique_slug(business.name, exclude_pk=business.pk)
            business.save(update_fields=["slug"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"{business.name} -> {business.slug}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Business slugs populated successfully."
            )
        )