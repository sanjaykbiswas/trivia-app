# backend/test_pack_topic_creation.py
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.utils.question_generation.pack_topic_creation import PackTopicCreation
from src.repositories.pack_creation_data_repository import PackCreationDataRepository
from src.utils.llm.llm_service import LLMService
from src.models.pack_creation_data import PackCreationData, PackCreationDataCreate, PackCreationDataUpdate


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    llm_service = MagicMock(spec=LLMService)
    # Mock the generate_content method to return a sample response
    llm_service.generate_content = AsyncMock()
    return llm_service


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    repo = MagicMock(spec=PackCreationDataRepository)
    # Mock the async methods
    repo.get_by_pack_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def pack_topic_creation(mock_repository, mock_llm_service):
    """Create a PackTopicCreation instance with mocked dependencies."""
    return PackTopicCreation(
        pack_creation_data_repository=mock_repository,
        llm_service=mock_llm_service
    )


@pytest.mark.asyncio
async def test_create_pack_topics(pack_topic_creation, mock_llm_service):
    """Test the create_pack_topics method."""
    # Setup mock response from LLM
    mock_response = """
    • Ancient Greek philosophers and their contributions
    • The Peloponnesian War and its impact
    • Greek mythology and its influence on modern culture
    • Architecture of ancient Greece
    • The Olympic games: origins and evolution
    """
    mock_llm_service.generate_content.return_value = mock_response
    
    # Call the method
    topics = await pack_topic_creation.create_pack_topics(
        creation_name="Ancient Greece",
        creation_description="A trivia pack about Ancient Greek history and culture",
        num_topics=5
    )
    
    # Verify LLM was called with appropriate prompt
    mock_llm_service.generate_content.assert_called_once()
    prompt_arg = mock_llm_service.generate_content.call_args[0][0]
    assert "Ancient Greece" in prompt_arg
    assert "5 specific topics" in prompt_arg
    
    # Verify correct topics were extracted
    assert len(topics) == 5
    assert "Ancient Greek philosophers and their contributions" in topics
    assert "The Olympic games: origins and evolution" in topics


@pytest.mark.asyncio
async def test_create_pack_topics_too_few_results(pack_topic_creation, mock_llm_service):
    """Test the create_pack_topics method handles too few topics correctly."""
    # First call returns only 3 topics
    mock_llm_service.generate_content.side_effect = [
        """
        • Ancient Greek philosophers
        • Greek mythology
        • The Olympic games
        """,
        """
        • The Peloponnesian War
        • Architecture of ancient Greece
        • Greek literature and drama
        """
    ]
    
    topics = await pack_topic_creation.create_pack_topics(
        creation_name="Ancient Greece",
        num_topics=5
    )
    
    # Should make a second call and combine results
    assert mock_llm_service.generate_content.call_count == 2
    assert len(topics) == 5  # Should have requested additional topics


def test_parse_topic_list(pack_topic_creation):
    """Test the _parse_topic_list method with different formats."""
    # Test with bullet points
    bullet_response = """
    • First topic
    • Second topic
    • Third topic
    """
    topics = pack_topic_creation._parse_topic_list(bullet_response)
    assert len(topics) == 3
    assert topics == ["First topic", "Second topic", "Third topic"]
    
    # Test with different bullet character
    asterisk_response = """
    * First topic
    * Second topic
    * Third topic
    """
    topics = pack_topic_creation._parse_topic_list(asterisk_response)
    assert len(topics) == 3
    
    # Test with numbered list
    numbered_response = """
    1. First topic
    2. Second topic
    3. Third topic
    """
    topics = pack_topic_creation._parse_topic_list(numbered_response)
    assert len(topics) == 3
    
    # Test with mixed format
    mixed_response = """
    Here are some topics:
    • First topic
    * Second topic
    - Third topic
    """
    topics = pack_topic_creation._parse_topic_list(mixed_response)
    assert len(topics) == 3


