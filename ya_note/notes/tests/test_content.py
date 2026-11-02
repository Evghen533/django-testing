import pytest
from notes.forms import NoteForm
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
        cls.user = User.objects.create_user(username='testuser', password='123')
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
        """Проверяем, что в контексте страницы списка заметок есть object_list."""
        url = reverse('notes:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('object_list', response.context)
        object_list = response.context['object_list']
        self.assertTrue(len(object_list) > 0)

    def test_notes_isolation(self):
        """Пользователь видит только свои заметки: чужие не попадают в список."""
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

        object_list = response.context['object_list']
        items = list(object_list)
        self.assertLessEqual(len(items), limit)

def test_note_in_list_for_author(note, author_client):
    url = reverse('notes:list')
    # Запрашиваем страницу со списком заметок:
    response = author_client.get(url)
    # Получаем список объектов из контекста:
    object_list = response.context['object_list']
    # Проверяем, что заметка находится в этом списке:
    assert note in object_list


# В этом тесте тоже используем фикстуру заметки,
# но в качестве клиента используем not_author_client;
# в этом клиенте авторизован не автор заметки,
# так что заметка не должна быть ему видна.
def test_note_not_in_list_for_another_user(note, not_author_client):
    url = reverse('notes:list')
    response = not_author_client.get(url)
    object_list = response.context['object_list']
    # Проверяем, что заметки нет в контексте страницы:
    assert note not in object_list

@pytest.mark.parametrize(
    # Задаём названия для параметров:
    'parametrized_client, note_in_list',
    (
        # Передаём фикстуры в параметры при помощи "ленивых фикстур":
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('not_author_client'), False),
    )
)
# Используем фикстуру заметки и параметры из декоратора:
def test_notes_list_for_different_users(
    note, parametrized_client, note_in_list
):
    url = reverse('notes:list')
    # Выполняем запрос от имени параметризованного клиента:
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    # Проверяем истинность утверждения "заметка есть в списке":
    assert (note in object_list) is note_in_list

def test_create_note_page_contains_form(author_client):
    url = reverse('notes:add')
    # Запрашиваем страницу создания заметки:
    response = author_client.get(url)
    # Проверяем, есть ли объект form в словаре контекста:
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], NoteForm)


# В параметры теста передаём фикстуру slug_for_args и клиент с автором заметки:
def test_edit_note_page_contains_form(slug_for_args, author_client):
    url = reverse('notes:edit', args=slug_for_args)
    # Запрашиваем страницу редактирования заметки:
    response = author_client.get(url)
    # Проверяем, есть ли объект form в словаре контекста:
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], NoteForm)

@pytest.mark.parametrize(
    # В качестве параметров передаём name и args для reverse.
    'name, args',
    (
        # Для тестирования страницы создания заметки
        # никакие дополнительные аргументы для reverse() не нужны.
        ('notes:add', None),
        # Для тестирования страницы редактирования заметки нужен slug заметки.
        ('notes:edit', pytest.lazy_fixture('slug_for_args'))
    )
)
def test_pages_contains_form(author_client, name, args):
    # Формируем URL.
    url = reverse(name, args=args)
    # Запрашиваем нужную страницу:
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста:
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], NoteForm)
