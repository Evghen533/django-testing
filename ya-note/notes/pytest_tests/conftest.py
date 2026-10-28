"""Фикстуры для тестов приложения notes."""

import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


@pytest.fixture
def author(django_user_model):
    """Создаёт и возвращает пользователя-автора заметки."""
    return django_user_model.objects.create_user(
        username='Автор',
        password='password',
    )


@pytest.fixture
def not_author(django_user_model):
    """Создаёт и возвращает пользователя, не являющегося автором."""
    return django_user_model.objects.create_user(
        username='Не автор',
        password='password',
    )


@pytest.fixture
def author_client(client, author):
    """Клиент с авторизованным пользователем-автором."""
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(client, not_author):
    """Клиент с авторизованным пользователем, не являющимся автором."""
    client.force_login(not_author)
    return client


@pytest.fixture
def note(author):
    """Одна заметка для базовых тестов."""
    return Note.objects.create(
        title='Заголовок заметки',
        text='Текст заметки',
        slug='note-slug',
        author=author,
    )


@pytest.fixture
def slug_for_args(note):
    """Кортеж со slug заметки для удобной передачи в args reverse()."""
    return (note.slug,)


@pytest.fixture
def many_notes(author):
    """Много заметок для проверки лимита и сортировки на странице списка."""
    base_time = timezone.now()
    count = 15
    notes_list = [
        Note(
            title=f'Заметка {i}',
            text='Просто текст для теста.',
            slug=f'note-slug-{i}',
            author=author,
            created_at=base_time - timedelta(days=i),
        )
        for i in range(count)
    ]
    return Note.objects.bulk_create(notes_list)


@pytest.fixture
def single_note(author):
    """Отдельная заметка для detail-страницы (независимо от note)."""
    return Note.objects.create(
        title='Тестовая заметка для detail',
        text='Текст для проверки detail-страницы.',
        slug='test-detail-slug',
        author=author,
    )


@pytest.fixture
def form_data():
    """Данные формы для создания/редактирования заметки."""
    return {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug',
    }
