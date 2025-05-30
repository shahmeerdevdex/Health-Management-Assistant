from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.crud.health_diary import get_health_diary, get_health_summary
from app.crud.medication import get_today_medications
from app.crud.emergency_health import get_emergency_health
from app.crud.appointment import get_upcoming_appointments
from app.crud.vaccination import get_vaccination_records
from app.crud.monitoring import get_chronic_monitoring
from app.schemas.report import CustomReportCreate
import logging
import os
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger("report_service")

async def generate_health_report(user_id: int):
    """Generate a comprehensive PDF health report for the user asynchronously."""
    
    async with SessionLocal() as db:
        # Fetch all relevant health data
        health_entries = await get_health_diary(db, user_id)
        health_summary = await get_health_summary(db, user_id, days=30)
        medications = await get_today_medications(db, user_id)
        emergency_health = await get_emergency_health(db, user_id)
        appointments = await get_upcoming_appointments(db, user_id)
        vaccinations = await get_vaccination_records(db, user_id)
        chronic_data = await get_chronic_monitoring(db, user_id)

    if not health_entries and not medications and not emergency_health:
        return None

    def create_pdf():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title Page
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Comprehensive Health Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        pdf.ln(10)

        # Health Summary Section
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Health Summary", ln=True)
        pdf.set_font("Arial", '', 12)
        if health_summary:
            pdf.cell(200, 10, txt=f"Total Entries: {health_summary['total_entries']}", ln=True)
            pdf.cell(200, 10, txt=f"Most Recent Mood: {health_summary['most_recent_mood']}", ln=True)
            pdf.cell(200, 10, txt=f"Frequent Symptoms: {', '.join(health_summary['frequent_symptoms'])}", ln=True)
        pdf.ln(10)

        # Medications Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Current Medications", ln=True)
        pdf.set_font("Arial", '', 12)
        if medications:
            for med in medications:
                pdf.cell(200, 10, txt=f"* {med.name} - {med.dosage} ({med.frequency})", ln=True)
        pdf.ln(10)

        # Emergency Health Information
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Emergency Health Information", ln=True)
        pdf.set_font("Arial", '', 12)
        if emergency_health:
            pdf.cell(200, 10, txt=f"Blood Type: {emergency_health.blood_type}", ln=True)
            pdf.cell(200, 10, txt=f"Allergies: {emergency_health.allergies}", ln=True)
            pdf.cell(200, 10, txt=f"Critical Conditions: {emergency_health.critical_conditions}", ln=True)
        pdf.ln(10)

        # Recent Health Diary Entries
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Recent Health Diary Entries", ln=True)
        pdf.set_font("Arial", '', 12)
        for entry in health_entries[:10]:  # Show last 10 entries
            pdf.cell(200, 10, txt=f"Date: {entry.date.strftime('%Y-%m-%d')}", ln=True)
            if entry.symptoms:
                pdf.cell(200, 10, txt=f"Symptoms: {', '.join(entry.symptoms)}", ln=True)
            pdf.cell(200, 10, txt=f"Mood: {entry.mood}", ln=True)
            if entry.notes:
                pdf.cell(200, 10, txt=f"Notes: {entry.notes}", ln=True)
            pdf.ln(5)

        # Chronic Monitoring Data
        if chronic_data:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Chronic Condition Monitoring", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.cell(200, 10, txt=f"Condition: {chronic_data.condition}", ln=True)
            if chronic_data.blood_pressure:
                latest_bp = chronic_data.blood_pressure[-1]
                pdf.cell(200, 10, txt=f"Latest BP: {latest_bp['systolic']}/{latest_bp['diastolic']}", ln=True)
            if chronic_data.blood_sugar:
                latest_bs = chronic_data.blood_sugar[-1]
                pdf.cell(200, 10, txt=f"Latest Blood Sugar: {latest_bs}", ln=True)

        # Vaccination Records
        if vaccinations:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Vaccination Records", ln=True)
            pdf.set_font("Arial", '', 12)
            for vax in vaccinations:
                pdf.cell(200, 10, txt=f"* {vax.vaccine_name} - Dose {vax.dose_number}", ln=True)
                pdf.cell(200, 10, txt=f"  Administered: {vax.date_administered}", ln=True)
                if vax.next_due_date:
                    pdf.cell(200, 10, txt=f"  Next Due: {vax.next_due_date}", ln=True)

        # Upcoming Appointments
        if appointments:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Upcoming Appointments", ln=True)
            pdf.set_font("Arial", '', 12)
            for apt in appointments:
                pdf.cell(200, 10, txt=f"* {apt.date.strftime('%Y-%m-%d %H:%M')} - {apt.appointment_type}", ln=True)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/user_{user_id}_health_report.pdf"
        pdf.output(report_path)
        return report_path

    # Run PDF generation in an executor to avoid blocking
    loop = asyncio.get_running_loop()
    report_path = await loop.run_in_executor(None, create_pdf)
    
    logger.info(f"Health report generated: {report_path}")
    return report_path

