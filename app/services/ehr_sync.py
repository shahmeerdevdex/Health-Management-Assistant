from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import jwt
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
    NationalDatabaseSyncConfig
)
from app.db.models.ehr_sync import EHRConnection, EHRRecord, FHIRResourceCache,NationalDatabaseConnection

from app.core.config import settings
import logging
import json
from cryptography.fernet import Fernet
import base64
import asyncio

logger = logging.getLogger(__name__)

class EHRService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ehr_systems = {
            EHRSystem.EPIC: self._handle_epic,
            EHRSystem.CERNER: self._handle_cerner,
            EHRSystem.AHPRA: self._handle_ahpra,
            EHRSystem.CUSTOM: self._handle_custom
        }

    async def connect_ehr_system(
        self,
        user_id: int,
        config: EHRConnectionConfig
    ) -> EHRConnection:
        """Establish connection with an EHR system using the Hybrid Proxy Model."""
        try:
            # For AHPRA, use direct integration
            if config.ehr_system == EHRSystem.AHPRA:
                token = await self._get_ahpra_token(config)
            else:
                # For other systems, validate provider credentials
                if not config.additional_config.get("provider_id"):
                    raise ValueError("Provider ID is required for non-AHPRA systems")
                token = await self._get_provider_token(config)

            # Create connection record
            connection = EHRConnection(
                user_id=user_id,
                ehr_system=config.ehr_system,
                connection_config=config.dict(),
                access_token=token["access_token"],
                refresh_token=token.get("refresh_token"),
                token_expires_at=datetime.fromtimestamp(token.get("expires_at", 0)),
                last_sync=datetime.utcnow()
            )
            
            self.db.add(connection)
            await self.db.commit()
            await self.db.refresh(connection)
            
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to EHR system: {str(e)}")
            raise

    async def _get_provider_token(self, config: EHRConnectionConfig) -> Dict[str, Any]:
        """Get OAuth token using provider credentials (Hybrid Proxy Model)."""
        try:
            # Get provider credentials from secure storage
            provider_id = config.additional_config.get("provider_id")
            if not provider_id:
                raise ValueError("Provider ID is required")

            # Get provider credentials from secure storage
            provider_credentials = await self._get_provider_credentials(provider_id)
            if not provider_credentials:
                raise ValueError("Provider credentials not found")

            # Use provider credentials to get token
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.token_endpoint,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": provider_credentials["client_id"],
                        "client_secret": provider_credentials["client_secret"],
                        "scope": config.scope
                    }
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to get provider token: {await response.text()}")
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to get provider token: {str(e)}")
            raise

    async def _get_ahpra_token(self, config: EHRConnectionConfig) -> Dict[str, Any]:
        """Get AHPRA token (direct integration)."""
        try:
            # Use AHPRA API credentials from settings
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.token_endpoint,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.AHPRA_PIE_API_KEY,
                        "client_secret": config.client_secret,
                        "scope": config.scope
                    }
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to get AHPRA token: {await response.text()}")
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to get AHPRA token: {str(e)}")
            raise

    async def _get_provider_credentials(self, provider_id: int) -> Optional[Dict[str, Any]]:
        """Get provider credentials from secure storage."""
        try:
            # Get encrypted credentials from database
            result = await self.db.execute(
                select(NationalDatabaseConnection).where(
                    NationalDatabaseConnection.provider_id == provider_id,
                    NationalDatabaseConnection.is_active == True
                )
            )
            connection = result.scalar_one_or_none()
            if not connection:
                return None

            # Decrypt credentials (implement your decryption logic here)
            return connection.encrypted_credentials
        except Exception as e:
            logger.error(f"Failed to get provider credentials: {str(e)}")
            return None

    async def sync_ehr_data(
        self,
        request: EHRSyncRequest
    ) -> EHRSyncResponse:
        """Synchronize EHR data with the specified system."""
        try:
            # Get EHR connection
            connection = await self._get_ehr_connection(request.user_id, request.ehr_system)
            if not connection:
                raise ValueError(f"No active connection found for {request.ehr_system}")

            # Get handler for the EHR system
            handler = self.ehr_systems.get(request.ehr_system)
            if not handler:
                raise ValueError(f"Unsupported EHR system: {request.ehr_system}")

            # Sync data using the appropriate handler
            sync_result = await handler(connection, request)

            # Sync with national databases if specified
            national_sync_status = {}
            if request.national_databases:
                for db_type in request.national_databases:
                    try:
                        db_handler = self.national_databases.get(db_type)
                        if db_handler:
                            db_result = await db_handler(request.user_id, connection)
                            national_sync_status[db_type] = "success"
                            # Merge national database results with sync_result
                            sync_result = self._merge_sync_results(sync_result, db_result)
                    except Exception as e:
                        logger.error(f"Failed to sync with {db_type}: {str(e)}")
                        national_sync_status[db_type] = f"error: {str(e)}"

            # Update EHR record
            record = await self._update_ehr_record(request.user_id, sync_result)

            return EHRSyncResponse(
                ehr_id=f"EHR-{record.user_id}",
                ehr_system=request.ehr_system,
                medical_history=sync_result.get("medical_history", []),
                medications=sync_result.get("medications", []),
                procedures=sync_result.get("procedures", []),
                allergies=sync_result.get("allergies", []),
                immunizations=sync_result.get("immunizations", []),
                fhir_resources=sync_result.get("fhir_resources", []),
                last_updated=record.last_synced,
                sync_status=record.sync_status,
                sync_message=record.sync_message,
                national_database_sync_status=national_sync_status
            )
        except Exception as e:
            logger.error(f"Failed to sync EHR data: {str(e)}")
            raise

    async def _get_ehr_connection(
        self,
        user_id: int,
        ehr_system: EHRSystem
    ) -> Optional[EHRConnection]:
        """Get active EHR connection for user."""
        result = await self.db.execute(
            select(EHRConnection).where(
                EHRConnection.user_id == user_id,
                EHRConnection.ehr_system == ehr_system,
                EHRConnection.is_active == True
            )
        )
        return result.scalars().first()

    async def _update_ehr_record(
        self,
        user_id: int,
        sync_result: Dict[str, Any]
    ) -> EHRRecord:
        """Update or create EHR record with synced data."""
        result = await self.db.execute(
            select(EHRRecord).where(EHRRecord.user_id == user_id)
        )
        record = result.scalars().first()

        if record:
            record.medical_history = sync_result.get("medical_history", [])
            record.medications = sync_result.get("medications", [])
            record.procedures = sync_result.get("procedures", [])
            record.allergies = sync_result.get("allergies", [])
            record.fhir_resources = sync_result.get("fhir_resources", [])
            record.last_synced = datetime.utcnow()
            record.sync_status = "success"
        else:
            record = EHRRecord(
                user_id=user_id,
                ehr_system=sync_result["ehr_system"],
                medical_history=sync_result.get("medical_history", []),
                medications=sync_result.get("medications", []),
                procedures=sync_result.get("procedures", []),
                allergies=sync_result.get("allergies", []),
                fhir_resources=sync_result.get("fhir_resources", []),
                sync_status="success"
            )
            self.db.add(record)

        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def _handle_epic(
        self,
        connection: EHRConnection,
        request: EHRSyncRequest
    ) -> Dict[str, Any]:
        """Handle Epic EHR system synchronization."""
        try:
            # Get Epic API configuration
            config = connection.connection_config
            api_endpoint = config["api_endpoint"]
            access_token = connection.access_token

            # Prepare headers with authentication
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/fhir+json",
                "Epic-Client-ID": config.get("additional_config", {}).get("epic_client_id", "")
            }

            # Fetch patient data
            async with aiohttp.ClientSession() as session:
                # Fetch patient demographics
                async def fetch_patient():
                    patient_url = f"{api_endpoint}/Patient"
                    async with session.get(patient_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching patient data")
                        patient_data = await response.json()
                        if not self._validate_fhir_resource(patient_data, FHIRResourceType.PATIENT):
                            raise ValueError("Invalid patient resource")
                        return patient_data

                # Fetch medical history
                async def fetch_conditions():
                    conditions_url = f"{api_endpoint}/Condition"
                    async with session.get(conditions_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching conditions")
                        conditions_data = await response.json()
                        for entry in conditions_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.CONDITION):
                                raise ValueError("Invalid condition resource")
                        return conditions_data

                # Fetch medications
                async def fetch_medications():
                    medications_url = f"{api_endpoint}/MedicationRequest"
                    async with session.get(medications_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching medications")
                        medications_data = await response.json()
                        for entry in medications_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.MEDICATION):
                                raise ValueError("Invalid medication resource")
                        return medications_data

                # Fetch procedures
                async def fetch_procedures():
                    procedures_url = f"{api_endpoint}/Procedure"
                    async with session.get(procedures_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching procedures")
                        procedures_data = await response.json()
                        for entry in procedures_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.PROCEDURE):
                                raise ValueError("Invalid procedure resource")
                        return procedures_data

                # Fetch allergies
                async def fetch_allergies():
                    allergies_url = f"{api_endpoint}/AllergyIntolerance"
                    async with session.get(allergies_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching allergies")
                        allergies_data = await response.json()
                        for entry in allergies_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.ALLERGY):
                                raise ValueError("Invalid allergy resource")
                        return allergies_data

                # Fetch immunizations
                async def fetch_immunizations():
                    immunizations_url = f"{api_endpoint}/Immunization"
                    async with session.get(immunizations_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching immunizations")
                        immunizations_data = await response.json()
                        for entry in immunizations_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.IMMUNIZATION):
                                raise ValueError("Invalid immunization resource")
                        return immunizations_data

                # Execute all fetches with retry logic
                patient_data = await self._retry_with_backoff(fetch_patient)
                conditions_data = await self._retry_with_backoff(fetch_conditions)
                medications_data = await self._retry_with_backoff(fetch_medications)
                procedures_data = await self._retry_with_backoff(fetch_procedures)
                allergies_data = await self._retry_with_backoff(fetch_allergies)
                immunizations_data = await self._retry_with_backoff(fetch_immunizations)

            # Transform data to our format
            return {
                "ehr_system": EHRSystem.EPIC,
                "medical_history": self._transform_conditions(conditions_data),
                "medications": self._transform_medications(medications_data),
                "procedures": self._transform_procedures(procedures_data),
                "allergies": self._transform_allergies(allergies_data),
                "immunizations": self._transform_immunizations(immunizations_data),
                "fhir_resources": [
                    FHIRResource(
                        resource_type=FHIRResourceType.PATIENT,
                        resource_id=patient_data["id"],
                        data=patient_data,
                        version="1",
                        last_updated=datetime.utcnow(),
                        source_system="epic"
                    )
                ]
            }
        except Exception as e:
            logger.error(f"Failed to sync with Epic: {str(e)}")
            raise

    async def _handle_cerner(
        self,
        connection: EHRConnection,
        request: EHRSyncRequest
    ) -> Dict[str, Any]:
        """Handle Cerner EHR system synchronization."""
        try:
            # Get Cerner API configuration
            config = connection.connection_config
            api_endpoint = config["api_endpoint"]
            access_token = connection.access_token

            # Prepare headers with authentication
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/fhir+json",
                "Cerner-Client-ID": config.get("additional_config", {}).get("cerner_client_id", "")
            }

            # Fetch patient data
            async with aiohttp.ClientSession() as session:
                # Fetch patient demographics
                async def fetch_patient():
                    patient_url = f"{api_endpoint}/Patient"
                    async with session.get(patient_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching patient data")
                        patient_data = await response.json()
                        if not self._validate_fhir_resource(patient_data, FHIRResourceType.PATIENT):
                            raise ValueError("Invalid patient resource")
                        return patient_data

                # Fetch medical history
                async def fetch_conditions():
                    conditions_url = f"{api_endpoint}/Condition"
                    async with session.get(conditions_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching conditions")
                        conditions_data = await response.json()
                        for entry in conditions_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.CONDITION):
                                raise ValueError("Invalid condition resource")
                        return conditions_data

                # Fetch medications
                async def fetch_medications():
                    medications_url = f"{api_endpoint}/MedicationRequest"
                    async with session.get(medications_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching medications")
                        medications_data = await response.json()
                        for entry in medications_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.MEDICATION):
                                raise ValueError("Invalid medication resource")
                        return medications_data

                # Fetch procedures
                async def fetch_procedures():
                    procedures_url = f"{api_endpoint}/Procedure"
                    async with session.get(procedures_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching procedures")
                        procedures_data = await response.json()
                        for entry in procedures_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.PROCEDURE):
                                raise ValueError("Invalid procedure resource")
                        return procedures_data

                # Fetch allergies
                async def fetch_allergies():
                    allergies_url = f"{api_endpoint}/AllergyIntolerance"
                    async with session.get(allergies_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching allergies")
                        allergies_data = await response.json()
                        for entry in allergies_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.ALLERGY):
                                raise ValueError("Invalid allergy resource")
                        return allergies_data

                # Fetch immunizations
                async def fetch_immunizations():
                    immunizations_url = f"{api_endpoint}/Immunization"
                    async with session.get(immunizations_url, headers=headers) as response:
                        if response.status != 200:
                            await self._handle_api_error(response, "fetching immunizations")
                        immunizations_data = await response.json()
                        for entry in immunizations_data.get("entry", []):
                            if not self._validate_fhir_resource(entry.get("resource", {}), FHIRResourceType.IMMUNIZATION):
                                raise ValueError("Invalid immunization resource")
                        return immunizations_data

                # Execute all fetches with retry logic
                patient_data = await self._retry_with_backoff(fetch_patient)
                conditions_data = await self._retry_with_backoff(fetch_conditions)
                medications_data = await self._retry_with_backoff(fetch_medications)
                procedures_data = await self._retry_with_backoff(fetch_procedures)
                allergies_data = await self._retry_with_backoff(fetch_allergies)
                immunizations_data = await self._retry_with_backoff(fetch_immunizations)

            # Transform data to our format
            return {
                "ehr_system": EHRSystem.CERNER,
                "medical_history": self._transform_conditions(conditions_data),
                "medications": self._transform_medications(medications_data),
                "procedures": self._transform_procedures(procedures_data),
                "allergies": self._transform_allergies(allergies_data),
                "immunizations": self._transform_immunizations(immunizations_data),
                "fhir_resources": [
                    FHIRResource(
                        resource_type=FHIRResourceType.PATIENT,
                        resource_id=patient_data["id"],
                        data=patient_data,
                        version="1",
                        last_updated=datetime.utcnow(),
                        source_system="cerner"
                    )
                ]
            }
        except Exception as e:
            logger.error(f"Failed to sync with Cerner: {str(e)}")
            raise

    async def _handle_ahpra(
        self,
        connection: EHRConnection,
        request: EHRSyncRequest
    ) -> Dict[str, Any]:
        """Handle AHPRA system synchronization."""
        try:
            # Get AHPRA API configuration
            config = connection.connection_config
            api_endpoint = config["api_endpoint"]
            access_token = connection.access_token

            # Prepare headers with authentication
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/fhir+json"
            }

            # Fetch provider data
            async with aiohttp.ClientSession() as session:
                provider_url = f"{api_endpoint}/Practitioner"
                async with session.get(provider_url, headers=headers) as response:
                    if response.status != 200:
                        await self._handle_api_error(response, "fetching provider data")
                    provider_data = await response.json()

            return {
                "ehr_system": EHRSystem.AHPRA,
                "fhir_resources": [
                    FHIRResource(
                        resource_type=FHIRResourceType.PATIENT,
                        resource_id=provider_data["id"],
                        data=provider_data,
                        version="1",
                        last_updated=datetime.utcnow(),
                        source_system="ahpra"
                    )
                ]
            }
        except Exception as e:
            logger.error(f"Failed to sync with AHPRA: {str(e)}")
            raise

    async def _handle_custom(
        self,
        connection: EHRConnection,
        request: EHRSyncRequest
    ) -> Dict[str, Any]:
        """Handle custom EHR system synchronization."""
        try:
            # Get custom system configuration
            config = connection.connection_config
            if not config:
                raise ValueError("Custom system configuration not found")

            # Prepare headers with authentication
            headers = {
                "Authorization": f"Bearer {connection.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/fhir+json"
            }

            # Fetch data based on custom configuration
            async with aiohttp.ClientSession() as session:
                # Implement custom data fetching logic here
                # This is a placeholder that should be customized based on the specific system
                return {
                    "ehr_system": EHRSystem.CUSTOM,
                    "medical_history": [],
                    "medications": [],
                    "procedures": [],
                    "allergies": [],
                    "immunizations": [],
                    "fhir_resources": []
                }
        except Exception as e:
            logger.error(f"Failed to sync with custom system: {str(e)}")
            raise

    def _transform_conditions(self, conditions_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform FHIR conditions to our format."""
        conditions = []
        for entry in conditions_data.get("entry", []):
            resource = entry.get("resource", {})
            conditions.append({
                "condition": resource.get("code", {}).get("text", ""),
                "diagnosed_on": datetime.fromisoformat(resource.get("onsetDateTime", "")).date(),
                "severity": resource.get("severity", {}).get("text"),
                "status": resource.get("clinicalStatus", {}).get("code"),
                "notes": resource.get("note", [{}])[0].get("text") if resource.get("note") else None,
                "source_system": "my_health_record"
            })
        return conditions

    def _transform_medications(self, medications_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform FHIR medications to our format."""
        medications = []
        for entry in medications_data.get("entry", []):
            resource = entry.get("resource", {})
            medications.append({
                "name": resource.get("medicationCodeableConcept", {}).get("text", ""),
                "dosage": resource.get("dosageInstruction", [{}])[0].get("text", ""),
                "frequency": resource.get("dosageInstruction", [{}])[0].get("timing", {}).get("code", {}).get("text", ""),
                "start_date": datetime.fromisoformat(resource.get("authoredOn", "")).date(),
                "end_date": None,  # Implement if available
                "prescribed_by": resource.get("requester", {}).get("display"),
                "notes": resource.get("note", [{}])[0].get("text") if resource.get("note") else None,
                "source_system": "my_health_record"
            })
        return medications

    def _transform_immunizations(self, immunizations_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform FHIR immunizations to our format."""
        immunizations = []
        for entry in immunizations_data.get("entry", []):
            resource = entry.get("resource", {})
            immunizations.append({
                "vaccine_name": resource.get("vaccineCode", {}).get("text", ""),
                "dose_number": resource.get("doseNumber", 1),
                "date_administered": datetime.fromisoformat(resource.get("occurrenceDateTime", "")).date(),
                "provider": resource.get("performer", [{}])[0].get("actor", {}).get("display", ""),
                "lot_number": resource.get("lotNumber"),
                "manufacturer": resource.get("manufacturer", {}).get("display"),
                "next_due_date": None,  # Implement if available
                "source_system": "my_health_record"
            })
        return immunizations

    def _transform_procedures(self, procedures_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform FHIR procedures to our format."""
        procedures = []
        for entry in procedures_data.get("entry", []):
            resource = entry.get("resource", {})
            procedures.append({
                "name": resource.get("code", {}).get("text", ""),
                "date": datetime.fromisoformat(resource.get("performedDateTime", "")).date(),
                "provider": resource.get("performer", [{}])[0].get("actor", {}).get("display", ""),
                "location": resource.get("location", {}).get("display"),
                "notes": resource.get("note", [{}])[0].get("text") if resource.get("note") else None,
                "procedure_code": resource.get("code", {}).get("coding", [{}])[0].get("code"),
                "source_system": "epic" if resource.get("meta", {}).get("source", "").startswith("epic") else "cerner"
            })
        return procedures

    def _transform_allergies(self, allergies_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform FHIR allergies to our format."""
        allergies = []
        for entry in allergies_data.get("entry", []):
            resource = entry.get("resource", {})
            allergies.append({
                "allergen": resource.get("code", {}).get("text", ""),
                "reaction": resource.get("reaction", [{}])[0].get("manifestation", [{}])[0].get("text", ""),
                "severity": resource.get("reaction", [{}])[0].get("severity"),
                "onset_date": datetime.fromisoformat(resource.get("onsetDateTime", "")).date() if resource.get("onsetDateTime") else None,
                "notes": resource.get("note", [{}])[0].get("text") if resource.get("note") else None,
                "source_system": "epic" if resource.get("meta", {}).get("source", "").startswith("epic") else "cerner"
            })
        return allergies

    def _merge_sync_results(
        self,
        base_result: Dict[str, Any],
        additional_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge results from different sync sources."""
        merged = base_result.copy()
        
        # Merge medical history
        merged["medical_history"].extend(additional_result.get("medical_history", []))
        
        # Merge medications
        merged["medications"].extend(additional_result.get("medications", []))
        
        # Merge immunizations
        merged["immunizations"].extend(additional_result.get("immunizations", []))
        
        # Merge FHIR resources
        merged["fhir_resources"].extend(additional_result.get("fhir_resources", []))
        
        return merged

    async def cache_fhir_resource(
        self,
        user_id: int,
        resource_type: FHIRResourceType,
        resource_id: str,
        ehr_system: EHRSystem,
        data: Dict[str, Any],
        version: str
    ) -> FHIRResourceCache:
        """Cache a FHIR resource."""
        cache = FHIRResourceCache(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ehr_system=ehr_system,
            data=data,
            version=version
        )
        self.db.add(cache)
        await self.db.commit()
        await self.db.refresh(cache)
        return cache

    async def get_cached_fhir_resource(
        self,
        user_id: int,
        resource_type: FHIRResourceType,
        resource_id: str,
        ehr_system: EHRSystem
    ) -> Optional[FHIRResourceCache]:
        """Get a cached FHIR resource."""
        result = await self.db.execute(
            select(FHIRResourceCache).where(
                FHIRResourceCache.user_id == user_id,
                FHIRResourceCache.resource_type == resource_type,
                FHIRResourceCache.resource_id == resource_id,
                FHIRResourceCache.ehr_system == ehr_system,
                FHIRResourceCache.is_deleted == False
            )
        )
        return result.scalars().first()

    def _validate_fhir_resource(self, resource: Dict[str, Any], resource_type: FHIRResourceType) -> bool:
        """Validate FHIR resource structure and required fields."""
        try:
            # Check resource type
            if resource.get("resourceType") != resource_type:
                logger.error(f"Invalid resource type: expected {resource_type}, got {resource.get('resourceType')}")
                return False

            # Validate required fields based on resource type
            if resource_type == FHIRResourceType.PATIENT:
                required_fields = ["id", "name", "gender", "birthDate"]
            elif resource_type == FHIRResourceType.CONDITION:
                required_fields = ["id", "code", "subject", "clinicalStatus"]
            elif resource_type == FHIRResourceType.MEDICATION:
                required_fields = ["id", "medicationCodeableConcept", "subject", "status"]
            elif resource_type == FHIRResourceType.PROCEDURE:
                required_fields = ["id", "code", "subject", "status", "performedDateTime"]
            elif resource_type == FHIRResourceType.ALLERGY:
                required_fields = ["id", "code", "patient", "clinicalStatus"]
            elif resource_type == FHIRResourceType.IMMUNIZATION:
                required_fields = ["id", "vaccineCode", "patient", "occurrenceDateTime"]
            else:
                required_fields = ["id"]

            # Check required fields
            for field in required_fields:
                if field not in resource:
                    logger.error(f"Missing required field {field} in {resource_type} resource")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error validating FHIR resource: {str(e)}")
            return False

    async def _handle_api_error(self, response: aiohttp.ClientResponse, context: str) -> None:
        """Handle API error responses with proper logging and error messages."""
        try:
            error_data = await response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = error_data.get("code", "UNKNOWN")
            
            if response.status == 401:
                raise ValueError(f"Authentication failed: {error_message}")
            elif response.status == 403:
                raise ValueError(f"Authorization failed: {error_message}")
            elif response.status == 404:
                raise ValueError(f"Resource not found: {error_message}")
            elif response.status == 429:
                raise ValueError(f"Rate limit exceeded: {error_message}")
            else:
                raise ValueError(f"API error in {context}: {error_message} (Code: {error_code})")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Unexpected error in {context}: {str(e)}")

    async def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs):
        """Retry a function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) * 1  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time} seconds: {str(e)}")
                await asyncio.sleep(wait_time)
