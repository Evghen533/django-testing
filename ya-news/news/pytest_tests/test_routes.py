import pytest
from http import HTTPStatus
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_home_page(client):
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_detail_page(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_pages_availability(client, news):
    urls = [
        ('news:home', None),
        ('news:detail', (news.id,)),
        ('users:login', None),
        ('users:signup', None),
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, (
            f"Страница {name} недоступна"
        )


def test_availability_for_comment_edit_and_delete(
        client,
        comment,
        author,
        reader
    ):
    users_statuses = [
        (author, HTTPStatus.OK),
        (reader, HTTPStatus.NOT_FOUND),
    ]
    for user, status in users_statuses:
        client.force_login(user)
        for name in ('news:edit', 'news:delete'):
            url = reverse(name, args=(comment.id,))
            response = client.get(url)
            assert response.status_code == status, (
                f"Для пользователя {user.username} и действия {name} "
                f"ожидали {status}, но получили {response.status_code}"
            )


def test_redirect_for_anonymous_client(client, comment):
    login_url = reverse('users:login')
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        redirect_url = f'{login_url}?next={url}'
        response = client.get(url)
        assert response.status_code == 302, f"Не было редиректа для {name}"
        assert response.url == redirect_url, (
            f"Ожидался редирект на {redirect_url}, но был на {response.url}"
        )
