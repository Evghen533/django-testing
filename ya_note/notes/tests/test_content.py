from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from notes.models import Note


class ContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username='testuser',
            password='123'
        )
        base_date = timezone.now()
        for i in range(15):
            Note.objects.create(
                title=f'Note {i}',
                slug=f'note-{i}',
                text='text',
                author=cls.user,
                pub_date=base_date - timedelta(days=i),
            )

    def setUp(self):
        self.client.force_login(self.user)

    def test_object_list_in_context(self):
        """Проверяем, что на странице списка заметок есть object_list."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']
        self.assertTrue(len(object_list) > 0)

    def test_notes_isolation(self):
        """Пользователь видит только свои заметки: чужие не попадаются."""
        User = get_user_model()
        other_user = User.objects.create_user(username='other', password='123')

        Note.objects.create(
            title='Other note',
            slug='other-note',
            text='text',
            author=other_user,
            pub_date=timezone.now(),
        )

        Note.objects.create(
            title='My note',
            slug='my-note',
            text='text',
            author=self.user,
            pub_date=timezone.now(),
        )

        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        titles = [n.title for n in response.context['object_list']]
        self.assertIn('My note', titles)
        self.assertNotIn('Other note', titles)

    def test_notes_order_on_list(self):
        """Заметки в списке идут по убыванию даты публикации (новые сверху)."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        object_list = response.context['object_list']
        dates = [n.pub_date for n in object_list]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_pagination_limit(self):
        """На странице отображается не больше NOTES_PER_PAGE заметок."""
        from django.conf import settings
        limit = getattr(settings, 'NOTES_PER_PAGE', 10)

        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        items = list(response.context['object_list'])
        self.assertLessEqual(len(items), limit)
