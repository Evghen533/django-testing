import pytest
from http import HTTPStatus
from django.urls import reverse
from news.models import News, Comment
from news.forms import BAD_WORDS, WARNING


@pytest.fixture
def news():
    """Одна тестовая новость."""
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username='Мимо Крокодил', password='pass')


@pytest.fixture
def auth_client(user, client):
    client.force_login(user)
    return client


@pytest.fixture
def comment(news, user):
    """Комментарий, принадлежащий пользователю."""
    return Comment.objects.create(
        news=news,
        author=user,
        text='Текст комментария'
    )


@pytest.fixture
def reader():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username='Читатель', password='pass')


@pytest.fixture
def reader_client(reader, client):
    client.force_login(reader)
    return client


@pytest.mark.django_db
def test_anonymous_cannot_create_comment(client, news):
    """Анонимный пользователь не может создать комментарий."""
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': 'Текст комментария'}
    response = client.post(url, data=form_data)

    assert response.status_code in (301, 302)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_authorized_user_can_create_comment(auth_client, news, user):
    """Авторизованный пользователь может создать комментарий к новости."""
    url = reverse('news:detail', args=(news.id,))
    comment_text = 'Текст комментария'
    form_data = {'text': comment_text}

    response = auth_client.post(url, data=form_data)

    expected_redirect = f'{url}#comments'
    assert response.status_code in (301, 302)
    assert response.url == expected_redirect

    comments = Comment.objects.all()
    assert comments.count() == 1
    comment = comments.first()
    assert comment.text == comment_text
    assert comment.news == news
    assert comment.author == user


@pytest.mark.django_db
def test_comment_validation_bad_words(auth_client, news):
    """Форма отклоняет комментарий с запрещёнными словами."""
    url = reverse('news:detail', args=(news.id,))
    bad_text = f'Какой-то текст, {BAD_WORDS[0]}, еще текст'
    form_data = {'text': bad_text}

    response = auth_client.post(url, data=form_data)
    assert response.status_code == 200

    form = response.context.get('form')
    assert form is not None
    assert 'text' in form.errors
    assert WARNING in form.errors['text']

    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_delete_comment(auth_client, comment, news):
    """Автор может удалить свой комментарий (DELETE-запрос)."""
    url = reverse('news:delete', args=(comment.id,))
    expected_redirect = f"{reverse('news:detail', args=(news.id,))}#comments"

    response = auth_client.delete(url)
    assert response.status_code in (301, 302)
    assert response.url == expected_redirect
    assert not Comment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_other_user_cannot_delete_comment(reader_client, comment):
    """Другой пользователь не может удалить чужой комментарий — 404."""
    url = reverse('news:delete', args=(comment.id,))

    response = reader_client.delete(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_author_can_edit_comment(auth_client, comment, news):
    """Автор может отредактировать свой комментарий (POST)."""
    url = reverse('news:edit', args=(comment.id,))
    new_text = 'Обновлённый комментарий'
    form_data = {'text': new_text}
    expected_redirect = f"{reverse('news:detail', args=(news.id,))}#comments"

    response = auth_client.post(url, data=form_data)
    assert response.status_code in (301, 302)
    assert response.url == expected_redirect

    comment.refresh_from_db()
    assert comment.text == new_text


@pytest.mark.django_db
def test_other_user_cannot_edit_comment(reader_client, comment):
    url = reverse('news:edit', args=(comment.id,))
    new_text = 'Попытка подмены'
    form_data = {'text': new_text}

    response = reader_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment.refresh_from_db()
    assert comment.text == 'Комментарий к новости'
