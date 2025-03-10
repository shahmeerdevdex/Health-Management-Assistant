from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.crud.health_diary import get_health_diary
import logging
import os
import asyncio  # Required for async file handling

logger = logging.getLogger("report_service")

async def generate_health_report(user_id: int):
    """Generate a PDF health report for the user asynchronously."""
    
    async with SessionLocal() as db:
        health_entries = await get_health_diary(db, user_id)  # Await async function

    if not health_entries:
        return None  

    # Function to generate PDF (runs in a separate thread to avoid blocking)
    def create_pdf():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Health Report for User {user_id}", ln=True, align='C')

        for entry in health_entries:
            pdf.cell(200, 10, txt=f"{entry.date}: {entry.symptoms}", ln=True)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/user_{user_id}_health_report.pdf"
        pdf.output(report_path)
        return report_path

    # Run PDF generation in an executor to avoid blocking
    loop = asyncio.get_running_loop()
    report_path = await loop.run_in_executor(None, create_pdf)
    
    logger.info(f"Health report generated: {report_path}")

    return report_path
from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.crud.health_diary import get_health_diary
import logging
import os
import asyncio  # Required for async file handling

logger = logging.getLogger("report_service")

async def generate_health_report(user_id: int):
    """Generate a PDF health report for the user asynchronously."""
    
    async with SessionLocal() as db:
        health_entries = await get_health_diary(db, user_id)  # Await async function

    if not health_entries:
        return None  

    # Function to generate PDF (runs in a separate thread to avoid blocking)
    def create_pdf():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Health Report for User {user_id}", ln=True, align='C')

        for entry in health_entries:
            pdf.cell(200, 10, txt=f"{entry.date}: {entry.symptoms}", ln=True)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/user_{user_id}_health_report.pdf"
        pdf.output(report_path)
        return report_path

    # Run PDF generation in an executor to avoid blocking
    loop = asyncio.get_running_loop()
    report_path = await loop.run_in_executor(None, create_pdf)
    
    logger.info(f"Health report generated: {report_path}")

    return report_path
