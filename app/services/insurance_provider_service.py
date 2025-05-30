from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from fastapi import HTTPException
from app.core.config import settings

class InsuranceProviderService:
    def __init__(self):
        self.api_key = settings.INSURANCE_PROVIDER_API_KEY
        self.base_url = settings.INSURANCE_PROVIDER_API_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def verify_coverage(
        self,
        policy_number: str,
        member_id: str,
        date_of_birth: str,
        first_name: str,
        last_name: str
    ) -> Dict[str, Any]:
        """Verify insurance coverage with the provider's API."""
        try:
            response = await self.client.post(
                "/verify-coverage",
                json={
                    "policy_number": policy_number,
                    "member_id": member_id,
                    "date_of_birth": date_of_birth,
                    "first_name": first_name,
                    "last_name": last_name
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to verify coverage with insurance provider: {str(e)}"
            )

    async def get_coverage_details(
        self,
        policy_number: str,
        member_id: str
    ) -> Dict[str, Any]:
        """Get detailed coverage information from the provider."""
        try:
            response = await self.client.get(
                f"/coverage-details/{policy_number}/{member_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get coverage details: {str(e)}"
            )

    async def submit_claim(
        self,
        policy_number: str,
        member_id: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit a claim to the insurance provider."""
        try:
            response = await self.client.post(
                "/submit-claim",
                json={
                    "policy_number": policy_number,
                    "member_id": member_id,
                    **claim_data
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit claim: {str(e)}"
            )

    async def get_claim_status(
        self,
        claim_id: str
    ) -> Dict[str, Any]:
        """Get the status of a submitted claim."""
        try:
            response = await self.client.get(f"/claim-status/{claim_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get claim status: {str(e)}"
            )

    async def get_benefits(
        self,
        policy_number: str,
        member_id: str
    ) -> Dict[str, Any]:
        """Get detailed benefits information."""
        try:
            response = await self.client.get(
                f"/benefits/{policy_number}/{member_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get benefits: {str(e)}"
            )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 