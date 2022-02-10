from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(verbose_name='Email', unique=True)
    first_name = models.CharField(verbose_name='First name', max_length=150)
    last_name = models.CharField(verbose_name='Last name', max_length=150)
    followings = models.ManyToManyField(
        verbose_name='Followings',
        to='User',
        related_name='followers',
    )

    class Meta:
        ordering = ['id', ]
