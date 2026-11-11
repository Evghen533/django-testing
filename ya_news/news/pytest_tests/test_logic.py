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
def test_authorized_user_can_create_comment(author_client, detail_url, form_data):
    """Авторизованный пользователь может отправить комментарий."""
    initial_count = Comment.objects.count()
    initial_pk = Comment.objects.order_by('pk').last().pk if initial_count else 0

    response = author_client.post(detail_url, data=form_data)

    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.count() == initial_count + 1

    # Берём последнюю созданную запись, а не произвольную по фильтру
    comment = Comment.objects.order_by('pk').last()
    assert comment.pk > initial_pk
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author_client.user


@pytest.mark.django_db
def test_comment_with_bad_words_not_published(
    author_client,
    news,
    bad_words_data
):
    """Комментарий со стоп-словами не публикуется, форма возвращает ошибку."""
    url = reverse('news:detail', args=(news.id,))
    initial_count = Comment.objects.count()

    response = author_client.post(url, data=bad_words_data)

    assert response.status_code == HTTPStatus.OK
    assert 'text' in response.context['form'].errors
    assert Comment.objects.count() == initial_count


@pytest.mark.django_db
def test_author_can_edit_own_comment(author_client, comment):
    """Автор может редактировать свой комментарий."""
    url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': 'Обновлённый текст комментария'}

    response = author_client.post(url, data=form_data)

    assert response.status_code == HTTPStatus.FOUND
    comment.refresh_from_db()
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_author_can_delete_own_comment(author_client, comment):
    """Автор может удалить свой комментарий."""
    url = reverse('news:delete', args=(comment.id,))

    response = author_client.post(url)

    assert response.status_code == HTTPStatus.FOUND
    assert not Comment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_other_user_cannot_edit_foreign_comment(reader_client, comment):
    """Чужой комментарий нельзя редактировать."""
    url = reverse('news:edit', args=(comment.id,))
    original_text = comment.text

    response = reader_client.post(url, data={'text': 'Попытка подмены'})

    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_text


@pytest.mark.django_db
def test_other_user_cannot_delete_foreign_comment(reader_client, comment):
    """Чужой комментарий нельзя удалить."""
    url = reverse('news:delete', args=(comment.id,))

    response = reader_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.filter(pk=comment.pk).exists()
