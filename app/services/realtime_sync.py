from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import asyncio
import logging
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.ehr_sync import (
    EHRSystem,
    FHIRResourceType,
    EHRConnectionConfig,
    EHRSyncRequest,
    EHRSyncResponse,
    FHIRResource,
    NationalDatabaseType,
    WebhookEvent
)
from app.db.models.ehr_sync import EHRConnection, EHRRecord
from app.services.ehr_sync import EHRService

logger = logging.getLogger(__name__)

class RealtimeSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ehr_service = EHRService(db)
        self.sync_tasks: Dict[int, asyncio.Task] = {}
        self.sync_intervals: Dict[int, int] = {}  # Store sync intervals in seconds
        self.active_websockets: Dict[int, Set[WebSocket]] = {}  # Store active WebSocket connections
        self.webhook_handlers: Dict[str, List[callable]] = {}  # Store webhook handlers

    async def start_sync(
        self,
        user_id: int,
        ehr_system: EHRSystem,
        sync_interval: int = 300,  # Default 5 minutes
        national_databases: Optional[List[NationalDatabaseType]] = None
    ) -> Dict[str, Any]:
        """Start real-time synchronization for a user's EHR data."""
        try:
            # Check if sync is already running
            if user_id in self.sync_tasks and not self.sync_tasks[user_id].done():
                return {
                    "status": "already_running",
                    "message": "Real-time sync is already running for this user"
                }

            # Store sync interval
            self.sync_intervals[user_id] = sync_interval

            # Create sync task
            self.sync_tasks[user_id] = asyncio.create_task(
                self._run_sync_loop(user_id, ehr_system, national_databases)
            )

            return {
                "status": "started",
                "message": f"Real-time sync started with interval of {sync_interval} seconds",
                "user_id": user_id,
                "ehr_system": ehr_system,
                "sync_interval": sync_interval
            }
        except Exception as e:
            logger.error(f"Failed to start real-time sync: {str(e)}")
            raise

    async def stop_sync(self, user_id: int) -> Dict[str, Any]:
        """Stop real-time synchronization for a user."""
        try:
            if user_id not in self.sync_tasks:
                return {
                    "status": "not_running",
                    "message": "No real-time sync running for this user"
                }

            # Cancel the sync task
            self.sync_tasks[user_id].cancel()
            try:
                await self.sync_tasks[user_id]
            except asyncio.CancelledError:
                pass

            # Clean up
            del self.sync_tasks[user_id]
            if user_id in self.sync_intervals:
                del self.sync_intervals[user_id]

            return {
                "status": "stopped",
                "message": "Real-time sync stopped successfully",
                "user_id": user_id
            }
        except Exception as e:
            logger.error(f"Failed to stop real-time sync: {str(e)}")
            raise

    async def get_sync_status(self, user_id: int) -> Dict[str, Any]:
        """Get the current status of real-time synchronization."""
        try:
            if user_id not in self.sync_tasks:
                return {
                    "status": "not_running",
                    "message": "No real-time sync running for this user"
                }

            task = self.sync_tasks[user_id]
            if task.done():
                if task.exception():
                    return {
                        "status": "error",
                        "message": f"Sync failed: {str(task.exception())}",
                        "user_id": user_id
                    }
                return {
                    "status": "completed",
                    "message": "Sync completed successfully",
                    "user_id": user_id
                }

            return {
                "status": "running",
                "message": "Real-time sync is running",
                "user_id": user_id,
                "sync_interval": self.sync_intervals.get(user_id)
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {str(e)}")
            raise

    async def _run_sync_loop(
        self,
        user_id: int,
        ehr_system: EHRSystem,
        national_databases: Optional[List[NationalDatabaseType]]
    ) -> None:
        """Run the synchronization loop."""
        try:
            while True:
                # Create sync request
                request = EHRSyncRequest(
                    user_id=user_id,
                    ehr_system=ehr_system,
                    national_databases=national_databases or []
                )

                # Perform sync
                await self.ehr_service.sync_ehr_data(request)

                # Wait for next sync interval
                await asyncio.sleep(self.sync_intervals[user_id])
        except asyncio.CancelledError:
            logger.info(f"Real-time sync cancelled for user {user_id}")
            raise
        except Exception as e:
            logger.error(f"Error in sync loop for user {user_id}: {str(e)}")
            raise

    async def update_sync_interval(
        self,
        user_id: int,
        new_interval: int
    ) -> Dict[str, Any]:
        """Update the synchronization interval for a user."""
        try:
            if user_id not in self.sync_tasks:
                return {
                    "status": "error",
                    "message": "No real-time sync running for this user"
                }

            # Update interval
            self.sync_intervals[user_id] = new_interval

            return {
                "status": "updated",
                "message": f"Sync interval updated to {new_interval} seconds",
                "user_id": user_id,
                "new_interval": new_interval
            }
        except Exception as e:
            logger.error(f"Failed to update sync interval: {str(e)}")
            raise

    async def connect_websocket(self, websocket: WebSocket, user_id: int) -> None:
        """Connect a WebSocket client for real-time updates."""
        await websocket.accept()
        if user_id not in self.active_websockets:
            self.active_websockets[user_id] = set()
        self.active_websockets[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect_websocket(self, websocket: WebSocket, user_id: int) -> None:
        """Disconnect a WebSocket client."""
        if user_id in self.active_websockets:
            self.active_websockets[user_id].remove(websocket)
            if not self.active_websockets[user_id]:
                del self.active_websockets[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def broadcast_update(self, user_id: int, message: Dict[str, Any]) -> None:
        """Broadcast an update to all connected WebSocket clients for a user."""
        if user_id in self.active_websockets:
            disconnected = set()
            for websocket in self.active_websockets[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {str(e)}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                await self.disconnect_websocket(websocket, user_id)

    async def handle_webhook(self, connection_id: int, event_type: str, data: Dict[str, Any]) -> None:
        """Handle incoming webhook events."""
        try:
            # Get connection details
            connection = await self._get_connection(connection_id)
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")

            # Process webhook based on event type
            if event_type == "data_update":
                # Trigger immediate sync
                request = EHRSyncRequest(
                    user_id=connection.user_id,
                    ehr_system=connection.ehr_system,
                    national_databases=[]  # Add if needed
                )
                sync_result = await self.ehr_service.sync_ehr_data(request)
                
                # Broadcast update to connected clients
                await self.broadcast_update(
                    connection.user_id,
                    {
                        "type": "data_update",
                        "data": sync_result.dict()
                    }
                )
            elif event_type == "connection_status":
                # Update connection status
                connection.status = data.get("status", "unknown")
                await self.db.commit()
                
                # Broadcast status update
                await self.broadcast_update(
                    connection.user_id,
                    {
                        "type": "connection_status",
                        "data": {"status": connection.status}
                    }
                )
            else:
                logger.warning(f"Unknown webhook event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise

    async def _get_connection(self, connection_id: int) -> Optional[EHRConnection]:
        """Get EHR connection by ID."""
        result = await self.db.execute(
            select(EHRConnection).where(EHRConnection.id == connection_id)
        )
        return result.scalars().first()

    async def get_user_connections(self, user_id: int) -> List[EHRConnection]:
        """Get all active EHR connections for a user."""
        result = await self.db.execute(
            select(EHRConnection).where(
                EHRConnection.user_id == user_id,
                EHRConnection.is_active == True
            )
        )
        return result.scalars().all()

    async def update_connection(
        self,
        connection_id: int,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> EHRConnection:
        """Update an EHR connection."""
        connection = await self._get_connection(connection_id)
        if not connection or connection.user_id != user_id:
            raise ValueError("Connection not found or unauthorized")

        for key, value in update_data.items():
            setattr(connection, key, value)

        await self.db.commit()
        await self.db.refresh(connection)
        return connection 