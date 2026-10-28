import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create_user(
        username='Автор',
        password='password'
    )


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create_user(
        username='Не автор',
        password='password'
    )


@pytest.fixture
def author_client(client, author):
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(client, not_author):
    client.force_login(not_author)
    return client


@pytest.fixture
def note(author):
    return Note.objects.create(
        title='Заголовок заметки',
        text='Текст заметки',
        slug='note-slug',
        author=author,
    )


@pytest.fixture
def slug_for_args(note):
    return (note.slug,)


@pytest.fixture
def many_notes(author):
    base_time = timezone.now()
    count = 15
    notes_list = [
        Note(
            title=f'Заметка {i}',
            text='Просто текст для теста.',
            slug=f'note-slug-{i}',
            author=author,
            created_at=base_time - timedelta(days=i)
        )
        for i in range(count)
    ]
    return Note.objects.bulk_create(notes_list)


@pytest.fixture
def single_note(author):
    return Note.objects.create(
        title='Тестовая заметка для detail',
        text='Текст для проверки detail-страницы.',
        slug='test-detail-slug',
        author=author
    )


@pytest.fixture
def form_data():
    return {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }
