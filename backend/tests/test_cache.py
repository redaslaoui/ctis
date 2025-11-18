"""
Tests for the cache service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.cache import CacheService, cached
import json


class TestCacheService:
    """Test suite for CacheService"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        with patch('app.services.cache.redis.from_url') as mock_from_url:
            mock_client = Mock()
            mock_from_url.return_value = mock_client
            mock_client.ping.return_value = True
            yield mock_client

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Create a CacheService instance with mocked Redis"""
        return CacheService()

    def test_generate_cache_key(self, cache_service):
        """Test cache key generation"""
        key1 = cache_service._generate_cache_key("test", "arg1", "arg2", key="value")
        key2 = cache_service._generate_cache_key("test", "arg1", "arg2", key="value")
        key3 = cache_service._generate_cache_key("test", "arg1", "arg3", key="value")

        # Same arguments should generate same key
        assert key1 == key2

        # Different arguments should generate different keys
        assert key1 != key3

        # Key should have prefix
        assert key1.startswith("test:")

    def test_get_cache_hit(self, cache_service, mock_redis):
        """Test cache get with hit"""
        test_value = {"data": "test"}
        mock_redis.get.return_value = json.dumps(test_value)

        result = cache_service.get("test_key")

        assert result == test_value
        mock_redis.get.assert_called_once_with("test_key")

    def test_get_cache_miss(self, cache_service, mock_redis):
        """Test cache get with miss"""
        mock_redis.get.return_value = None

        result = cache_service.get("test_key")

        assert result is None

    def test_set_cache(self, cache_service, mock_redis):
        """Test cache set"""
        test_value = {"data": "test"}
        ttl = 3600

        result = cache_service.set("test_key", test_value, ttl=ttl)

        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0] == "test_key"
        assert call_args[1] == ttl
        assert json.loads(call_args[2]) == test_value

    def test_delete_cache(self, cache_service, mock_redis):
        """Test cache delete"""
        result = cache_service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    def test_clear_pattern(self, cache_service, mock_redis):
        """Test clearing cache by pattern"""
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3

        count = cache_service.clear_pattern("test:*")

        assert count == 3
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    def test_get_stats(self, cache_service, mock_redis):
        """Test getting cache statistics"""
        mock_redis.info.return_value = {
            "total_connections_received": 100,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }

        stats = cache_service.get_stats()

        assert stats["status"] == "connected"
        assert stats["keyspace_hits"] == 800
        assert stats["keyspace_misses"] == 200
        assert stats["hit_rate"] == 80.0  # 800 / (800+200) * 100

    def test_cached_decorator(self, mock_redis):
        """Test the cached decorator"""
        call_count = 0

        @cached("test_func", ttl=3600)
        def test_function(arg1, arg2):
            nonlocal call_count
            call_count += 1
            return f"{arg1}_{arg2}"

        # First call should execute the function
        mock_redis.get.return_value = None
        result1 = test_function("a", "b")

        assert result1 == "a_b"
        assert call_count == 1

        # Second call with same args should use cache
        mock_redis.get.return_value = json.dumps("a_b")
        result2 = test_function("a", "b")

        assert result2 == "a_b"
        assert call_count == 1  # Function not called again

    def test_cache_connection_failure(self):
        """Test cache service with connection failure"""
        with patch('app.services.cache.redis.from_url') as mock_from_url:
            mock_from_url.side_effect = Exception("Connection failed")

            cache = CacheService()

            # Operations should not fail, but return None/False
            assert cache.get("key") is None
            assert cache.set("key", "value") is False
            assert cache.delete("key") is False
            assert cache.clear_pattern("*") == 0
