import os

from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver
from django.contrib.auth.models import AnonymousUser
from colorfield.fields import ColorField


User = get_user_model()


class Recipe(models.Model):
    name = models.CharField(verbose_name='Name', max_length=250)
    image = models.ImageField(verbose_name='Image', upload_to='recipes/')
    text = models.TextField(verbose_name='Description')
    author = models.ForeignKey(
        verbose_name='Author',
        to=User,
        related_name='recipes',
        on_delete=models.CASCADE,
    )
    ingredients = models.ManyToManyField(
        verbose_name='Ingredients',
        to='Ingredient',
        through='RecipeIngredientMap',
    )
    tags = models.ManyToManyField(
        verbose_name='Tags',
        to='Tag',
        through='RecipeTagMap',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Cooking time in minutes'
    )
    pub_date = models.DateTimeField(
        verbose_name='Publication date',
        auto_now_add=True,
    )

    def get_is_favorite(self, user) -> bool:
        if isinstance(user, AnonymousUser):
            return False
        return user.favourite_recipes.filter(recipe=self).exists()

    def get_is_in_shopping_cart(self, user) -> bool:
        if isinstance(user, AnonymousUser):
            return False

        shopping_cart = user.shopping_cart.first()
        if not shopping_cart:
            return False

        return shopping_cart.recipes.filter(pk=self.pk).exists()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ('-pub_date',)


@receiver(models.signals.post_delete, sender=Recipe)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes image from filesystem
    when corresponding `Recipe` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=Recipe)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old image from filesystem
    when corresponding `Recipe` object is updated
    with new image.
    """
    if not instance.pk:
        return False

    try:
        old_image = Recipe.objects.get(pk=instance.pk).image
    except Recipe.DoesNotExist:
        return False

    new_image = instance.image
    if not old_image == new_image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)


class MeasurementUnit(models.Model):
    name = models.CharField(verbose_name='Name', max_length=20, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Name', max_length=250)
    measurement_unit = models.ForeignKey(
        verbose_name='Measurement unit',
        to=MeasurementUnit,
        related_name='ingredients',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.name} ({self.measurement_unit.name})'


class Tag(models.Model):
    name = models.CharField(verbose_name='Name', max_length=50, unique=True)
    hexcolor = ColorField(verbose_name='Hex color', default='#FFDEAD')
    slug = models.SlugField(verbose_name='Slug', max_length=150, unique=True)

    def __str__(self):
        return self.name


class RecipeIngredientMap(models.Model):
    recipe = models.ForeignKey(
        verbose_name='Recipe',
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_maps'
    )
    ingredient = models.ForeignKey(
        verbose_name='Ingredient',
        to=Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(verbose_name='Amount')

    def __str__(self):
        return self.recipe.name + ' -- ' + self.ingredient.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipe_ingredient_map_unique'
            )
        ]


class RecipeTagMap(models.Model):
    recipe = models.ForeignKey(
        verbose_name='Recipe',
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='tag_maps',
    )
    tag = models.ForeignKey(
        verbose_name='Tag',
        to=Tag,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.recipe.name + ' -- ' + self.tag.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipe_tag_map_unique'
            )
        ]


class UserFavouriteRecipeMap(models.Model):
    user = models.ForeignKey(
        verbose_name='User',
        to=User,
        related_name='favourite_recipes',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        verbose_name='Recipe',
        to=Recipe,
        related_name='followers',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_favourite_recipe_map_unique'
            )
        ]
