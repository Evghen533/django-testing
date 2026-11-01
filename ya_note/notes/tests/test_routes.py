import pytest
from django.urls import reverse
from http import HTTPStatus
from notes.models import Note
from django.db.models.query import QuerySet


@pytest.fixture
def author(db):
    """Фикстура для создания автора заметки."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username='author', password='123')


@pytest.fixture
def other_user(db):
    """Фикстура для создания другого пользователя (для проверки прав)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username='other', password='123')


@pytest.fixture
def note(author):
    """Фикстура для создания заметки."""
    return Note.objects.create(
        title='Test Note',
        slug='test-note',
        text='text',
        author=author
    )


@pytest.mark.django_db
def test_home_availability_for_anonymous(client):
    """Главная страница доступна анонимному пользователю."""
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_basic_public_pages_availability(client):
    """Публичные страницы доступны анонимусу."""
    login_url = reverse('users:login')
    signup_url = reverse('users:signup')
    home_url = reverse('notes:home')

    public_urls = [home_url, login_url, signup_url]

    for url in public_urls:
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_logout_behavior(client, author):
    """Проверка работы страницы выхода (обычно это POST с редиректом)."""
    client.force_login(author)
    url = reverse('users:logout')
    response = client.post(url)

    assert response.status_code in (HTTPStatus.FOUND, HTTPStatus.OK)


@pytest.mark.django_db
def test_protected_pages_available_for_author(client, author):
    """Автор видит страницы списка, добавления и успеха."""
    client.force_login(author)

    list_url = reverse('notes:list')
    add_url = reverse('notes:add')
    success_url = reverse('notes:success')

    protected_urls = [list_url, add_url, success_url]

    for url in protected_urls:
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_author_access_to_own_note_actions(client, note):
    """Автор может работать со своей заметкой (просмотр, редактирование, удаление)."""
    client.force_login(note.author)

    detail_url = reverse('notes:detail', args=(note.slug,))
    edit_url = reverse('notes:edit', args=(note.slug,))
    delete_url = reverse('notes:delete', args=(note.slug,))

    actions_urls = [detail_url, edit_url, delete_url]

    for url in actions_urls:
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_other_user_gets_404_on_foreign_note(client, note, other_user):
    """Чужой пользователь получает 404 на чужую заметку."""
    client.force_login(other_user)

    detail_url = reverse('notes:detail', args=(note.slug,))
    edit_url = reverse('notes:edit', args=(note.slug,))
    delete_url = reverse('notes:delete', args=(note.slug,))

    restricted_urls = [detail_url, edit_url, delete_url]

    for url in restricted_urls:
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_anonymous_redirect_on_protected_pages(client):
    """Аноним редиректится на страницу входа при попытке доступа к защищенным страницам."""
    add_url = reverse('notes:add')
    login_url = reverse('users:login')
    protected_urls = [add_url]

    for url in protected_urls:
        response = client.get(url, follow=True)
        assert response.status_code in (200, 302)

        redirected_to_login = any(
            r['location'].endswith(login_url)
            for r in response.redirect_chain
        )

        on_login_page = (
            response.request['PATH_INFO']
            .endswith(login_url.lstrip('/'))
        )

        assert (
            redirected_to_login or on_login_page
        ), f"Аноним не был редиректнут на login при доступе к {url}"


@pytest.mark.django_db
def test_list_page_contains_object_list(client, author):
    """В контексте списка заметок есть object_list (QuerySet или список)."""
    Note.objects.create(
        title='Test note',
        slug='test-note-2',
        text='Text',
        author=author,
    )

    client.force_login(author)
    url = reverse('notes:list')
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'object_list' in response.context

    object_list = response.context['object_list']
    assert isinstance(object_list, (list, QuerySet))
    assert len(object_list) >= 1
    assert any(n.title == 'Test note' for n in object_list)
