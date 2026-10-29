"""Фикстуры для тестов приложения news."""

import pytest
from django.contrib.auth import get_user_model
from datetime import date
from news.models import News, Comment


@pytest.fixture
def author():
    """Создаёт пользователя-автора."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username='Автор', password='password'
    )


@pytest.fixture
def reader():
    """Создаёт обычного читателя (не автора)."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username='Читатель простой', password='pass'
    )


@pytest.fixture
def news(author):
    """Создаёт одну тестовую новость."""
    return News.objects.create(
        title='Заголовок новости',
        text='Текст новости для тестов контента',
        date=date.today(),
    )


@pytest.fixture
def comment(news, author):
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
