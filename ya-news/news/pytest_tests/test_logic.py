import pytest
from django.urls import reverse
from http import HTTPStatus
from pytest_django.asserts import assertRedirects
from datetime import date, timedelta

pytestmark = pytest.mark.django_db

def test_news_list_sorted_by_date_desc(client):
    """Новости на главной должны быть отсортированы по дате (новые сверху)."""
    from news.models import News
    from django.contrib.auth import get_user_model
    User = get_user_model()
    author = User.objects.create_user(username='sort_author', password='pass')

    # Создаём новости с разными датами
    old_news = News.objects.create(
        title='Старая новость',
        text='Старый текст',
        date=date.today() - timedelta(days=10),
        # author=author  # раскомментируй, если есть поле author
    )
    new_news = News.objects.create(
        title='Новая новость',
        text='Новый текст',
        date=date.today(),
        # author=author
    )

    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news_feed' in response.context

    news_feed = list(response.context['news_feed'])

    # Проверяем порядок: новая новость должна быть первой
    assert len(news_feed) >= 2
    assert news_feed[0].pk == new_news.pk, "Первая новость должна быть самой новой"
    assert news_feed[-1].pk == old_news.pk, "Последняя новость должна быть самой старой"


def test_comment_add_via_post_with_csrf(client, news, author):
    """Проверка добавления комментария через POST с CSRF-токеном."""
    client.force_login(author)
    detail_url = reverse('news:detail', kwargs={'pk': news.pk})

    # Сначала GET, чтобы получить CSRF-токен в cookies
    resp_get = client.get(detail_url)
    csrf_token = client.cookies['csrftoken'].value

    data = {
        'text': 'Комментарий с CSRF',
        'csrfmiddlewaretoken': csrf_token,
    }

    post_response = client.post(detail_url, data, follow=True)
    assert post_response.status_code in [200, 302]

    from news.models import Comment
    assert Comment.objects.filter(text='Комментарий с CSRF').exists(), "Комментарий не был создан в БД"


def test_comment_edit_own_access(client, comment, author):
    """Автор может редактировать свой комментарий."""
    client.force_login(author)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == 200, "Автор не может получить страницу редактирования своего комментария"
    assert 'form' in response.context, "Форма редактирования отсутствует"


def test_comment_edit_other_user_denied(client, comment, reader):
    """Читатель не может редактировать чужой комментарий (должен получить 404)."""
    client.force_login(reader)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == 404, "Чужой пользователь смог получить страницу редактирования"


def test_comment_delete_own_access(client, comment, author):
    """Автор может удалить свой комментарий."""
    client.force_login(author)
    url = reverse('news:delete', kwargs={'pk': comment.pk})
    response = client.get(url)  # или .post(), зависит от твоей реализации

    assert response.status_code == 200, "Автор не может получить страницу удаления своего комментария"


def test_comment_delete_other_user_denied(client, comment, reader):
    """Читатель не может удалить чужой комментарий."""
    client.force_login(reader)
    url = reverse('news:delete', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == 404, "Чужой пользователь смог получить страницу удаления"


def test_detail_page_shows_only_related_comments(client, comment, news):
    """На странице новости отображаются только комментарии к этой новости."""
    from news.models import Comment, News
    from django.contrib.auth import get_user_model
    User = get_user_model()
    other_author = User.objects.create_user(username='other_author', password='pass')

    # Создаём другую новость и комментарий к ней
    other_news = News.objects.create(
        title='Другая новость',
        text='Текст другой новости',
        date=date.today(),
        # author=other_author
    )
    Comment.objects.create(
        news=other_news,
        author=other_author,
        text='Комментарий к ДРУГОЙ новости'
    )

    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    content = response.content.decode('utf-8')

    # Комментарий к текущей новости должен быть виден
    assert comment.text in content, "Комментарий к новости не отображается"

    # Комментарий к ДРУГОЙ новости НЕ должен быть виден на этой странице
    assert 'Комментарий к ДРУГОЙ новости' not in content, (
        "На странице новости отображаются комментарии от других новостей!"
    )
