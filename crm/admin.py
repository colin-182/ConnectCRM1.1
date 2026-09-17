from django.contrib import admin

from .models import Business, Company, Contact, Deal, Invitation, Membership, Task


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("created_at",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "business", "role")
    list_filter = ("role", "business")
    search_fields = ("user__username", "user__email", "business__name")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "business",
        "role",
        "created_at",
        "expires_at",
        "accepted_at",
    )
    list_filter = ("role", "business", "accepted_at")
    search_fields = ("email", "business__name", "token")
    readonly_fields = ("token", "created_at", "accepted_at")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "industry", "email", "created_at")
    list_filter = ("business",)
    search_fields = ("name", "industry", "email")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "company",
        "business",
        "email",
    )
    list_filter = ("business",)
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "company__name",
    )


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "value", "stage", "updated_at")
    list_filter = ("business", "stage")
    search_fields = ("title", "company__name", "contact__first_name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "business",
        "due_date",
        "due_time",
        "completed",
    )
    list_filter = ("business", "completed")
    search_fields = ("title", "description", "company__name")
