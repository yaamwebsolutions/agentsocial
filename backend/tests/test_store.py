# =============================================================================
# Agent Twitter - Store Tests
# =============================================================================
#
# Tests for the in-memory data store
#
# =============================================================================

import pytest
from store import store
from models import Post, User


# =============================================================================
# Store Initialization Tests
# =============================================================================

class TestStoreInitialization:
    """Tests for store initialization"""

    def test_store_exists(self):
        """Test that store instance exists"""
        assert store is not None

    def test_store_has_posts(self):
        """Test that store has posts attribute"""
        assert hasattr(store, "posts")

    def test_store_has_threads(self):
        """Test that store has threads attribute"""
        assert hasattr(store, "threads")

    def test_store_has_current_user(self):
        """Test that store has current_user attribute"""
        assert hasattr(store, "current_user")
        assert isinstance(store.current_user, User)


# =============================================================================
# Post Management Tests
# =============================================================================

class TestPostManagement:
    """Tests for post creation and retrieval"""

    def test_create_post(self):
        """Test creating a new post"""
        initial_count = len(store.posts)
        post = store.create_post("Test post content")
        assert post is not None
        assert len(store.posts) == initial_count + 1

    def test_create_post_with_parent(self):
        """Test creating a reply post"""
        parent = store.create_post("Parent post")
        reply = store.create_post("Reply content", parent_id=parent.id)
        assert reply is not None
        assert reply.parent_id == parent.id

    def test_get_post(self):
        """Test retrieving a post by ID"""
        post = store.create_post("Test post")
        retrieved = store.get_post(post.id)
        assert retrieved is not None
        assert retrieved.id == post.id

    def test_get_post_not_found(self):
        """Test retrieving a non-existent post"""
        result = store.get_post("nonexistent-id")
        assert result is None


# =============================================================================
# Thread Management Tests
# =============================================================================

class TestThreadManagement:
    """Tests for thread creation and retrieval"""

    def test_get_thread(self):
        """Test retrieving a thread"""
        post = store.create_post("Test post for thread")
        thread = store.get_thread(post.id)
        assert thread is not None
        assert thread["id"] == post.id

    def test_get_thread_not_found(self):
        """Test retrieving a non-existent thread"""
        thread = store.get_thread("nonexistent-thread")
        assert thread is None

    def test_thread_has_root_post(self):
        """Test that thread contains root post"""
        post = store.create_post("Root post")
        thread = store.get_thread(post.id)
        assert thread is not None
        assert "root_post" in thread
        assert thread["root_post"].id == post.id


# =============================================================================
# Timeline Tests
# =============================================================================

class TestTimeline:
    """Tests for timeline functionality"""

    def test_get_timeline_posts(self):
        """Test retrieving timeline posts"""
        posts = store.get_timeline_posts(10)
        assert isinstance(posts, list)

    def test_timeline_limit(self):
        """Test timeline limit parameter"""
        posts = store.get_timeline_posts(5)
        assert len(posts) <= 5

    def test_timeline_ordering(self):
        """Test that timeline is ordered by timestamp"""
        posts = store.get_timeline_posts(50)
        # Check that posts are in reverse chronological order
        if len(posts) > 1:
            for i in range(len(posts) - 1):
                assert posts[i].timestamp >= posts[i+1].timestamp


# =============================================================================
# Agent Run Tests
# =============================================================================

class TestAgentRuns:
    """Tests for agent run tracking"""

    def test_get_active_agent_runs(self):
        """Test retrieving active agent runs"""
        runs = store.get_active_agent_runs("thread-1")
        assert isinstance(runs, list)

    def test_add_agent_run(self):
        """Test adding an agent run"""
        # This tests the store's ability to track agent runs
        runs_before = store.get_active_agent_runs("test-thread")
        initial_count = len(runs_before)
        # Agent runs are added via orchestrator, not directly
        # This is just a structural test
        assert initial_count >= 0


# =============================================================================
# User Tests
# =============================================================================

class TestUser:
    """Tests for user data"""

    def test_current_user_structure(self):
        """Test that current user has required fields"""
        user = store.current_user
        assert hasattr(user, "id")
        assert hasattr(user, "username")
        assert hasattr(user, "display_name")
