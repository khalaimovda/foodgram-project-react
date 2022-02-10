import io
import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import BadRequest
from django.db.models import QuerySet, Sum
from recipes.models import Ingredient, Recipe
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from shopping_carts.models import ShoppingCart

"""In this module there are different functions which makes the business logic
of the project.
"""

logger = logging.getLogger(__name__)

User = get_user_model()


def email_authentication(email=None, password=None):
    """User authentication using email and password."""
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None
    else:
        if user.check_password(password):
            return user


def make_user_shopping_cart(user: User) -> bytes:
    """Makes shopping cart (byte string) of the user's favorite recipes."""
    ingredients = Ingredient.objects.filter(
        recipe__shopping_carts__owner=user
    ).annotate(
        amount=Sum('recipeingredientmap__amount')
    ).select_related('measurement_unit')

    return make_shopping_cart_pdf_from_ingredients(ingredients=ingredients)


def make_shopping_cart_pdf_from_ingredients(
        ingredients: QuerySet[Ingredient]
) -> bytes:
    """Gets QuerySet of Ingredients and makes shopping cart (byte string)."""
    buff = io.BytesIO()

    doc = SimpleDocTemplate(
        buff, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    story = []

    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 15

    # For cyrillic symbols
    try:
        font_path = os.path.join(settings.FONT_ROOT, 'DejaVuSerif.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path, 'UTF-8'))
    except TTFError:
        logger.error(msg='There is no cyrillic font for pdf constructor')
    else:
        styles['Normal'].fontName = 'DejaVuSerif'
        styles['Heading1'].fontName = 'DejaVuSerif'

    title_style = styles['Heading1']
    title_style.alignment = 1

    text_style = styles['Normal']

    # Document header
    story.append(Paragraph('Список продуктов', title_style))
    story.append(Spacer(1, 12))

    # Shopping List
    for ingredient in ingredients:
        story.append(Paragraph(
            f'{ingredient.name} ({ingredient.measurement_unit}) — '
            f'{ingredient.amount}', text_style, bulletText='•')
        )

    doc.build(story)

    result = buff.getvalue()
    buff.close()
    return result


def add_recipe_to_shopping_cart(
    recipe: Recipe, shopping_cart: ShoppingCart
) -> None:
    """Adds recipe to shopping_cart. Raise BadRequest exception
    if this recipe has already exists in this shopping_cart."""
    if shopping_cart.recipes.filter(pk=recipe.pk).exists():
        raise BadRequest('This recipe has already in shopping cart')
    shopping_cart.recipes.add(recipe)


def remove_recipe_from_shopping_cart(
    recipe: Recipe, shopping_cart: ShoppingCart
) -> None:
    """Removes recipe from shopping_cart. Raise BadRequest exception
    if there is no this recipe in this shopping_cart."""
    if not shopping_cart.recipes.filter(pk=recipe.pk).exists():
        raise BadRequest('There is no this recipe in shopping cart')
    shopping_cart.recipes.remove(recipe)


def add_recipe_to_favorites(recipe: Recipe, user: User) -> None:
    """Adds recipe to user favorites. Raise BadRequest exception
    if this recipe has already exists in user favorites."""
    if user.favourite_recipes.filter(pk=recipe.pk).exists():
        raise BadRequest('This recipe has already in user favorites')
    user.favourite_recipes.add(recipe)


def remove_recipe_from_favorites(recipe: Recipe, user: User) -> None:
    """Removes recipe from user favorites. Raise BadRequest exception
    if there is no this recipe in user favorites."""
    if not user.favourite_recipes.filter(pk=recipe.pk).exists():
        raise BadRequest('There is no this recipe in user favorites')
    user.favourite_recipes.remove(recipe)


def subscribe(following: User, follower: User) -> None:
    """Follower subscribes to following. Raise BadRequest exception
    if this following has already exists in followings or
    if following == follower."""
    if follower.followings.filter(pk=following.pk).exists():
        raise BadRequest('This user has already in followings')
    if follower == following:
        raise BadRequest('Self-subscription is banned')
    follower.followings.add(following)


def unsubscribe(following: User, follower: User) -> None:
    """Follower unsubscribes from following. Raise BadRequest exception
    if there is no this following in followings."""
    if not follower.followings.filter(pk=following.pk).exists():
        raise BadRequest('There is no this user in followings')
    follower.followings.remove(following)


def get_is_subscribed(following: User, follower: User) -> bool:
    """Returns True if User2 (follower) is following User1 (following)."""
    if isinstance(follower, AnonymousUser):
        return False
    return follower.followings.filter(pk=following.pk).exists()
