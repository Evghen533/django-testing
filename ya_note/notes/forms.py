from pytils.translit import slugify

from django import forms
from django.core.exceptions import ValidationError

from .models import Note

WARNING = ' - такой slug уже существует, придумайте уникальное значение!'


class NoteForm(forms.ModelForm):
    """Форма для создания или обновления заметки."""

    class Meta:
        model = Note
        fields = ('title', 'text', 'slug')

    def clean_slug(self):
        cleaned_data = super().clean()
        slug = cleaned_data.get('slug')
        title = cleaned_data.get('title')

        if not slug or slug.strip() == '':
            if not title:
                raise ValidationError(
                    'Заголовок обязателен, если не указан slug.'
                )
            slug = slugify(title)[:100]

        qs = Note.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(id=self.instance.pk)

        if qs.exists():
            raise ValidationError(f'{slug}{WARNING}')

        return slug
