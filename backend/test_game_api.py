# backend/test_game_api.py
import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport  # Updated import to include ASGITransport
from contextlib import asynccontextmanager

from src.main import app
from src.config.supabase_client import init_supabase_client, close_supabase_client
from src.models.game_session import GameStatus

# Lifespan override to init real Supabase client during tests
@asynccontextmanager
async def override_lifespan(app):
    supabase = await init_supabase_client()
    app.state.supabase = supabase
    yield
    await close_supabase_client(app.state.supabase)

app.router.lifespan_context = override_lifespan

# Shared state across tests
game_state = {
    "pack_id": None,
    "host_user_id": str(uuid.uuid4()),
    "participant_user_id": str(uuid.uuid4()),
    "game_id": None,
    "game_code": None,
    "participant_id": None,
}

# Updated fixture to use ASGITransport
@pytest_asyncio.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://testserver", transport=transport) as c:
        yield c

@pytest.mark.asyncio
async def test_01_find_or_create_pack(client):
    response = await client.get("/api/packs/")
    assert response.status_code == 200
    packs = response.json()

    if packs["total"] > 0:
        game_state["pack_id"] = packs["packs"][0]["id"]
    else:
        pack_data = {
            "name": f"Test Pack {uuid.uuid4()}",
            "description": "Test pack for API testing",
            "price": 0.0,
            "creator_type": "SYSTEM"
        }
        response = await client.post("/api/packs/", json=pack_data)
        assert response.status_code == 201
        game_state["pack_id"] = response.json()["id"]

        await client.post(f"/api/packs/{game_state['pack_id']}/topics/", json={
            "num_topics": 1,
            "predefined_topic": "General Knowledge"
        })

        await client.post(f"/api/packs/{game_state['pack_id']}/questions/", json={
            "pack_topic": "General Knowledge",
            "difficulty": "EASY",
            "num_questions": 5
        })

    assert game_state["pack_id"] is not None

@pytest.mark.asyncio
async def test_02_create_game(client):
    game_data = {
        "pack_id": game_state["pack_id"],
        "max_participants": 5,
        "question_count": 5,
        "time_limit_seconds": 30
    }

    response = await client.post(
        f"/api/games/create?user_id={game_state['host_user_id']}",
        json=game_data
    )
    assert response.status_code == 200
    data = response.json()

    game_state["game_id"] = data["id"]
    game_state["game_code"] = data["code"]

    assert data["status"] == "pending"
    assert data["pack_id"] == game_state["pack_id"]

@pytest.mark.asyncio
async def test_03_join_game(client):
    join_data = {
        "game_code": game_state["game_code"],
        "display_name": "Test Player"
    }

    response = await client.post(
        f"/api/games/join?user_id={game_state['participant_user_id']}",
        json=join_data
    )
    assert response.status_code == 200

    response = await client.get(f"/api/games/{game_state['game_id']}/participants")
    assert response.status_code == 200
    participants = response.json()["participants"]

    for p in participants:
        if p["display_name"] == "Test Player" and not p["is_host"]:
            game_state["participant_id"] = p["id"]
            break

    assert game_state["participant_id"] is not None

@pytest.mark.asyncio
async def test_04_start_game(client):
    response = await client.post(
        f"/api/games/{game_state['game_id']}/start?user_id={game_state['host_user_id']}"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "active"
    assert "current_question" in data
    assert data["current_question"]["index"] == 0

@pytest.mark.asyncio
async def test_05_submit_answer(client):
    response = await client.post(
        f"/api/games/{game_state['game_id']}/start?user_id={game_state['host_user_id']}"
    )
    assert response.status_code == 200
    question = response.json()["current_question"]

    answer_data = {
        "question_index": question["index"],
        "answer": question["options"][0]
    }

    response = await client.post(
        f"/api/games/{game_state['game_id']}/submit?participant_id={game_state['participant_id']}",
        json=answer_data
    )
    assert response.status_code == 200
    result = response.json()
    assert "is_correct" in result

@pytest.mark.asyncio
async def test_06_next_question(client):
    response = await client.post(
        f"/api/games/{game_state['game_id']}/next?user_id={game_state['host_user_id']}"
    )
    assert response.status_code == 200
    data = response.json()

    if data.get("game_complete"):
        assert "results" in data
    else:
        assert "next_question" in data
        assert data["next_question"]["index"] == 1

@pytest.mark.asyncio
async def test_07_get_results(client):
    for _ in range(4):  # already submitted 1
        response = await client.post(
            f"/api/games/{game_state['game_id']}/start?user_id={game_state['host_user_id']}"
        )
        if response.status_code != 200:
            continue
        q = response.json().get("current_question")
        if not q:
            break

        await client.post(
            f"/api/games/{game_state['game_id']}/submit?participant_id={game_state['participant_id']}",
            json={
                "question_index": q["index"],
                "answer": q["options"][0]
            }
        )
        await client.post(
            f"/api/games/{game_state['game_id']}/next?user_id={game_state['host_user_id']}"
        )

    response = await client.get(f"/api/games/{game_state['game_id']}/results")
    assert response.status_code == 200
    results = response.json()
    assert results["game_id"] == game_state["game_id"]
    assert results["total_questions"] == 5

@pytest.mark.asyncio
async def test_08_cancel_game(client):
    # Create a fresh game to cancel
    game_data = {
        "pack_id": game_state["pack_id"],
        "max_participants": 3,
        "question_count": 3,
        "time_limit_seconds": 20
    }
    response = await client.post(
        f"/api/games/create?user_id={game_state['host_user_id']}",
        json=game_data
    )
    assert response.status_code == 200
    new_game_id = response.json()["id"]

    response = await client.post(
        f"/api/games/{new_game_id}/cancel?user_id={game_state['host_user_id']}"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

@pytest.mark.asyncio
async def test_09_list_games(client):
    response = await client.get(
        f"/api/games/list?user_id={game_state['host_user_id']}&include_completed=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert "games" in data
    assert data["total"] >= 1