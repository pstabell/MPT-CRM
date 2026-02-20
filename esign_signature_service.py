# E-Signature Phase 3: Signature Application Service
# Handles applying signatures to PDF documents using ReportLab

import os
import io
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import json

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import inch
    from PyPDF2 import PdfReader, PdfWriter
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"[esign_signature_service] ReportLab/PyPDF2 not available: {e}")
    REPORTLAB_AVAILABLE = False

from db_service import get_db


@dataclass
class SignatureData:
    """Data class for signature information"""
    pdf_field_id: str
    document_id: str
    signature_type: str  # 'draw' or 'type'
    signature_data: str  # base64 image or text
    x_coordinate: float
    y_coordinate: float
    width: float
    height: float
    page_number: int
    font_family: Optional[str] = None
    font_size: Optional[int] = 16


def apply_signature_to_pdf(signature_data: SignatureData, pdf_path: str, output_path: str) -> Dict[str, Any]:
    """
    Apply a signature to a PDF document at the specified coordinates.
    
    Args:
        signature_data: SignatureData object containing signature information
        pdf_path: Path to the input PDF file
        output_path: Path for the output signed PDF file
    
    Returns:
        Dict with success status, message, and any error information
    """
    if not REPORTLAB_AVAILABLE:
        return {
            "success": False,
            "error": "ReportLab or PyPDF2 not installed. Install with: pip install reportlab PyPDF2 Pillow"
        }
    
    try:
        # Read the original PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Get page count and validate page number
        total_pages = len(reader.pages)
        if signature_data.page_number < 1 or signature_data.page_number > total_pages:
            return {
                "success": False,
                "error": f"Invalid page number {signature_data.page_number}. PDF has {total_pages} pages."
            }
        
        # Process each page
        for page_num in range(total_pages):
            page = reader.pages[page_num]
            
            # If this is the target page, overlay the signature
            if page_num + 1 == signature_data.page_number:  # Convert to 1-based indexing
                # Create signature overlay
                overlay_buffer = create_signature_overlay(signature_data, page)
                if overlay_buffer:
                    # Create PDF from overlay buffer
                    overlay_reader = PdfReader(overlay_buffer)
                    overlay_page = overlay_reader.pages[0]
                    
                    # Merge signature overlay onto the original page
                    page.merge_page(overlay_page)
            
            # Add page to writer
            writer.add_page(page)
        
        # Write the final PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return {
            "success": True,
            "message": f"Signature applied successfully to page {signature_data.page_number}",
            "output_path": output_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error applying signature to PDF: {str(e)}"
        }


def create_signature_overlay(signature_data: SignatureData, pdf_page) -> Optional[io.BytesIO]:
    """
    Create a PDF overlay containing the signature at the specified coordinates.
    
    Args:
        signature_data: SignatureData object
        pdf_page: The PDF page to get dimensions from
    
    Returns:
        BytesIO buffer containing the signature overlay PDF, or None on error
    """
    try:
        # Get page dimensions
        page_width = float(pdf_page.mediabox[2])
        page_height = float(pdf_page.mediabox[3])
        
        # Create a BytesIO buffer for the overlay PDF
        buffer = io.BytesIO()
        
        # Create canvas with page dimensions
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        # Convert coordinates (PDF coordinate system has origin at bottom-left)
        x = signature_data.x_coordinate
        y = page_height - signature_data.y_coordinate - signature_data.height
        
        if signature_data.signature_type == 'draw':
            # Handle drawn signature (base64 image)
            success = apply_image_signature(c, signature_data, x, y)
            if not success:
                return None
        
        elif signature_data.signature_type == 'type':
            # Handle typed signature (text)
            success = apply_text_signature(c, signature_data, x, y)
            if not success:
                return None
        
        else:
            print(f"[esign_signature_service] Unknown signature type: {signature_data.signature_type}")
            return None
        
        # Save the canvas
        c.save()
        
        # Reset buffer position and return
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"[esign_signature_service] Error creating signature overlay: {e}")
        return None


