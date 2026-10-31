from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

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
        response = self.client.get(self.url_home)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_basic_pages_available_for_anonymous(self):
        for url in [self.url_home, self.url_login, self.url_signup]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_post_for_anonymous(self):
        response = self.client.post(self.url_logout)
        self.assertIn(response.status_code, [HTTPStatus.FOUND, HTTPStatus.OK])

    def test_list_add_success_available_for_auth_user(self):
        self.client.force_login(self.author)
        for url in [self.url_list, self.url_add, self.url_success]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_detail_edit_delete_for_author(self):
        self.client.force_login(self.author)
        for url in [self.url_detail, self.url_edit, self.url_delete]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_control_for_other_user(self):
        self.client.force_login(self.other)
        for url in [self.url_detail, self.url_edit, self.url_delete]:
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_on_protected_pages(self):
        protected_urls = [
            self.url_add,
            self.url_detail,
            self.url_edit,
            self.url_delete,
        ]
        for url in protected_urls:
            expected_next = f'{self.url_login}?next={url}'
            response = self.client.get(url)
            self.assertRedirects(response, expected_next)
