from http import HTTPStatus

import pytest


@pytest.mark.django_db
def test_home_page_available_to_anonymous(client, home_url):
    response = client.get(home_url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_detail_page_available_to_anonymous(client, detail_url):
    response = client.get(detail_url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_auth_pages_available_to_anonymous(client, signup_url, login_url):
    """Страницы регистрации и входа доступны анонимам."""
    for url in (signup_url, login_url):
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_logout_available_to_anonymous(client, logout_url):
    """Страница выхода доступна анонимам."""
    response = client.post(logout_url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize('url_fixture_name', ['edit_url', 'delete_url'])
def test_comment_pages_available_to_author(
    client,
    comment,
    url_fixture_name,
    request
):
    """Страницы правки и удаления доступны автору комментария."""
    url = request.getfixturevalue(url_fixture_name)
    client.force_login(comment.author)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize('url_fixture_name', ['edit_url', 'delete_url'])
def test_comment_pages_not_available_to_other_user(
    client, comment, reader, url_fixture_name, request
):
    """Чужому пользователю правка и удаление дают 404."""
    url = request.getfixturevalue(url_fixture_name)
    client.force_login(reader)
    response = client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
@pytest.mark.parametrize('url_fixture_name', ['edit_url', 'delete_url'])
def test_anonymous_redirects_to_login(
    client,
    comment,
    login_url,
    url_fixture_name,
    request
):
    """Аноним с защищённых страниц уходит на логин."""
    url = request.getfixturevalue(url_fixture_name)
    expected = f'{login_url}?next={url}'
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == expected
