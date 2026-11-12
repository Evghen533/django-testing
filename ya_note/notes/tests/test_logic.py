from http import HTTPStatus

import pytest
from pytils.translit import slugify
from pytest_django.asserts import assertRedirects
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note

User = get_user_model()


@pytest.fixture
def author():
    return User.objects.create_user(username='author_user', email='')


@pytest.fixture
def not_author():
    return User.objects.create_user(username='not_author_user', email='')


@pytest.fixture
def form_data():
    # Возвращаем новый словарь при каждом вызове, чтобы не было мутаций
    return {
        'title': 'Тестовая заметка',
        'text': 'Текст заметки',
        'slug': 'test-note',
    }


@pytest.fixture
def note(author):
    return Note.objects.create(
        title='Существующая заметка',
        text='Текст существующей заметки',
        slug='existing-note',
        author=author,
    )


@pytest.fixture
def slug_for_args(note):
    # reverse ожидает кортеж или список для args
    return (note.slug,)


@pytest.fixture
def author_client(author):
    from django.test import Client
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    from django.test import Client
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def client():
    from django.test import Client
    return Client()


def test_user_can_create_note(author_client, author, form_data):
    url = reverse('notes:add')
    response = author_client.post(url, data=form_data)

    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1

    new_note = Note.objects.get()
    assert new_note.title == form_data['title']
    assert new_note.text == form_data['text']
    assert new_note.slug == form_data['slug']
    assert new_note.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    url = reverse('notes:add')
    response = client.post(url, data=form_data)

    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Note.objects.count() == 0


def test_not_unique_slug(author_client, note, form_data):
    url = reverse('notes:add')

    # Создаём локальную копию и меняем slug, не трогая исходную фикстуру
    form_data_with_conflict = {**form_data, 'slug': note.slug}

    response = author_client.post(url, data=form_data_with_conflict)

    form = response.context.get('form')
    assert form is not None
    assert 'slug' in form.errors

    # Заметка не должна быть создана: была 1 (note), стало 1
    assert Note.objects.count() == 1


def test_empty_slug(author_client, form_data):
    url = reverse('notes:add')

    # Копируем, чтобы не мутировать общую фикстуру form_data
    form_data_no_slug = {**form_data}
    if 'slug' in form_data_no_slug:
        del form_data_no_slug['slug']

    response = author_client.post(url, data=form_data_no_slug)

    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1

    new_note = Note.objects.get()
    expected_slug = slugify(form_data['title'])
    assert new_note.slug == expected_slug


def test_author_can_edit_note(author_client, form_data, note):
    url = reverse('notes:edit', args=(note.slug,))
    response = author_client.post(url, data=form_data)

    assertRedirects(response, reverse('notes:success'))

    note.refresh_from_db()
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']


def test_other_user_cant_edit_note(not_author_client, form_data, note):
    assert not_author_client.user != note.author

    url = reverse('notes:edit', args=(note.slug,))
    response = not_author_client.post(url, data=form_data)

    assert response.status_code == HTTPStatus.NOT_FOUND

    note_from_db = Note.objects.get(id=note.id)
    assert note_from_db.title == note.title
    assert note_from_db.text == note.text
    assert note_from_db.slug == note.slug


def test_author_can_delete_note(author_client, slug_for_args):
    url = reverse('notes:delete', args=slug_for_args)
    response = author_client.post(url)

    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 0


def test_other_user_cant_delete_note(not_author_client, slug_for_args):
    url = reverse('notes:delete', args=slug_for_args)
    response = not_author_client.post(url)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Note.objects.count() == 1
