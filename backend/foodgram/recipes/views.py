import io

from django.db.models import F, Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import filters, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .filters import IngredientSearchFilter, RecipeFilter
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)
from .pagination import LimitPageNumberPagination
from .permissions import OwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, TagSerializer)
from .utils import delete, post

FONT_SIZE_HEADER = 24
POSITION_X = 150
POSITION_Y = 800
FONT_SIZE = 16
FROM_BOTTOM = 750
MIN_BOTTOM = 50
FROM_LEFT = 50
LINE_SPACING = 20


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ['get']


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None
    http_method_names = ['get']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter
    filterset_fields = ('tags', 'author')
    ordering_fields = ('id',)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RecipeCreateSerializer
        return RecipeSerializer


class FavoriteView(APIView):
    def delete(self, request, recipe_id):
        return delete(request, recipe_id, Favorite)

    def post(self, request, recipe_id):
        return post(request, recipe_id, Favorite)


class ShoppingCardView(APIView):
    def get(self, request):
        user = request.user
        shopping_list = (
            IngredientInRecipe.objects.filter(recipe__shopping_cart__user=user)
            .values(name=F('ingredient__name'),
                    unit=F('ingredient__measurement_unit'))
            .annotate(amount=Sum('amount'))
        )
        font = 'ComforterBrush-Regular'
        pdfmetrics.registerFont(TTFont('ComforterBrush-Regular',
                                       'ComforterBrush-Regular.ttf',
                                       'UTF-8'))
        buffer = io.BytesIO()
        pdf_file = canvas.Canvas(buffer)
        pdf_file.setFont(font, FONT_SIZE_HEADER)
        pdf_file.drawString(POSITION_X, POSITION_Y, 'Список покупок.')
        pdf_file.setFont(font, FONT_SIZE)
        from_bottom = FROM_BOTTOM
        for number, ingredient in enumerate(shopping_list, start=1):
            pdf_file.drawString(
                FROM_LEFT,
                from_bottom,
                f'{number}.  {ingredient["name"]} - {ingredient["amount"]} '
                f'{ingredient["unit"]}',
            )
            from_bottom -= LINE_SPACING
            if from_bottom <= MIN_BOTTOM:
                from_bottom = MIN_BOTTOM + FROM_BOTTOM
                pdf_file.showPage()
                pdf_file.setFont(font, FONT_SIZE)
        pdf_file.showPage()
        pdf_file.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='shopping_list.pdf')

    def delete(self, request, recipe_id):
        return delete(request, recipe_id, ShoppingCart)

    def post(self, request, recipe_id):
        return post(request, recipe_id, ShoppingCart)
