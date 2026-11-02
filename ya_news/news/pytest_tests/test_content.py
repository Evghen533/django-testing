import pytest
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse
from news.models import News, Comment
from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count_on_home_page(client):
    """На главной странице отображается NEWS_COUNT_ON_HOME_PAGE новостей."""
    today = datetime.today()
    count_to_create = settings.NEWS_COUNT_ON_HOME_PAGE + 1
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(count_to_create)
    ]
    News.objects.bulk_create(all_news)

    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == 200
    object_list = response.context['object_list']
    news_count = object_list.count() if hasattr(
        object_list,
        'count'
    ) else len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_home_page(client):
    """Новости на главной странице отсортированы по дате: новые сверху."""
    today = datetime.today()
    count_to_create = 5
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(count_to_create)
    ]
    News.objects.bulk_create(all_news)

    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == 200

    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.fixture
def news_with_comments():
    """Создаёт новость и 10 комментариев с искусственными датами."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    news = News.objects.create(
        title='Тестовая новость',
        text='Просто текст.'
    )
    author = User.objects.create_user(username='Комментатор', password='pass')

    now = timezone.now()
    comments = []
    for index in range(10):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        comments.append(comment)

    return news, author, comments


@pytest.mark.django_db
def test_comments_order_on_detail_page(client, news_with_comments):
    news, author, _ = news_with_comments
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == 200

    assert 'news' in response.context
    assert response.context['news'].pk == news.pk

    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form_on_detail(client, news_with_comments):
    news, _, _ = news_with_comments
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == 200
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_comment_form(client, news_with_comments):
    news, author, _ = news_with_comments
    url = reverse('news:detail', args=(news.id,))

    client.force_login(author)
    response = client.get(url)
    assert response.status_code == 200
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
