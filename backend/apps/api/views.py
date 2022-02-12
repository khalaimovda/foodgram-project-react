import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import BadRequest
from django.db.models import BooleanField, Case, IntegerField, Sum, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from recipes.models import Ingredient, Recipe, Tag
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from shopping_carts.models import ShoppingCart

from .filters import (IngredientNameSearchFilter, RecipeFilter,
                      RecipesLimitFilterBackend)
from .permissions import ReadAllCreateAuthenticatedChangeAuthor
from .serializers import (IngredientSerializer, RecipeBriefSerializer,
                          RecipeCreateUpdateRequestSerializer,
                          RecipeGetSerializer, RecipeResponseSerializer,
                          SetPasswordSerializer, TagSerializer,
                          TokenLoginRequestSerializer,
                          TokenLoginResponseSerializer, UserCreateSerializer,
                          UserGetSerializer, UserSubscriptionSerializer)
from .utils import (add_recipe_to_favorites, add_recipe_to_shopping_cart,
                    make_user_shopping_cart, remove_recipe_from_favorites,
                    remove_recipe_from_shopping_cart, subscribe, unsubscribe)

logger = logging.getLogger(__name__)

User = get_user_model()


class TokenLoginView(views.APIView):
    permission_classes = []

    @swagger_auto_schema(
        request_body=TokenLoginRequestSerializer,
        responses={ # noqa
            status.HTTP_201_CREATED: TokenLoginResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = TokenLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class TokenLogoutView(views.APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action in ('subscriptions', 'subscribe'):
            return UserSubscriptionSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in (
                'retrieve', 'me', 'set_password',
                'subscriptions', 'subscribe'
        ):
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    @action(
        methods=['GET'],
        detail=False,
        pagination_class=None
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=SetPasswordSerializer,
        responses={
            status.HTTP_204_NO_CONTENT: '',
        }
    )
    @action(methods=['POST'], detail=False)
    def set_password(self, request):
        serializer = self.get_serializer(
            data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'], detail=False,
        filter_backends=[RecipesLimitFilterBackend],
    )
    def subscriptions(self, request):
        subscriptions = request.user.followings.all()

        page = self.paginate_queryset(queryset=subscriptions)
        if page is not None:
            serializer = self.get_serializer(
                instance=page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            instance=subscriptions, many=True, context={'request': request}, )

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        # Needs because filter_backends=[RecipesLimitFilterBackend] in @action
        # does not work for POST methods
        method='POST',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='recipes_limit',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Recipes limit'
            ),
        ]
    )
    @action(
        methods=['POST'], detail=True,
        filter_backends=[RecipesLimitFilterBackend],
        pagination_class=None,
    )
    def subscribe(self, request, pk):
        following = get_object_or_404(klass=User, pk=pk)
        try:
            subscribe(following=following, follower=request.user)
            serializer = self.get_serializer(
                instance=following, context={'request': request}, )
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        except BadRequest as e:
            logger.warning(msg=str(e))
            return Response(
                data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        following = get_object_or_404(klass=User, pk=pk)
        try:
            unsubscribe(following=following, follower=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BadRequest as e:
            logger.warning(msg=str(e))
            return Response(
                data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = []
    pagination_class = None


class IngredientViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = []
    pagination_class = None
    filter_backends = [IngredientNameSearchFilter]
    filterset_fields = ['category', ]


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadAllCreateAuthenticatedChangeAuthor]
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.prefetch_related(
            'ingredients'
        ).prefetch_related(
            'tags'
        ).prefetch_related(
            'author'
        )
        if not user.is_anonymous:
            queryset = queryset.annotate(
                is_favorited_int=Sum(Case(
                    When(followers=user, then=1),
                    default=0,
                    output_field=IntegerField()
                ))
            ).annotate(
                is_favorited=Case(
                    When(is_favorited_int__gt=0, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            ).annotate(
                is_in_shopping_cart_int=Sum(
                    Case(
                        When(shopping_carts__owner=user, then=1),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
            ).annotate(
                is_in_shopping_cart=Case(
                    When(is_in_shopping_cart_int__gt=0, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Case(
                    default=False,
                    output_field=BooleanField()
                )
            ).annotate(
                is_in_shopping_cart=Case(
                    default=False,
                    output_field=BooleanField()
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateRequestSerializer

    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,)
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def create(self, request, *args, **kwargs):
        request_serializer = self.get_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_serializer.save(author=request.user)

        response_serializer = RecipeResponseSerializer(
            instance=request_serializer.instance,
            context={'request': request},
        )
        return Response(
            data=response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk):  # noqa
        data = self._update_recipe(request=request, pk=pk)
        return Response(data=data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk):  # noqa
        data = self._update_recipe(request=request, pk=pk)
        return Response(data=data, status=status.HTTP_200_OK)

    @action(
        methods=['GET'], detail=False, filter_backends=None,
        pagination_class=None, permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        response = HttpResponse(content_type='application/pdf')
        pdf_name = 'Shopping list.pdf'
        response['Content-Disposition'] = f'attachment; filename={pdf_name}'
        response.write(make_user_shopping_cart(user=request.user))
        return response

    @action(
        methods=['POST', ], detail=True, filter_backends=None,
        pagination_class=None, permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        shopping_cart = ShoppingCart.objects.get_or_create(
            owner=request.user)[0]
        try:
            add_recipe_to_shopping_cart(
                recipe=recipe, shopping_cart=shopping_cart)
            serializer = RecipeBriefSerializer(instance=recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        except BadRequest as e:
            logger.warning(msg=str(e))
            return Response(
                data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk):
        recipe = self.get_object()
        shopping_cart = ShoppingCart.objects.get_or_create(
            owner=request.user)[0]
        try:
            remove_recipe_from_shopping_cart(
                recipe=recipe, shopping_cart=shopping_cart)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BadRequest as e:
            logger.warning(msg=str(e))
            return Response(
                data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['POST'], detail=True, filter_backends=None,
        pagination_class=None, permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = self.get_object()
        try:
            add_recipe_to_favorites(recipe=recipe, user=request.user)
            serializer = RecipeBriefSerializer(instance=recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        except BadRequest as e:
            logger.warning(msg=str(e))
            return Response(
                data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk):
        recipe = self.get_object()
        try:
            remove_recipe_from_favorites(recipe=recipe, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BadRequest as e:
            logger.warning(msg=str(e))
            return Response(
                data={'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _update_recipe(self, request, pk):
        """Updates Recipe model using request and pk."""
        instance = self.get_object()
        self.check_object_permissions(request=request, obj=instance)

        request_serializer = self.get_serializer(
            data=request.data, instance=instance)
        request_serializer.is_valid(raise_exception=True)
        request_serializer.save(author=request.user)

        response_serializer = RecipeResponseSerializer(
            instance=request_serializer.instance,
            context={'request': request},
        )
        return response_serializer.data
