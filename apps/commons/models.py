import uuid

from django.contrib.gis.db import models
from django.utils.timezone import now


class AbstractUUIDModel(models.Model):
    """
    Abstract base model with created, modified, and uuid fields.
    """

    created = models.DateTimeField(default=now, editable=False)
    modified = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created']
