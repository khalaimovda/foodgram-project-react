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
        through='ShoppingCartRecipeMap',
        related_name='shopping_carts',
    )

    def __str__(self):
        return f'Shopping cart of {self.owner.username}'


class ShoppingCartRecipeMap(models.Model):
    shopping_cart = models.ForeignKey(
        verbose_name='Shopping cart',
        to=ShoppingCart,
        on_delete=models.CASCADE,
    )

    recipe = models.ForeignKey(
        verbose_name='Recipe',
        to=Recipe,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.shopping_cart.owner.username + ' -- ' + self.recipe.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('shopping_cart', 'recipe'),
                name='shopping_cart_recipe_map_unique'
            )
        ]
