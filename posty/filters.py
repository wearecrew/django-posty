from django.contrib import admin


class SentFilter(admin.SimpleListFilter):
    title = "Sent"
    parameter_name = "sent"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(last_sent_at__isnull=False)
        if self.value() == "no":
            return queryset.filter(last_sent_at__isnull=True)


class DeliveredFilter(admin.SimpleListFilter):
    title = "Delivered"
    parameter_name = "delivered"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Yes"),
            ("no", "No"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(last_delivered_at__isnull=False)
        if self.value() == "no":
            return queryset.filter(last_delivered_at__isnull=True)
