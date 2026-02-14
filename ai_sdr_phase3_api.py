"""
ai_sdr_phase3_api.py — API Endpoints for AI SDR Phase 3: Auto Proposal Generation
==================================================================================

Flask API endpoints for generating proposals from CRM discovery data.
Integrates with Phase 2 discovery data to create professional proposals.

Endpoints:
- POST /api/proposal/generate - Generate proposal from contact ID
- GET /api/proposal/recommendations/<contact_id> - Get service recommendations
- GET /api/proposal/services - List available services
- GET /api/proposal/status/<proposal_id> - Get proposal status
- POST /api/proposal/approve/<proposal_id> - Approve/send proposal

Usage:
    import requests
    response = requests.post('http://localhost:5002/api/proposal/generate',
                           json={"contact_id": "uuid-here"})
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import our proposal generation module
from ai_sdr_proposal_generation import (
    generate_proposal_from_discovery,
    get_service_recommendations,
    list_available_services,
    ProposalGenerationEngine
)

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/proposal/generate', methods=['POST'])
def generate_proposal():
    """
    Generate complete proposal from CRM discovery data
    
    Request body:
    {
        "contact_id": "uuid-string",
        "custom_notes": "optional additional notes"
    }
    
    Response:
    {
        "success": true,
        "contact_id": "uuid",
        "proposal_id": "uuid", 
        "proposal_path": "/path/to/proposal.pdf",
        "total_investment": 25000,
        "recommendations_count": 3,
        "valid_until": "2026-03-15T00:00:00",
        "download_url": "/api/proposal/download/proposal-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'contact_id' not in data:
            return jsonify({
                "success": False,
                "error": "contact_id is required"
            }), 400
        
        contact_id = data['contact_id']
        custom_notes = data.get('custom_notes', '')
        
        logger.info(f"Generating proposal for contact: {contact_id}")
        
        # Generate proposal
        result = generate_proposal_from_discovery(contact_id)
        
        if not result['success']:
            logger.error(f"Proposal generation failed: {result.get('error')}")
            return jsonify(result), 400
        
        # Add download URL
        if result.get('proposal_id'):
            result['download_url'] = f"/api/proposal/download/{result['proposal_id']}"
        
        logger.info(f"✅ Proposal generated successfully: {result['proposal_id']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Proposal generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/proposal/recommendations/<contact_id>', methods=['GET'])
def get_recommendations(contact_id: str):
    """
    Get service recommendations for a contact without generating full proposal
    
    Response:
    {
        "success": true,
        "contact_id": "uuid",
        "recommendations": [
            {
                "service_name": "Professional Website",
                "service_category": "Web Development", 
                "estimated_price": 6500,
                "estimated_timeline": "4-8 weeks",
                "reasoning": "Professional web presence needed...",
                "priority": 1
            }
        ]
    }
    """
    try:
        logger.info(f"Getting recommendations for contact: {contact_id}")
        
        recommendations = get_service_recommendations(contact_id)
        
        if not recommendations:
            return jsonify({
                "success": False,
                "error": "No discovery data found or no suitable services identified"
            }), 404
        
        return jsonify({
            "success": True,
            "contact_id": contact_id,
            "recommendations": recommendations
        })
        
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/proposal/services', methods=['GET'])
def get_services():
    """
    List all available MPT services
    
    Response:
    {
        "success": true,
        "services": [
            {
                "name": "Professional Website",
                "description": "Custom responsive website...",
                "base_price": 5000,
                "category": "Web Development",
                "timeline_weeks": [4, 8]
            }
        ]
    }
    """
    try:
        services = list_available_services()
        
        return jsonify({
            "success": True,
            "services": services
        })
        
    except Exception as e:
        logger.error(f"Services listing error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/proposal/download/<proposal_id>', methods=['GET'])
def download_proposal(proposal_id: str):
    """
    Download proposal PDF by proposal ID
    
    Returns PDF file for download
    """
    try:
        # Get proposal record from database
        engine = ProposalGenerationEngine()
        
        query = "SELECT file_path, title FROM proposals WHERE id = %s"
        result = engine.db.query(query, (proposal_id,))
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Proposal not found"
            }), 404
        
        file_path = result[0]['file_path']
        title = result[0]['title']
        
        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "error": "Proposal file not found"
            }), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{title}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/proposal/status/<proposal_id>', methods=['GET'])
