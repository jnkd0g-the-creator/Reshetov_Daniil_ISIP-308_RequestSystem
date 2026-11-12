import pytest
from pydantic import ValidationError

from coffeedesk.models import RequestCreate


def test_bug01_boolean_is_not_an_integer_identifier():
    with pytest.raises(ValidationError):
        RequestCreate(title="Проверка ID", description="Булево значение не должно превращаться в ID бара.", cafe_id=True, category_id=1)
