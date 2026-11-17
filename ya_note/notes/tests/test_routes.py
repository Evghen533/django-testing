from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст.',
            slug='zagolovok',
            author=cls.author,
        )
        cls.note_args = (cls.note.slug,)
        cls.login_url = reverse('users:login')
        cls.logout_url = reverse('users:logout')
        cls.signup_url = reverse('users:signup')
        cls.list_url = reverse('notes:list')
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.detail_url = reverse('notes:detail', args=cls.note_args)
        cls.edit_url = reverse('notes:edit', args=cls.note_args)
        cls.delete_url = reverse('notes:delete', args=cls.note_args)

    def test_home_page_available_to_anonymous(self):
        response = self.client.get(reverse('notes:home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_pages_available_to_all_users(self):
        """Страницы входа и регистрации доступны анонимам."""
        for url in (self.login_url, self.signup_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_available_to_all_users(self):
        """Страница выхода доступна анонимам."""
        response = self.client.post(self.logout_url)
        self.assertIn(
            response.status_code,
            (HTTPStatus.OK, HTTPStatus.FOUND)
        )

    def test_note_pages_available_for_auth_user(self):
        """Список, добавление и success доступны залогиненному."""
        self.client.force_login(self.reader)
        for url in (self.list_url, self.add_url, self.success_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_pages_available_for_author(self):
        """Детали, правка и удаление доступны автору заметки."""
        self.client.force_login(self.author)
        for url in (self.detail_url, self.edit_url, self.delete_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_pages_return_404_for_other_user(self):
        """Чужому пользователю заметки недоступны: 404."""
        self.client.force_login(self.reader)
        for url in (self.detail_url, self.edit_url, self.delete_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_anonymous_redirects_to_login(self):
        """Анонима с защищённых страниц уводит на логин с next."""
        urls = (
            self.list_url,
            self.add_url,
            self.success_url,
            self.detail_url,
            self.edit_url,
            self.delete_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                expected = f'{self.login_url}?next={url}'
                self.assertRedirects(response, expected)
