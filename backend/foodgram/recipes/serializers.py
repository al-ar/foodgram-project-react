from rest_framework import serializers

from users.serializers import UserSerializer

from .fields import Base64ImageField
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)

MIN_AMOUNT = 1
MAX_AMOUNT = 32000


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(source='ingredient_to_recipe',
                                               many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, recipe):
        current_user = self.context['request'].user
        return (
            self.context['request'].user.is_authenticated
            and Favorite.objects.filter(recipe=recipe,
                                        user=current_user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        current_user = self.context['request'].user
        return (
            self.context['request'].user.is_authenticated
            and ShoppingCart.objects.filter(recipe=recipe,
                                            user=current_user).exists()
        )


class IngredientToCreateRecipeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), required=True
    )
    amount = serializers.IntegerField(required=True)
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if not MIN_AMOUNT < value < MAX_AMOUNT:
            raise serializers.ValidationError(
                f'Количество ингредиентов должно быть >{MIN_AMOUNT}'
                f'и <{MAX_AMOUNT}'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientToCreateRecipeSerializer(
        source='ingredient_to_recipe', many=True
    )
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, recipe):
        current_user = self.context['request'].user
        return Favorite.objects.filter(recipe=recipe,
                                       user=current_user).exists()

    def get_is_in_shopping_cart(self, recipe):
        current_user = self.context['request'].user
        return ShoppingCart.objects.filter(recipe=recipe,
                                           user=current_user).exists()

    def create_ingredients(self, ingredients, recipe):
        bulk_list = list()
        for ingredient in ingredients:
            current_ingredient = ingredient['id']
            if IngredientInRecipe.objects.filter(
                ingredient=current_ingredient,
                recipe=recipe,
            ).exists():
                raise serializers.ValidationError(
                    'Убедитесь, что отсутствуют повторяющиеся ингредиенты'
                )
            bulk_list.append(
                IngredientInRecipe(
                    ingredient=current_ingredient,
                    recipe=recipe,
                    amount=ingredient['amount'])
            )
        IngredientInRecipe.objects.bulk_create(bulk_list)

    def create(self, validated_data):
        author = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient_to_recipe')
        recipe = Recipe.objects.create(**validated_data, author=author)
        for tag in tags:
            recipe.tags.add(tag)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        if 'ingredient_to_recipe' in validated_data:
            ingredients = validated_data.pop('ingredient_to_recipe')
            recipe.ingredients.clear()
            self.create_ingredients(ingredients, recipe)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ShoppingListSerializer(serializers.ModelSerializer):
    ingredient = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('ingredient',)

    def get_ingredient(self, recipe):
        ingredient = recipe.ingredients.all()
        return IngredientSerializer(ingredient, many=True).data
