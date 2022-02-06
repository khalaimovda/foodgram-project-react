from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (
    Tag, Recipe, Ingredient, RecipeIngredientMap, RecipeTagMap)
from .utils import email_authentication

User = get_user_model()


class TokenLoginRequestSerializer(serializers.Serializer):
    email = serializers.CharField(
        label='Email',
        write_only=True
    )
    password = serializers.CharField(
        label='Password',
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label='Token',
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = email_authentication(email=email, password=password)
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class TokenLoginResponseSerializer(serializers.Serializer):
    auth_token = serializers.CharField()


class UserGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed')

    def get_is_subscribed(self, obj) -> bool:
        user = self.context['request'].user
        return obj.get_is_subscribed(user=user)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed',
        )


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')
        read_only_fields = ('id', )

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
        return user


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)

    def validate_current_password(self, value):
        user = self.context['user']
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect current password')
        return value

    def save(self, **kwargs):
        user = self.context['user']
        with transaction.atomic():
            user.set_password(self.data['new_password'])
            user.save()


class TagSerializer(serializers.ModelSerializer):
    color = serializers.CharField(source='hexcolor')

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.CharField(source='measurement_unit.name')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField(method_name='get_amount')
    measurement_unit = serializers.CharField(source='measurement_unit.name')

    def get_amount(self, obj):
        recipe = self.context['recipe']
        amount = recipe.ingredients.through.objects.get(
            recipe=recipe, ingredient=obj).amount
        return amount

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeBriefSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserGetSerializer()
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients')
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    def get_ingredients(self, obj) -> RecipeIngredientSerializer.data:
        ingredients = obj.ingredients.all()
        serializer = RecipeIngredientSerializer(
            instance=ingredients, many=True, context={'recipe': obj})
        return serializer.data

    def get_is_favorited(self, obj) -> bool:
        user = self.context['request'].user
        return obj.get_is_favorite(user=user)

    def get_is_in_shopping_cart(self, obj) -> bool:
        user = self.context['request'].user
        return obj.get_is_in_shopping_cart(user=user)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )


class RecipeIngredientMapSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredientMap
        fields = ('id', 'amount')


class RecipeCreateUpdateRequestSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    ingredients = RecipeIngredientMapSerializer(
        many=True, source='ingredient_maps')
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tag_maps', many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'author', 'image', 'name', 'text',
            'cooking_time',
        )

    def update(self, instance, validated_data):
        ingredient_data = validated_data.pop('ingredient_maps')
        RecipeIngredientMap.objects.filter(recipe=instance).delete()
        ingredient_data_distinct = {}
        for item in ingredient_data:
            ingredient = item['ingredient']
            amount = item['amount']
            if ingredient in ingredient_data_distinct:
                ingredient_data_distinct[ingredient] += amount
            else:
                ingredient_data_distinct[ingredient] = amount
        for ingredient, amount in ingredient_data_distinct.items():
            RecipeIngredientMap.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=amount,
            )

        tag_data = validated_data.pop('tag_maps')
        RecipeTagMap.objects.filter(recipe=instance).delete()
        tag_data_distinct = set(tag_data)
        for tag in tag_data_distinct:
            RecipeTagMap.objects.create(
                recipe=instance,
                tag=tag,
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def create(self, validated_data):
        ingredient_data = validated_data.pop('ingredient_maps')
        tag_data = validated_data.pop('tag_maps')
        recipe = Recipe.objects.create(**validated_data)

        ingredient_data_distinct = {}
        for item in ingredient_data:
            ingredient = item['ingredient']
            amount = item['amount']
            if ingredient in ingredient_data_distinct:
                ingredient_data_distinct[ingredient] += amount
            else:
                ingredient_data_distinct[ingredient] = amount
        for ingredient, amount in ingredient_data_distinct.items():
            RecipeIngredientMap.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount,
            )

        tag_data_distinct = set(tag_data)
        for tag in tag_data_distinct:
            RecipeTagMap.objects.create(
                recipe=recipe,
                tag=tag,
            )
        return recipe


class UserSubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed')
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count')

    def get_is_subscribed(self, obj) -> bool:
        user = self.context['request'].user
        return obj.get_is_subscribed(user=user)

    def get_recipes(self, obj) -> RecipeBriefSerializer.data:
        recipes = obj.recipes.all()
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except (TypeError, ValueError) as e:
                raise serializers.ValidationError(
                    'Incorrect type of recipes_limit query parameter'
                )
            else:
                recipes = recipes[:recipes_limit]
        serializer = RecipeBriefSerializer(instance=recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj) -> int:
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )