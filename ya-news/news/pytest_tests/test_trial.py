"""Заготовки тестов (trial) для приложения news."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from news.models import News

User = get_user_model()


class TestNews(TestCase):
    """Базовые тесты для модели News."""

    TITLE = 'Заголовок новости'
    TEXT = 'Тестовый текст'

    @classmethod
    def setUpTestData(cls):
        """Подготовка тестовых данных для всех тестов класса."""
        cls.user = User.objects.create(username='testUser')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.news = News.objects.create(
            title=cls.TITLE,
            text=cls.TEXT,
            date='2024-01-01'
        )

    def test_successful_creation(self):
        """Проверка, что тестовая новость была создана."""
        news_count = News.objects.count()
        self.assertEqual(news_count, 1)

    def test_title(self):
        """Проверка корректности заголовка новости."""
        self.assertEqual(self.news.title, self.TITLE)
