"""Тесты бизнес-логики: сортировка, комментарии, права доступа."""

import pytest
from django.urls import reverse
from http import HTTPStatus
from django.test import Client, TestCase
from datetime import date, timedelta
from news.models import News, Comment
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestCommentCreation(TestCase):
    COMMENT_TEXT = 'Текст комментария'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        cls.url = reverse('news:detail', args=(cls.news.id,))
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        self.client.post(self.url, data=self.form_data)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

    def test_user_can_create_comment(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, f'{self.url}#comments')
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        from news.forms import BAD_WORDS, WARNING
        bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
        response = self.auth_client.post(self.url, data=bad_words_data)
        form = response.context['form']
        self.assertFormError(
            form=form,
            field='text',
            errors=WARNING
        )
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)


@pytest.mark.django_db
def test_news_list_sorted_by_date_desc(client):
    """Новости на главной сортируются по дате (новые сверху).

    Тест создаёт новости с разными датами и проверяет, что в списке
    первой идёт самая свежая новость, а последней — самая старая.
    """
    old_news = News.objects.create(
        title='Старая новость',
        text='Старый текст',
        date=date.today() - timedelta(days=10),
    )
    new_news = News.objects.create(
        title='Новая новость',
        text='Новый текст',
        date=date.today(),
    )

    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert 'news_feed' in response.context

    news_feed = list(response.context['news_feed'])

    assert len(news_feed) >= 2
    assert (
        news_feed[0].pk == new_news.pk
    ), "Первая новость должна быть самой новой"
    assert (
        news_feed[-1].pk == old_news.pk
    ), "Последняя новость должна быть самой старой"


@pytest.mark.django_db
def test_comment_add_via_post_with_csrf(client, news, author):
    """Добавление комментария через POST с CSRF-токеном работает.

    Тест проверяет, что комментарий успешно создаётся при POST-запросе
    с корректным CSRF-токеном.
    """
    client.force_login(author)
    detail_url = reverse('news:detail', kwargs={'pk': news.pk})

    resp_get = client.get(detail_url)
    csrf_token = resp_get.cookies['csrftoken'].value

    data = {
        'text': 'Комментарий с CSRF',
        'csrfmiddlewaretoken': csrf_token,
    }

    post_response = client.post(detail_url, data, follow=True)
    assert post_response.status_code in [200, 302]

    assert Comment.objects.filter(text='Комментарий с CSRF').exists(), (
        "Комментарий не был создан в БД"
    )


@pytest.mark.django_db
def test_comment_edit_own_access(client, comment, author):
    """Автор может получить страницу редактирования своего комментария.

    Автор комментария должен иметь доступ к странице редактирования
    своего комментария и видеть там форму.
    """
    client.force_login(author)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == 200, (
        "Автор не может получить страницу редактирования"
    )
    assert 'form' in response.context, "Форма редактирования отсутствует"


@pytest.mark.django_db
def test_comment_edit_other_user_denied(client, comment, reader):
    """Читатель не может получить страницу чужого комментария (403 Forbidden).

    Пользователь, не являющийся автором комментария, не должен иметь
    доступа к странице редактирования чужого комментария.
    """
    client.force_login(reader)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        "Чужой пользователь не должен иметь доступ "
        "к редактированию чужого комментария"
    )


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(client, comment, reader):
    """Читатель не может редактировать чужой комментарий (403 Forbidden)."""
    old_text = comment.text

    client.force_login(reader)
    url = reverse('news:edit', kwargs={'pk': comment.pk})
    form_data = {'text': 'Попытка чужого редактирования'}

    response = client.post(url, data=form_data)

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        "Читатель не должен иметь права редактировать чужой комментарий"
    )

    comment.refresh_from_db()
    assert comment.text == old_text, "Комментарий не должен был измениться"


@pytest.mark.django_db
def test_comment_delete_own_access(client, comment, author):
    """Автор может получить страницу удаления своего комментария.

    Автор комментария должен иметь возможность открыть страницу удаления
    своего комментария.
    """
    client.force_login(author)
    url = reverse('news:delete', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == 200, (
        "Автор не может получить страницу удаления"
    )


@pytest.mark.django_db
def test_comment_delete_other_user_denied(client, comment, reader):
    """Читатель не может получить страницу удаления чужого комментария
    (403 Forbidden).

    Читатель не должен иметь доступа к странице удаления чужого комментария.
    """
    client.force_login(reader)
    url = reverse('news:delete', kwargs={'pk': comment.pk})
    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        "Чужой пользователь не должен иметь доступ "
        "к удалению чужого комментария"
    )


@pytest.mark.django_db
def test_detail_page_shows_only_related_comments(client, comment, news):
    """На странице новости отображаются только комментарии к ней.

    На detail-странице конкретной новости не должны показываться
    комментарии, относящиеся к другим новостям.
    """
    user_model = get_user_model()
    other_author = user_model.objects.create_user(
        username='other_author',
        password='pass123456',
    )

    other_news = News.objects.create(
        title='Другая новость',
        text='Текст другой новости',
        date=date.today(),
    )
    Comment.objects.create(
        news=other_news,
        author=other_author,
        text='Комментарий к ДРУГОЙ новости',
    )

    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    content = response.content.decode('utf-8')

    assert comment.text in content, "Комментарий к новости не отображается"
    assert 'Комментарий к ДРУГОЙ новости' not in content, (
        "На странице новости отображаются комментарии от других новостей!"
    )