def apply_image_signature(c: canvas.Canvas, signature_data: SignatureData, x: float, y: float) -> bool:
    """
    Apply a drawn signature (image) to the canvas.
    
    Args:
        c: ReportLab Canvas object
        signature_data: SignatureData object
        x: X coordinate on canvas
        y: Y coordinate on canvas
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract base64 image data
        image_data = signature_data.signature_data
        
        # Remove data URL prefix if present (data:image/png;base64,)
        if image_data.startswith('data:image'):
            image_data = image_data.split(',', 1)[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Create PIL Image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (remove alpha channel)
        if image.mode in ('RGBA', 'LA'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
            else:
                background.paste(image)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save image to temporary buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Draw image on canvas
        c.drawInlineImage(
            img_buffer,
            x, y,
            width=signature_data.width,
            height=signature_data.height,
            preserveAspectRatio=True
        )
        
        return True
        
    except Exception as e:
        print(f"[esign_signature_service] Error applying image signature: {e}")
        return False


def apply_text_signature(c: canvas.Canvas, signature_data: SignatureData, x: float, y: float) -> bool:
    """
    Apply a typed signature (text) to the canvas.
    
    Args:
        c: ReportLab Canvas object
        signature_data: SignatureData object
        x: X coordinate on canvas
        y: Y coordinate on canvas
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Set font based on signature data
        font_family = signature_data.font_family or 'Helvetica'
        font_size = signature_data.font_size or 16
        
        # Map font family names to ReportLab font names
        font_mapping = {
            'cursive': 'Times-Italic',
            'serif': 'Times-Roman',
            'sans-serif': 'Helvetica'
        }
        
        reportlab_font = font_mapping.get(font_family, 'Helvetica')
        
        # Set font and size
        c.setFont(reportlab_font, font_size)
        
        # Set text color to black
        c.setFillColorRGB(0, 0, 0)
        
        # Calculate vertical position (center text in field height)
        text_y = y + (signature_data.height - font_size) / 2
        
        # Draw the signature text
        c.drawString(x + 5, text_y, signature_data.signature_data)  # Small padding from left edge
        
        return True
        
    except Exception as e:
        print(f"[esign_signature_service] Error applying text signature: {e}")
        return False


def store_signature_record(signature_data: SignatureData) -> Dict[str, Any]:
    """
    Store signature record in the Supabase signatures table.
    
    Args:
        signature_data: SignatureData object
    
    Returns:
        Dict with success status and signature record data
    """
    db = get_db()
    if not db:
        return {"success": False, "error": "Database not connected"}
    
    try:
        signature_record = {
            "pdf_field_id": signature_data.pdf_field_id,
            "document_id": signature_data.document_id,
            "signature_type": signature_data.signature_type,
            "signature_data": signature_data.signature_data,
            "x_coordinate": signature_data.x_coordinate,
            "y_coordinate": signature_data.y_coordinate,
            "width": signature_data.width,
            "height": signature_data.height,
            "page_number": signature_data.page_number,
            "font_family": signature_data.font_family,
            "font_size": signature_data.font_size,
            "applied_at": datetime.now().isoformat()
        }
        
        response = db.table("signatures").insert(signature_record).execute()
        
        if response.data:
            return {
                "success": True,
                "signature_record": response.data[0]
            }
        else:
            return {"success": False, "error": "Failed to store signature record"}
            
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}


def process_signature_application(payload: Dict[str, Any], pdf_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to process signature application request.
    
    Args:
        payload: Dictionary containing signature data from frontend
        pdf_path: Path to the input PDF file
        output_path: Path for the output signed PDF file
    
    Returns:
        Dict with success status, message, and signature record data
    """
    try:
        # Create SignatureData object from payload
        signature_data = SignatureData(
            pdf_field_id=payload['pdf_field_id'],
            document_id=payload['document_id'],
            signature_type=payload['signature_type'],
            signature_data=payload['signature_data'],
            x_coordinate=float(payload['x_coordinate']),
            y_coordinate=float(payload['y_coordinate']),
            width=float(payload['width']),
            height=float(payload['height']),
            page_number=int(payload['page_number']),
            font_family=payload.get('font_family'),
            font_size=int(payload.get('font_size', 16))
        )
        
        # Apply signature to PDF
        pdf_result = apply_signature_to_pdf(signature_data, pdf_path, output_path)
        
        if not pdf_result['success']:
            return pdf_result
        
        # Store signature record in database
        db_result = store_signature_record(signature_data)
        
        if not db_result['success']:
            # PDF was created but database storage failed - log warning but don't fail
            print(f"[esign_signature_service] Warning: PDF created but database storage failed: {db_result['error']}")
        
        return {
            "success": True,
            "message": "Signature applied successfully",
            "pdf_result": pdf_result,
            "signature_record": db_result.get('signature_record'),
            "database_warning": None if db_result['success'] else db_result['error']
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing signature application: {str(e)}"
        }


def get_signature_records(document_id: str) -> Dict[str, Any]:
    """
    Get all signature records for a document.
    
    Args:
        document_id: UUID of the document
    
    Returns:
        Dict with success status and list of signature records
    """
    db = get_db()
    if not db:
        return {"success": False, "error": "Database not connected"}
    
    try:
        response = db.table("signatures").select("*").eq(
            "document_id", document_id
        ).order("applied_at", desc=True).execute()
        
        return {
            "success": True,
            "signatures": response.data or []
        }
        
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}


def check_field_signed(pdf_field_id: str) -> Dict[str, Any]:
    """
    Check if a PDF field has already been signed.
    
    Args:
        pdf_field_id: ID of the PDF field
    
    Returns:
        Dict with success status and signature information
    """
    db = get_db()
    if not db:
        return {"success": False, "error": "Database not connected"}
    
    try:
        response = db.table("signatures").select("*").eq(
            "pdf_field_id", pdf_field_id
        ).limit(1).execute()
        
        if response.data:
            return {
                "success": True,
                "is_signed": True,
                "signature": response.data[0]
            }
        else:
            return {
                "success": True,
                "is_signed": False,
                "signature": None
            }
        
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}