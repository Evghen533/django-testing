from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note

User = get_user_model()


class TestNotesLogic(TestCase):
    """Тесты логики работы с заметками на Django unittest."""

    def setUp(self):
        """Подготовка данных перед каждым тестом."""
        self.author = User.objects.create_user(username='author_user')
        self.other_user = User.objects.create_user(username='other_user')

        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.other_user_client = Client()
        self.other_user_client.force_login(self.other_user)

        self.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            slug='test-note',
            author=self.author
        )

        self.form_data = {
            'title': 'Новая заметка',
            'text': 'Новый текст',
            'slug': 'new-note',
        }

    def test_user_can_create_note(self):
        """Автор может создать заметку."""
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)

        # assertRedirects работает только при запуске через manage.py test
        self.assertRedirects(response, reverse('notes:success'))

        self.assertEqual(Note.objects.count(), 2)  # Старая + новая
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        client = Client()  # анонимный клиент
        url = reverse('notes:add')
        login_url = reverse('users:login')
        expected_next = f'{login_url}?next={url}'

        response = client.post(url, data=self.form_data)
        self.assertRedirects(response, expected_next)

        # Количество заметок не должно увеличиться
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """Нельзя создать заметку с существующим slug."""
        conflict_data = {**self.form_data, 'slug': self.note.slug}
        url = reverse('notes:add')

        response = self.author_client.post(url, data=conflict_data)
        form = response.context.get('form')

        self.assertIsNotNone(form)
        self.assertIn('slug', form.errors)
        # Новая заметка не создана
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug_generates_automatically(self):
        """Если slug не передан, он генерируется автоматически."""
        data_without_slug = {
            'title': 'Заметка без slug',
            'text': 'Текст заметки',
        }
        expected_slug = slugify(data_without_slug['title'])

        url = reverse('notes:add')
        response = self.author_client.post(url, data=data_without_slug)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)

        new_note = Note.objects.last()
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, data=self.form_data)

        self.assertRedirects(response, reverse('notes:success'))

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Другой пользователь не может редактировать чужую заметку."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.other_user_client.post(url, data=self.form_data)

        # Твой view возвращает 404, если пользователь не тот. Если будет 403 — тоже ок
        self.assertEqual(response.status_code, 404)

        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.delete(url)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Другой пользователь не может удалить чужую заметку."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.other_user_client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Note.objects.count(), 1)
