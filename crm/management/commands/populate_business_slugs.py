from django.core.management.base import BaseCommand
from django.utils.text import slugify

from crm.models import Business


class Command(BaseCommand):
    """Populate unique workspace slugs for existing businesses."""

    help = "Populate unique slugs for existing businesses."

    def handle(self, *args, **options):
        businesses = Business.objects.all().order_by("id")

        for business in businesses:
            base_slug = slugify(business.name) or f"business-{business.id}"
            slug = base_slug
            counter = 2

            while (
                Business.objects
                .exclude(pk=business.pk)
                .filter(slug=slug)
                .exists()
            ):
                slug = f"{base_slug}-{counter}"
                counter += 1

            business.slug = slug
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