@pytest.mark.asyncio
async def test_store_pack_topics_new(pack_topic_creation, mock_repository):
    """Test storing pack topics when no existing data is present."""
    # Setup mock to return None (no existing data)
    mock_repository.get_by_pack_id.return_value = None
    
    pack_id = uuid.uuid4()
    topics = ["Topic 1", "Topic 2", "Topic 3"]
    description = "Test description"
    
    await pack_topic_creation.store_pack_topics(pack_id, topics, description)
    
    # Verify repository.create was called with correct data
    mock_repository.create.assert_called_once()
    create_call = mock_repository.create.call_args[1]["obj_in"]
    assert isinstance(create_call, PackCreationDataCreate)
    assert create_call.pack_id == pack_id
    assert create_call.pack_topics == topics
    assert create_call.creation_description == description


@pytest.mark.asyncio
async def test_store_pack_topics_existing(pack_topic_creation, mock_repository):
    """Test storing pack topics when existing data is present."""
    # Setup mock to return existing data
    existing_id = uuid.uuid4()
    existing_data = PackCreationData(
        id=existing_id,
        pack_id=uuid.uuid4(),
        pack_topics=["Old topic"],
        custom_difficulty_description=[]
    )
    mock_repository.get_by_pack_id.return_value = existing_data
    
    pack_id = existing_data.pack_id
    topics = ["Topic 1", "Topic 2", "Topic 3"]
    description = "Test description"
    
    await pack_topic_creation.store_pack_topics(pack_id, topics, description)
    
    # Verify repository.update was called with correct data
    mock_repository.update.assert_called_once()
    update_id = mock_repository.update.call_args[1]["id"]
    update_data = mock_repository.update.call_args[1]["obj_in"]
    assert update_id == existing_id
    assert isinstance(update_data, PackCreationDataUpdate)
    assert update_data.pack_topics == topics
    assert update_data.creation_description == description


@pytest.mark.asyncio
async def test_get_existing_pack_topics(pack_topic_creation, mock_repository):
    """Test retrieving existing pack topics."""
    # Setup mock repository response
    pack_id = uuid.uuid4()
    expected_topics = ["Topic 1", "Topic 2", "Topic 3"]
    mock_repository.get_by_pack_id.return_value = PackCreationData(
        id=uuid.uuid4(),
        pack_id=pack_id,
        pack_topics=expected_topics,
        custom_difficulty_description=[]
    )
    
    # Get topics
    topics = await pack_topic_creation.get_existing_pack_topics(pack_id)
    
    # Verify correct topics returned
    assert topics == expected_topics
    mock_repository.get_by_pack_id.assert_called_once_with(pack_id)


@pytest.mark.asyncio
async def test_get_existing_pack_topics_none(pack_topic_creation, mock_repository):
    """Test retrieving existing pack topics when none exist."""
    # Setup mock repository response
    pack_id = uuid.uuid4()
    mock_repository.get_by_pack_id.return_value = None
    
    # Get topics when none exist
    topics = await pack_topic_creation.get_existing_pack_topics(pack_id)
    
    # Verify empty list returned
    assert topics == []
    mock_repository.get_by_pack_id.assert_called_once_with(pack_id)


@pytest.mark.asyncio
async def test_add_additional_topics(pack_topic_creation, mock_repository, mock_llm_service):
    """Test adding additional topics to existing ones."""
    # Setup existing topics
    pack_id = uuid.uuid4()
    existing_topics = ["Existing topic 1", "Existing topic 2"]
    mock_repository.get_by_pack_id.return_value = PackCreationData(
        id=uuid.uuid4(),
        pack_id=pack_id,
        pack_topics=existing_topics,
        custom_difficulty_description=[]
    )
    
    # Setup LLM response
    new_topics_response = """
    • New topic 1
    • New topic 2
    • New topic 3
    """
    mock_llm_service.generate_content.return_value = new_topics_response
    
    # Add additional topics
    all_topics = await pack_topic_creation.add_additional_topics(
        pack_id=pack_id,
        creation_name="Test Pack",
        num_additional_topics=3
    )
    
    # Verify LLM prompt contained existing topics
    prompt = mock_llm_service.generate_content.call_args[0][0]
    for topic in existing_topics:
        assert topic in prompt
    
    # Verify store_pack_topics was called with combined list
    assert len(all_topics) == 5  # 2 existing + 3 new
    assert "Existing topic 1" in all_topics
    assert "New topic 3" in all_topics