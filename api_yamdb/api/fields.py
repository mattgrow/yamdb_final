from django.http import Http404
from rest_framework import fields

from reviews.models import Review, Title


class CustomTitle(fields.CurrentUserDefault):
    requires_context = True

    def __call__(self, serializer_field):
        view = serializer_field.context.get('view')
        title_id = view.kwargs.get('title_id')
        try:
            title = Title.objects.get(pk=title_id)
        except Title.DoesNotExist:
            raise Http404(
                'Объект не найден. '
                'Проверьте правильность написания PATH PARAMETER: title_id'
            )
        return title


class CustomReview(CustomTitle):
    def __call__(self, serializer_field):
        view = serializer_field.context.get('view')
        title_id = view.kwargs.get('title_id')
        review_id = view.kwargs.get('review_id')
        try:
            Title.objects.get(pk=title_id)
        except Title.DoesNotExist:
            raise Http404(
                'Объект не найден. '
                'Проверьте правильность написания PATH PARAMETER: title_id'
            )
        try:
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            raise Http404(
                'Объект не найден. '
                'Проверьте правильность написания PATH PARAMETER: review_id'
            )
        return review
