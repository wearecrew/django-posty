from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

from .constants import HTML, TEXT
from .exceptions import MissingTemplateError
from .managers import EmailManager


class PreviewMixin:
    @classmethod
    def get_preview_url_base(self):
        return f"{self._meta.app_label}_{self._meta.model_name}_preview"

    @classmethod
    def get_preview_launcher_url_base(self):
        return f"{self._meta.app_label}_{self._meta.model_name}_preview_launcher"

    @classmethod
    def get_preview_url_name(self):
        return f"admin:{self.get_preview_url_base()}"

    @classmethod
    def get_preview_launcher_url_name(self):
        return f"admin:{self.get_preview_launcher_url_base()}"

    @property
    def preview_launcher_url(self):
        return reverse(
            self.get_preview_launcher_url_name(),
            kwargs={
                "object_id": self.id,
            },
        )

    @property
    def preview_link(self):
        if self.id:
            return mark_safe(
                f'<a target="_blank" href="{self.preview_launcher_url}">Preview</a>'
            )
        return ""

    def get_preview_template(self, request, mode_name):
        return "posty/preview.html"


class EmailPreviewMixin(PreviewMixin):
    @property
    def preview_modes(self):
        return [HTML, TEXT]

    def get_preview_template(self, request, mode_name):
        if mode_name == TEXT:
            return "posty/preview_text.html"
        return "posty/preview.html"


class EmailTemplate(EmailPreviewMixin, models.Model):
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    text_template = models.TextField()
    html_template = models.TextField()
    preview_data = models.JSONField(null=True, blank=True)

    def get_preview_context(self, request, mode_name):
        context = Context(self.preview_data or {})
        if mode_name == "Text":
            template = Template(self.text_template)
        else:
            template = Template(self.html_template)
        content = template.render(context)
        return {"content": content}

    def __str__(self):
        return self.name


class Email(EmailPreviewMixin, models.Model):
    class Meta:
        ordering = ["-created_at"]

    from_email = models.CharField(max_length=255)
    to_email = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    text_content = models.TextField(blank=False)
    html_content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(null=True, blank=True)
    template = models.ForeignKey(
        EmailTemplate, on_delete=models.PROTECT, null=True, blank=True
    )
    objects = EmailManager()

    def __str__(self):
        return f"{self.subject} | {self.to_email}"

    def get_preview_context(self, request, mode_name):
        if mode_name == TEXT:
            content = self.text_content
        else:
            content = mark_safe(self.html_content)
        return {"content": content}

    @staticmethod
    def render_template(template_str, data):
        template = Template(template_str)
        context = Context(data)
        return template.render(context)

    def render(self):
        if not self.template:
            raise MissingTemplateError
        self.subject = self.template.subject
        self.text_content = self.render_template(self.template.text_template, self.data)
        self.html_content = self.render_template(self.template.html_template, self.data)
        self.save(update_fields=["subject", "text_content", "html_content"])

    def create_message(self, attachments=[]):
        message = EmailMultiAlternatives(
            subject=self.subject,
            body=self.text_content,
            from_email=self.from_email,
            to=[self.to_email],
            attachments=attachments,
        )
        message.attach_alternative(self.html_content, "text/html")
        return message

    def send(self, attachments=[]):
        if self.template:
            self.render()
        message = self.create_message(attachments)
        message.send()
        Event.objects.create(email=self, event_type=Event.EventType.SENT)
        return message


class Event(models.Model):
    class EventType(models.TextChoices):
        QUEUED = "queued"
        SENT = "sent"
        REJECTED = "rejected"
        FAILED = "failed"
        BOUNCED = "bounced"
        DEFERRED = "deferred"
        DELIVERED = "delivered"
        OPENED = "opened"
        CLICKED = "clicked"
        UNKNOWN = "unknown"

    event_type = models.CharField(max_length=255, choices=EventType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)

    def __str__(self):
        if settings.USE_TZ:
            tz = timezone.get_current_timezone()
            created_at = self.created_at.astimezone(tz)
        else:
            created_at = self.created_at
        formatted = date_format(created_at, "DATETIME_FORMAT")
        return f"{self.event_type} | {formatted}"
