import pytest
from http import HTTPStatus
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_home_page(client):
    """Главная страница должна возвращать 200 OK."""
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_detail_page(client, news):
    """Detail-страница новости должна возвращать 200 OK."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_public_pages_availability(client):
    """Публичные страницы (главная, вход, регистрация) должны быть доступны."""
    urls = [
        ('news:home', None),
        ('users:login', None),
        ('users:signup', None),
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, f"{name} недоступна"


def test_comment_edit_delete_permissions(client, comment, author, reader):
    """
    Проверка прав доступа к редактированию и удалению комментария.

    Автор: 200 OK (доступ к форме).
    Другой пользователь: 403 Forbidden (ресурс существует, но нет прав).
    """
    actions = [
        ('news:edit', comment.id),
        ('news:delete', comment.id),
    ]

    client.force_login(author)
    for name, obj_id in actions:
        url = reverse(name, args=(obj_id,))
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK

    client.force_login(reader)
    for name, obj_id in actions:
        url = reverse(name, args=(obj_id,))
        response = client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN


def test_redirect_for_anonymous_on_protected_pages(client, comment):
    """
    Анонимные пользователи перенаправляются на страницу входа."""
    login_url = reverse('users:login')
    actions = [
        ('news:edit', comment.id),
        ('news:delete', comment.id),
    ]

    for name, obj_id in actions:
        url = reverse(name, args=(obj_id,))
        expected_redirect = f"{login_url}?next={url}"

        response = client.get(url)

        assert response.status_code == HTTPStatus.FOUND
        assert response.has_header('Location')
        assert response.url == expected_redirect
