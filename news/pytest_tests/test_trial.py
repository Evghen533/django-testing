# news/tests/test_trial.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.test import TestCase

from news.models import News

User = get_user_model()


class TestNews(TestCase):
    TITLE = 'Заголовок новости'
    TEXT = 'Тестовый текст'

class TestNews(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя.
        cls.user = User.objects.create(username='testUser')
        # Создаём объект клиента.
        cls.user_client = Client()
        # "Логинимся" в клиенте при помощи метода force_login().
        cls.user_client.force_login(cls.user)

    def test_successful_creation(self):
        news_count = News.objects.count()
        self.assertEqual(news_count, 1)

    def test_title(self):
        self.assertEqual(self.news.title, self.TITLE)
