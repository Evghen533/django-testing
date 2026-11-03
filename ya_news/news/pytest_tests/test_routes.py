import pytest
from http import HTTPStatus
from django.urls import reverse


@pytest.mark.django_db
def test_home_page(client):
    url = reverse('news:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_detail_page(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "name,args",
    [
        ('news:home', None),
        ('users:login', None),
        ('users:signup', None),
    ],
)
@pytest.mark.django_db
def test_public_pages_availability(client, name, args):
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_news_detail_with_existing_news(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_author_can_access_comment_edit_and_delete(client, comment, author):
    client.force_login(author)
    actions = ['news:edit', 'news:delete']
    for action_name in actions:
        url = reverse(action_name, args=(comment.id,))
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_reader_cannot_access_comment_edit_and_delete(client, comment, reader):
    client.force_login(reader)
    actions = ['news:edit', 'news:delete']
    for action_name in actions:
        url = reverse(action_name, args=(comment.id,))
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_redirect_for_anonymous_on_comment_actions(client, comment):
    login_url = reverse('users:login')
    actions = ['news:edit', 'news:delete']
    for action_name in actions:
        url = reverse(action_name, args=(comment.id,))
        redirect_url = f'{login_url}?next={url}'
        response = client.get(url, follow=True)
        assert any(
            redirect_url in redirect for redirect in response.redirect_chain
        )
        assert response.status_code == HTTPStatus.OK
