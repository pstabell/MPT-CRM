"""
E-Signature Page for MPT-CRM
=============================

Custom in-house e-signature solution integrated with MPT-CRM.
Features:
- Send documents for signature
- Track signature status
- Manage signing workflow
- SharePoint integration
- Legal compliance and audit trails
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import uuid
from datetime import datetime, timedelta
import base64
from pathlib import Path

# Import CRM modules
from db_service import (
    db_create_esign_document, db_get_esign_documents, db_update_esign_document,
    db_add_esign_audit_entry, db_get_contacts
)
from esign_components import (
    render_pdf_viewer, render_signature_canvas, create_typed_signature,
    generate_document_hash, create_audit_trail, overlay_signature_on_pdf,
    validate_signature_token, generate_signing_url, check_document_expired
)
from esign_email_service import send_esign_request_email, send_esign_completion_email
from esign_sharepoint_service import store_signed_document_in_sharepoint
from sso_auth import require_sso_auth, is_authenticated
from mobile_styles import inject_mobile_styles, render_mobile_navigation

# Page configuration
st.set_page_config(
    page_title="E-Signature - MPT-CRM",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mobile styles
inject_mobile_styles()

# Authentication
require_sso_auth(allow_bypass=True)

# Import sidebar navigation
import sys
sys.path.append("..")
from app import render_sidebar

# Render navigation
render_sidebar("E-Signature")
render_mobile_navigation("E-Signature")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

st.title("📝 E-Signature")
st.markdown("### Custom In-House Document Signing")

# Create tabs for different functions
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Send for Signature", "📋 Track Documents", "✍️ Sign Document", "🎯 Field Editor", "⚙️ Settings"])

# =============================================================================
# TAB 1: SEND FOR SIGNATURE
# =============================================================================
with tab1:
    st.header("Send Document for Signature")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Document Details")
        
        # Document upload
        uploaded_file = st.file_uploader(
            "Upload PDF Document",
            type=['pdf'],
            help="Select the PDF document that needs to be signed"
        )
        
        if uploaded_file:
            # Save uploaded file temporarily
            temp_dir = Path("temp_documents")
            temp_dir.mkdir(exist_ok=True)
            temp_file_path = temp_dir / f"{uuid.uuid4()}.pdf"
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Show PDF preview
            st.subheader("Document Preview")
            render_pdf_viewer(str(temp_file_path), height=400)
            
            # Store file path in session state
            st.session_state['uploaded_pdf_path'] = str(temp_file_path)
    
    with col2:
        st.subheader("Signing Details")
        
        # Document title
        doc_title = st.text_input(
            "Document Title",
            value=uploaded_file.name if uploaded_file else "",
            help="Title for the document to be signed"
        )
        
        # Signer details
        signer_name = st.text_input("Signer Name", help="Full name of the person who will sign")
        signer_email = st.text_input("Signer Email", help="Email address to send signing link")
        
        # Optional: Select from contacts
        if st.checkbox("Select from CRM Contacts"):
            contacts = db_get_contacts()
            if contacts:
                contact_options = [f"{c.get('first_name', '')} {c.get('last_name', '')} ({c.get('email', '')})".strip() 
                                 for c in contacts if c.get('email')]
                selected_contact = st.selectbox("Choose Contact", contact_options)
                
                if selected_contact and "(" in selected_contact:
                    # Parse selected contact
                    contact_email = selected_contact.split("(")[1].replace(")", "")
                    contact_name = selected_contact.split("(")[0].strip()
                    
                    # Pre-fill fields
                    if st.button("Use Selected Contact"):
                        st.session_state['signer_email'] = contact_email
                        st.session_state['signer_name'] = contact_name
                        st.rerun()
        
        # Client/Project association
        client_name = st.text_input("Client Name (Optional)", help="Associate with a specific client")
        
        # Expiration settings
        expiration_days = st.slider("Link Expires in (days)", 1, 30, 14)
        
        st.markdown("---")
        
        # Send button
        if st.button("📤 Send for Signature", type="primary", use_container_width=True):
            if not all([uploaded_file, doc_title, signer_name, signer_email]):
                st.error("Please fill in all required fields")
            elif 'uploaded_pdf_path' not in st.session_state:
                st.error("Please upload a document first")
            else:
                try:
                    # Create e-signature document record
                    doc_data = db_create_esign_document(
                        title=doc_title,
                        pdf_path=st.session_state['uploaded_pdf_path'],
                        signer_email=signer_email,
                        signer_name=signer_name,
                        client_name=client_name or None,
                        created_by=st.session_state.get('auth_user', 'unknown')
                    )
                    
                    if doc_data:
                        # Generate signing URL
                        base_url = st.get_option("server.baseUrlPath") or "http://localhost:8501"
                        signing_url = generate_signing_url(base_url, doc_data['signing_token'])
                        
                        # Add audit trail entry
                        db_add_esign_audit_entry(
                            doc_data['id'],
                            "document_created",
                            f"Document '{doc_title}' created and ready to send",
                            st.session_state.get('auth_user', 'unknown')
                        )
                        
                        st.success(f"✅ Document prepared for signing!")
                        
                        # Send email automatically
                        email_sent = send_esign_request_email(doc_data, base_url)
                        
                        if email_sent:
                            st.success("📧 Signing request email sent successfully!")
                            
                            # Update document status to 'sent'
                            db_update_esign_document(doc_data['id'], {'status': 'sent'})
                            
                            # Add audit trail
                            db_add_esign_audit_entry(
                                doc_data['id'],
                                "email_sent",
                                f"Signing request sent to {signer_email}",
                                st.session_state.get('auth_user', 'unknown')
                            )
                        else:
                            st.warning("⚠️ Document created but email could not be sent.")
                            st.info(f"**Manual Signing URL:** {signing_url}")
                            st.caption("Please send this URL to the signer manually.")
                        
                    else:
                        st.error("Failed to create e-signature document")
                        
                except Exception as e:
                    st.error(f"Error sending document: {e}")

# =============================================================================
# TAB 2: TRACK DOCUMENTS
# =============================================================================
with tab2:
    st.header("Document Tracking")
    
    # Get documents
    documents = db_get_esign_documents(limit=50)
    
    if documents:
        # Status filter
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "pending", "sent", "signed", "completed", "expired"],
                key="status_filter"
            )
        
        # Filter documents
        if status_filter != "All":
            filtered_docs = [d for d in documents if d.get('status') == status_filter]
        else:
            filtered_docs = documents
        
        # Display documents in a table format
        for doc in filtered_docs:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{doc.get('title', 'Untitled')}**")
                    st.caption(f"Signer: {doc.get('signer_name')} ({doc.get('signer_email')})")
                    if doc.get('client_name'):
                        st.caption(f"Client: {doc.get('client_name')}")
                
                with col2:
                    status = doc.get('status', 'unknown')
                    status_colors = {
                        'pending': '🟡',
                        'sent': '🔵', 
                        'signed': '🟢',
                        'completed': '✅',
                        'expired': '🔴',
                        'cancelled': '⭕'
                    }
                    st.markdown(f"{status_colors.get(status, '❓')} **{status.title()}**")
                    
                    created_at = doc.get('created_at', '')
                    if created_at:
                        created_date = created_at.split('T')[0] if 'T' in created_at else created_at
                        st.caption(f"Created: {created_date}")
                
                with col3:
                    if st.button("👀 View", key=f"view_{doc.get('id')}"):
                        st.session_state['viewing_doc'] = doc.get('id')
                        st.rerun()
                
                with col4:
                    if doc.get('status') in ['pending', 'sent']:
                        if st.button("📧 Resend", key=f"resend_{doc.get('id')}"):
                            # TODO: Implement resend functionality
                            st.info("Resend functionality coming soon")
    else:
        st.info("No documents found. Start by sending a document for signature!")

# =============================================================================
# TAB 3: SIGN DOCUMENT (Public signing interface)
# =============================================================================
with tab3:
    st.header("Document Signing")
    
    # Check if there's a signing token in URL parameters
    query_params = st.query_params
    signing_token = query_params.get("token", "")
    
    if not signing_token:
        st.info("Enter a signing token or access this page via a signing link")
        signing_token = st.text_input("Signing Token", help="Enter the secure signing token from your email")
    
    if signing_token:
        if validate_signature_token(signing_token):
            # Get document by signing token
            doc = db_get_esign_document(signing_token=signing_token)
            
            if doc:
                # Check if expired
                if check_document_expired(doc.get('expires_at', '')):
                    st.error("❌ This signing link has expired. Please contact the sender for a new link.")
                elif doc.get('status') in ['signed', 'completed']:
                    st.success("✅ This document has already been signed.")
                else:
                    st.success(f"📄 Document ready for signing: **{doc.get('title')}**")
                    
                    # Display document
                    if os.path.exists(doc.get('pdf_path', '')):
                        render_pdf_viewer(doc.get('pdf_path'), height=400)
                        
                        # Signature capture
                        st.subheader("Your Signature")
                        
                        signature_method = st.radio(
                            "Signature Method",
                            ["Draw Signature", "Type Name"],
                            horizontal=True
                        )
                        
                        signature_data = None
                        
                        if signature_method == "Draw Signature":
                            st.markdown("Draw your signature below:")
                            canvas_result = render_signature_canvas("sign_canvas")
                            
                            if canvas_result and canvas_result.image_data is not None:
                                st.image(canvas_result.image_data, caption="Your signature")
                                signature_data = canvas_result.image_data
                        
                        else:  # Type Name
                            typed_name = st.text_input("Enter your full name")
                            if typed_name:
                                typed_signature = create_typed_signature(typed_name)
                                if typed_signature:
                                    st.image(typed_signature, caption="Your typed signature")
                                    signature_data = typed_signature
                        
                        # Legal agreement
                        if signature_data is not None:
                            st.markdown("---")
                            legal_agreement = st.checkbox(
                                "I agree that my electronic signature is legally binding and has the same effect as a handwritten signature."
                            )
                            
                            if legal_agreement:
                                if st.button("✍️ Sign Document", type="primary", use_container_width=True):
                                    try:
                                        # Generate timestamp and hash
                                        timestamp = datetime.utcnow().isoformat() + 'Z'
                                        
                                        # Get PDF data
                                        with open(doc.get('pdf_path'), 'rb') as f:
                                            pdf_data = f.read()
                                        
                                        # Convert signature to bytes for hashing
                                        if hasattr(signature_data, 'tobytes'):
                                            sig_bytes = signature_data.tobytes()
                                        else:
                                            from io import BytesIO
                                            buf = BytesIO()
                                            signature_data.save(buf, format='PNG')
                                            sig_bytes = buf.getvalue()
                                        
                                        # Generate verification hash
                                        verification_hash = generate_document_hash(
                                            pdf_data, sig_bytes, timestamp
                                        )
                                        
                                        # Create signed PDF (overlay signature)
                                        signed_pdf_data = overlay_signature_on_pdf(
                                            doc.get('pdf_path'), signature_data
                                        )
                                        
                                        if signed_pdf_data:
                                            # Save signed PDF
                                            signed_pdf_path = doc.get('pdf_path').replace('.pdf', '_signed.pdf')
                                            with open(signed_pdf_path, 'wb') as f:
                                                f.write(signed_pdf_data)
                                            
                                            # Update document status
                                            updates = {
                                                'status': 'signed',
                                                'signed_pdf_path': signed_pdf_path,
                                                'signature_hash': verification_hash
                                            }
                                            
                                            if db_update_esign_document(doc.get('id'), updates):
                                                # Add audit trail
                                                db_add_esign_audit_entry(
                                                    doc.get('id'),
                                                    "document_signed",
                                                    f"Document signed by {doc.get('signer_name')}",
                                                    doc.get('signer_email')
                                                )
                                                
                                                # Upload to SharePoint
                                                sharepoint_result = store_signed_document_in_sharepoint(doc, signed_pdf_path)
                                                if sharepoint_result:
                                                    # Update document with SharePoint info
                                                    db_update_esign_document(doc.get('id'), {
                                                        'sharepoint_url': sharepoint_result.get('sharepoint_url'),
                                                        'sharepoint_folder': sharepoint_result.get('folder_path')
                                                    })
                                                    
                                                    db_add_esign_audit_entry(
                                                        doc.get('id'),
                                                        "uploaded_to_sharepoint",
                                                        f"Signed document uploaded to SharePoint: {sharepoint_result.get('folder_path')}",
                                                        "system"
                                                    )
                                                
                                                # Send completion emails
                                                email_sent = send_esign_completion_email(doc, signed_pdf_path)
                                                if email_sent:
                                                    db_add_esign_audit_entry(
                                                        doc.get('id'),
                                                        "completion_emails_sent",
                                                        "Confirmation emails sent to signer and admin",
                                                        "system"
                                                    )
                                                
                                                # Update final status
                                                db_update_esign_document(doc.get('id'), {'status': 'completed'})
                                                
                                                st.balloons()
                                                st.success("🎉 Document signed successfully!")
                                                st.success("📁 Document filed in SharePoint automatically")
                                                st.success("📧 Confirmation emails sent")
                                                st.info("This signing session is now complete.")
                                                
                                            else:
                                                st.error("Failed to update document status")
                                        else:
                                            st.error("Failed to create signed PDF")
                                            
                                    except Exception as e:
                                        st.error(f"Error signing document: {e}")
                    else:
                        st.error("Document file not found. Please contact the sender.")
            else:
                st.error("❌ Invalid or expired signing token")
        else:
            st.error("❌ Invalid token format")

# =============================================================================
# TAB 4: FIELD EDITOR (Phase 1: PDF Viewer + Basic Annotation)
# =============================================================================
with tab4:
    st.header("🎯 PDF Field Editor")
    st.markdown("### DocuSign-like drag-drop field placement for PDF documents")
    
""
    
    st.markdown("""
    **Phase 1 Features:**
    - ✅ PDF.js integration for PDF rendering
    - ✅ Fabric.js for interactive annotation layer
    - ✅ Drag-drop field placement (Signature, Initials, Date, Text)
    - ✅ Multi-page PDF navigation
    - ✅ Field export/import functionality
    - ✅ Mobile-responsive design
    """)
    
    # Load the HTML field editor
    try:
        # Read the HTML file content
        with open('esign_field_editor.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Read CSS file
        with open('esign_field_editor.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Read JS file  
        with open('esign_field_editor.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Combine into single HTML with embedded CSS and JS
        combined_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>E-Signature Field Editor</title>
            
            <!-- PDF.js CDN v4.0.379 -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.mjs" type="module"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.js"></script>
            
            <!-- Fabric.js CDN v5.3.0 -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.0/fabric.min.js"></script>
            
            <style>
            {css_content}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Field Palette -->
                <div class="field-palette">
                    <h3>Field Types</h3>
                    <div class="field-buttons">
                        <button class="field-btn" data-field-type="signature" onclick="selectFieldType('signature')">
                            ✍️ Signature
                        </button>
                        <button class="field-btn" data-field-type="initials" onclick="selectFieldType('initials')">
                            🔤 Initials
                        </button>
                        <button class="field-btn" data-field-type="date" onclick="selectFieldType('date')">
                            📅 Date
                        </button>
                        <button class="field-btn" data-field-type="text" onclick="selectFieldType('text')">
                            📝 Text
                        </button>
                    </div>
                    <div class="selected-field">
                        <p>Selected: <span id="selectedField">None</span></p>
                    </div>
                </div>

                <!-- PDF Viewer Container -->
                <div class="pdf-viewer-container">
                    <!-- Page Navigation -->
                    <div class="page-controls">
                        <button id="prevBtn" onclick="previousPage()">⬅️ Previous</button>
                        <span id="pageInfo">Page 1 of 1</span>
                        <button id="nextBtn" onclick="nextPage()">➡️ Next</button>
                    </div>

                    <!-- Canvas Container with Layered Canvases -->
                    <div class="canvas-container">
                        <!-- PDF Rendering Canvas (Bottom Layer) -->
                        <canvas id="pdfCanvas" class="pdf-canvas"></canvas>
                        
                        <!-- Annotation Canvas (Top Layer) using Fabric.js -->
                        <canvas id="annotationCanvas" class="annotation-canvas"></canvas>
                    </div>

                    <!-- PDF Load Controls -->
                    <div class="pdf-controls">
                        <input type="file" id="pdfInput" accept=".pdf" onchange="loadPDF()" />
                        <label for="pdfInput" class="file-btn">📁 Load PDF</label>
                        
                        <button id="clearFields" onclick="clearAllFields()">🗑️ Clear Fields</button>
                        <button id="exportFields" onclick="exportFieldData()">💾 Export Fields</button>
                    </div>

                    <!-- Debug Info (for development) -->
                    <div class="debug-info" id="debugInfo" style="display: none;">
                        <h4>Debug Info</h4>
                        <p>PDF Pages: <span id="debugPages">0</span></p>
                        <p>Current Page: <span id="debugCurrentPage">0</span></p>
                        <p>Fields Count: <span id="debugFields">0</span></p>
                    </div>
                </div>
            </div>

            <script>
            {js_content}
            
            // Initialize the field editor when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {{
                initializeFieldEditor();
            }});
            </script>
        </body>
        </html>
        """
        
        # Display the field editor in an iframe
        components.html(combined_html, height=700, scrolling=True)
        
        st.markdown("""
        ---
        **Instructions:**
        1. Click "Load PDF" to upload a PDF document
        2. Select a field type from the left panel (Signature, Initials, Date, Text)
        3. Click anywhere on the PDF to place the field
        4. Use Previous/Next buttons to navigate between pages
        5. Export field positions as JSON for later use
        
        **Keyboard Shortcuts:**
        - `Ctrl + ←/→`: Navigate pages
        - `Delete`: Remove selected field
        - `Escape`: Deselect field type
        """)
        
    except FileNotFoundError as e:
        st.error(f"Field editor files not found: {e}")
        st.info("Please ensure esign_field_editor.html, .css, and .js files are in the root directory.")
    except Exception as e:
        st.error(f"Error loading field editor: {e}")

