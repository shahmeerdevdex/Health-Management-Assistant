from typing import Dict, Any, Optional
from datetime import datetime
import json
import qrcode
import base64
from io import BytesIO
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from app.schemas.digital_wallet import SmartHealthCard, MedicareDigitalCard
from app.core.config import settings
import aiohttp
from fastapi import HTTPException

class DigitalWalletService:
    def __init__(self):
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()
        self.team_id = settings.APPLE_TEAM_ID
        self.pass_type_id = settings.APPLE_PASS_TYPE_ID
        self.organization_name = settings.ORGANIZATION_NAME

    def _load_private_key(self) -> rsa.RSAPrivateKey:
        """Load the private key for JWT signing."""
        with open(settings.JWT_PRIVATE_KEY_PATH, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=settings.JWT_PRIVATE_KEY_PASSWORD.encode() if settings.JWT_PRIVATE_KEY_PASSWORD else None
            )

    def _load_public_key(self) -> rsa.RSAPublicKey:
        """Load the public key for JWT verification."""
        with open(settings.JWT_PUBLIC_KEY_PATH, "rb") as key_file:
            return serialization.load_pem_public_key(key_file.read())

    async def generate_smart_health_card(
        self,
        credential_data: Dict[str, Any],
        issuer: str,
        expiration_date: Optional[datetime] = None
    ) -> SmartHealthCard:
        """Generate a SMART Health Card following the SMART Health Cards Framework."""
        # Create the JWT payload
        payload = {
            "iss": issuer,
            "iat": datetime.utcnow().timestamp(),
            "exp": expiration_date.timestamp() if expiration_date else None,
            "vc": {
                "type": ["SmartHealthCard"],
                "credentialSubject": credential_data
            }
        }

        # Sign the JWT
        jwt_token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers={
                "typ": "JWT",
                "kid": settings.JWT_KEY_ID
            }
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"shc:/{jwt_token}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        return SmartHealthCard(
            type="smart_health_card",
            version="1.0",
            issuer=issuer,
            issuance_date=datetime.utcnow(),
            expiration_date=expiration_date,
            credential_data=credential_data,
            verification_url=f"{settings.VERIFICATION_BASE_URL}/verify/{jwt_token}",
            qr_code=qr_code
        )

    @staticmethod
    async def generate_medicare_digital_card(
        medicare_number: str,
        beneficiary_name: str,
        date_of_birth: str,
        gender: str,
        coverage_type: str,
        effective_date: datetime,
        expiration_date: Optional[datetime] = None
    ) -> MedicareDigitalCard:
        """
        Generate a Medicare digital card.
        This is a simplified implementation - in production, you would need to:
        1. Verify the Medicare number with Medicare's systems
        2. Follow Medicare's digital card specifications
        3. Implement proper security measures
        """
        return MedicareDigitalCard(
            type="medicare_card",
            medicare_number=medicare_number,
            beneficiary_name=beneficiary_name,
            date_of_birth=date_of_birth,
            gender=gender,
            coverage_type=coverage_type,
            effective_date=effective_date,
            expiration_date=expiration_date,
            verification_status=False  # Will be updated after verification
        )

    @staticmethod
    async def verify_medicare_card(
        medicare_number: str,
        beneficiary_name: str,
        date_of_birth: str
    ) -> Dict[str, Any]:
        """
        Verify a Medicare card with Medicare's systems.
        This is a placeholder implementation - in production, you would need to:
        1. Integrate with Medicare's verification API
        2. Handle various verification scenarios
        3. Implement proper error handling
        """
        # Simulate verification
        # In production, this would make an API call to Medicare's systems
        return {
            "is_valid": True,
            "verification_timestamp": datetime.utcnow(),
            "verification_details": {
                "status": "verified",
                "message": "Card verified successfully"
            }
        }

    async def verify_smart_health_card(
        self,
        jwt_token: str
    ) -> Dict[str, Any]:
        """Verify a SMART Health Card JWT."""
        try:
            # Verify the JWT signature
            payload = jwt.decode(
                jwt_token,
                self.public_key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True
                }
            )

            return {
                "is_valid": True,
                "verification_timestamp": datetime.utcnow(),
                "verification_details": {
                    "status": "verified",
                    "message": "Card verified successfully",
                    "issuer_verified": True,
                    "signature_valid": True,
                    "payload": payload
                }
            }
        except jwt.InvalidTokenError as e:
            return {
                "is_valid": False,
                "verification_timestamp": datetime.utcnow(),
                "verification_details": {
                    "status": "invalid",
                    "message": str(e),
                    "issuer_verified": False,
                    "signature_valid": False
                }
            }

    async def generate_apple_wallet_pass(
        self,
        credential_type: str,
        credential_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an Apple Wallet pass."""
        async with aiohttp.ClientSession() as session:
            try:
                # Create the pass data
                pass_data = {
                    "passTypeIdentifier": self.pass_type_id,
                    "teamIdentifier": self.team_id,
                    "organizationName": self.organization_name,
                    "description": f"{credential_type.title()} Card",
                    "generic": {
                        "primaryFields": [
                            {
                                "key": "name",
                                "label": "NAME",
                                "value": credential_data.get("name", "")
                            }
                        ],
                        "secondaryFields": [
                            {
                                "key": "type",
                                "label": "TYPE",
                                "value": credential_type.title()
                            }
                        ]
                    }
                }

                # Add type-specific fields
                if credential_type == "medicare":
                    pass_data["generic"]["auxiliaryFields"] = [
                        {
                            "key": "number",
                            "label": "MEDICARE NUMBER",
                            "value": credential_data.get("medicare_number", "")
                        }
                    ]
                elif credential_type == "insurance":
                    pass_data["generic"]["auxiliaryFields"] = [
                        {
                            "key": "policy",
                            "label": "POLICY NUMBER",
                            "value": credential_data.get("policy_number", "")
                        }
                    ]

                # Sign the pass
                pass_data["signature"] = jwt.encode(
                    pass_data,
                    self.private_key,
                    algorithm="RS256"
                )

                return pass_data

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate Apple Wallet pass: {str(e)}"
                )

    async def generate_google_wallet_pass(
        self,
        credential_type: str,
        credential_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a Google Wallet pass."""
        try:
            # Create the pass data following Google Wallet API format
            pass_data = {
                "genericObjects": [{
                    "id": f"{credential_type}_{credential_data.get('id', '')}",
                    "cardTitle": {
                        "defaultValue": {
                            "language": "en-US",
                            "value": f"{credential_type.title()} Card"
                        }
                    },
                    "subheader": {
                        "defaultValue": {
                            "language": "en-US",
                            "value": credential_data.get("name", "")
                        }
                    },
                    "header": {
                        "defaultValue": {
                            "language": "en-US",
                            "value": credential_type.title()
                        }
                    }
                }]
            }

            # Add type-specific fields
            if credential_type == "medicare":
                pass_data["genericObjects"][0]["barcode"] = {
                    "type": "QR_CODE",
                    "value": credential_data.get("medicare_number", "")
                }
            elif credential_type == "insurance":
                pass_data["genericObjects"][0]["barcode"] = {
                    "type": "QR_CODE",
                    "value": credential_data.get("policy_number", "")
                }

            return pass_data

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate Google Wallet pass: {str(e)}"
            )

    @staticmethod
    async def export_to_wallet_format(
        credential_type: str,
        credential_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export a credential to a format compatible with Apple/Google Wallet.
        This is a simplified implementation - in production, you would need to:
        1. Follow Apple/Google Wallet's pass specifications
        2. Generate proper pass files
        3. Handle different credential types appropriately
        """
        if credential_type == "smart_health_card":
            return {
                "type": "healthCard",
                "formatVersion": 1,
                "passTypeIdentifier": "pass.com.health.credential",
                "serialNumber": credential_data.get("id"),
                "teamIdentifier": "YOUR_TEAM_ID",
                "organizationName": credential_data.get("issuer"),
                "description": "SMART Health Card",
                "logoText": "Health Card",
                "generic": {
                    "primaryFields": [
                        {
                            "key": "name",
                            "label": "NAME",
                            "value": credential_data.get("name", "")
                        }
                    ],
                    "secondaryFields": [
                        {
                            "key": "type",
                            "label": "TYPE",
                            "value": "SMART Health Card"
                        }
                    ],
                    "auxiliaryFields": [
                        {
                            "key": "issuer",
                            "label": "ISSUER",
                            "value": credential_data.get("issuer", "")
                        }
                    ]
                }
            }
        elif credential_type == "medicare_card":
            return {
                "type": "healthCard",
                "formatVersion": 1,
                "passTypeIdentifier": "pass.com.medicare.card",
                "serialNumber": credential_data.get("medicare_number"),
                "teamIdentifier": "YOUR_TEAM_ID",
                "organizationName": "Medicare",
                "description": "Medicare Card",
                "logoText": "Medicare",
                "generic": {
                    "primaryFields": [
                        {
                            "key": "name",
                            "label": "NAME",
                            "value": credential_data.get("beneficiary_name", "")
                        }
                    ],
                    "secondaryFields": [
                        {
                            "key": "number",
                            "label": "MEDICARE NUMBER",
                            "value": credential_data.get("medicare_number", "")
                        }
                    ],
                    "auxiliaryFields": [
                        {
                            "key": "coverage",
                            "label": "COVERAGE TYPE",
                            "value": credential_data.get("coverage_type", "")
                        }
                    ]
                }
            }
        else:
            raise ValueError(f"Unsupported credential type: {credential_type}") 