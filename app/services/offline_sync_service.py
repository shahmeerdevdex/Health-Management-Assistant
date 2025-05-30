from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import json
from typing import Dict, List, Optional, Any
import logging
from app.db.models.ehr_sync import EHRRecord, FHIRResourceCache
from app.schemas.ehr_sync import EHRSyncRequest, EHRSyncResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class OfflineSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.offline_storage = {}  # In-memory cache for offline data
        self.sync_queue = []  # Queue for pending sync operations
        self.last_sync_time = None

    async def store_offline_data(self, user_id: int, data: Dict[str, Any]) -> None:
        """Store data for offline access."""
        try:
            # Store in memory cache
            self.offline_storage[user_id] = {
                "data": data,
                "timestamp": datetime.utcnow(),
                "sync_status": "pending"
            }
            
            # Store in local storage (IndexedDB/AsyncStorage)
            await self._persist_to_local_storage(user_id, data)
            
            # Add to sync queue
            self.sync_queue.append({
                "user_id": user_id,
                "data": data,
                "timestamp": datetime.utcnow(),
                "type": "store"
            })
            
            logger.info(f"Data stored offline for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store offline data: {str(e)}")
            raise

    async def get_offline_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve offline data for a user."""
        try:
            # Try memory cache first
            if user_id in self.offline_storage:
                return self.offline_storage[user_id]["data"]
            
            # Try local storage
            data = await self._get_from_local_storage(user_id)
            if data:
                # Update memory cache
                self.offline_storage[user_id] = {
                    "data": data,
                    "timestamp": datetime.utcnow(),
                    "sync_status": "cached"
                }
                return data
            
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve offline data: {str(e)}")
            return None

    async def sync_offline_data(self, user_id: int) -> bool:
        """Sync offline data with the server."""
        try:
            # Get offline data
            offline_data = await self.get_offline_data(user_id)
            if not offline_data:
                return True

            # Create sync request
            sync_request = EHRSyncRequest(
                user_id=user_id,
                **offline_data
            )

            # Perform sync
            result = await self._perform_sync(sync_request)
            
            if result:
                # Clear offline storage
                self.offline_storage.pop(user_id, None)
                await self._clear_local_storage(user_id)
                
                # Update sync status
                self.last_sync_time = datetime.utcnow()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to sync offline data: {str(e)}")
            return False

    async def get_sync_status(self, user_id: int) -> Dict[str, Any]:
        """Get the sync status for a user."""
        try:
            offline_data = self.offline_storage.get(user_id, {})
            return {
                "has_offline_data": bool(offline_data),
                "last_sync": self.last_sync_time,
                "pending_changes": len(self.sync_queue),
                "sync_status": offline_data.get("sync_status", "unknown")
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {str(e)}")
            return {
                "has_offline_data": False,
                "last_sync": None,
                "pending_changes": 0,
                "sync_status": "error"
            }

    async def _persist_to_local_storage(self, user_id: int, data: Dict[str, Any]) -> None:
        """Persist data to local storage."""
        try:
            # This would be implemented based on the client-side storage mechanism
            # For example, using IndexedDB in web browsers or AsyncStorage in React Native
            pass
        except Exception as e:
            logger.error(f"Failed to persist to local storage: {str(e)}")
            raise

    async def _get_from_local_storage(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve data from local storage."""
        try:
            # This would be implemented based on the client-side storage mechanism
            return None
        except Exception as e:
            logger.error(f"Failed to get from local storage: {str(e)}")
            return None

    async def _clear_local_storage(self, user_id: int) -> None:
        """Clear data from local storage."""
        try:
            # This would be implemented based on the client-side storage mechanism
            pass
        except Exception as e:
            logger.error(f"Failed to clear local storage: {str(e)}")
            raise

    async def _perform_sync(self, sync_request: EHRSyncRequest) -> bool:
        """Perform the actual sync operation."""
        try:
            # Get EHR record
            result = await self.db.execute(
                select(EHRRecord).where(EHRRecord.user_id == sync_request.user_id)
            )
            record = result.scalars().first()

            if record:
                # Update existing record
                record.medical_history = sync_request.medical_history
                record.medications = sync_request.medications
                record.procedures = sync_request.procedures
                record.allergies = sync_request.allergies
                record.last_synced = datetime.utcnow()
                record.sync_status = "success"
            else:
                # Create new record
                record = EHRRecord(
                    user_id=sync_request.user_id,
                    medical_history=sync_request.medical_history,
                    medications=sync_request.medications,
                    procedures=sync_request.procedures,
                    allergies=sync_request.allergies,
                    sync_status="success"
                )
                self.db.add(record)

            await self.db.commit()
            await self.db.refresh(record)
            return True
        except Exception as e:
            logger.error(f"Failed to perform sync: {str(e)}")
            return False 