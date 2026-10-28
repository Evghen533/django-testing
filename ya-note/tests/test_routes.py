import pytest
from http import HTTPStatus
from django.urls import reverse

@pytest.mark.django_db
def test_home_page_anonymous(client):
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

@pytest.mark.django_db
def test_detail_page_anonymous(client, note):
    url = reverse('notes:detail', args=[note.slug])
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

@pytest.mark.django_db
def test_edit_redirect_anonymous(client, note):
    url = reverse('notes:edit', args=[note.slug])
    response = client.get(url, follow=True)
    # Аноним должен быть редиректнут на страницу входа
    assert response.redirect_chain
    login_url = reverse('users:login')
    assert response.redirect_chain[-1][0].startswith(login_url)
    assert 'next' in response.redirect_chain[-1][0]

@pytest.mark.django_db
def test_delete_redirect_anonymous(client, note):
    url = reverse('notes:delete', args=[note.slug])
    response = client.get(url, follow=True)
    assert response.redirect_chain
    login_url = reverse('users:login')
    assert response.redirect_chain[-1][0].startswith(login_url)

@pytest.mark.django_db
def test_edit_other_user_note_404(client, author, other_user, note):
    client.force_login(other_user)
    url = reverse('notes:edit', args=[note.slug])
    response = client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_delete_other_user_note_404(client, author, other_user, note):
    client.force_login(other_user)
    url = reverse('notes:delete', args=[note.slug])
    response = client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_pages_availability(client):
    urls = [
        ('notes:home', None),
        ('users:login', None),
        ('users:signup', None),
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, f"URL {url} не доступен"
