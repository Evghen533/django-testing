import pytest
from http import HTTPStatus
from django.urls import reverse
from datetime import date, timedelta
from django.utils import timezone
from django.conf import settings
from news.models import News, Comment

pytestmark = pytest.mark.django_db


@pytest.fixture
def many_news():
    """Создаёт много новостей для теста пагинации и сортировки."""
    limit = getattr(settings, 'NEWS_COUNT_ON_HOME_PAGE', 10)
    news_list = []
    today = date.today()
    for i in range(limit + 5):
        news_list.append(
            News.objects.create(
                title=f'Новость {i}',
                text=f'Текст новости {i}',
                date=today - timedelta(days=i),
            )
        )
    return news_list


@pytest.fixture
def sorted_comments(news, author):
    """Создаёт комментарии с разными датами, чтобы проверить сортировку."""
    now = timezone.now()
    comments = []
    for index in range(10):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save(update_fields=['created'])
        comments.append(comment)
    return comments


def test_news_count_on_home(client, many_news):
    """На главной странице отображается ровно NEWS_COUNT_ON_HOME_PAGE новостей."""
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    news_feed = response.context['news_feed']
    limit = getattr(settings, 'NEWS_COUNT_ON_HOME_PAGE', 10)
    assert len(news_feed) == limit


def test_news_order_on_home(client, many_news):
    """Новости на главной отсортированы по дате: новые сверху."""
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    news_feed = response.context['news_feed']
    dates = [n.date for n in news_feed]
    assert dates == sorted(dates, reverse=True)


def test_comments_order_on_detail(client, news, sorted_comments):
    """Комментарии на странице новости отсортированы по времени: старые сверху."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    news_obj = response.context['news']
    comments = list(news_obj.comment_set.all())
    timestamps = [c.created for c in comments]

    assert timestamps == sorted(timestamps)


def test_anonymous_client_no_form_on_detail(client, news):
    """Анонимный пользователь не видит форму комментария на detail-странице."""
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' not in response.context


def test_authorized_client_sees_form_on_detail(client, news, author):
    """Авторизованный пользователь видит форму комментария."""
    client.force_login(author)
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    from news.forms import CommentForm
    assert isinstance(response.context['form'], CommentForm)


def test_comment_appears_under_news(client, comment, news):
    """Текст комментария и имя автора отображаются на странице новости."""
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    content = response.content.decode('utf-8')
    assert comment.text in content
    assert comment.author.username in content


def test_own_comment_edit_page_contains_form(client, comment, author):
    """Автор комментария видит форму редактирования на странице edit."""
    client.force_login(author)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    from news.forms import CommentForm
    assert isinstance(response.context['form'], CommentForm)


def test_other_user_cannot_access_comment_edit(client, comment, reader):
    """Читатель не может открыть страницу редактирования чужого комментария."""
    client.force_login(reader)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN)
