from datetime import timedelta
from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from news.forms import CommentForm
from news.models import Comment, News

HOME_URL = reverse('news:home')

User = get_user_model()


@pytest.mark.django_db
def test_news_count_on_home_page(client):
    """На главной странице не более NEWS_COUNT_ON_HOME_PAGE новостей."""
    today = timezone.now()
    News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index),
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )
    response = client.get(HOME_URL)
    assert response.status_code == HTTPStatus.OK
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_home_page(client):
    """Новости отсортированы от самых свежих к самым старым."""
    today = timezone.now()
    News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index),
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )
    response = client.get(HOME_URL)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    assert all_dates == sorted(all_dates, reverse=True)


@pytest.mark.django_db
def test_comments_order_on_detail_page(client, news):
    """Комментарии на странице новости идут от старых к новым."""
    author = User.objects.create(username='Комментатор')
    now = timezone.now()
    Comment.objects.bulk_create(
        Comment(
            news=news,
            author=author,
            text=f'Текст {index}',
            created=now + timedelta(days=index),
        )
        for index in range(3)
    )
    response = client.get(reverse('news:detail', args=(news.id,)))
    comments = response.context['news'].comment_set.all()
    all_timestamps = [comment.created for comment in comments]
    assert all_timestamps == sorted(all_timestamps)


@pytest.mark.django_db
def test_anonymous_has_no_comment_form(client, news):
    """Анониму форма комментария на странице новости недоступна."""
    response = client.get(reverse('news:detail', args=(news.id,)))
    assert response.status_code == HTTPStatus.OK
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_has_comment_form(author_client, news):
    """Авторизованному доступна форма комментария нужного класса."""
    response = author_client.get(reverse('news:detail', args=(news.id,)))
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
