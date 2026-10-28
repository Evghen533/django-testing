import pytest
from django.urls import reverse
from notes.models import Note
from notes.forms import WARNING

pytestmark = pytest.mark.django_db


def test_anonymous_cannot_create_note(client):
    data = {'title': 'Test', 'text': 'Text'}
    url = reverse('notes:add')
    response = client.post(url, data)
    assert response.status_code == 302
    assert '/auth/login/' in response.url


def test_author_can_create_note(client, author):
    client.force_login(author)
    data = {'title': 'My note', 'text': 'Content'}
    url = reverse('notes:add')
    response = client.post(url, data)
    assert response.status_code == 302
    # Проверяем, что редирект ведёт на success
    assert reverse('notes:success') in response.url
    assert Note.objects.filter(title='My note').exists()


def test_author_can_edit_own_note(client, author, note):
    client.force_login(author)
    new_text = 'Updated content'
    url = reverse('notes:edit', args=[note.slug])
    response = client.post(url, {'title': note.title, 'text': new_text})
    assert response.status_code == 302
    note.refresh_from_db()
    assert note.text == new_text


def test_other_user_cannot_edit_foreign_note(client, note, other_user):
    client.force_login(other_user)
    url = reverse('notes:edit', args=[note.slug])
    response = client.post(url, {'title': note.title, 'text': 'No way'})
    assert response.status_code == 404
    note.refresh_from_db()
    assert note.text != 'No way'


def test_empty_title_validation(client, author):
    client.force_login(author)
    data = {'title': '', 'text': 'Some text'}
    url = reverse('notes:add')
    response = client.post(url, data)
    assert response.status_code == 200
    assert 'form' in response.context
    assert 'title' in response.context['form'].errors


def test_slug_uniqueness_validation(client, author, note):
    """
    Проверяем, что нельзя создать заметку с существующим slug.
    Используем WARNING из forms.py.
    """
    client.force_login(author)
    # Берём slug существующей заметки
    duplicate_slug = note.slug
    data = {
        'title': 'Another note',
        'text': 'Some text',
        'slug': duplicate_slug,
    }
    url = reverse('notes:add')
    response = client.post(url, data)

    assert response.status_code == 200
    assert 'form' in response.context
    errors = response.context['form'].errors.get('slug', [])
    # В ошибке должно быть наше сообщение WARNING
    assert WARNING in str(errors)
