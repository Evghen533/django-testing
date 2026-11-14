import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse

from news.models import Comment

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_anonymous_user_cant_create_comment(client, news):
    """Анонимный пользователь не может оставить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': 'Текст комментария'}

    response = client.post(url, data=form_data)

    assert Comment.objects.count() == 0
    assert response.status_code == 302


def test_user_can_create_comment(author, author_client, news):
    """Авторизованный пользователь может оставить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': 'Текст комментария'}

    initial_count = Comment.objects.count()

    response = author_client.post(url, data=form_data)

    assert response.status_code == 302
    assert Comment.objects.count() == initial_count + 1

    comment = Comment.objects.order_by('-created').first()
    assert comment is not None
    assert comment.text == 'Текст комментария'
    assert comment.news == news
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, news, bad_words_data):
    """Пользователь не может использовать запрещённые слова в комментарии."""
    url = reverse('news:detail', args=(news.id,))

    response = author_client.post(url, data=bad_words_data)

    assert response.status_code == 200

    form = response.context.get('form')
    assert form is not None
    assert 'text' in form.errors

    assert Comment.objects.count() == 0


def test_author_can_delete_comment(author_client, comment):
    """Автор может удалить свой комментарий."""
    url = reverse('news:delete', args=(comment.pk,))
    detail_url = reverse('news:detail', args=(comment.news.id,))

    response = author_client.delete(url)

    assert response.status_code == 302
    assert response.url.startswith(detail_url)
    assert not Comment.objects.filter(pk=comment.pk).exists()


def test_user_cant_delete_comment_of_another_user(reader_client, comment):
    """Читатель не может удалить комментарий автора."""
    url = reverse('news:delete', args=(comment.pk,))

    response = reader_client.delete(url)

    assert response.status_code in (404, 403)
    assert Comment.objects.filter(pk=comment.pk).exists()


def test_author_can_edit_comment(author_client, comment):
    """Автор может редактировать свой комментарий."""
    url = reverse('news:edit', args=(comment.pk,))
    new_text = 'Обновлённый комментарий'
    form_data = {'text': new_text}

    response = author_client.post(url, data=form_data)

    assert response.status_code == 302

    comment.refresh_from_db()
    assert comment.text == new_text


def test_user_cant_edit_comment_of_another_user(reader_client, comment):
    """Читатель не может редактировать комментарий автора."""
    url = reverse('news:edit', args=(comment.pk,))
    new_text = 'Попытка взлома'
    form_data = {'text': new_text}

    response = reader_client.post(url, data=form_data)

    assert response.status_code in (404, 403)

    comment.refresh_from_db()
    assert comment.text != new_text
