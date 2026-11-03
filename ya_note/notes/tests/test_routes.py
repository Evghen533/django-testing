import unittest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class RoutesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.author = User.objects.create_user(username='author', password='123')

    def setUp(self):
        self.client.force_login(self.author)

    def _anonymous_client(self):
        client = self.client
        client.logout()
        return client

    def test_home_availability_for_anonymous_user(self):
        client = self._anonymous_client()
        url = reverse('notes:home')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_pages_availability_for_anonymous_user(self):
        client = self._anonymous_client()
        urls = [
            reverse('notes:home'),
            reverse('users:login'),
            reverse('users:signup'),
        ]
        for url in urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_logout_availability_for_anonymous_user(self):
        client = self._anonymous_client()
        url = reverse('users:logout')
        response = client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_pages_availability_for_author(self):
        urls = [
            reverse('notes:list'),
            reverse('notes:add'),
            reverse('notes:success'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_detail_edit_delete_availability_for_author(self):
        from notes.models import Note
        note = Note.objects.create(
            title='For routes test',
            text='text',
            slug='routes-test',
            author=self.author,
        )

        detail_url = reverse('notes:detail', args=(note.slug,))
        edit_url = reverse('notes:edit', args=(note.slug,))
        delete_url = reverse('notes:delete', args=(note.slug,))

        for url in [detail_url, edit_url]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        # delete — POST
        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse('notes:success'))

    def test_detail_edit_delete_unavailable_for_other_user(self):
        User = get_user_model()
        not_author = User.objects.create_user(username='not_author', password='123')

        from notes.models import Note
        note = Note.objects.create(
            title='Private note',
            text='text',
            slug='private-note',
            author=self.author,
        )

        client = self.client
        client.force_login(not_author)

        detail_url = reverse('notes:detail', args=(note.slug,))
        edit_url = reverse('notes:edit', args=(note.slug,))
        delete_url = reverse('notes:delete', args=(note.slug,))

        for url in [detail_url, edit_url]:
            response = client.get(url)
            self.assertEqual(response.status_code, 404)

        response = client.post(delete_url)
        self.assertEqual(response.status_code, 404)

    def test_redirects_for_anonymous(self):
        """Проверка, что аноним получает редирект на login для защищённых страниц."""
        login_url = reverse('users:login')

        protected_urls = [
            reverse('notes:detail', args=('any-slug',)),
            reverse('notes:edit', args=('any-slug',)),
            reverse('notes:delete', args=('any-slug',)),
            reverse('notes:add'),
            reverse('notes:list'),
        ]

        client = self._anonymous_client()

        for url in protected_urls:
            response = client.get(url)
            expected_next = f'{login_url}?next={url}'
            self.assertRedirects(response, expected_next)

    def test_success_page_available_without_login(self):
        client = self._anonymous_client()
        url = reverse('notes:success')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
