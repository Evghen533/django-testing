from django.conf import settings
from django.urls import reverse

import pytest

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, news_list):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, news_list):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    assert all_dates == sorted(all_dates, reverse=True)


@pytest.mark.django_db
def test_comments_order(client, news, three_comments):
    detail_url = reverse('news:detail', args=(news.id,))
    response = client.get(detail_url)

    assert 'news' in response.context
    comments = response.context['news'].comment_set.all()
    all_timestamps = [c.created for c in comments]
    assert all_timestamps == sorted(all_timestamps)


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, detail_url):
    response = client.get(detail_url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(author_client, detail_url):
    response = author_client.get(detail_url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
