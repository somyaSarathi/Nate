import os
import sys
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone, timedelta
import logging
import asyncio
from dataclasses import dataclass
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class DiscordBot:
    """Simple interface for bot verification."""
    guilds: List[Dict[str, List[str]]]

class Conversation(BaseModel):
    channel_id: str
    messages: List[Dict[str, str]]
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

class DatabaseClient:
    def __init__(self) -> None:
        """Initialize database client with cleanup task."""
        try:
            # Construct MongoDB URI
            uri = (
                f"mongodb+srv://{settings.MONGODB_USERNAME}:{settings.MONGODB_PASSWORD}"
                f"@{settings.MONGODB_CLUSTER}/{settings.MONGODB_DB_NAME}"
                "?retryWrites=true&w=majority&appName=Cluster0"
            )
            logger.info(f"Connecting to MongoDB cluster: {settings.MONGODB_CLUSTER}")
            self.client = AsyncIOMotorClient(uri)
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.conversations = self.db.conversations
            self.cleanup_task = None
            self.is_running = False
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def start_cleanup_task(self, bot: Any) -> None:  # type: ignore
        """
        Start the daily cleanup task.

        Args:
            bot: Discord client instance for channel verification
        """
        if self.cleanup_task is None:
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_routine(bot))
            logger.info("Started database cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop the cleanup task."""
        if self.cleanup_task:
            self.is_running = False
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
            logger.info("Stopped database cleanup task")

    async def _cleanup_routine(self, bot: Any) -> None:  # type: ignore
        """
        Routine to clean up conversations from deleted channels.

        Args:
            bot: Discord client instance for channel verification
        """
        while self.is_running:
            try:
                # Get all channel IDs from database
                cursor = self.conversations.find({}, {"channel_id": 1})
                stored_channel_ids = set()
                async for doc in cursor:
                    stored_channel_ids.add(doc["channel_id"])

                # Get all active channel IDs from bot
                active_channel_ids = set()
                for guild in bot.guilds:
                    for channel in guild.text_channels:
                        active_channel_ids.add(str(channel.id))

                # Find and delete conversations from non-existent channels
                deleted_channels = stored_channel_ids - active_channel_ids
                if deleted_channels:
                    result = await self.conversations.delete_many(
                        {"channel_id": {"$in": list(deleted_channels)}}
                    )
                    logger.info(
                        f"Cleaned up {result.deleted_count} conversations from deleted channels"
                    )

            except Exception as e:
                logger.error(f"Error in cleanup routine: {e}")

            # Wait for 24 hours before next cleanup
            await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds

    async def get_conversation(self, channel_id: str) -> Optional[Conversation]:
        """Get conversation by channel ID."""
        try:
            result = await self.conversations.find_one({"channel_id": channel_id})
            return Conversation(**result) if result else None
        except Exception as e:
            logger.error(f"Error fetching conversation: {e}")
            raise

    async def save_conversation(self, conversation: Conversation) -> bool:
        """Save or update a conversation."""
        try:
            conversation.updated_at = datetime.now(timezone.utc)
            result = await self.conversations.update_one(
                {"channel_id": conversation.channel_id},
                {"$set": conversation.dict()},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            raise

    async def delete_conversation(self, channel_id: str) -> bool:
        """Delete a conversation by channel ID."""
        try:
            result = await self.conversations.delete_one({"channel_id": channel_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    
    async def test_database():
        db = DatabaseClient()
        conversation = Conversation(
            channel_id="test_channel",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        try:
            # Test basic operations
            await db.save_conversation(conversation)
            result = await db.get_conversation("test_channel")
            print(f"Saved and retrieved conversation: {result}")

            # Mock bot for testing cleanup
            mock_bot = DiscordBot(guilds=[
                {"text_channels": [{"id": "test_channel"}]}
            ])
            print("Database operations working correctly")
            print("Note: Actual cleanup task will be tested with Discord bot instance")

        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test_database())
