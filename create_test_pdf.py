#!/usr/bin/env python3
"""
Create a simple test PDF for the E-Signature field editor
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os

def create_test_contract_pdf():
    filename = "test_contract.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("SERVICE AGREEMENT CONTRACT", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Contract content
    content = [
        "This Service Agreement is entered into between Metro Point Technology LLC ('Company') and the Client.",
        "",
        "SCOPE OF WORK:",
        "Company agrees to provide custom software development services including but not limited to:",
        "• Web application development",
        "• Database design and implementation", 
        "• System integration services",
        "• Technical consulting",
        "",
        "TERMS AND CONDITIONS:",
        "1. Payment terms: Net 30 days from invoice date",
        "2. Project timeline: As specified in project proposal",
        "3. Intellectual property remains with Company until final payment",
        "",
        "CLIENT INFORMATION:",
        "Client Name: _________________________",
        "",
        "Address: _____________________________",
        "",
        "Phone: _______________________________",
        "",
        "Email: _______________________________",
        "",
        "",
        "SIGNATURES:",
        "",
        "Client Signature: _________________________ Date: ________________",
        "",
        "",
        "Company Representative: __________________ Date: ________________",
        "",
        "",
        "Initials: _____ (Client)     Initials: _____ (Company)",
        "",
        "This contract contains sensitive information and should be handled confidentially.",
    ]
    
    for line in content:
        if line == "":
            story.append(Spacer(1, 12))
        else:
            para = Paragraph(line, styles['Normal'])
            story.append(para)
            story.append(Spacer(1, 6))
    
    doc.build(story)
    print(f"Created test contract PDF: {filename}")
    return filename

def create_simple_test_pdf():
    filename = "simple_test.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "E-Signature Field Editor Test Document")
    
    c.setFont("Helvetica", 12)
    y = height - 100
    
    lines = [
        "This is a test PDF for the E-Signature field editor.",
        "",
        "Please place signature fields in the designated areas:",
        "",
        "Client Signature: ___________________________",
        "",
        "Date: __________",
        "",
        "Initial here: _____",
        "",
        "Additional comments:",
        "_________________________________________________",
        "_________________________________________________",
        "",
        "Page 1 of 2"
    ]
    
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    
    c.showPage()  # New page
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Page 2 - Additional Signature Fields")
    
    c.setFont("Helvetica", 12)
    y = height - 100
    
    lines2 = [
        "Witness Signature: ___________________________",
        "",
        "Witness Print Name: __________________________",
        "",
        "Date: __________",
        "",
        "Notary Signature: ____________________________",
        "",
        "Notary Seal:",
        "",
        "[NOTARY SEAL AREA - DO NOT WRITE]",
        "",
        "",
        "Final Initials: Client: _____ Witness: _____",
        "",
        "This completes the test document.",
        "",
        "Page 2 of 2"
    ]
    
    for line in lines2:
        c.drawString(50, y, line)
        y -= 20
    
    c.save()
    print(f"Created simple test PDF: {filename}")
    return filename

if __name__ == "__main__":
    try:
        # Try to create contract PDF (needs reportlab)
        create_test_contract_pdf()
        create_simple_test_pdf()
    except ImportError:
        print("reportlab not installed, creating basic PDF instead")
        create_simple_test_pdf()