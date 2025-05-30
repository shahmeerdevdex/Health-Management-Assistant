from pydantic import BaseModel, Field, HttpUrl
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class FHIRResourceType(str, Enum):
    PATIENT = "Patient"
    CONDITION = "Condition"
    OBSERVATION = "Observation"
    MEDICATION = "Medication"
    PROCEDURE = "Procedure"
    ALLERGY = "AllergyIntolerance"
    IMMUNIZATION = "Immunization"
    DOCUMENT = "DocumentReference"
    COVERAGE = "Coverage"
    CLAIM = "Claim"
    EXPLANATION_OF_BENEFIT = "ExplanationOfBenefit"

class EHRSystem(str, Enum):
    EPIC = "epic"
    CERNER = "cerner"
    MY_HEALTH_RECORD = "my_health_record"
    NATIONAL_IMMUNIZATION = "national_immunization"
    NATIONAL_PRESCRIPTION = "national_prescription"
    NATIONAL_HEALTH_ID = "national_health_id"
    CUSTOM = "custom"
    MEDITECH = "meditech"
    ALLSCRIPTS = "allscripts"
    OTHER = "other"

class NationalDatabaseType(str, Enum):
    AHPRA = "ahpra"  # Only direct integration we need

class FHIRResource(BaseModel):
    resource_type: FHIRResourceType
    resource_id: str
    data: Dict[str, Any]
    version: str
    last_updated: datetime
    source_system: str

class MedicalHistoryEntry(BaseModel):
    condition: str
    diagnosed_on: date
    severity: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    fhir_resource: Optional[FHIRResource] = None
    source_system: Optional[str] = None
    verification_status: Optional[str] = None

class MedicationEntry(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None
    fhir_resource: Optional[FHIRResource] = None
    prescription_id: Optional[str] = None
    pharmacy: Optional[str] = None
    source_system: Optional[str] = None

class ProcedureEntry(BaseModel):
    name: str
    date: date
    provider: str
    location: Optional[str] = None
    notes: Optional[str] = None
    fhir_resource: Optional[FHIRResource] = None
    procedure_code: Optional[str] = None
    source_system: Optional[str] = None

class AllergyEntry(BaseModel):
    allergen: str
    reaction: str
    severity: Optional[str] = None
    onset_date: Optional[date] = None
    notes: Optional[str] = None
    fhir_resource: Optional[FHIRResource] = None
    source_system: Optional[str] = None

class ImmunizationEntry(BaseModel):
    vaccine_name: str
    dose_number: int
    date_administered: date
    provider: str
    lot_number: Optional[str] = None
    manufacturer: Optional[str] = None
    next_due_date: Optional[date] = None
    fhir_resource: Optional[FHIRResource] = None
    source_system: Optional[str] = None

class EHRSyncRequest(BaseModel):
    user_id: int
    ehr_system: EHRSystem
    medical_history: Optional[List[MedicalHistoryEntry]] = None
    medications: Optional[List[MedicationEntry]] = None
    procedures: Optional[List[ProcedureEntry]] = None
    allergies: Optional[List[AllergyEntry]] = None
    immunizations: Optional[List[ImmunizationEntry]] = None
    fhir_resources: Optional[List[FHIRResource]] = None
    sync_type: str = Field(..., description="Type of sync: full, incremental, or specific")
    last_sync_timestamp: Optional[datetime] = None
    national_databases: Optional[List[NationalDatabaseType]] = None

class EHRSyncResponse(BaseModel):
    ehr_id: str
    ehr_system: EHRSystem
    medical_history: List[MedicalHistoryEntry]
    medications: List[MedicationEntry]
    procedures: List[ProcedureEntry]
    allergies: List[AllergyEntry]
    immunizations: List[ImmunizationEntry]
    fhir_resources: List[FHIRResource]
    last_updated: datetime
    sync_status: str
    sync_message: Optional[str] = None
    national_database_sync_status: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True

class EHRConnectionConfig(BaseModel):
    ehr_system: EHRSystem
    api_endpoint: str
    client_id: str
    client_secret: str
    auth_endpoint: str
    token_endpoint: str
    scope: str
    fhir_version: str = "R4"
    additional_config: Optional[Dict[str, Any]] = None
    national_database_configs: Optional[Dict[NationalDatabaseType, Dict[str, Any]]] = None

class EHRConnectionStatus(BaseModel):
    ehr_system: EHRSystem
    is_connected: bool
    last_sync: Optional[datetime] = None
    connection_error: Optional[str] = None
    fhir_version: Optional[str] = None
    supported_resources: Optional[List[FHIRResourceType]] = None
    national_database_status: Optional[Dict[NationalDatabaseType, bool]] = None

class NationalDatabaseSyncConfig(BaseModel):
    database_type: NationalDatabaseType
    api_endpoint: HttpUrl
    auth_method: str
    credentials: Dict[str, Any]
    sync_frequency: str
    data_mapping: Dict[str, str]
    additional_config: Optional[Dict[str, Any]] = None

class NationalDatabaseSyncStatus(BaseModel):
    database_type: NationalDatabaseType
    is_connected: bool
    last_sync: Optional[datetime] = None
    sync_status: Optional[str] = None
    sync_message: Optional[str] = None

    class Config:
        from_attributes = True

class EHRConnectionBase(BaseModel):
    ehr_system: EHRSystem
    connection_config: Dict[str, Any]

class EHRConnectionCreate(EHRConnectionBase):
    pass

class EHRConnectionUpdate(BaseModel):
    is_active: Optional[bool] = None
    connection_config: Optional[Dict[str, Any]] = None

class EHRConnectionInDB(EHRConnectionBase):
    id: int
    user_id: int
    access_token: str
    refresh_token: Optional[str]
    token_expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NationalDatabaseConnectionBase(BaseModel):
    database_type: NationalDatabaseType
    connection_config: Dict[str, Any]

class NationalDatabaseConnectionCreate(NationalDatabaseConnectionBase):
    pass

class NationalDatabaseConnectionUpdate(BaseModel):
    is_active: Optional[bool] = None
    connection_config: Optional[Dict[str, Any]] = None

class NationalDatabaseConnectionInDB(NationalDatabaseConnectionBase):
    id: int
    ehr_connection_id: int
    access_token: str
    refresh_token: Optional[str]
    token_expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class EHRRecordBase(BaseModel):
    medical_history: Optional[Dict[str, Any]] = None
    medications: Optional[Dict[str, Any]] = None
    procedures: Optional[Dict[str, Any]] = None
    allergies: Optional[Dict[str, Any]] = None

class EHRRecordCreate(EHRRecordBase):
    pass

class EHRRecordUpdate(EHRRecordBase):
    pass

class EHRRecordInDB(EHRRecordBase):
    id: int
    user_id: int
    connection_id: int
    last_synced: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class WebhookEvent(BaseModel):
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SyncStatus(BaseModel):
    is_syncing: bool
    last_sync: Optional[datetime]
    error: Optional[str]
    progress: Optional[float]  # 0-100 percentage

class SyncResponse(BaseModel):
    status: SyncStatus
    message: str
