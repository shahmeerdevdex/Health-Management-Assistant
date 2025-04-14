from sqlalchemy.orm import Session
from app.schemas.diagnostics import HomeDiagnosticsRequest, HomeDiagnosticsResponse, DiagnosticInsight
from app.services.ai_services import analyze_test_results  

async def process_home_diagnostics(request: HomeDiagnosticsRequest, db: Session) -> HomeDiagnosticsResponse:
    """
    Processes home diagnostic test results and integrates AI-generated insights.
    """
    insights = []
    recommendation = "Monitor your results and consult a healthcare professional if needed."

    # Ensure test_results is valid
    if not isinstance(request.test_results, dict):
        raise ValueError("Invalid test_results format. Expected a dictionary.")

    # AI Analysis: Send test results to AI model
    ai_insight = await analyze_test_results(request.test_type, request.test_results)
    if ai_insight:
        insights.append(DiagnosticInsight(insight=ai_insight))

    # Traditional Rule-Based Analysis
    if request.test_type.lower() == "blood pressure":
        systolic = request.test_results.get("systolic", 0)
        diastolic = request.test_results.get("diastolic", 0)
        if systolic > 140 or diastolic > 90:
            insights.append(DiagnosticInsight(insight="High blood pressure detected. Consider lifestyle changes and consult a doctor."))
        elif systolic < 90 or diastolic < 60:
            insights.append(DiagnosticInsight(insight="Low blood pressure detected. Ensure proper hydration and check for symptoms."))

    elif request.test_type.lower() == "malaria":
        result = request.test_results.get("positive", False)
        if isinstance(result, bool) and result:
            insights.append(DiagnosticInsight(insight="Malaria test is positive. Seek immediate medical attention and start treatment."))
            recommendation = "Visit a healthcare provider for treatment."

    return HomeDiagnosticsResponse(
        user_id=request.user_id,
        test_type=request.test_type,
        insights=insights,
        recommendation=recommendation
    )
