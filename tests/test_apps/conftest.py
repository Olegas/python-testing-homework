import json
from http import HTTPStatus
from typing import TypedDict
from urllib.parse import urljoin

import httpretty
import pytest
from django_fakery import factory
from mimesis import Field, Schema
from mimesis.locales import Locale

from server.apps.identity.models import User
from server.common.django.types import Settings


@pytest.fixture()
def user_data_factory(faker_seed):
    """Factory to create fake random data user data."""

    def factory(**fields):
        field = Field(locale=Locale.EN, seed=faker_seed)
        schema = Schema(
            schema=lambda: {
                'email': field('person.email'),
                'first_name': field('person.first_name'),
                'last_name': field('person.last_name'),
                'date_of_birth': field('date'),
                'address': field('address'),
                'job_title': field('person.occupation'),
                'phone': field('person.phone_number'),
                'lead_id': field('numeric.integer_number', start=1),
            },
            iterations=1,
        )
        user_data = schema.create()[0]
        return {
            **user_data,
            **fields,
        }

    return factory


@pytest.fixture()
def mock_user_data(user_data_factory):
    """Returns random user data."""
    return user_data_factory()


@pytest.fixture()
def mock_registration_data(mock_user_data, faker_seed):
    """Returns random registration data."""
    field = Field(locale=Locale.RU, seed=faker_seed)
    password = field('password')
    return {
        **mock_user_data,
        **{'password1': password, 'password2': password},
    }


@pytest.fixture()
def mock_user_model(mock_user_data) -> User:
    """Returns random user model."""
    return factory.m(User)(**mock_user_data)


@pytest.fixture()
def mock_user_update_api(settings: Settings, mock_user_data):  # noqa: PT004
    """Mocks Placeholder API call for specified user."""
    with httpretty.enabled(allow_net_connect=False):
        httpretty.register_uri(
            httpretty.PATCH,
            urljoin(
                settings.PLACEHOLDER_API_URL,
                'users/{0}'.format(mock_user_data['lead_id']),
            ),
            status=HTTPStatus.OK,
        )
        yield
        assert httpretty.has_request()


class ExternalApiCreateResponse(TypedDict):
    """Represent Placeholder API create user response."""

    id: int


@pytest.fixture()
def external_api_create_response(faker_seed) -> ExternalApiCreateResponse:
    """Returns random response for create user request."""
    field = Field(locale=Locale.EN, seed=faker_seed)
    schema = Schema(
        schema=lambda: {
            'id': field('numeric.increment'),
        },
        iterations=1,
    )
    return schema.create()[0]


@pytest.fixture()
def mock_user_create_api(
    settings: Settings,
    external_api_create_response: ExternalApiCreateResponse,
) -> ExternalApiCreateResponse:
    """Mocks Placeholder API call for user create request."""
    with httpretty.enabled(allow_net_connect=False):
        httpretty.register_uri(
            httpretty.POST,
            urljoin(
                settings.PLACEHOLDER_API_URL,
                '/users',
            ),
            body=json.dumps(external_api_create_response),
            status=HTTPStatus.OK,
        )
        yield external_api_create_response
        assert httpretty.has_request()


@pytest.fixture(scope='session')
def assert_correct_user():
    """Returns a function to validate user."""

    def factory(email: str, expected) -> None:
        user = User.objects.get(email=email)
        for field_name, data_value in expected.items():
            assert getattr(user, field_name) == data_value

    return factory