async def generate_custom_health_report(user_id: int, report_options: CustomReportCreate):
    """Generate a customizable PDF health report for the user asynchronously."""
    
    async with SessionLocal() as db:
        # Fetch all relevant health data with filters
        health_entries = await get_health_diary(db, user_id)
        
        # Filter entries by date range if specified
        if report_options.start_date and report_options.end_date:
            # Ensure all dates are timezone-aware for comparison
            start_date = report_options.start_date
            end_date = report_options.end_date
            
            health_entries = [
                entry for entry in health_entries 
                if entry.date.tzinfo and start_date <= entry.date <= end_date
            ]
        
        # Calculate days for health summary
        days = 30
        if report_options.start_date and report_options.end_date:
            days = (report_options.end_date - report_options.start_date).days
        
        health_summary = await get_health_summary(db, user_id, days=days)
        
        medications = await get_today_medications(db, user_id) if report_options.include_medications else None
        emergency_health = await get_emergency_health(db, user_id)
        appointments = await get_upcoming_appointments(db, user_id) if report_options.include_appointments else None
        vaccinations = await get_vaccination_records(db, user_id) if report_options.include_vaccinations else None
        chronic_data = await get_chronic_monitoring(db, user_id) if report_options.include_chronic_data else None

    if not health_entries and not medications and not emergency_health:
        return None

    def create_pdf():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title Page
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Custom Health Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        
        if report_options.start_date and report_options.end_date:
            pdf.cell(200, 10, txt=f"Report Period: {report_options.start_date.strftime('%Y-%m-%d')} to {report_options.end_date.strftime('%Y-%m-%d')}", ln=True, align='C')
        pdf.ln(10)

        # Health Summary Section
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Health Summary", ln=True)
        pdf.set_font("Arial", '', 12)
        if health_summary:
            pdf.cell(200, 10, txt=f"Total Entries: {health_summary['total_entries']}", ln=True)
            pdf.cell(200, 10, txt=f"Most Recent Mood: {health_summary['most_recent_mood']}", ln=True)
            pdf.cell(200, 10, txt=f"Frequent Symptoms: {', '.join(health_summary['frequent_symptoms'])}", ln=True)
        pdf.ln(10)

        # Medications Section
        if report_options.include_medications and medications:
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Current Medications", ln=True)
            pdf.set_font("Arial", '', 12)
            for med in medications:
                pdf.cell(200, 10, txt=f"* {med.name} - {med.dosage} ({med.frequency})", ln=True)
            pdf.ln(10)

        # Emergency Health Information
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Emergency Health Information", ln=True)
        pdf.set_font("Arial", '', 12)
        if emergency_health:
            pdf.cell(200, 10, txt=f"Blood Type: {emergency_health.blood_type}", ln=True)
            pdf.cell(200, 10, txt=f"Allergies: {emergency_health.allergies}", ln=True)
            pdf.cell(200, 10, txt=f"Critical Conditions: {emergency_health.critical_conditions}", ln=True)
        pdf.ln(10)

        # Health Diary Entries
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Health Diary Entries", ln=True)
        pdf.set_font("Arial", '', 12)
        for entry in health_entries:
            pdf.cell(200, 10, txt=f"Date: {entry.date.strftime('%Y-%m-%d')}", ln=True)
            if entry.symptoms:
                pdf.cell(200, 10, txt=f"Symptoms: {', '.join(entry.symptoms)}", ln=True)
            pdf.cell(200, 10, txt=f"Mood: {entry.mood}", ln=True)
            if entry.notes:
                pdf.cell(200, 10, txt=f"Notes: {entry.notes}", ln=True)
            pdf.ln(5)

        # Chronic Monitoring Data
        if report_options.include_chronic_data and chronic_data:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Chronic Condition Monitoring", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.cell(200, 10, txt=f"Condition: {chronic_data.condition}", ln=True)
            if chronic_data.blood_pressure:
                latest_bp = chronic_data.blood_pressure[-1]
                pdf.cell(200, 10, txt=f"Latest BP: {latest_bp['systolic']}/{latest_bp['diastolic']}", ln=True)
            if chronic_data.blood_sugar:
                latest_bs = chronic_data.blood_sugar[-1]
                pdf.cell(200, 10, txt=f"Latest Blood Sugar: {latest_bs}", ln=True)

        # Vaccination Records
        if report_options.include_vaccinations and vaccinations:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Vaccination Records", ln=True)
            pdf.set_font("Arial", '', 12)
            for vax in vaccinations:
                pdf.cell(200, 10, txt=f"* {vax.vaccine_name} - Dose {vax.dose_number}", ln=True)
                pdf.cell(200, 10, txt=f"  Administered: {vax.date_administered}", ln=True)
                if vax.next_due_date:
                    pdf.cell(200, 10, txt=f"  Next Due: {vax.next_due_date}", ln=True)

        # Upcoming Appointments
        if report_options.include_appointments and appointments:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Upcoming Appointments", ln=True)
            pdf.set_font("Arial", '', 12)
            for apt in appointments:
                pdf.cell(200, 10, txt=f"* {apt.date.strftime('%Y-%m-%d %H:%M')} - {apt.appointment_type}", ln=True)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/user_{user_id}_custom_health_report.pdf"
        pdf.output(report_path)
        return report_path

    # Run PDF generation in an executor to avoid blocking
    loop = asyncio.get_running_loop()
    report_path = await loop.run_in_executor(None, create_pdf)
    
    logger.info(f"Custom health report generated: {report_path}")
    return report_path
