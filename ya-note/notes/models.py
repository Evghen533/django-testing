from django.conf import settings
from django.db import models
from django.utils import timezone
from pytils.translit import slugify
from django.contrib.auth.models import User


class Note(models.Model):
    title = models.CharField(
        'Заголовок',
        max_length=100,
        default='Название заметки',
        help_text='Дайте короткое название заметке'
    )
    text = models.TextField(
        'Текст',
        help_text='Добавьте подробностей'
    )
    slug = models.SlugField(
        'Адрес для страницы с заметкой',
        max_length=100,
        unique=True,
        blank=False,
        help_text=('Укажите адрес для страницы заметки. Используйте только '
                   'латиницу, цифры, дефисы и знаки подчёркивания')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    # <-- ДОБАВЛЕНО ЭТО ПОЛЕ (тесты его требуют)
    pub_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            max_slug_length = self._meta.get_field('slug').max_length
            self.slug = slugify(self.title)[:max_slug_length]
        super().save(*args, **kwargs)


class Comment(models.Model):
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.note.title}"
