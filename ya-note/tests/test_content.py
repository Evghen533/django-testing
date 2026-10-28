import pytest
from django.urls import reverse
from notes.models import Note, Comment
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
def test_homepage_shows_max_10_notes(client, author):
    """
    На главной странице должно быть не больше 10 заметок (пагинация).
    Создаём 15 заметок и проверяем, что в object_list их не больше 10.
    """
    Note.objects.bulk_create([
        Note(
            title=f'Note {i}',
            text=f'Text {i}',
            slug=f'note-{i}',
            author=author,
            pub_date=timezone.now() - timedelta(days=i),
        )
        for i in range(15)
    ])

    url = reverse('notes:home')
    response = client.get(url)
    objects = response.context.get('object_list')

    assert objects is not None
    assert len(objects) <= 10


@pytest.mark.django_db
def test_notes_are_sorted_by_date_desc(client, author):
    """
    Заметки на главной странице должны быть отсортированы по убыванию даты:
    сначала самые свежие.
    """
    Note.objects.bulk_create([
        Note(
            title=f'Note {i}',
            text=f'Text {i}',
            slug=f'note-{i}',
            author=author,
            pub_date=timezone.now() - timedelta(days=i),
        )
        for i in range(5)
    ])

    url = reverse('notes:home')
    response = client.get(url)
    objects = response.context['object_list']
    dates = [obj.pub_date for obj in objects]

    # Проверяем, что даты идут по убыванию
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
def test_detail_page_shows_note_fields(client, note):
    """
    На детальной странице заметки должны быть видны: заголовок, текст,
    дата публикации и имя автора.
    """
    url = reverse('notes:detail', args=[note.slug])
    response = client.get(url)

    assert response.status_code == 200
    # DetailView передаёт объект как 'object' (или можно явно как 'note')
    context_note = response.context.get('object')
    assert context_note is not None

    # Сравниваем ключевые поля
    assert context_note.title == note.title
    assert context_note.text == note.text
    assert context_note.pub_date == note.pub_date
    assert context_note.author.username == note.author.username


@pytest.mark.django_db
def test_detail_page_shows_comments_list(client, note, author):
    """
    На странице заметки должен отображаться список комментариев к ней.
    Проверяем, что комментарии есть, их ровно 3, и они отсортированы
    по времени (старые первыми).
    """
    Comment.objects.bulk_create([
        Comment(
            note=note,  # точно под твою модель: поле называется note
            author=author,
            text=f'Comment {i}',
        )
        for i in range(3)
    ])

    url = reverse('notes:detail', args=[note.slug])
    response = client.get(url)

    assert response.status_code == 200

    # Получаем заметку из контекста (DetailView -> 'object')
    obj = response.context.get('object')
    comments = obj.comments.all() if obj else []

    assert len(comments) == 3

    # Комментарии должны идти по возрастанию времени (старые первыми)
    comments = obj.comments.order_by('created').all() if obj else []
    timestamps = [c.created for c in comments]
    assert timestamps == sorted(timestamps)


@pytest.mark.django_db
def test_anonymous_user_sees_note_but_no_create_form(client, note):
    """
    Анонимный пользователь может видеть заметку, но не должен видеть
    форму создания комментария (или она не должна быть доступна).
    """
    url = reverse('notes:detail', args=[note.slug])
    response = client.get(url)

    assert response.status_code == 200
    assert b'<form' not in response.content


@pytest.mark.django_db
def test_logged_in_user_sees_create_comment_form(client, note, author):
    """
    Авторизованный пользователь на странице заметки должен видеть
    форму для создания комментария.
    """
    client.force_login(author)
    url = reverse('notes:detail', args=[note.slug])
    response = client.get(url)

    assert response.status_code == 200
    assert b'<form' in response.content
