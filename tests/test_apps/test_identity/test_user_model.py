import pytest

from server.apps.identity.models import User


@pytest.mark.django_db()
def test_email_is_required(user_data_factory):
    """Test validation of user data with empty email field."""
    user_data = user_data_factory()
    user_data.pop('email')
    with pytest.raises(ValueError, match='Users must have an email address'):
        User.objects.create_user(None, 'a', **user_data)
