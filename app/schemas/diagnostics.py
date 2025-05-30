from pydantic import BaseModel, Field
from typing import Dict, Union, List, Optional
from datetime import date

class HomeDiagnosticsRequest(BaseModel):
    user_id: int  # ID of the user submitting the test results
    test_type: str  # Type of home test (e.g., "Blood Pressure", "Glucose", "COVID-19")
    
    # Ensure test_results is a dictionary with valid types
    test_results: Dict[str, Union[str, int, float, bool]] = Field(..., description="Dictionary of test result values")
    
    # Use date instead of string for test_date validation
    test_date: Optional[date] = Field(None, description="Date of the test in YYYY-MM-DD format")

class DiagnosticInsight(BaseModel):
    insight: str  # AI-generated or predefined health insight

class HomeDiagnosticsResponse(BaseModel):
    user_id: int
    test_type: str
    insights: List[DiagnosticInsight]  # Insights based on the test results
    recommendation: str  # Suggested next steps
