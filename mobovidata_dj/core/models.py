from __future__ import unicode_literals

from django.db import models


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """

    created_dt = models.DateTimeField(auto_now_add=True)
    created_date = models.DateField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
    modified_date = models.DateField(auto_now=True)

    class Meta:
        abstract = True
