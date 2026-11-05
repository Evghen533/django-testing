import pytest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import News, Comment

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text='Текст комментария'
        )

    def test_home_page(self):
        url = reverse('news:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_detail_page(self):
        url = reverse('news:detail', args=(self.news.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability(self):
        urls = (
            ('news:home', None),
            ('news:detail', (self.news.id,)),
            ('users:login', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_comment_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('news:edit', 'news:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.comment.id,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in ('news:edit', 'news:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.comment.id,))
                # Получаем ожидаемый адрес страницы логина,
                # на который будет перенаправлен пользователь.
                # Учитываем, что в адресе будет параметр next,
                # в котором передаётся адрес страницы,
                # с которой пользователь был переадресован.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)


LOGIN_URL = reverse('users:login')
SIGNUP_URL = reverse('users:signup')
LOGOUT_URL = reverse('users:logout')


@pytest.mark.django_db
def test_home_page_available_to_anonymous(client):
    """Главная страница доступна анонимному пользователю."""
    response = client.get(reverse('news:home'))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_detail_page_available_to_anonymous(client, news):
    """Страница отдельной новости доступна анонимному пользователю."""
    response = client.get(reverse('news:detail', args=(news.id,)))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ['users:signup', 'users:login'],
)
def test_auth_pages_available_to_anonymous(client, name):
    """Страницы регистрации, входа и выхода доступны анонимам."""
    response = client.get(reverse(name))
    assert response.status_code in (HTTPStatus.OK, HTTPStatus.FOUND)


def test_logout_available_to_anonymous(client):
    url = reverse('users:logout')
    response = client.post(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'].endswith('/login/')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'action_name',
    ['news:edit', 'news:delete'],
)
def test_comment_pages_available_to_author(client, comment, action_name):
    """Страницы правки и удаления комментария доступны автору."""
    client.force_login(comment.author)
    response = client.get(reverse(action_name, args=(comment.id,)))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'action_name',
    ['news:edit', 'news:delete'],
)
def test_comment_pages_not_available_to_other_user(
    client, comment, reader, action_name
):
    """Чужому пользователю правка и удаление комментария дают 404."""
    client.force_login(reader)
    response = client.get(reverse(action_name, args=(comment.id,)))
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize(
    'action_name',
    ['news:edit', 'news:delete'],
)
def test_anonymous_redirects_to_login(client, comment, action_name):
    """Аноним с защищённых страниц перенаправляется на логин."""
    url = reverse(action_name, args=(comment.id,))
    expected_redirect = f'{LOGIN_URL}?next={url}'

    response = client.get(url, follow=True)

    assert response.redirect_chain
    last_url, _ = response.redirect_chain[-1]
    assert last_url == expected_redirect
