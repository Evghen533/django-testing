"""Тесты маршрутов и доступности страниц приложения notes."""

import pytest
from http import HTTPStatus
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture as lf
from pytest_django.asserts import assertRedirects
from notes.models import Note


@pytest.mark.django_db
def test_home_availability_for_anonymous_user(client):
    """Главная страница доступна анонимному пользователю (статус 200)."""
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:home', 'users:login', 'users:signup')
)
@pytest.mark.django_db
def test_pages_availability_for_anonymous_user(client, name):
    """Базовые страницы доступны анонимному пользователю."""
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_logout_availability_for_anonymous_user(client):
    """POST на logout от анонимного пользователя не должен вызывать ошибку."""
    url = reverse('users:logout')
    response = client.post(url)
    # Обычно Django редиректит или отдаёт 200; главное — не 500.
    assert response.status_code in (HTTPStatus.FOUND, HTTPStatus.OK)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(not_author_client, name):
    """Страницы list, add, success доступны авторизованному пользователю."""
    url = reverse(name)
    response = not_author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_note_exists(note):
    """Фикстура note создаёт одну заметку с ожидаемым заголовком."""
    assert Note.objects.count() == 1
    assert note.title == 'Заголовок заметки'


@pytest.mark.django_db
def test_empty_db():
    """В чистой БД заметок нет (если фикстуры не применялись)."""
    assert Note.objects.count() == 0


@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete')
)
def test_pages_availability_for_author(author_client, name, note):
    """Автор заметки может получить detail/edit/delete (статус 200)."""
    url = reverse(name, args=(note.slug,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    [
        (lf('not_author_client'), HTTPStatus.NOT_FOUND),
        (lf('author_client'), HTTPStatus.OK),
    ]
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
@pytest.mark.django_db
def test_pages_availability_for_different_users(
    parametrized_client,
    name,
    note,
    expected_status,
):
    """Доступ к detail/edit/delete различается для автора и не-автора."""
    url = reverse(name, args=(note.slug,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, note_object',
    (
        ('notes:detail', lf('note')),
        ('notes:edit', lf('note')),
        ('notes:delete', lf('note')),
    ),
)
def test_redirects_for_anonymous(client, name, note_object):
    """Анонимные пользователи редиректятся на login для защищённых страниц."""
    login_url = reverse('users:login')
    args = (note_object.slug,) if note_object else None
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:list', None),
        ('notes:success', None),
    ),
)
def test_public_pages_available_for_anonymous(client, name, args):
    """Публичные страницы должны отдавать 200 для анонима."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == 200
