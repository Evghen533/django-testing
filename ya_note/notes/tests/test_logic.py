import unittest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note
from pytils.translit import slugify
from notes.forms import WARNING


class LogicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.author = User.objects.create_user(username='author', password='123')
        cls.not_author = User.objects.create_user(username='not_author', password='123')

        cls.note = Note.objects.create(
            title='Test note',
            text='Text',
            slug='test-note',
            author=cls.author,
        )

    def setUp(self):
        # Логиним автора для большинства тестов
        self.client.force_login(self.author)

    def _logout(self):
        self.client.logout()

    def test_user_can_create_note(self):
        form_data = {
            'title': 'Новая заметка',
            'text': 'Текст заметки',
            'slug': 'new-note-slug'
        }
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)  # старая + новая

        new_note = Note.objects.exclude(id=self.note.id).get()
        self.assertEqual(new_note.title, form_data['title'])
        self.assertEqual(new_note.text, form_data['text'])
        self.assertEqual(new_note.slug, form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        self._logout()
        form_data = {
            'title': 'Заметка анонима',
            'text': 'Текст от анонима',
            'slug': 'anonymous-note'
        }
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)

        login_url = reverse('users:login')
        expected_next = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_next)
        # Заметка не создана: осталась только исходная
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        form_data = {
            'title': 'Дублирующая заметка',
            'text': 'Текст дубликата',
            'slug': self.note.slug
        }
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200, "Ожидался статус 200 (страница с формой), а не редирект/ошибка")
        self.assertIn('form', response.context, "В контексте ответа нет формы")

        form = response.context['form']
        self.assertTrue(form.is_bound, "Форма не привязана к данным")

        self.assertIn('slug', form.errors, "При дубликате slug не возникла ошибка валидации в поле slug")

        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        form_data = {
            'title': 'Заметка без слэга',
            'text': 'Текст заметки'
        }
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)

        new_note = Note.objects.exclude(id=self.note.id).get()
        expected_slug = slugify(form_data['title'])[:100]
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        form_data = {
            'title': 'Отредактированная заметка',
            'text': 'Новый текст заметки',
            'slug': 'edited-note-slug'
        }
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))

        edited_note = Note.objects.get(id=self.note.id)
        self.assertEqual(edited_note.title, form_data['title'])
        self.assertEqual(edited_note.text, form_data['text'])
        self.assertEqual(edited_note.slug, form_data['slug'])

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.not_author)
        form_data = {
            'title': 'Попытка редактирования',
            'text': 'Текст для редактирования',
            'slug': 'other-user-slug'
        }
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 404)

        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.not_author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Note.objects.count(), 1)
