from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Автор')
        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Текст заметки',
            'slug': 'novaya-zametka',
        }
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.login_url = reverse('users:login')

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        self.client.force_login(self.user)
        response = self.client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_cant_create_note(self):
        """Аноним не может создать заметку."""
        response = self.client.post(self.add_url, data=self.form_data)
        expected = f'{self.login_url}?next={self.add_url}'
        self.assertRedirects(response, expected)
        self.assertEqual(Note.objects.count(), 0)

    def test_slug_must_be_unique(self):
        """Две заметки с одинаковым slug создать нельзя."""
        note = Note.objects.create(
            title='Старая заметка',
            text='Текст',
            slug=self.form_data['slug'],
            author=self.user,
        )
        self.client.force_login(self.user)
        response = self.client.post(self.add_url, data=self.form_data)
        self.assertEqual(Note.objects.count(), 1)
        self.assertFormError(
            response, 'form', 'slug', note.slug + WARNING
        )

    def test_empty_slug_autofilled_with_slugify(self):
        """Без slug он формируется автоматически через pytils.translit."""
        self.client.force_login(self.user)
        data = {k: v for k, v in self.form_data.items() if k != 'slug'}
        response = self.client.post(self.add_url, data=data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.slug, slugify(data['title']))


class TestNoteEditDelete(TestCase):

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
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.new_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст.',
            'slug': 'novyi-zagolovok',
        }

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        self.client.force_login(self.author)
        response = self.client.post(self.edit_url, data=self.new_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.new_data['title'])
        self.assertEqual(self.note.text, self.new_data['text'])
        self.assertEqual(self.note.slug, self.new_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Чужую заметку редактировать нельзя: 404, текст не меняется."""
        self.client.force_login(self.reader)
        response = self.client.post(self.edit_url, data=self.new_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Заголовок')

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        self.client.force_login(self.author)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Чужую заметку удалить нельзя: 404, заметка на месте."""
        self.client.force_login(self.reader)
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
