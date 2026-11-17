from http import HTTPStatus

import pytest
from django.conf import settings

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count_on_home_page(client, home_url, news_list):
    """На главной странице не более NEWS_COUNT_ON_HOME_PAGE новостей."""
    response = client.get(home_url)
    assert response.status_code == HTTPStatus.OK
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_home_page(client, home_url, news_list):
    """Новости отсортированы от самых свежих к самым старым."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    assert all_dates == sorted(all_dates, reverse=True)


@pytest.mark.django_db
def test_comments_order_on_detail_page(
    client,
    detail_url,
    three_comments
):
    """Комментарии на странице новости идут от старых к новым."""
    response = client.get(detail_url)

    comments = response.context['news'].comment_set.all()
    all_timestamps = [comment.created for comment in comments]

    assert all_timestamps == sorted(all_timestamps)


@pytest.mark.django_db
def test_anonymous_has_no_comment_form(client, news, detail_url):
    """Анониму форма комментария на странице новости недоступна."""
    response = client.get(detail_url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_has_comment_form(author_client, news, detail_url):
    """Авторизованному доступна форма комментария нужного класса."""
    response = author_client.get(detail_url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
