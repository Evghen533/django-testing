# ya-news/news/pytest_tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from datetime import date
from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def author(db):
    """Создаёт пользователя-автора."""
    return User.objects.create_user(username='Лев Толстой', password='pass')


@pytest.fixture
def reader(db):
    """Создаёт обычного читателя (не автора)."""
    return User.objects.create_user(
        username='Читатель простой', password='pass'
    )


@pytest.fixture
def news(author, db):
    """Создаёт одну тестовую новость."""
    return News.objects.create(
        title='Заголовок новости',
        text='Текст новости для тестов контента',
        date=date.today(),
    )


@pytest.fixture
def comment(news, author, db):
    """Создаёт комментарий к новости от автора."""
    return Comment.objects.create(
        news=news,
        author=author,
        text='Комментарий к новости',
    )


@pytest.fixture
def news_form_data():
    """Данные для создания новости (без slug, так как в News его нет)."""
    return {
        'title': 'Новая новость через форму',
        'text': 'Полный текст новой новости',
    }
