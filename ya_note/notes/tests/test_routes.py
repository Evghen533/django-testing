from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()

class RoutesTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='123')
        self.note = None

    def test_home_availability_for_anonymous(self):
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_basic_pages_available_for_anonymous(self):
        for name in ['notes:home', 'users:login', 'users:signup']:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_post_for_anonymous(self):
        url = reverse('users:logout')
        response = self.client.post(url)
        self.assertIn(response.status_code, [HTTPStatus.FOUND, HTTPStatus.OK])

    def test_list_add_success_available_for_auth_user(self):
        self.client.force_login(self.author)
        for name in ['notes:list', 'notes:add', 'notes:success']:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_detail_edit_delete_for_author(self):
        self.client.force_login(self.author)
        self.note = Note.objects.create(
            title='Test',
            slug='test',
            text='text',
            author=self.author
        )
        for name in ['notes:detail', 'notes:edit', 'notes:delete']:
            url = reverse(name, args=(self.note.slug,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_control_for_other_user(self):
        other = User.objects.create_user(username='other', password='123')
        self.client.force_login(other)
        # note должен быть создан до этого теста, чтобы у него был slug
        if self.note is None:
            self.note = Note.objects.create(
                title='Test2',
                slug='test2',
                text='text',
                author=self.author
            )
        for name in ['notes:detail', 'notes:edit', 'notes:delete']:
            url = reverse(name, args=(self.note.slug,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous_on_protected_pages(self):
        login_url = reverse('users:login')
        # Сначала создадим заметку, чтобы был slug для detail/edit/delete
        self.note = Note.objects.create(
            title='Protected',
            slug='protected',
            text='text',
            author=self.author
        )

        for name in ['notes:detail', 'notes:edit', 'notes:delete', 'notes:add']:
            if name in ['notes:detail', 'notes:edit', 'notes:delete']:
                url = reverse(name, args=(self.note.slug,))
            else:
                url = reverse(name)

            expected_next = f'{login_url}?next={url}'
            response = self.client.get(url)
            self.assertRedirects(response, expected_next)
