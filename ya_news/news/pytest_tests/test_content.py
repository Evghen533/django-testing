"""Тесты отображения контента новостей и пагинации."""

import pytest
from django.urls import reverse
from http import HTTPStatus
from datetime import date, timedelta
from news.models import News
from django.contrib.auth import get_user_model
from django.conf import settings
from news.forms import CommentForm

pytestmark = pytest.mark.django_db


def test_news_list_renders_news_feed(client, news):
    """Проверка, что список новостей содержит news_feed и нужную новость.

    Убеждается, что в контексте страницы списка новостей присутствует
    news_feed и что в нём есть ожидаемая новость.
    """
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news_list' in response.context
    news_feed = response.context['news_feed']
    assert news in news_feed


def test_news_detail_page_shows_full_content(client, news):
    """На detail-странице отображаются заголовок, текст, дата и объект новости.

    Проверяется наличие заголовка, текста, корректной даты и объекта новости
    в контексте страницы.
    """
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
        "Поле date должно быть типа date, а получено {}".format(
            type(context_news.date)
        )
    )
    assert context_news.date == news.date, (
        "Дата в контексте не совпадает с датой объекта"
    )

    assert 'form' not in response.context


def test_authenticated_user_sees_comment_form_on_detail(client, news, author):
    """Авторизованный пользователь видит форму комментария на detail-странице.

    У авторизованного пользователя в контексте страницы должна быть
    форма для добавления комментария.
    """
    client.force_login(author)
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)


def test_comment_appears_under_news(client, comment, news):
    """Комментарий отображается под новостью на detail-странице.

    Текст комментария и имя его автора должны присутствовать
    в HTML-ответе страницы новости.
    """
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    content = response.content.decode('utf-8')
    assert comment.text in content
    assert comment.author.username in content


def test_pagination_limit_via_settings(client):
    """Пагинация на главной странице соблюдает лимит из настроек.

    Создаётся больше новостей, чем разрешено показывать на одной странице,
    затем проверяется, что в news_feed попадает не больше лимита.
    """
    user_model = get_user_model()
    user_model.objects.create_user(username='pag_author', password='pass')

    for i in range(15):
        News.objects.create(
            title=f'News {i}',
            text=f'Text {i}',
            date=date.today() - timedelta(days=i),
        )

    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news_list' in response.context

    news_feed = response.context['news_feed']
    limit = getattr(settings, 'NEWS_COUNT_ON_HOME_PAGE', 10)

    assert len(news_feed) <= limit, (
        "На главной больше новостей, чем разрешено "
        "(лимит {}, найдено {})".format(limit, len(news_feed))
    )


def test_own_comment_edit_page_contains_form(client, comment, author):
    """Страница редактирования собственного комментария содержит форму.

    Автор комментария должен видеть форму редактирования
    на странице изменения своего комментария.
    """
    client.force_login(author)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)


def test_other_user_cannot_access_comment_edit(client, comment, reader):
    """Пользователь не может редактировать чужой комментарий (404).

    Читатель, пытающийся открыть страницу редактирования чужого комментария,
    должен получить ответ 404.
    """
    client.force_login(reader)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)
    assert response.status_code == 404
