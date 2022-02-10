from django.contrib import admin

from .models import ShoppingCart


class RecipeInline(admin.TabularInline):
    model = ShoppingCart.recipes.through
    extra = 0


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    fields = ('owner', )
    inlines = [RecipeInline]
