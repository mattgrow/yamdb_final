from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import TokenGenerator, get_access_tokens_for_user
from .filters import TitleFilter
from .mixins import CustomModelViewSet
from .permissions import (HasAccessOrReadOnly, IsAdmin, IsAdminOrReadOnly,
                          IsOwnerOrStaff)
from .serializers import (AuthenticationSerializer, CategorySerializer,
                          CommentSerializer, GenreSerializer,
                          RegistrationSerializer, ReviewSerializer,
                          TitleReadSerializer, TitleWriteSerializer,
                          UserpatchSerializer, UserpostSerializer,
                          UserSerializer)
from api_yamdb.settings import EMAIL_SOURCE
from reviews.models import Category, Comment, Genre, Review, Title, User

account_activation_token = TokenGenerator()


class RegistrationAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        try:
            user = User.objects.get(username=username)
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            user = serializer.save()
            resp = Response(request.data, status=status.HTTP_200_OK)
        confirmation_code = account_activation_token.make_token(user)
        send_mail(
            'Confirmation code',
            confirmation_code,
            EMAIL_SOURCE,
            [email],
        )
        return resp


class AuthenticationAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = AuthenticationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        confirmation_code = serializer.validated_data.get('confirmation_code')
        user = get_object_or_404(User, username=username)
        if user is not None and account_activation_token.check_token(
            user=user, token=confirmation_code
        ):
            token = get_access_tokens_for_user(user)
            return Response({'token': token})
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    lookup_field = 'username'
    permission_classes = (IsAdmin,)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserpostSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsOwnerOrStaff]
    )
    def me(self, request):
        self.kwargs['username'] = request.user.username
        self.get_serializer = UserpatchSerializer
        if request.method == 'GET':
            return self.retrieve(request)
        elif request.method == 'PATCH':
            return self.partial_update(request)
        else:
            raise Exception('Not implemented')


class CategoryViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = Category.objects.all()
    pagination_class = PageNumberPagination
    lookup_field = 'slug'
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = [SearchFilter]
    search_fields = ('name',)


class GenreViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin,
    mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = Genre.objects.all()
    pagination_class = PageNumberPagination
    lookup_field = 'slug'
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = [SearchFilter]
    search_fields = ['=name', ]


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg('reviews__score'))
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    pagination_class = PageNumberPagination
    permission_classes = (IsAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(CustomModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (HasAccessOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        get_object_or_404(Title, pk=title_id)
        new_queryset = Review.objects.filter(title=title_id)
        return new_queryset


class CommentViewSet(CustomModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (HasAccessOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        if not title_id or not review_id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        new_queryset = Comment.objects.filter(review=review_id)
        return new_queryset
