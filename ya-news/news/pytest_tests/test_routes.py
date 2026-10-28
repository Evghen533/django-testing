"""Тесты маршрутов и доступности страниц приложения news."""

import pytest
from http import HTTPStatus
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_home_page(client):
    """Главная страница должна возвращать 200 OK.

    Проверка, что маршрут главной страницы корректно обрабатывается
    и возвращает успешный HTTP-ответ.
    """
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_detail_page(client, news):
    """Detail-страница новости должна возвращать 200 OK.

    Убеждаемся, что страница конкретной новости доступна и возвращает
    успешный HTTP-ответ.
    """
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_pages_availability(client, news):
    """Основные страницы приложения должны быть доступны.

    Проверяются несколько ключевых маршрутов (главная, новость,
    вход, регистрация)
    на доступность и возврат статуса 200.
    """
    urls = [
        ('news:home', None),
        ('news:detail', (news.id,)),
        ('users:login', None),
        ('users:signup', None),
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        msg = "Страница {} недоступна".format(name)
        assert response.status_code == HTTPStatus.OK, msg


def test_availability_for_comment_edit_and_delete(
    client, comment, author, reader
):
    """Права доступа на редактирование/удаление работают корректно.

    Для автора комментария ожидается статус 200, для обычного читателя — 404.
    Проверяются оба действия: редактирование и удаление.
    """
    users_statuses = [
        (author, HTTPStatus.OK),
        (reader, HTTPStatus.NOT_FOUND),
    ]
    for user, status in users_statuses:
        client.force_login(user)
        for name in ('news:edit', 'news:delete'):
            url = reverse(name, args=(comment.id,))
            response = client.get(url)
            msg = (
                "Для пользователя {} и действия {} ожидали {}, "
                "но получили {}".format(
                    user.username,
                    name,
                    status,
                    response.status_code,
                )
            )
            assert response.status_code == status, msg


def test_redirect_for_anonymous_client(client, comment):
    """Анонимные пользователи перенаправляются на вход при действиях.

    При попытке доступа к страницам редактирования/удаления без авторизации
    ожидается редирект на страницу входа с корректным next-параметром.
    """
    login_url = reverse('users:login')
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        redirect_url = "{0}?next={1}".format(login_url, url)
        response = client.get(url)
        msg_redirect = "Не было редиректа для {}".format(name)
        assert response.status_code == 302, msg_redirect
        msg_url = "Ожидался редирект на {}, но был на {}".format(
            redirect_url,
            response.url,
        )
        assert response.url == redirect_url, msg_url
