# notes/pytest_tests/test_content.py
import pytest

from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_notes_list_limit(client, many_notes):
    """На странице списка должно отображаться ровно NOTES_PER_PAGE заметок."""
    url = reverse('notes:list')
    response = client.get(url)
    assert response.status_code == 200
    object_list = response.context['object_list']
    limit = getattr(settings, 'NOTES_PER_PAGE', 10)  # подставь своё значение, если нет в settings
    assert len(object_list) == limit


@pytest.mark.django_db
def test_notes_order_on_list(client, many_notes):
    """Заметки должны идти по убыванию created_at (новые сверху)."""
    url = reverse('notes:list')
    response = client.get(url)
    assert response.status_code == 200
    object_list = response.context['object_list']
    dates = [n.created_at for n in object_list]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'parametrized_client, note_in_list',
    (
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('not_author_client'), False),
    )
)
def test_notes_list_for_different_users(note, parametrized_client, note_in_list):
    url = reverse('notes:list')
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    assert (note in object_list) is note_in_list


@pytest.mark.django_db
def test_detail_page_shows_correct_note_data(client, single_note):
    """Detail-страница должна отображать корректные title, text и slug заметки."""
    url = reverse('notes:detail', args=(single_note.slug,))
    response = client.get(url)
    assert response.status_code == 200

    note_obj = response.context.get('note') or response.context.get('object')
    # Если в DetailView контекстная переменная называется иначе — поправь эту строку.
    assert note_obj is not None
    assert note_obj.title == single_note.title
    assert note_obj.text == single_note.text
    assert note_obj.slug == single_note.slug
    assert note_obj.author.username == single_note.author.username


@pytest.mark.django_db
def test_create_note_page_contains_form(author_client):
    url = reverse('notes:add')
    response = author_client.get(url)
    assert 'form' in response.context
    from notes.forms import NoteForm
    assert isinstance(response.context['form'], NoteForm)


@pytest.mark.django_db
def test_edit_note_page_contains_form(slug_for_args, author_client):
    url = reverse('notes:edit', args=slug_for_args)
    response = author_client.get(url)
    assert 'form' in response.context
    from notes.forms import NoteForm
    assert isinstance(response.context['form'], NoteForm)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),
        ('notes:edit', pytest.lazy_fixture('slug_for_args'))
    )
)
def test_pages_contain_form(author_client, name, args):
    url = reverse(name, args=args)
    response = author_client.get(url)
    assert 'form' in response.context
    from notes.forms import NoteForm
    assert isinstance(response.context['form'], NoteForm)