def get_proposal_status(proposal_id: str):
    """
    Get proposal status and details
    
    Response:
    {
        "success": true,
        "proposal_id": "uuid",
        "title": "Technology Solutions Proposal - John Doe",
        "status": "draft",
        "total_amount": 25000,
        "proposal_date": "2026-02-09",
        "valid_until": "2026-03-11",
        "contact_id": "uuid",
        "services": [...],
        "file_path": "/path/to/proposal.pdf"
    }
    """
    try:
        engine = ProposalGenerationEngine()
        
        query = """
            SELECT id, contact_id, title, total_amount, status, 
                   proposal_date, valid_until, file_path, services, 
                   created_at, updated_at
            FROM proposals 
            WHERE id = %s
        """
        result = engine.db.query(query, (proposal_id,))
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Proposal not found"
            }), 404
        
        proposal = result[0]
        
        # Parse services JSON
        services = json.loads(proposal.get('services', '[]'))
        
        return jsonify({
            "success": True,
            "proposal_id": proposal['id'],
            "title": proposal['title'],
            "status": proposal['status'],
            "total_amount": proposal['total_amount'],
            "proposal_date": proposal['proposal_date'],
            "valid_until": proposal['valid_until'],
            "contact_id": proposal['contact_id'],
            "services": services,
            "file_path": proposal['file_path'],
            "created_at": proposal['created_at'],
            "updated_at": proposal['updated_at']
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/proposal/approve/<proposal_id>', methods=['POST'])
def approve_proposal(proposal_id: str):
    """
    Approve proposal and update status
    
    Request body:
    {
        "action": "approve" | "reject" | "send",
        "notes": "optional approval notes"
    }
    
    Response:
    {
        "success": true,
        "proposal_id": "uuid",
        "new_status": "approved",
        "timestamp": "2026-02-09T14:30:00"
    }
    """
    try:
        data = request.get_json()
        action = data.get('action', 'approve')
        notes = data.get('notes', '')
        
        # Validate action
        valid_actions = ['approve', 'reject', 'send']
        if action not in valid_actions:
            return jsonify({
                "success": False,
                "error": f"Invalid action. Must be one of: {valid_actions}"
            }), 400
        
        # Map action to status
        status_map = {
            'approve': 'approved',
            'reject': 'rejected', 
            'send': 'sent'
        }
        new_status = status_map[action]
        
        engine = ProposalGenerationEngine()
        
        # Update proposal status
        update_query = """
            UPDATE proposals 
            SET status = %s, updated_at = NOW()
            WHERE id = %s
        """
        engine.db.execute(update_query, (new_status, proposal_id))
        
        # Log activity
        activity_query = """
            INSERT INTO activities (id, contact_id, activity_type, notes, created_at)
            SELECT gen_random_uuid(), contact_id, %s, %s, NOW()
            FROM proposals WHERE id = %s
        """
        activity_type = f"proposal_{action}d"
        activity_notes = f"Proposal {action}d" + (f": {notes}" if notes else "")
        
        engine.db.execute(activity_query, (activity_type, activity_notes, proposal_id))
        
        logger.info(f"✅ Proposal {proposal_id} {action}d successfully")
        
        return jsonify({
            "success": True,
            "proposal_id": proposal_id,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Approval error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/proposal/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Response:
    {
        "success": true,
        "status": "healthy",
        "timestamp": "2026-02-09T14:30:00",
        "database": "connected",
        "services_count": 7,
        "version": "1.0"
    }
    """
    try:
        engine = ProposalGenerationEngine()
        
        # Test database connection
        test_query = "SELECT 1"
        engine.db.query(test_query)
        db_status = "connected"
        
        services_count = len(list_available_services())
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "services_count": services_count,
            "version": "1.0"
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/proposal/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with sample data"""
    try:
        return jsonify({
            "success": True,
            "message": "AI SDR Phase 3 API is working!",
            "endpoints": [
                "POST /api/proposal/generate",
                "GET /api/proposal/recommendations/<contact_id>",
                "GET /api/proposal/services",
                "GET /api/proposal/status/<proposal_id>",
                "POST /api/proposal/approve/<proposal_id>",
                "GET /api/proposal/download/<proposal_id>",
                "GET /api/proposal/health",
                "GET /api/proposal/test"
            ],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================================================
# INTEGRATION WITH PHASE 2
# ============================================================================

@app.route('/api/proposal/auto-generate', methods=['POST'])
def auto_generate_from_phase2():
    """
    Auto-generate proposal when Phase 2 completes discovery
    Called automatically by Phase 2 for hot leads
    
    Request body:
    {
        "contact_id": "uuid",
        "lead_score": 85,
        "trigger": "hot_lead"
    }
    """
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        lead_score = data.get('lead_score', 0)
        trigger = data.get('trigger', 'manual')
        
        if not contact_id:
            return jsonify({"success": False, "error": "contact_id required"}), 400
        
        logger.info(f"🔥 Auto-generating proposal for hot lead: {contact_id} (score: {lead_score})")
        
        # Generate proposal
        result = generate_proposal_from_discovery(contact_id)
        
        if result['success']:
            # Log auto-generation
            engine = ProposalGenerationEngine()
            activity_query = """
                INSERT INTO activities (id, contact_id, activity_type, notes, created_at)
                VALUES (gen_random_uuid(), %s, %s, %s, NOW())
            """
            engine.db.execute(activity_query, (
                contact_id,
                "proposal_auto_generated",
                f"🔥 Auto-generated proposal for hot lead (score: {lead_score})"
            ))
            
            result['trigger'] = trigger
            result['lead_score'] = lead_score
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Auto-generation error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "Check API documentation for available endpoints"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": "Check the HTTP method for this endpoint"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    # Ensure proposals directory exists
    Path("C:/Users/Patri/clawd/proposals").mkdir(exist_ok=True)
    
    print("🚀 Starting AI SDR Phase 3 API Server")
    print("=" * 50)
    print("🔗 Available endpoints:")
    print("  • POST /api/proposal/generate")
    print("  • GET  /api/proposal/recommendations/<id>")
    print("  • GET  /api/proposal/services") 
    print("  • GET  /api/proposal/status/<id>")
    print("  • POST /api/proposal/approve/<id>")
    print("  • GET  /api/proposal/download/<id>")
    print("  • GET  /api/proposal/health")
    print("  • GET  /api/proposal/test")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5002,  # Different port from Phase 2 (5001)
        debug=True,
        threaded=True
    )