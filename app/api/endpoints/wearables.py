from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.schemas.wearables import WearableDataRequest, WearableDataResponse
from app.services.wearable_service import (
    process_wearable_data,
    fetch_fitbit_data, fetch_google_fit_data,
    parse_fitbit_to_wearable_schema,
    parse_google_fit_to_wearable_schema
)
from app.services.auth_service import get_user_oauth_token,save_or_update_oauth_token
from app.api.endpoints.dependencies import get_db, get_current_user
from fastapi.responses import RedirectResponse
import httpx
import urllib.parse
from app.core.config import settings
from datetime import datetime,timedelta
import base64
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/data", response_model=WearableDataResponse)
async def wearable_data(
    request: WearableDataRequest,
    db: Session = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Processes and analyzes user-submitted wearable data directly.
    """
    try:
        analysis = await process_wearable_data(request, db)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/fetch", response_model=WearableDataResponse)
async def fetch_google_fit_data_endpoint(
    db: Session = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Fetches and analyzes Google Fit data for the authenticated user.
    Requires prior authorization.
    """
    try:
        token_record = await get_user_oauth_token(db, db_user.id, provider="google_fit")
        if not token_record:
            raise HTTPException(status_code=401, detail="Google Fit not connected")

        raw_data = await fetch_google_fit_data(token_record.access_token)
        wearable_input = parse_google_fit_to_wearable_schema(raw_data)
        return await process_wearable_data(wearable_input, db)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Fit fetch failed: {str(e)}")


@router.get("/fitbit/fetch", response_model=WearableDataResponse)
async def fetch_fitbit_data_endpoint(
    db: Session = Depends(get_db),
    db_user=Depends(get_current_user)
):
    """
    Fetches and analyzes Fitbit data for the authenticated user.
    Requires prior authorization.
    """
    try:
        token_record = await get_user_oauth_token(db, db_user.id, provider="fitbit")
        if not token_record:
            raise HTTPException(status_code=401, detail="Fitbit not connected")

        raw_data = await fetch_fitbit_data(token_record.access_token)
        wearable_input = parse_fitbit_to_wearable_schema(raw_data)
        return await process_wearable_data(wearable_input, db)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fitbit fetch failed: {str(e)}")


GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read"
]

@router.get("/google/authorize")
async def authorize_google_fit(request: Request):
    """
    Redirect user to Google OAuth2 authorization screen.
    """
    # Generate and store state parameter
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }

    url = f"{GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)

@router.get("/google/callback")
async def google_fit_callback(
    code: str,
    state: str,
    error: str = None,
    db: Session = Depends(get_db),
    db_user=Depends(get_current_user),
    request: Request = None
):
    """
    Handle OAuth2 callback from Google and store tokens.
    """
    try:
        # Verify state parameter
        stored_state = request.session.get("oauth_state")
        if not stored_state or stored_state != state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Check for OAuth errors
        if error:
            if error == "access_denied":
                raise HTTPException(status_code=403, detail="User denied access to Google Fit")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                    "grant_type": "authorization_code"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Google OAuth token exchange failed: {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to exchange authorization code: {error_data.get('error_description', 'Unknown error')}"
                )

            token_data = response.json()

        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="Failed to retrieve Google Fit token")

        # Clear the state parameter from session
        request.session.pop("oauth_state", None)

        await save_or_update_oauth_token(
            db=db,
            user_id=db_user.id,
            provider="google_fit",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        )

        return {"message": "Google Fit connected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google Fit callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth2 callback failed: {str(e)}")


FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_SCOPES = ["activity", "heartrate", "sleep", "profile"]

@router.get("/fitbit/authorize")
async def authorize_fitbit():
    """
    Redirect the user to Fitbit OAuth2 consent screen.
    """
    params = {
        "client_id": settings.FITBIT_CLIENT_ID,
        "response_type": "code",
        "scope": " ".join(FITBIT_SCOPES),
        "redirect_uri": settings.FITBIT_REDIRECT_URI,
        "expires_in": "604800"  # 7 days
    }

    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(f"{FITBIT_AUTH_URL}?{query}")


@router.get("/fitbit/callback")
async def fitbit_callback(code: str, db: Session = Depends(get_db), db_user=Depends(get_current_user)):
    """
    Handle Fitbit OAuth2 callback and store token.
    """
    try:
        basic_auth = base64.b64encode(
            f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        body = {
            "client_id": settings.FITBIT_CLIENT_ID,
            "grant_type": "authorization_code",
            "redirect_uri": settings.FITBIT_REDIRECT_URI,
            "code": code
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(FITBIT_TOKEN_URL, data=body, headers=headers)
            token_data = response.json()

        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="Fitbit token exchange failed")

        await save_or_update_oauth_token(
            db=db,
            user_id=db_user.id,
            provider="fitbit",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        )

        return {"message": "Fitbit connected successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fitbit callback failed: {str(e)}")
