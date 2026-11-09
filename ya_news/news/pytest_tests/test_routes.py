from http import HTTPStatus

import pytest
from django.urls import reverse

LOGIN_URL = reverse('users:login')
SIGNUP_URL = reverse('users:signup')
LOGOUT_URL = reverse('users:logout')


@pytest.mark.django_db
def test_home_page_available_to_anonymous(client):
    response = client.get(reverse('news:home'))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_detail_page_available_to_anonymous(client, news):
    response = client.get(reverse('news:detail', args=(news.id,)))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_auth_pages_available_to_anonymous(client):
    """Страницы регистрации и входа доступны анонимам."""
    for url in (SIGNUP_URL, LOGIN_URL):
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_logout_available_to_anonymous(client):
    """Страница выхода доступна анонимам."""
    response = client.post(LOGOUT_URL)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['news:edit', 'news:delete'])
def test_comment_pages_available_to_author(client, comment, name):
    """Страницы правки и удаления доступны автору комментария."""
    client.force_login(comment.author)
    response = client.get(reverse(name, args=(comment.id,)))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['news:edit', 'news:delete'])
def test_comment_pages_not_available_to_other_user(
    client, comment, reader, name
):
    """Чужому пользователю правка и удаления дают 404."""
    client.force_login(reader)
    response = client.get(reverse(name, args=(comment.id,)))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize('name', ['news:edit', 'news:delete'])
def test_anonymous_redirects_to_login(client, comment, name):
    """Аноним с защищённых страниц уходит на логин."""
    url = reverse(name, args=(comment.id,))
    expected = f'{LOGIN_URL}?next={url}'
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == expected
