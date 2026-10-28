import pytest
from django.urls import reverse
from http import HTTPStatus
from datetime import date

pytestmark = pytest.mark.django_db


def test_news_list_renders_news_feed(client, news):
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news_feed' in response.context
    news_feed = response.context['news_feed']
    assert news in news_feed


def test_news_detail_page_shows_full_content(client, news):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    content = response.content.decode('utf-8')
    assert news.title in content, "Заголовок новости не отображается"
    assert news.text in content, "Текст новости не отображается"

    assert 'news' in response.context, "Объект новости отсутствует в контексте"

    context_news = response.context['news']
    assert context_news.pk == news.pk, "В контекст попала не та новость"
    assert isinstance(context_news.date, date), (
        f"Поле date должно быть типа date,"
        "а получено {type(context_news.date)}"
    )
    assert context_news.date == news.date, "Дата в контексте не совпадает с датой объекта"

    assert 'form' not in response.context


def test_authenticated_user_sees_comment_form_on_detail(client, news, author):
    client.force_login(author)
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    from news.forms import CommentForm
    assert isinstance(response.context['form'], CommentForm)


def test_comment_appears_under_news(client, comment, news):
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    content = response.content.decode('utf-8')
    assert comment.text in content
    assert comment.author.username in content


def test_pagination_limit_via_settings(client):
    from news.models import News
    from django.contrib.auth import get_user_model
    from datetime import date, timedelta

    User = get_user_model()
    author = User.objects.create_user(username='pag_author', password='pass')

    for i in range(15):
        News.objects.create(
            title=f'News {i}',
            text=f'Text {i}',
            date=date.today() - timedelta(days=i),
        )

    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news_feed' in response.context

    news_feed = response.context['news_feed']
    from django.conf import settings
    limit = getattr(settings, 'NEWS_COUNT_ON_HOME_PAGE', 10)

    assert len(news_feed) <= limit, (
        f"На главной больше новостей, чем разрешено"
        "(лимит {limit}, найдено {len(news_feed)})"
    )


def test_own_comment_edit_page_contains_form(client, comment, author):
    client.force_login(author)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    from news.forms import CommentForm
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)


def test_other_user_cannot_access_comment_edit(client, comment, reader):
    client.force_login(reader)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)
    assert response.status_code == 404
