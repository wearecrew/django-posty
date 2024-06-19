from django.db import models


class EmailQuerySet(models.QuerySet):
    def with_last_sent_at(self):
        return self.annotate(
            last_sent_at=models.Max(
                "event__created_at", filter=models.Q(event__event_type="sent")
            )
        )

    def with_last_delivered_at(self):
        return self.annotate(
            last_delivered_at=models.Max(
                "event__created_at", filter=models.Q(event__event_type="delivered")
            )
        )


class EmailManager(models.Manager):
    def get_queryset(self):
        return EmailQuerySet(self.model, using=self._db)

    def with_last_sent_at(self):
        return self.get_queryset().with_last_sent_at()

    def with_last_delivered_at(self):
        return self.get_queryset().with_last_delivered_at()
