"""
E-Signature Components for MPT-CRM
==================================

Custom components for the e-signature workflow:
1. PDF Viewer using PDF.js
2. Signature capture canvas
3. Legal verification and hashing
4. Document processing utilities
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
import hashlib
import json
import uuid
import fitz  # PyMuPDF
from datetime import datetime
from io import BytesIO
from PIL import Image
import os

def render_pdf_viewer(pdf_path: str, height: int = 600) -> None:
    """
    Render a PDF using PDF.js viewer embedded in Streamlit
    
    Args:
        pdf_path: Path to the PDF file
        height: Height of the viewer in pixels
    """
    try:
        # Read PDF file and encode as base64
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            pdf_base64 = base64.b64encode(pdf_data).decode()
        
        # Create PDF.js viewer HTML
        pdf_viewer_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                    background: #f0f0f0;
                }}
                #pdfContainer {{
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    overflow: auto;
                    max-height: {height - 60}px;
                }}
                .pdf-page {{
                    margin: 10px auto;
                    display: block;
                    border: 1px solid #ccc;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .controls {{
                    margin-bottom: 10px;
                    text-align: center;
                }}
                .btn {{
                    background: #0066cc;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    margin: 0 4px;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                .btn:hover {{
                    background: #0052a3;
                }}
                .page-info {{
                    display: inline-block;
                    margin: 0 10px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="controls">
                <button class="btn" onclick="zoomOut()">Zoom Out</button>
                <button class="btn" onclick="zoomIn()">Zoom In</button>
                <span class="page-info" id="pageInfo">Loading...</span>
            </div>
            <div id="pdfContainer"></div>
            
            <script>
                let pdfDoc = null;
                let currentScale = 1.0;
                
                // PDF.js setup
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                
                // Load PDF from base64 data
                const pdfData = atob('{pdf_base64}');
                const pdfArray = new Uint8Array(pdfData.length);
                for (let i = 0; i < pdfData.length; i++) {{
                    pdfArray[i] = pdfData.charCodeAt(i);
                }}
                
                pdfjsLib.getDocument(pdfArray).promise.then(function(pdf) {{
                    pdfDoc = pdf;
                    document.getElementById('pageInfo').textContent = `Page 1 of ${{pdf.numPages}}`;
                    renderAllPages();
                }}).catch(function(error) {{
                    console.error('Error loading PDF:', error);
                    document.getElementById('pdfContainer').innerHTML = '<p style="text-align:center;color:red;">Error loading PDF</p>';
                }});
                
                function renderAllPages() {{
                    const container = document.getElementById('pdfContainer');
                    container.innerHTML = '';
                    
                    for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {{
                        renderPage(pageNum, container);
                    }}
                }}
                
                function renderPage(pageNum, container) {{
                    pdfDoc.getPage(pageNum).then(function(page) {{
                        const viewport = page.getViewport({{scale: currentScale}});
                        const canvas = document.createElement('canvas');
                        const context = canvas.getContext('2d');
                        
                        canvas.className = 'pdf-page';
                        canvas.height = viewport.height;
                        canvas.width = viewport.width;
                        
                        container.appendChild(canvas);
                        
                        const renderContext = {{
                            canvasContext: context,
                            viewport: viewport
                        }};
                        
                        page.render(renderContext);
                    }});
                }}
                
                function zoomIn() {{
                    currentScale += 0.2;
                    renderAllPages();
                }}
                
                function zoomOut() {{
                    if (currentScale > 0.4) {{
                        currentScale -= 0.2;
                        renderAllPages();
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        # Render the HTML component
        components.html(pdf_viewer_html, height=height)
        
    except Exception as e:
        st.error(f"Error loading PDF: {e}")


def render_signature_canvas(key: str = "signature", width: int = 400, height: int = 200) -> dict:
    """
    Render a signature capture canvas
    
    Args:
        key: Unique key for the canvas component
        width: Canvas width in pixels
        height: Canvas height in pixels
    
    Returns:
        dict: Canvas data with signature image
    """
    try:
        from streamlit_drawable_canvas import st_canvas
        
        # Create signature canvas
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  # Transparent background
            stroke_width=2,
            stroke_color="black",
            background_color="white",
            background_image=None,
            update_streamlit=True,
            width=width,
            height=height,
            drawing_mode="freedraw",
            point_display_radius=0,
            key=key,
        )
        
        return canvas_result
        
    except ImportError:
        st.error("streamlit-drawable-canvas not installed. Please install it: pip install streamlit-drawable-canvas")
        return None
    except Exception as e:
        st.error(f"Error creating signature canvas: {e}")
        return None


def create_typed_signature(name: str, font_size: int = 48) -> Image.Image:
    """
    Create a typed signature using a cursive font
    
    Args:
        name: Name to convert to signature
        font_size: Font size for the signature
    
    Returns:
        PIL Image of the typed signature
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create image with transparent background
        img_width = len(name) * font_size // 2 + 40
        img_height = font_size + 20
        
        img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to use a cursive font, fallback to default
        try:
            # Common cursive fonts on Windows
            font_paths = [
                "C:/Windows/Fonts/Segmdl2.ttf",  # Segoe MDL2 Assets
                "C:/Windows/Fonts/calibri.ttf",   # Calibri (italic-like)
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            
            if font is None:
                font = ImageFont.load_default()
                
        except Exception:
            font = ImageFont.load_default()
        
        # Draw the signature
        draw.text((20, 10), name, font=font, fill=(0, 0, 0, 255))
        
        return img
        
    except Exception as e:
        st.error(f"Error creating typed signature: {e}")
        return None


def generate_document_hash(pdf_data: bytes, signature_data: bytes, timestamp: str) -> str:
    """
    Generate SHA-256 hash for legal verification
    
    Args:
        pdf_data: Original PDF file data
        signature_data: Signature image data
        timestamp: ISO timestamp string
    
    Returns:
        str: SHA-256 hash hex string
    """
    try:
        # Combine all data for hashing
        combined_data = pdf_data + signature_data + timestamp.encode('utf-8')
        
        # Generate SHA-256 hash
        hash_object = hashlib.sha256(combined_data)
        return hash_object.hexdigest()
        
    except Exception as e:
        st.error(f"Error generating document hash: {e}")
        return None


def create_audit_trail(document_id: str, signer_email: str, signature_hash: str, timestamp: str) -> dict:
    """
    Create an audit trail for legal compliance
    
    Args:
        document_id: Unique document identifier
        signer_email: Email of the signer
        signature_hash: Hash of the signature process
        timestamp: ISO timestamp of signing
    
    Returns:
        dict: Audit trail data
    """
    audit_data = {
        "document_id": document_id,
        "signer_email": signer_email,
        "signature_hash": signature_hash,
        "timestamp": timestamp,
        "verification_data": {
            "hash_algorithm": "SHA-256",
            "signature_method": "electronic_signature",
            "compliance_level": "electronic_signature_act",
            "ip_address": "pending",  # Could be captured from request headers
            "user_agent": "mpt_crm_esign_v1"
        },
        "legal_disclaimer": "This document was signed electronically using MPT-CRM E-Signature system. The signature is legally binding according to the Electronic Signatures in Global and National Commerce Act (E-SIGN Act)."
    }
    
    return audit_data


def overlay_signature_on_pdf(pdf_path: str, signature_image: Image.Image, 
                           position: tuple = None, page_num: int = 1) -> bytes:
    """
    Overlay signature on PDF and return signed PDF data
    
    Args:
        pdf_path: Path to original PDF
        signature_image: PIL Image of signature
        position: (x, y) position for signature placement
        page_num: Page number to sign (1-indexed)
    
    Returns:
        bytes: Signed PDF data
    """
    try:
        # Open PDF with PyMuPDF
        pdf_doc = fitz.open(pdf_path)
        
        if page_num > len(pdf_doc):
            raise ValueError(f"Page {page_num} does not exist in PDF")
        
        page = pdf_doc[page_num - 1]  # Convert to 0-indexed
        
        # Convert PIL image to bytes
        img_buffer = BytesIO()
        signature_image.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
        
        # Default position (bottom right)
        if position is None:
            page_rect = page.rect
            sig_width = 150
            sig_height = 75
            position = (page_rect.width - sig_width - 50, page_rect.height - sig_height - 50)
        
        # Create signature rectangle
        sig_rect = fitz.Rect(position[0], position[1], 
                            position[0] + 150, position[1] + 75)
        
        # Insert signature image
        page.insert_image(sig_rect, stream=img_data)
        
        # Save modified PDF
        output_buffer = BytesIO()
        pdf_doc.save(output_buffer)
        pdf_doc.close()
        
        return output_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error overlaying signature on PDF: {e}")
        return None


def validate_signature_token(token: str) -> bool:
    """
    Validate a signing token format
    
    Args:
        token: UUID token string
    
    Returns:
        bool: True if valid UUID format
    """
    try:
        uuid.UUID(token)
        return True
    except ValueError:
        return False


def generate_signing_url(base_url: str, signing_token: str) -> str:
    """
    Generate a secure signing URL
    
    Args:
        base_url: Base URL of the application
        signing_token: Secure UUID token
    
    Returns:
        str: Complete signing URL
    """
    return f"{base_url}/sign/{signing_token}"


def check_document_expired(expires_at: str) -> bool:
    """
    Check if a document signing link has expired
    
    Args:
        expires_at: ISO timestamp string
    
    Returns:
        bool: True if expired
    """
    try:
        expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        return datetime.now() > expiry_time
    except Exception:
        return True  # Assume expired if can't parse date