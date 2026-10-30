from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from notes.models import Note
from django.contrib.auth import get_user_model

User = get_user_model()

class ContentTests(TestCase):
    def setUp(self):
        # Создаём пользователя правильно — через модель
        self.user = User.objects.create_user(username='testuser', password='123')
        # Логиним его в клиент
        self.client.force_login(self.user)

        # Создаём 15 заметок от этого пользователя
        for i in range(15):
            Note.objects.create(
                title=f'Note {i}',
                slug=f'note-{i}',
                text='text',
                author=self.user
            )

    def test_notes_list_limit(self):
        """На странице списка должно отображаться ровно NOTES_PER_PAGE заметок."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        object_list = response.context['object_list']
        limit = getattr(settings, 'NOTES_PER_PAGE', 10)
        self.assertEqual(len(object_list), limit)

    def test_notes_order_on_list(self):
        """Заметки должны идти по убыванию pub_date (новые сверху)."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        object_list = response.context['object_list']
        dates = [n.pub_date for n in object_list]
        self.assertEqual(dates, sorted(dates, reverse=True))
