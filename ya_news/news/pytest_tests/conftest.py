"""Фикстуры для тестов приложения news."""

import datetime
from datetime import date, timedelta

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from news.forms import BAD_WORDS
from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def author():
    """Создаёт пользователя-автора (пароль не нужен)."""
    return User.objects.create_user(username='Автор')


@pytest.fixture
def reader():
    """Создаёт обычного читателя (не автора)."""
    return User.objects.create_user(username='Читатель простой')


@pytest.fixture
def news():
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
        text='Текст комментария',
    )


@pytest.fixture
def news_form_data():
    """Данные для создания новости (без slug)."""
    return {
        'title': 'Новая новость через форму',
        'text': 'Полный текст новой новости',
    }


@pytest.fixture
def form_data():
    return {
        'title': 'Новый заголовок',
        'text': 'Новый текст',
        'slug': 'new-slug'
    }


@pytest.fixture
def author_client(author, client):
    """Клиент, авторизованный под автором."""
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader, client):
    """Клиент, авторизованный под читателем (не автором)."""
    client.force_login(reader)
    return client


@pytest.fixture
def bad_words_data():
    """Данные для проверки запрета плохих слов в комментарии (только text)."""
    return {
        'text': f'Какая-то {BAD_WORDS} редакция!',
    }


@pytest.fixture
def detail_url(news):
    """URL страницы детали новости."""
    return reverse('news:detail', args=(news.id,))


@pytest.fixture
def home_url():
    return reverse('news:home')


@pytest.fixture
def login_url():
    return reverse('users:login')


@pytest.fixture
def signup_url():
    return reverse('users:signup')


@pytest.fixture
def logout_url():
    return reverse('users:logout')


@pytest.fixture
def edit_url(comment):
    return reverse('news:edit', args=(comment.pk,))


@pytest.fixture
def delete_url(comment):
    return reverse('news:delete', args=(comment.pk,))


@pytest.fixture
def three_comments(news):
    """Создаёт 3 комментария от одного автора с разной датой создания."""
    author = User.objects.create_user(username='Комментатор')
    now = timezone.now()

    comments = [
        Comment(
            news=news,
            author=author,
            text=f'Текст {index}',
            created=now + timedelta(days=index),
        )
        for index in range(3)
    ]
    return Comment.objects.bulk_create(comments)


@pytest.fixture
def news_list(db):
    base_date = datetime.date(2023, 1, 1)
    return [
        News.objects.create(
            title=f'News {i}',
            text=f'Text {i}',
            pub_date=base_date + datetime.timedelta(days=i),
        )
        for i in range(5)
    ]
