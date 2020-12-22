# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.core import validators
# from registration.supplements.base import RegistrationSupplementBase

@python_2_unicode_compatible
class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})


# class UserRegistrationSupplement(RegistrationSupplementBase):
#     # bcryptsha256
#     # Can I set these charfields as password fields automatically?
#     password = models.CharField(max_length=50, validators=[validators.MinLengthValidator(5)])
#     password_verify = models.CharField(max_length=50, validators=[validators.MinLengthValidator(5)])
#
#     def clean(self):
#         if self.password != self.password_verify:
#             raise ValidationError('Passwords do not match!')