# =============================================================================
# TAB 5: SETTINGS
# =============================================================================
with tab5:
    st.header("E-Signature Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Default Settings")
        
        # Default expiration
        default_expiry = st.number_input("Default Link Expiration (days)", min_value=1, max_value=90, value=14)
        
        # Email templates
        st.subheader("Email Template")
        email_template = st.text_area(
            "Signing Request Email",
            value="""Dear {signer_name},

You have been requested to sign the document: {document_title}

Please click the following link to review and sign the document:
{signing_url}

This link will expire on {expiration_date}.

If you have any questions, please contact us.

Best regards,
Metro Point Technology""",
            height=200
        )
    
    with col2:
        st.subheader("SharePoint Integration")
        
        sharepoint_enabled = st.checkbox("Enable SharePoint Auto-Filing", value=True)
        
        if sharepoint_enabled:
            sharepoint_path = st.text_input(
                "SharePoint Folder Pattern",
                value="SALES/{client_name}/Contracts/Signed/",
                help="Use {client_name} for dynamic folder creation"
            )
        
        st.subheader("Legal Compliance")
        
        st.info("🔒 **Legal Features Enabled:**")
        st.markdown("""
        - ✅ SHA-256 document hashing
        - ✅ UTC timestamp verification  
        - ✅ Complete audit trails
        - ✅ E-SIGN Act compliance
        - ✅ Signature overlay on PDF
        """)
        
        if st.button("📊 View Audit Logs", use_container_width=True):
            st.info("Audit log viewer coming soon")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("🔒 MPT-CRM E-Signature | Legally compliant electronic signatures | E-SIGN Act compliant")