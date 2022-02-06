from django.contrib import admin

from .models import Ingredient, MeasurementUnit, Recipe, Tag


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 0


class TagInline(admin.TabularInline):
    model = Recipe.tags.through
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', )
    inlines = [IngredientInline, TagInline]
    list_filter = ('name', 'author__username', 'tags')
    readonly_fields = ('followers_count', )

    def followers_count(self, obj):
        return obj.followers.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'hexcolor')
