from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ehr_sync import EHRSystem, FHIRResourceType, NationalDatabaseType
from app.db.models.ehr_sync import EHRConnection, EHRRecord, NationalDatabaseConnection
from app.services.data_mapping_service import DataMappingService
from app.core.config import settings
import aiohttp
import jwt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class RealtimeSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_mapper = DataMappingService()
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.sync_tasks: Dict[int, asyncio.Task] = {}
        self.encryption_key = Fernet(settings.ENCRYPTION_KEY.encode())

    async def connect_websocket(self, websocket: WebSocket, user_id: int):
        """Connect a new WebSocket client."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

        # Start sync task if not already running
        if user_id not in self.sync_tasks:
            self.sync_tasks[user_id] = asyncio.create_task(
                self._start_sync_loop(user_id)
            )

    async def disconnect_websocket(self, websocket: WebSocket, user_id: int):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                # Stop sync task if no active connections
                if user_id in self.sync_tasks:
                    self.sync_tasks[user_id].cancel()
                    del self.sync_tasks[user_id]

    async def _start_sync_loop(self, user_id: int):
        """Start the sync loop for a user."""
        try:
            while True:
                await self._sync_user_data(user_id)
                await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info(f"Sync loop cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in sync loop for user {user_id}: {str(e)}")

    async def _sync_user_data(self, user_id: int):
        """Sync user data with all connected systems."""
        try:
            # Get all active EHR connections
            connections = await self._get_active_connections(user_id)
            
            for connection in connections:
                try:
                    # Sync with EHR system
                    await self._sync_ehr_system(connection)
                    
                    # Sync with national databases
                    await self._sync_national_databases(connection)
                except Exception as e:
                    logger.error(f"Error syncing connection {connection.id}: {str(e)}")
                    await self._notify_error(user_id, str(e))

        except Exception as e:
            logger.error(f"Error in sync_user_data: {str(e)}")
            await self._notify_error(user_id, str(e))

    async def _get_active_connections(self, user_id: int) -> List[EHRConnection]:
        """Get all active EHR connections for a user."""
        # Implementation depends on your database setup
        return []  # Placeholder

    async def _sync_ehr_system(self, connection: EHRConnection):
        """Sync with an EHR system."""
        try:
            # Get webhook URL for the system
            webhook_url = connection.connection_config.get("webhook_url")
            if not webhook_url:
                return

            # Subscribe to webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json={
                        "event_types": ["patient.update", "medication.update", "condition.update"],
                        "callback_url": f"{settings.API_BASE_URL}/webhooks/ehr/{connection.id}"
                    },
                    headers={"Authorization": f"Bearer {connection.access_token}"}
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to subscribe to webhook: {await response.text()}")

        except Exception as e:
            logger.error(f"Error syncing EHR system: {str(e)}")
            raise

    async def _sync_national_databases(self, connection: EHRConnection):
        """Sync with national databases."""
        try:
            for db_connection in connection.national_database_connections:
                if not db_connection.is_active:
                    continue

                # Get webhook URL for the database
                webhook_url = db_connection.connection_config.get("webhook_url")
                if not webhook_url:
                    continue

                # Subscribe to webhook
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url,
                        json={
                            "event_types": ["record.update", "record.create", "record.delete"],
                            "callback_url": f"{settings.API_BASE_URL}/webhooks/national/{db_connection.id}"
                        },
                        headers={"Authorization": f"Bearer {db_connection.access_token}"}
                    ) as response:
                        if response.status != 200:
                            raise ValueError(f"Failed to subscribe to webhook: {await response.text()}")

        except Exception as e:
            logger.error(f"Error syncing national databases: {str(e)}")
            raise

    async def handle_webhook(self, connection_id: int, event_type: str, data: Dict[str, Any]):
        """Handle incoming webhook events."""
        try:
            # Get connection
            connection = await self._get_connection(connection_id)
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")

            # Process event based on type
            if event_type == "patient.update":
                await self._handle_patient_update(connection, data)
            elif event_type == "medication.update":
                await self._handle_medication_update(connection, data)
            elif event_type == "condition.update":
                await self._handle_condition_update(connection, data)
            elif event_type == "record.update":
                await self._handle_record_update(connection, data)
            else:
                logger.warning(f"Unhandled event type: {event_type}")

            # Notify connected clients
            await self._notify_update(connection.user_id, event_type, data)

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise

    async def _handle_patient_update(self, connection: EHRConnection, data: Dict[str, Any]):
        """Handle patient update event."""
        try:
            # Map data to our format
            mapped_data = self.data_mapper.map_resource(
                connection.ehr_system,
                FHIRResourceType.PATIENT,
                data
            )

            # Update local record
            await self._update_local_record(connection.user_id, mapped_data)

        except Exception as e:
            logger.error(f"Error handling patient update: {str(e)}")
            raise

    async def _handle_medication_update(self, connection: EHRConnection, data: Dict[str, Any]):
        """Handle medication update event."""
        try:
            # Map data to our format
            mapped_data = self.data_mapper.map_resource(
                connection.ehr_system,
                FHIRResourceType.MEDICATION,
                data
            )

            # Update local record
            await self._update_local_record(connection.user_id, mapped_data)

        except Exception as e:
            logger.error(f"Error handling medication update: {str(e)}")
            raise

    async def _handle_condition_update(self, connection: EHRConnection, data: Dict[str, Any]):
        """Handle condition update event."""
        try:
            # Map data to our format
            mapped_data = self.data_mapper.map_resource(
                connection.ehr_system,
                FHIRResourceType.CONDITION,
                data
            )

            # Update local record
            await self._update_local_record(connection.user_id, mapped_data)

        except Exception as e:
            logger.error(f"Error handling condition update: {str(e)}")
            raise

    async def _handle_record_update(self, connection: EHRConnection, data: Dict[str, Any]):
        """Handle record update event from national database."""
        try:
            # Map data to our format
            mapped_data = self.data_mapper.map_resource(
                connection.ehr_system,
                FHIRResourceType.PATIENT,  # Default to patient, adjust as needed
                data
            )

            # Update local record
            await self._update_local_record(connection.user_id, mapped_data)

        except Exception as e:
            logger.error(f"Error handling record update: {str(e)}")
            raise

    async def _update_local_record(self, user_id: int, data: Dict[str, Any]):
        """Update local record with new data."""
        try:
            # Get existing record
            record = await self._get_ehr_record(user_id)
            if not record:
                # Create new record
                record = EHRRecord(user_id=user_id)
                self.db.add(record)

            # Update record
            record.medical_history = data.get("medical_history", record.medical_history)
            record.medications = data.get("medications", record.medications)
            record.procedures = data.get("procedures", record.procedures)
            record.allergies = data.get("allergies", record.allergies)
            record.last_synced = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(record)

        except Exception as e:
            logger.error(f"Error updating local record: {str(e)}")
            raise

    async def _notify_update(self, user_id: int, event_type: str, data: Dict[str, Any]):
        """Notify connected clients of an update."""
        if user_id not in self.active_connections:
            return

        # Encrypt sensitive data
        encrypted_data = self._encrypt_sensitive_data(data)

        message = {
            "type": "update",
            "event_type": event_type,
            "data": encrypted_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all connected clients
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                await self.disconnect_websocket(websocket, user_id)
            except Exception as e:
                logger.error(f"Error sending update to client: {str(e)}")

    async def _notify_error(self, user_id: int, error_message: str):
        """Notify connected clients of an error."""
        if user_id not in self.active_connections:
            return

        message = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all connected clients
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                await self.disconnect_websocket(websocket, user_id)
            except Exception as e:
                logger.error(f"Error sending error to client: {str(e)}")

    def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data fields."""
        sensitive_fields = ["ssn", "medicare_number", "health_identifier"]
        encrypted_data = data.copy()

        for field in sensitive_fields:
            if field in encrypted_data:
                encrypted_data[field] = self.encryption_key.encrypt(
                    str(encrypted_data[field]).encode()
                ).decode()

        return encrypted_data 