from django.urls import include, path
from rest_framework import routers

from .views import (
    UserViewSet, TokenLoginView, TokenLogoutView, TagViewSet, RecipeViewSet,
    IngredientViewSet,
)

router = routers.DefaultRouter()

router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = router.urls

urlpatterns += [
    path(r'auth/token/login/', TokenLoginView.as_view()),
    path(r'auth/token/logout/', TokenLogoutView.as_view())
]
