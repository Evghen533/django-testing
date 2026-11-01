import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from notes.models import Note

User = get_user_model()


class ContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser', password='123'
        )
        base_date = timezone.now()
        for i in range(15):
            Note.objects.create(
                title=f'Note {i}',
                slug=f'note-{i}',
                text='text',
                author=cls.user,
                pub_date=base_date - timedelta(days=i)
            )

    def setUp(self):
        self.client.force_login(self.user)

    def test_notes_list_limit(self):
        """Список содержит NOTES_PER_PAGE заметок."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        object_list = response.context['object_list']
        limit = getattr(settings, 'NOTES_PER_PAGE', 10)
        self.assertLessEqual(len(object_list), limit)

    def test_notes_order_on_list(self):
        """Заметки должны идти по убыванию pub_date (новые сверху)."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        object_list = response.context['object_list']
        dates = [n.pub_date for n in object_list]
        self.assertEqual(dates, sorted(dates, reverse=True))


@pytest.mark.django_db
def test_notes_isolation(client, user):
    """У каждого пользователя свои заметки, чужие не видны."""
    User = get_user_model()

    # Создаём другого пользователя и его заметку
    other_user = User.objects.create_user(username='other', password='123')
    Note.objects.create(
        title='Other note',
        slug='other-note',
        text='text',
        author=other_user,
        pub_date=timezone.now(),
    )

    # Своя заметка
    Note.objects.create(
        title='My note',
        slug='my-note',
        text='text',
        author=user,
        pub_date=timezone.now(),
    )

    client.force_login(user)
    url = reverse('notes:list')
    response = client.get(url)

    assert response.status_code == 200
    object_list = response.context.get('object_list')
    assert object_list is not None

    titles = [n.title for n in object_list]
    assert 'My note' in titles
    assert 'Other note' not in titles
