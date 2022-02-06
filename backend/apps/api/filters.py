from django_filters import rest_framework as filters
from django.db.models import Q
from rest_framework.filters import (
    BaseFilterBackend, SearchFilter, coreapi, coreschema
)

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='is_favorited_filter',)
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter')
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.CharFilter(method='tags_filter')

    def is_favorited_filter(self, queryset, name, value):
        return queryset.filter(followers__user=self.request.user)

    def is_in_shopping_cart_filter(self, queryset, name, value):
        return queryset.filter(shopping_carts__owner=self.request.user)

    def tags_filter(self, queryset, name, value):
        return queryset.filter(tags__slug=value)

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', )


class RecipesLimitFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        fields = [
            coreapi.Field(name='recipes_limit', description='Recipes limit',
                          required=False, location='query',
                          schema=coreschema.Integer(), ),
        ]
        return fields


class IngredientNameSearchFilter(SearchFilter):
    """Search filter for name field of Ingredient.
    Case-insensitive search at the beginning of the ingredient name"""

    search_param = 'name'

    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)

        if not search_terms:
            return queryset

        # Ignoring case (need for not latin symbols)
        if search_terms[0].isalpha():
            search_term_lower = search_terms[0].lower()
            search_term_upper = search_terms[0].upper()
        else:
            search_term_lower = search_term_upper = search_terms[0]

        queryset = queryset.filter(
            Q(name__startswith=search_term_lower) |
            Q(name__startswith=search_term_upper)
        )

        return queryset
