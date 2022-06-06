from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .fields import CustomReview, CustomTitle
from reviews.models import Category, Comment, Genre, Review, Title, User


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def validate(self, data):
        username = data.get('username')
        if username == 'me':
            raise serializers.ValidationError(
                'Username must not be me'
            )
        return data


class AuthenticationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255, read_only=True)
    username = serializers.CharField(max_length=255)
    confirmation_code = serializers.CharField(max_length=255, write_only=True)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        ]


class UserpostSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        ]

    def validate(self, data):
        role = data.get('role')
        if role is None:
            data['role'] = 'user'
        return data


class UserpatchSerializer(serializers.ModelSerializer):
    role = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        ]


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        exclude = ('id',)
        model = Category


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        exclude = ('id',)
        model = Genre


class TitleReadSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(read_only=True, many=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = '__all__'
        model = Title


class TitleWriteSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field='slug', many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    class Meta:
        fields = '__all__'
        model = Title


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    title = serializers.HiddenField(default=CustomTitle())

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('id', 'author', 'pub_date')
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=['author', 'title']
            )
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    review = serializers.HiddenField(default=CustomReview())

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('id', 'author', 'pub_date')
