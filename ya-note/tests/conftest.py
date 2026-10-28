import pytest
from django.contrib.auth import get_user_model
from notes.models import Note
from django.utils import timezone

User = get_user_model()

@pytest.fixture
def author(db):
    return User.objects.create_user(username='author', password='pass')

@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='other', password='pass')

@pytest.fixture
def note(author, db):
    # slug будет сгенерирован автоматически, если у тебя в модели Note есть save() с slugify
    return Note.objects.create(
        title='Test note',
        text='Text',
        author=author,
        pub_date=timezone.now(),
    )
