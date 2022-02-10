from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from recipes.models import Recipe

from .models import User


class FollowInline(admin.TabularInline):
    model = User.followings.through
    fk_name = 'from_user'
    extra = 0
    verbose_name = 'Following'
    verbose_name_plural = 'Followings'


class RecipeInline(admin.TabularInline):
    model = Recipe
    fields = ('name', 'image', 'text',)
    readonly_fields = ('name', 'image', 'text', )
    extra = 0
    verbose_name = 'Recipe'
    verbose_name_plural = 'Recipes'


class FavouriteRecipeInline(admin.TabularInline):
    model = User.favourite_recipes.through
    extra = 0
    verbose_name = 'Favorite recipe'
    verbose_name_plural = 'Favourite recipes'


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    inlines = [FollowInline, RecipeInline, FavouriteRecipeInline]
    list_filter = ('username', 'email')
