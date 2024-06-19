from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path

from . import models
from .filters import DeliveredFilter, SentFilter
from .forms import EmailTemplateForm


@admin.action(description="Send emails")
def send_emails(modeladmin, request, queryset):
    for obj in queryset:
        obj.send()
    messages.add_message(request, messages.INFO, f"{queryset.count()} email(s) sent")


class EventInline(admin.TabularInline):
    readonly_fields = ["event_type"]
    model = models.Event

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PostyMixin:
    change_form_template = "posty/change_form.html"

    def change_form_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["preview_link"] = self.model.objects.get(
            id=object_id
        ).preview_link
        return super().change_form_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )

    def get_urls(self):
        return [
            path(
                "<str:object_id>/preview/",
                self.admin_site.admin_view(self.preview_launcher),
                name=self.model.get_preview_launcher_url_base(),
            ),
            path(
                "<str:object_id>/preview-object/",
                self.admin_site.admin_view(self.preview),
                name=self.model.get_preview_url_base(),
            ),
        ] + super().get_urls()

    def preview_launcher(self, request, object_id):
        obj = self.model.objects.get(id=object_id)
        preview_mode = request.GET.get("mode")
        if preview_mode is None and obj.preview_modes:
            try:
                preview_mode = obj.preview_modes[0]
            except IndexError:
                pass
        return render(
            request,
            "posty/preview_launcher.html",
            {
                "preview_url_name": self.model.get_preview_url_name(),
                "preview_url_launcher_name": self.model.get_preview_launcher_url_name(),
                "preview_mode": preview_mode,
                "obj": obj,
            },
        )

    def preview(self, request, object_id):
        obj = self.model.objects.get(id=object_id)
        preview_mode = request.GET.get("mode", obj.preview_modes[0])
        return render(
            request,
            obj.get_preview_template(request, preview_mode),
            obj.get_preview_context(request, preview_mode),
        )


@admin.register(models.Email)
class EmailAdmin(PostyMixin, admin.ModelAdmin):
    actions = [send_emails]
    inlines = [EventInline]
    list_display = [
        "subject",
        "to_email",
        "created_at",
        "last_delivered_at",
        "preview_link",
    ]
    list_filter = [SentFilter, DeliveredFilter]
    readonly_fields = ["preview_link"]
    search_fields = ["to_email"]

    @admin.display(description="Last Sent At")
    def last_sent_at(self, obj):
        return obj.last_sent_at

    last_sent_at.admin_order_field = "last_sent_at"

    @admin.display(description="Last Delivered At")
    def last_delivered_at(self, obj):
        return obj.last_delivered_at

    last_delivered_at.admin_order_field = "last_delivered_at"

    def get_queryset(self, request):
        return (
            super().get_queryset(request).with_last_sent_at().with_last_delivered_at()
        )

    def send(self, request, queryset):
        for obj in queryset:
            obj.send()
        count = queryset.count()
        self.message_user(request, f"{count} email(s) sent")
        return HttpResponseRedirect(".")


@admin.register(models.EmailTemplate)
class EmailTemplateAdmin(PostyMixin, admin.ModelAdmin):
    form = EmailTemplateForm
    list_display = ["__str__", "preview_link"]
    readonly_fields = ["preview_link"]
