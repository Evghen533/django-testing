import pytest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from django.db.models.query import QuerySet

User = get_user_model()


class RoutesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(
            username='author',
            password='123'
        )
        cls.other = get_user_model().objects.create_user(
            username='other',
            password='123'
        )
        cls.note = Note.objects.create(
            title='Test Note',
            slug='test-note',
            text='text',
            author=cls.author
        )

        cls.url_home = reverse('notes:home')
        cls.url_list = reverse('notes:list')
        cls.url_add = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.url_login = reverse('users:login')
        cls.url_logout = reverse('users:logout')
        cls.url_signup = reverse('users:signup')

        cls.url_detail = reverse('notes:detail', args=(cls.note.slug,))
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.url_delete = reverse('notes:delete', args=(cls.note.slug,))

    def test_home_availability_for_anonymous(self):
        """Главная страница доступна анонимному пользователю."""
        response = self.client.get(self.url_home)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_basic_public_pages_availability(self):
        """Публичные страницы доступны анонимусу."""
        public_urls = [self.url_home, self.url_login, self.url_signup]
        for url in public_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_behavior(self):
        """Проверка работы страницы выхода (обычно это POST с редиректом)."""
        response = self.client.post(self.url_logout)

        self.assertIn(response.status_code, [HTTPStatus.FOUND, HTTPStatus.OK])

    def test_protected_pages_available_for_author(self):
        """Автор видит страницы списка, добавления и успеха."""
        self.client.force_login(self.author)
        protected_urls = [self.url_list, self.url_add, self.url_success]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_access_to_own_note_actions(self):
        """Автор может работать со своей заметкой."""
        self.client.force_login(self.author)
        actions_urls = [self.url_detail, self.url_edit, self.url_delete]

        for url in actions_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_other_user_gets_404_on_foreign_note(self):
        """Чужой пользователь получает 404 на чужую заметку."""
        self.client.force_login(self.other)
        restricted_urls = [self.url_detail, self.url_edit, self.url_delete]

        for url in restricted_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.NOT_FOUND,
                "Не 404"
            )

@pytest.mark.django_db
def test_anonymous_redirect_on_protected_pages(client):
    """Аноним редиректится на страницу входа."""
    protected_urls = [
        reverse('notes:add'),
    ]
    login_url = reverse('users:login')

    for url in protected_urls:
        response = client.get(url, follow=True)
        assert response.status_code in (200, 302)

        redirected_to_login = any(
            r['location'].endswith(login_url)
            for r in response.redirect_chain
        )
        on_login_page = (
            response.request['PATH_INFO']
            .endswith(login_url.lstrip('/'))
        )

        assert (
            redirected_to_login or on_login_page
        ), f"Аноним не был редиректнут на login при доступе к {url}"

@pytest.mark.django_db
def test_list_page_contains_object_list(client, author):
    """В контексте списка заметок есть object_list (QuerySet или список)."""
    Note.objects.create(
        title='Test note',
        slug='test-note',
        text='Text',
        author=author,
    )

    client.force_login(author)
    url = reverse('notes:list')
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'object_list' in response.context

    object_list = response.context['object_list']
    assert isinstance(object_list, (list, QuerySet))
    assert len(object_list) >= 1
    assert any(n.title == 'Test note' for n in object_list)
