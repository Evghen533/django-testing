"""Фикстуры для тестов приложения news."""

from datetime import date, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


@pytest.fixture
def author():
    """Создаёт пользователя-автора."""
    return User.objects.create_user(
        username='Автор',
        password='password'
    )


@pytest.fixture
def reader():
    """Создаёт обычного читателя (не автора)."""
    return User.objects.create_user(
        username='Читатель простой',
        password='pass123456'
    )


@pytest.fixture
def news():
    """Создаёт одну тестовую новость."""
    return News.objects.create(
        title='Заголовок новости',
        text='Текст новости для тестов контента',
        date=date.today(),
    )


@pytest.fixture
def news_list():
    """Создаёт больше новостей, чем помещается на главной странице."""
    today = date.today()
    return News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index),
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
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
    """Данные для проверки запрета плохих слов в комментарии."""
    return {
        'text': f'Какая-то {BAD_WORDS} редакция!',
        'warning': WARNING,
    }


@pytest.fixture
def three_comments(news):
    """Создаёт 3 комментария от одного автора с разной датой создания."""
    author = User.objects.create(username='Комментатор')
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
def home_url():
    return reverse('news:home')


@pytest.fixture
def detail_url(news):
    """URL страницы новости."""
    return reverse('news:detail', args=(news.id,))


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
