from django.contrib.auth import get_user_model
from django.db import models
from recipes.models import Recipe

User = get_user_model()


class ShoppingCart(models.Model):
    owner = models.ForeignKey(
        verbose_name='Owner',
        to=User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )
    recipes = models.ManyToManyField(
        verbose_name='Recipes',
        to=Recipe,
        related_name='shopping_carts',
    )

    def __str__(self):
        return f'Shopping cart of {self.owner.username}'
