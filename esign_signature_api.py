# E-Signature Phase 3: Flask API endpoints for signature application
# This file contains the API routes for handling signature requests

import os
import tempfile
from flask import Flask, request, jsonify
from datetime import datetime
from esign_signature_service import process_signature_application, get_signature_records, check_field_signed


def create_signature_api_routes(app: Flask):
    """
    Add signature application API routes to the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/esign/apply_signature', methods=['POST'])
    def apply_signature_endpoint():
        """
        API endpoint to apply a signature to a PDF document.
        
        Expected JSON payload:
        {
            "pdf_field_id": "field_123",
            "document_id": "doc_456", 
            "signature_type": "draw" or "type",
            "signature_data": "base64_image_data" or "text",
            "x_coordinate": 300.0,
            "y_coordinate": 400.0,
            "width": 120.0,
            "height": 40.0,
            "page_number": 1,
            "font_family": "cursive" (optional),
            "font_size": 16 (optional)
        }
        
        Returns:
            JSON response with success status and signature information
        """
        try:
            # Parse request data
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No JSON data provided"
                }), 400
            
            # Validate required fields
            required_fields = [
                'pdf_field_id', 'document_id', 'signature_type', 'signature_data',
                'x_coordinate', 'y_coordinate', 'width', 'height', 'page_number'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            # Check if field is already signed
            field_check = check_field_signed(data['pdf_field_id'])
            if field_check['success'] and field_check['is_signed']:
                return jsonify({
                    "success": False,
                    "error": "This field has already been signed",
                    "existing_signature": field_check['signature']
                }), 409
            
            # For demo/testing purposes, we'll use temporary files
            # In production, you would get the actual PDF path from the document_id
            temp_input = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_output = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            
            try:
                # TODO: Replace with actual PDF retrieval logic
                # For now, create a dummy PDF path (this would normally come from document storage)
                input_pdf_path = get_document_pdf_path(data['document_id'])
                if not input_pdf_path or not os.path.exists(input_pdf_path):
                    return jsonify({
                        "success": False,
                        "error": f"PDF document not found for document_id: {data['document_id']}"
                    }), 404
                
                output_pdf_path = temp_output.name
                
                # Process signature application
                result = process_signature_application(data, input_pdf_path, output_pdf_path)
                
                if result['success']:
                    # TODO: In production, save the signed PDF to proper location
                    # and update the document record with the new signed PDF path
                    update_document_with_signed_pdf(data['document_id'], output_pdf_path)
                    
                    return jsonify({
                        "success": True,
                        "message": result['message'],
                        "signature_record": result.get('signature_record'),
                        "pdf_field_id": data['pdf_field_id']
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": result['error']
                    }), 500
                    
            finally:
                # Clean up temporary files
                try:
                    if os.path.exists(temp_input.name):
                        os.unlink(temp_input.name)
                    # Don't delete output file immediately - it might be needed
                    # os.unlink(temp_output.name)
                except Exception as e:
                    print(f"[esign_signature_api] Warning: Failed to clean up temp files: {e}")
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }), 500
    
    
    @app.route('/api/esign/signatures/<document_id>', methods=['GET'])
    def get_document_signatures(document_id):
        """
        Get all signatures for a specific document.
        
        Args:
            document_id: UUID of the document
        
        Returns:
            JSON response with list of signature records
        """
        try:
            result = get_signature_records(document_id)
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "document_id": document_id,
                    "signatures": result['signatures']
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }), 500
    
    
    @app.route('/api/esign/check_field/<pdf_field_id>', methods=['GET'])
    def check_field_signature_status(pdf_field_id):
        """
        Check if a specific PDF field has been signed.
        
        Args:
            pdf_field_id: ID of the PDF field
        
        Returns:
            JSON response with signature status
        """
        try:
            result = check_field_signed(pdf_field_id)
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "pdf_field_id": pdf_field_id,
                    "is_signed": result['is_signed'],
                    "signature": result['signature']
                })
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 500
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }), 500


def get_document_pdf_path(document_id: str) -> str:
    """
    Get the file path for a document's PDF.
    
    This is a placeholder function that should be replaced with actual
    document retrieval logic from your document storage system.
    
    Args:
        document_id: UUID of the document
    
    Returns:
        Path to the PDF file, or empty string if not found
    """
    # TODO: Replace with actual document storage logic
    # This might involve:
    # 1. Querying the esign_documents table to get the pdf_path
    # 2. Checking if the file exists on disk or in cloud storage
    # 3. Downloading from cloud storage if needed
    
    from db_service import get_db
    
    try:
        db = get_db()
        if not db:
            return ""
        
        # Query esign_documents table for the PDF path
        response = db.table("esign_documents").select("pdf_path").eq(
            "id", document_id
        ).single().execute()
        
        if response.data and response.data.get('pdf_path'):
            pdf_path = response.data['pdf_path']
            
            # Check if file exists
            if os.path.exists(pdf_path):
                return pdf_path
            else:
                print(f"[esign_signature_api] PDF file not found: {pdf_path}")
                return ""
        else:
            print(f"[esign_signature_api] No PDF path found for document_id: {document_id}")
            return ""
    
    except Exception as e:
        print(f"[esign_signature_api] Error retrieving PDF path for {document_id}: {e}")
        return ""


def update_document_with_signed_pdf(document_id: str, signed_pdf_path: str) -> bool:
    """
    Update the document record with the path to the signed PDF.
    
    Args:
        document_id: UUID of the document
        signed_pdf_path: Path to the signed PDF file
    
    Returns:
        True if successful, False otherwise
    """
    # TODO: Implement logic to update the document record
    # This might involve:
    # 1. Moving the signed PDF to a permanent location
    # 2. Updating the esign_documents table with the new path
    # 3. Updating the document status to 'signed'
    
    from db_service import get_db
    
    try:
        db = get_db()
        if not db:
            return False
        
        # Update document record with signed PDF path and status
        response = db.table("esign_documents").update({
            "signed_pdf_path": signed_pdf_path,
            "signed_at": datetime.now().isoformat(),
            "status": "signed"
        }).eq("id", document_id).execute()
        
        return bool(response.data)
        
    except Exception as e:
        print(f"[esign_signature_api] Error updating document with signed PDF: {e}")
        return False


# Example of how to integrate with existing Flask app
if __name__ == '__main__':
    # This is for testing purposes only
    app = Flask(__name__)
    create_signature_api_routes(app)
    app.run(debug=True, port=5001)