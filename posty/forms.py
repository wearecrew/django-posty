from django import forms

from .models import EmailTemplate


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from django_ace import AceWidget

            self.fields["html_template"].widget = AceWidget(
                mode="html",
                width="100%",
                height="500px",
                wordwrap=True,
                showprintmargin=False,
                tabsize=2,
            )

        except ImportError:
            pass
        try:
            from flat_json_widget.widgets import FlatJsonWidget

            self.fields["preview_data"].widget = FlatJsonWidget()
        except ImportError:
            pass
