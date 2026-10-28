# test_routes.py
import pytest
from http import HTTPStatus
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture as lf
from pytest_django.asserts import assertRedirects
from notes.models import Note


def test_home_availability_for_anonymous_user(client):
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:home', 'users:login', 'users:signup')
)
def test_pages_availability_for_anonymous_user(client, name):
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_logout_availability_for_anonymous_user(client):
    url = reverse('users:logout')
    response = client.post(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(not_author_client, name):
    url = reverse(name)
    response = not_author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_note_exists(note):
    assert Note.objects.count() == 1
    assert note.title == 'Заголовок'


@pytest.mark.django_db
def test_empty_db():
    assert Note.objects.count() == 0


@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete')
)
def test_pages_availability_for_author(author_client, name, note):
    url = reverse(name, args=(note.slug,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    [
        (lf('not_author_client'), HTTPStatus.NOT_FOUND),
        (lf('author_client'), HTTPStatus.OK)
    ]
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete')
)
def test_pages_availability_for_different_users(
    parametrized_client, name, note, expected_status
):
    url = reverse(name, args=(note.slug,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


def test_logout_availability_for_anonymous_user(client):
    url = reverse('users:logout') # Получаем ссылку на страницу выхода.
    response = client.post(url) # Выполняем POST-запрос.
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name, note_object',
    (
        ('notes:detail', lf('note')),
        ('notes:edit', lf('note')),
        ('notes:delete', lf('note')),
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    )
)
def test_redirects_for_anonymous(client, name, note_object):
    login_url = reverse('users:login')
    url = reverse(name, args=(note_object.slug,) if note_object else None)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
