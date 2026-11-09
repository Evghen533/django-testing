from http import HTTPStatus

import pytest
from django.urls import reverse

from news.models import Comment

LOGIN_URL = reverse('users:login')


@pytest.mark.django_db
def test_anonymous_cannot_create_comment(client, news, form_data):
    """Аноним не может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    initial_count = Comment.objects.count()
    response = client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{LOGIN_URL}?next={url}'
    assert Comment.objects.count() == initial_count


@pytest.mark.django_db
def test_authorized_user_can_create_comment(author_client, news, form_data):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author is not None


@pytest.mark.django_db
def test_comment_with_bad_words_not_published(
    author_client, news, bad_words_data
):
    """Комментарий со стоп-словами не публикуется, форма возвращает ошибку."""
    url = reverse('news:detail', args=(news.id,))
    initial_count = Comment.objects.count()
    response = author_client.post(url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    assert 'text' in response.context['form'].errors
    assert Comment.objects.count() == initial_count


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['news:edit', 'news:delete'])
def test_author_can_edit_and_delete_own_comment(author_client, comment, name):
    """Автор может редактировать и удалять свои комментарии."""
    url = reverse(name, args=(comment.id,))
    form_data = {'text': 'Обновлённый текст комментария'}
    response = author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    if name == 'news:edit':
        comment.refresh_from_db()
        assert comment.text == form_data['text']
    else:
        assert not Comment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['news:edit', 'news:delete'])
def test_other_user_cannot_edit_or_delete_foreign_comment(
    reader_client, comment, name
):
    """Чужой комментарий нельзя редактировать или удалить."""
    url = reverse(name, args=(comment.id,))
    original_text = comment.text
    response = reader_client.post(url, data={'text': 'Попытка подмены'})
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_text
