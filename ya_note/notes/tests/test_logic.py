import uuid
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='Автор',
            password='password'
        )

    def setUp(self):
        suffix = str(uuid.uuid4())[:8]
        self.title = f'Новая заметка {suffix}'
        self.text = 'Текст заметки'
        self.slug = f'novaya-zametka-{suffix}'

        self.form_data = {
            'title': self.title,
            'text': self.text,
            'slug': self.slug,
        }

        self.add_url = reverse('notes:add')
        self.success_url = reverse('notes:success')
        self.login_url = reverse('users:login')

        other_user = User.objects.create_user(
            username=f'Другой-{suffix}',
            password='password'
        )
        Note.objects.create(
            title=f'Чужая заметка {suffix}',
            text='Текст чужой заметки',
            slug=f'chuzhaya-{suffix}',
            author=other_user,
        )

    def test_user_can_create_note(self):
        self.client.force_login(self.user)
        initial_count = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)

        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), initial_count + 1)

        note = Note.objects.order_by('-id').first()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_cant_create_note(self):
        initial_count = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)
        expected = f'{self.login_url}?next={self.add_url}'
        self.assertRedirects(response, expected)
        self.assertEqual(Note.objects.count(), initial_count)

def test_slug_must_be_unique(self):
    """Нельзя создать вторую заметку с существующим slug."""
    Note.objects.create(
        title='Существующая заметка',
        text='Текст.',
        slug=self.form_data['slug'],
        author=self.user,
    )

    self.client.force_login(self.user)
    initial_count = Note.objects.count()

    response = self.client.post(self.add_url, data=self.form_data)

    self.assertEqual(Note.objects.count(), initial_count)

    expected_error_msg = (
        f'{self.form_data["slug"]} - такой slug уже существует, '
        'придумайте уникальное значение!'
    )
    self.assertFormError(
        response.context['form'],
        'slug',
        [expected_error_msg]
    )

    def test_empty_slug_autofilled_with_slugify(self):
        self.client.force_login(self.user)
        initial_count = Note.objects.count()
        data = {k: v for k, v in self.form_data.items() if k != 'slug'}
        response = self.client.post(self.add_url, data=data)

        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), initial_count + 1)

        note = Note.objects.order_by('-id').first()
        expected_slug = slugify(data['title'])[:100]
        self.assertEqual(note.slug, expected_slug)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='Автор',
            password='password'
        )
        cls.reader = User.objects.create_user(
            username='Читатель',
            password='password'
        )

    def setUp(self):
        suffix = str(uuid.uuid4())[:8]
        self.note = Note.objects.create(
            title=f'Заголовок {suffix}',
            text='Текст.',
            slug=f'zagolovok-{suffix}',
            author=self.author,
        )
        self.edit_url = reverse('notes:edit', args=(self.note.slug,))
        self.delete_url = reverse('notes:delete', args=(self.note.slug,))
        self.success_url = reverse('notes:success')
        self.new_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст.',
            'slug': f'novyi-zagolovok-{suffix}',
        }

    def test_author_can_edit_note(self):
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
        original_title = self.note.title
        response = self.client.post(self.edit_url, data=self.new_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, original_title)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        initial_count = Note.objects.count()
        initial_id = self.note.id
        self.client.force_login(self.author)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), initial_count - 1)
        self.assertFalse(Note.objects.filter(id=initial_id).exists())

    def test_other_user_cant_delete_note(self):
        """Чужую заметку удалить нельзя: 404, заметка на месте."""
        initial_count = Note.objects.count()
        initial_id = self.note.id
        self.client.force_login(self.reader)
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), initial_count)
        self.assertTrue(Note.objects.filter(id=initial_id).exists())
