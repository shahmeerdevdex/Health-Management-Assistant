from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.db.models.ehr_sync import (
    EHRConnection,
    EHRRecord,
    FHIRResourceCache,
    NationalDatabaseConnection,
    NationalDatabaseSyncRecord
)
from app.schemas.ehr_sync import (
    EHRSystem,
    NationalDatabaseType,
    EHRConnectionConfig,
    NationalDatabaseSyncConfig
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EHRSyncCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ehr_connection(
        self,
        user_id: int,
        ehr_system: EHRSystem,
        config: EHRConnectionConfig
    ) -> EHRConnection:
        """Create a new EHR connection."""
        connection = EHRConnection(
            user_id=user_id,
            ehr_system=ehr_system,
            connection_config=config.dict()
        )
        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def get_ehr_connection(
        self,
        user_id: int,
        ehr_system: EHRSystem
    ) -> Optional[EHRConnection]:
        """Get an active EHR connection."""
        result = await self.db.execute(
            select(EHRConnection).where(
                and_(
                    EHRConnection.user_id == user_id,
                    EHRConnection.ehr_system == ehr_system,
                    EHRConnection.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_ehr_connection(
        self,
        connection_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[EHRConnection]:
        """Update an EHR connection."""
        connection = await self.db.get(EHRConnection, connection_id)
        if connection:
            for key, value in update_data.items():
                setattr(connection, key, value)
            connection.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(connection)
        return connection

    async def create_ehr_record(
        self,
        user_id: int,
        connection_id: int,
        data: Dict[str, Any]
    ) -> EHRRecord:
        """Create a new EHR record."""
        record = EHRRecord(
            user_id=user_id,
            connection_id=connection_id,
            medical_history=data.get("medical_history", []),
            medications=data.get("medications", []),
            procedures=data.get("procedures", []),
            allergies=data.get("allergies", []),
            immunizations=data.get("immunizations", []),
            sync_status="success",
            sync_message="Record created successfully"
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def update_ehr_record(
        self,
        record_id: int,
        data: Dict[str, Any]
    ) -> Optional[EHRRecord]:
        """Update an EHR record."""
        record = await self.db.get(EHRRecord, record_id)
        if record:
            for key, value in data.items():
                setattr(record, key, value)
            record.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(record)
        return record

    async def get_latest_ehr_record(
        self,
        user_id: int,
        connection_id: int
    ) -> Optional[EHRRecord]:
        """Get the latest EHR record for a user and connection."""
        result = await self.db.execute(
            select(EHRRecord)
            .where(
                and_(
                    EHRRecord.user_id == user_id,
                    EHRRecord.connection_id == connection_id
                )
            )
            .order_by(EHRRecord.last_synced.desc())
        )
        return result.scalar_one_or_none()

    async def create_fhir_resource_cache(
        self,
        record_id: int,
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any],
        version: str,
        source_system: str
    ) -> FHIRResourceCache:
        """Create a new FHIR resource cache entry."""
        cache = FHIRResourceCache(
            record_id=record_id,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
            version=version,
            source_system=source_system
        )
        self.db.add(cache)
        await self.db.commit()
        await self.db.refresh(cache)
        return cache

    async def get_fhir_resource_cache(
        self,
        record_id: int,
        resource_type: str,
        resource_id: str
    ) -> Optional[FHIRResourceCache]:
        """Get a FHIR resource cache entry."""
        result = await self.db.execute(
            select(FHIRResourceCache).where(
                and_(
                    FHIRResourceCache.record_id == record_id,
                    FHIRResourceCache.resource_type == resource_type,
                    FHIRResourceCache.resource_id == resource_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_national_database_connection(
        self,
        ehr_connection_id: int,
        database_type: NationalDatabaseType,
        config: NationalDatabaseSyncConfig
    ) -> NationalDatabaseConnection:
        """Create a new national database connection."""
        connection = NationalDatabaseConnection(
            ehr_connection_id=ehr_connection_id,
            database_type=database_type,
            connection_config=config.dict()
        )
        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def get_national_database_connection(
        self,
        ehr_connection_id: int,
        database_type: NationalDatabaseType
    ) -> Optional[NationalDatabaseConnection]:
        """Get an active national database connection."""
        result = await self.db.execute(
            select(NationalDatabaseConnection).where(
                and_(
                    NationalDatabaseConnection.ehr_connection_id == ehr_connection_id,
                    NationalDatabaseConnection.database_type == database_type,
                    NationalDatabaseConnection.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_national_database_sync_record(
        self,
        connection_id: int,
        sync_type: str,
        status: str,
        message: Optional[str] = None,
        data_synced: Optional[Dict[str, Any]] = None
    ) -> NationalDatabaseSyncRecord:
        """Create a new national database sync record."""
        sync_record = NationalDatabaseSyncRecord(
            connection_id=connection_id,
            sync_type=sync_type,
            status=status,
            message=message,
            data_synced=data_synced
        )
        self.db.add(sync_record)
        await self.db.commit()
        await self.db.refresh(sync_record)
        return sync_record

    async def update_national_database_sync_record(
        self,
        sync_record_id: int,
        status: str,
        message: Optional[str] = None,
        data_synced: Optional[Dict[str, Any]] = None
    ) -> Optional[NationalDatabaseSyncRecord]:
        """Update a national database sync record."""
        sync_record = await self.db.get(NationalDatabaseSyncRecord, sync_record_id)
        if sync_record:
            sync_record.status = status
            sync_record.message = message
            if data_synced:
                sync_record.data_synced = data_synced
            sync_record.completed_at = datetime.utcnow()
            sync_record.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(sync_record)
        return sync_record

    async def get_latest_sync_record(
        self,
        connection_id: int
    ) -> Optional[NationalDatabaseSyncRecord]:
        """Get the latest sync record for a national database connection."""
        result = await self.db.execute(
            select(NationalDatabaseSyncRecord)
            .where(NationalDatabaseSyncRecord.connection_id == connection_id)
            .order_by(NationalDatabaseSyncRecord.started_at.desc())
        )
        return result.scalar_one_or_none()
