import pytest
from http import HTTPStatus

from pytest_django.asserts import assertRedirects
from pytest_lazyfixture import lazy_fixture as lf
from notes.models import Note
from django.urls import reverse


def test_home_availability_for_anonymous_user(client):
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:home', 'users:login', 'users:signup'),
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
    ('notes:list', 'notes:add', 'notes:success'),
)
def test_pages_availability_for_author(author_client, name):
    url = reverse(name)
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_note_exists(note):
    notes_count = Note.objects.count()
    assert notes_count == 1
    assert note.title == 'Заголовок'


@pytest.mark.django_db
def test_empty_db():
    notes_count = Note.objects.count()
    assert notes_count == 0


@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
def test_pages_availability_for_author(author_client, name, note):
    url = reverse(name, args=(note.slug,))
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    [
        (lf('not_author_client'), HTTPStatus.NOT_FOUND),
        (lf('author_client'), HTTPStatus.OK),
    ],
)
def test_pages_availability_for_different_users(
    parametrized_client,
    name,
    note,
    expected_status,
):
    url = reverse(name, args=(note.slug,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args_value',
    (
        ('notes:detail', True),
        ('notes:edit', True),
        ('notes:delete', True),
        ('notes:add', False),
        ('notes:success', False),
        ('notes:list', False),
    ),
)
def test_redirects(client, name, args_value, note):
    if args_value:
        args = (note.slug,)
    else:
        args = None

    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
