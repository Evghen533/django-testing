"""Тесты контента и отображения заметок."""

import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_notes_list_limit(client, many_notes):
    """На странице списка должно отображаться ровно NOTES_PER_PAGE заметок."""
    url = reverse('notes:list')
    response = client.get(url)
    assert response.status_code == 200
    object_list = response.context['object_list']
    limit = getattr(settings, 'NOTES_PER_PAGE', 10)
    assert len(object_list) == limit


@pytest.mark.django_db
def test_notes_order_on_list(client, many_notes):
    """Заметки должны идти по убыванию pub_date (новые сверху)."""
    url = reverse('notes:list')
    response = client.get(url)
    assert response.status_code == 200
    object_list = response.context['object_list']
    dates = [n.pub_date for n in object_list]
    assert dates == sorted(dates, reverse=True)
