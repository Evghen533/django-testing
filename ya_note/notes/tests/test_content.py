from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestNotesList(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.author_note = Note.objects.create(
            title='Заметка автора',
            text='Текст автора.',
            slug='zametka-avtora',
            author=cls.author,
        )
        cls.reader_note = Note.objects.create(
            title='Заметка читателя',
            text='Текст читателя.',
            slug='zametka-chitatelya',
            author=cls.reader,
        )
        cls.list_url = reverse('notes:list')

    def test_note_in_object_list_for_author(self):
        """Своя заметка передаётся в object_list."""
        self.client.force_login(self.author)
        response = self.client.get(self.list_url)
        self.assertIn(self.author_note, response.context['object_list'])

    def test_foreign_note_not_in_object_list(self):
        """Чужая заметка не попадает в список пользователя."""
        self.client.force_login(self.author)
        response = self.client.get(self.list_url)
        self.assertNotIn(self.reader_note, response.context['object_list'])


class TestForms(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст.',
            slug='zagolovok',
            author=cls.author,
        )

    def test_add_page_contains_form(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:add'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_edit_page_contains_form(self):
        self.client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.get(url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)
