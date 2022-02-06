# Generated by Django 4.0.2 on 2022-02-06 16:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shopping_carts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppingcart',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to=settings.AUTH_USER_MODEL, verbose_name='Owner'),
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='recipes',
            field=models.ManyToManyField(related_name='shopping_carts', through='shopping_carts.ShoppingCartRecipeMap', to='recipes.Recipe', verbose_name='Recipes'),
        ),
        migrations.AddConstraint(
            model_name='shoppingcartrecipemap',
            constraint=models.UniqueConstraint(fields=('shopping_cart', 'recipe'), name='shopping_cart_recipe_map_unique'),
        ),
    ]