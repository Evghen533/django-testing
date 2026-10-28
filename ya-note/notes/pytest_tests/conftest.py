# notes/pytest_tests/conftest.py
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from news.models import News, Comment

from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create_user(username='Автор', password='password')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create_user(username='Не автор', password='password')


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
    """Одна заметка для базовых тестов."""
    return Note.objects.create(
        title='Заголовок заметки',
        text='Текст заметки',
        slug='note-slug',
        author=author,
    )


@pytest.fixture
def slug_for_args(note):
    """Возвращает кортеж со slug, чтобы удобно передавать в args для reverse."""
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
            created_at=base_time - timedelta(days=i)
        )
        for i in range(count)
    ]
    return Note.objects.bulk_create(notes_list)


@pytest.fixture
def single_note(author):
    """Ещё одна отдельная заметка для detail-страницы (чтобы не зависеть от note)."""
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


@pytest.fixture
def news(author):
    """Одна новость для базовых тестов."""
    return News.objects.create(
        title='Заголовок новости',
        text='Текст новости',
        slug='news-slug',
        author=author,
    )

@pytest.fixture
def slug_for_news_args(news):
    """Кортеж со slug новости для передачи в args reverse()."""
    return (news.slug,)

@pytest.fixture
def many_news(author):
    """Много новостей для проверки лимитов и сортировки."""
    base_time = timezone.now()
    count = 15
    news_list = [
        News(
            title=f'Новость {i}',
            text='Просто текст для теста.',
            slug=f'news-slug-{i}',
            author=author,
            created_at=base_time - timedelta(days=i)
        )
        for i in range(count)
    ]
    return News.objects.bulk_create(news_list)

@pytest.fixture
def single_news(author):
    """Отдельная новость для detail-страницы (независимо от news)."""
    return News.objects.create(
        title='Тестовая новость для detail',
        text='Текст для проверки detail-страницы.',
        slug='test-news-detail-slug',
        author=author
    )

@pytest.fixture
def comment_data():
    return {
        'text': 'Тестовый комментарий',
    }

@pytest.fixture
def single_comment(single_news, author):
    """Один комментарий к новости."""
    return Comment.objects.create(
        news=single_news,
        author=author,
        text='Тестовый комментарий',
        created_at=timezone.now(),
    )
