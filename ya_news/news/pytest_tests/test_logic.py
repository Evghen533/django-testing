from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    COMMENT_TEXT = 'Текст комментария'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        url = reverse('news:detail', args=(self.news.id,))
        self.client.post(url, data=self.form_data)
        self.assertEqual(Comment.objects.count(), 0)

    def test_user_can_create_comment(self):
        url = reverse('news:detail', args=(self.news.id,))
        response = self.auth_client.post(url, data=self.form_data)

        expected_url = reverse('news:detail', args=(self.news.id,))
        self.assertRedirects(response, expected_url)

        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        url = reverse('news:detail', args=(self.news.id,))
        bad_text = f'Какой-то текст, {BAD_WORDS}, еще текст'
        bad_words_data = {'text': bad_text}

        response = self.auth_client.post(url, data=bad_words_data)

        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIn('text', form.errors)

        self.assertEqual(Comment.objects.count(), 0)


class TestCommentEditDelete(TestCase):
    COMMENT_TEXT = 'Текст комментария'
    NEW_COMMENT_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')

        cls.author = User.objects.create(username='Автор комментария')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )

        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def _get_detail_url(self):
        return reverse('news:detail', args=(self.news.id,))

    def _get_edit_url(self):
        return reverse('news:edit', args=(self.comment.id,))

    def _get_delete_url(self):
        return reverse('news:delete', args=(self.comment.id,))

    def test_author_can_delete_comment(self):
        response = self.author_client.delete(self._get_delete_url())
        self.assertRedirects(response, self._get_detail_url())
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), 0)

    def test_user_cant_delete_comment_of_another_user(self, reader_client, comment):
        response = reader_client.delete(comment.get_delete_url())

        assert response.status_code in (
            HTTPStatus.NOT_FOUND,
            HTTPStatus.FORBIDDEN
        )
        assert Comment.objects.count() == 1

    def test_author_can_edit_comment(self):
        response = self.author_client.post(
            self._get_edit_url(),
            data=self.form_data
        )
        self.assertRedirects(response, self._get_detail_url())
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_user_cant_edit_comment_of_another_user(
            self,
            reader_client,
            comment,
            form_data
        ):
        response = reader_client.post(
            comment.get_edit_url(),
            data=form_data,
        )

        assert response.status_code in (
            HTTPStatus.NOT_FOUND,
            HTTPStatus.FORBIDDEN
        )

        comment.refresh_from_db()
        assert comment.text == form_data["text"]
