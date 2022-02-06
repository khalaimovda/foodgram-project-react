from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db import models
from django.db.models import F, Q


class User(AbstractUser):
    email = models.EmailField(verbose_name='Email', unique=True)
    first_name = models.CharField(verbose_name='First name', max_length=150)
    last_name = models.CharField(verbose_name='Last name', max_length=150)
    followings = models.ManyToManyField(
        verbose_name='Followings',
        to='User',
        through='FollowerFollowingMap',
        related_name='followers',
    )

    def get_is_subscribed(self, user) -> bool:
        if isinstance(user, AnonymousUser):
            return False
        return self.follower_maps.filter(follower=user).exists()

    class Meta:
        ordering = ['id', ]


class FollowerFollowingMap(models.Model):
    follower = models.ForeignKey(
        verbose_name='Follower',
        to=User,
        related_name='following_maps',
        on_delete=models.CASCADE,
    )

    following = models.ForeignKey(
        verbose_name='Following',
        to=User,
        related_name='follower_maps',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.follower.username + ' -- ' + self.following.username

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('follower', 'following'),
                name='follower_following_map_unique'
            ),
            models.CheckConstraint(
                check=~Q(follower=F('following')),
                name='ban_self_subscription',
            ),
        ]
