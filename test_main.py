from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
import pytest
from httpx import AsyncClient

from main import app

client = TestClient(app)

def test_login_correct():
    correct_details = {
        "email": "dj@test.com",
        "password": "dj"
    }
    response = client.post(
        "api/users/login",
        json=jsonable_encoder(correct_details)
    )
    assert response.status_code == 200

def test_login_incorrect():
    incorrect_details = {
        "email": "",
        "password": ""
    }
    response = client.post(
        "api/users/login",
        json=jsonable_encoder(incorrect_details)
    )
    assert response.status_code == 401

def test_get_events():
    user_id = "7e631e89-bfab-49c7-8139-3cc451b5cdf7"
    response = client.get(
        "api/users/%s/events" % user_id,
    )
    assert response.status_code == 200

def test_get_events_no_user():
    user_id = "0"
    response = client.get(
        "api/users/%s/events" % user_id,
    )
    assert response.status_code == 404

@pytest.mark.anyio
async def test_update_user_balance():
    user_id = "7e631e89-bfab-49c7-8139-3cc451b5cdf7"
    async with AsyncClient(app=app, base_url="https://djbuddy.online") as ac:
        user = await ac.get("api/users/%s" % user_id)
        current_balance = float(user.json()["balance"])
        assert current_balance is not None, "User has no balance"

        amount = 100
        new_amount = await ac.put("api/users/%s/balance/%s" % (user_id, amount))
        assert float(new_amount.json()) == current_balance + amount, "User balance not added correctly"

        old_amount = await ac.put("api/users/%s/balance/%s/remove" % (user_id, amount))
        assert float(old_amount.json()) == current_balance, "User balance not subtracted correctly"

@pytest.mark.anyio
async def test_update_user_balance_negative():
    user_id = "7e631e89-bfab-49c7-8139-3cc451b5cdf7"
    async with AsyncClient(app=app, base_url="https://djbuddy.online") as ac:
        user = await ac.get("api/users/%s" % user_id)
        current_balance = float(user.json()["balance"])
        assert current_balance is not None, "User has no balance"

        remove = await ac.put("api/users/%s/balance/%s/remove" % (user_id, current_balance + 1))
        assert remove.status_code == 400, "User balance could be subtracted to negative"

def test_get_event_theme():
    theme = "271f30fe-b540-4a73-8675-015227b381fd"
    response = client.get(
        "api/events/%s/theme" % theme,
    )
    assert response.status_code == 200, "Event theme not found"

def test_get_event_theme_not_found():
    theme = "notfound"
    response = client.get(
        "api/events/%s/theme" % theme,
    )
    assert response.status_code == 400, "Event theme found"
