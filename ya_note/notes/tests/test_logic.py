from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus
from notes.models import Note
from pytils.translit import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

class LogicTests(TestCase):
    def setUp(self):
        # Только пользователи, без заметок
        self.author = User.objects.create_user(username='author', password='123')
        self.other = User.objects.create_user(username='other', password='123')

        self.form_data = {
            'title': 'New Note',
            'text': 'Text here',
            'slug': 'new-note'
        }

    def test_user_can_create_note(self):
        self.client.force_login(self.author)
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_not_unique_slug(self):
        self.client.force_login(self.author)

        existing_note = Note.objects.create(
            title='Existing Note',
            slug='existing-note',
            text='text',
            author=self.author
        )

        url = reverse('notes:add')
        data = self.form_data.copy()
        data['slug'] = existing_note.slug
        response = self.client.post(url, data=data)

        # Проверяем, что в ошибке формы есть нужная фраза
        form_errors = response.context['form'].errors.get('slug', [])
        error_message_fragment = 'такой slug уже существует, придумайте уникальное значение!'
        found = any(error_message_fragment in err for err in form_errors)
        self.assertTrue(found, f"Не найдена фраза в ошибке: {error_message_fragment}")
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug_auto_generated(self):
        self.client.force_login(self.author)
        url = reverse('notes:add')
        data = self.form_data.copy()
        data['slug'] = ''
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        expected_slug = slugify(data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        self.client.force_login(self.author)

        note = Note.objects.create(
            title='Original',
            slug='original-slug',
            text='original text',
            author=self.author
        )

        url = reverse('notes:edit', args=(note.slug,))
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note.refresh_from_db()
        self.assertEqual(note.title, self.form_data['title'])

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.other)

        note = Note.objects.create(
            title='Protected Note',
            slug='protected-slug',
            text='text',
            author=self.author
        )

        url = reverse('notes:edit', args=(note.slug,))
        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=note.id)
        self.assertEqual(note_from_db.title, note.title)

    def test_author_can_delete_note(self):
        self.client.force_login(self.author)

        note = Note.objects.create(
            title='To Delete',
            slug='to-delete',
            text='text',
            author=self.author
        )

        url = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.other)

        note = Note.objects.create(
            title='Protected Note',
            slug='protected-delete',
            text='text',
            author=self.author
        )

        url = reverse('notes:delete', args=(note.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
