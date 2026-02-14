"""
ai_sdr_api.py — API Endpoints for AI SDR Phase 2 Integration
============================================================

Flask API endpoints that Phase 1 can call when discovery completes.
Handles discovery data processing, contact creation, and lead scoring.

Endpoints:
- POST /api/discovery/process - Main endpoint for processing discovery data
- GET /api/discovery/score/<contact_id> - Get lead score breakdown
- GET /api/discovery/test - Test endpoint with sample data
- GET /api/discovery/health - Health check

Usage from Phase 1:
    import requests
    response = requests.post('http://localhost:5001/api/discovery/process', 
                           json=discovery_data)
    result = response.json()
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Import our integration module
from ai_sdr_discovery_integration import (
    process_discovery_data,
    get_lead_score_breakdown,
    example_usage
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

@app.route('/api/discovery/process', methods=['POST'])
def api_process_discovery():
    """
    Main endpoint for processing completed discovery data
    
    Expected JSON payload:
    {
        "first_name": "John",
        "last_name": "Doe",
        "company": "Doe Industries",
        "email": "john@doeindustries.com",
        "phone": "239-555-0123",
        "project_types": ["website", "crm"],
        "budget_range": "10k to 25k",
        "decision_maker": "Yes - sole decision maker",
        ...
    }
    
    Returns:
    {
        "success": true,
        "contact_id": "uuid-here",
        "intake_id": "uuid-here", 
        "deal_id": "uuid-here",
        "lead_score": {
            "total": 85,
            "budget": 22,
            "timeline": 20,
            "authority": 25,
            "need": 18,
            "is_hot_lead": true,
            "notes": "Strong budget fit | High urgency/clear timeline | Strong decision authority"
        }
    }
    """
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        discovery_data = request.get_json()
        
        # Log the request
        logger.info(f"Processing discovery data for {discovery_data.get('first_name')} {discovery_data.get('last_name')}")
        
        # Process the discovery data
        result = process_discovery_data(discovery_data)
        
        # Log the result
        if result.get('success'):
            logger.info(f"Successfully processed discovery: Contact {result.get('contact_id')}, Score: {result.get('lead_score', {}).get('total', 0)}")
            if result.get('lead_score', {}).get('is_hot_lead'):
                logger.info(f"🔥 HOT LEAD DETECTED: {discovery_data.get('first_name')} {discovery_data.get('last_name')} - Score {result.get('lead_score', {}).get('total', 0)}")
        else:
            logger.error(f"Discovery processing failed: {result.get('error')}")
        
        # Return appropriate HTTP status
        status_code = 200 if result.get('success') else 500
        
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API error processing discovery: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"API error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/discovery/score/<contact_id>', methods=['GET'])
def api_get_lead_score(contact_id: str):
    """
    Get detailed lead score breakdown for a contact
    
    Returns:
    {
        "success": true,
        "contact_name": "John Doe",
        "company": "Doe Industries", 
        "lead_score": {
            "total": 85,
            "budget_score": 22,
            "timeline_score": 20,
            "authority_score": 25,
            "need_score": 18,
            "is_hot_lead": true,
            "scoring_notes": "Strong budget fit | High urgency"
        },
        "discovery_data": {
            "budget_range": "$10,000 - $25,000",
            "timeline": "Hard deadline",
            "project_types": ["Website Development", "Custom Software / CRM"]
        }
    }
    """
    
    try:
        logger.info(f"Getting lead score for contact: {contact_id}")
        
        result = get_lead_score_breakdown(contact_id)
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API error getting lead score: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error retrieving lead score: {str(e)}"
        }), 500

@app.route('/api/discovery/test', methods=['GET'])
def api_test_discovery():
    """
    Test endpoint with sample discovery data
    
    Useful for testing the integration without Phase 1 data
    """
    
    try:
        logger.info("Running discovery integration test")
        
        result = example_usage()
        
        return jsonify({
            "message": "Discovery integration test completed",
            "test_result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Test error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/discovery/health', methods=['GET'])
def api_health_check():
    """
    Health check endpoint
    
    Returns system status and database connectivity
    """
    
    try:
        from db_service import db_is_connected, db_test_connection
        
        # Check database connectivity
        db_connected = db_is_connected()
        db_status = "connected" if db_connected else "disconnected"
        
        # Test database with a simple query
        test_success = False
        test_message = "not tested"
        
        if db_connected:
            test_success, test_message = db_test_connection()
        
        return jsonify({
            "status": "healthy",
            "service": "AI SDR Discovery Integration API",
            "version": "1.0.0",
            "database": {
                "connected": db_connected,
                "status": db_status,
                "test_passed": test_success,
                "test_message": test_message
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/discovery/batch', methods=['POST'])
def api_batch_process_discovery():
    """
    Batch process multiple discovery records
    
    Expected JSON payload:
    {
        "discoveries": [
            {discovery_data_1},
            {discovery_data_2},
            ...
        ]
    }
    
    Returns:
    {
        "success": true,
        "processed": 2,
        "failed": 0,
        "results": [
            {result_1},
            {result_2}
        ],
        "summary": {
            "total_contacts": 2,
            "hot_leads": 1,
            "deals_created": 1
        }
    }
    """
    
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        discoveries = data.get('discoveries', [])
        
        if not discoveries:
            return jsonify({
                "success": False,
                "error": "No discoveries provided"
            }), 400
        
        logger.info(f"Processing batch of {len(discoveries)} discoveries")
        
        results = []
        processed = 0
        failed = 0
        hot_leads = 0
        deals_created = 0
        
        for i, discovery_data in enumerate(discoveries):
            try:
                result = process_discovery_data(discovery_data)
                results.append(result)
                
                if result.get('success'):
                    processed += 1
                    if result.get('lead_score', {}).get('is_hot_lead'):
                        hot_leads += 1
                    if result.get('deal_id'):
                        deals_created += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error processing discovery {i}: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "index": i
                })
                failed += 1
        
        summary = {
            "total_contacts": processed,
            "hot_leads": hot_leads,
            "deals_created": deals_created
        }
        
        logger.info(f"Batch processing complete: {processed} processed, {failed} failed, {hot_leads} hot leads")
        
        return jsonify({
            "success": True,
            "processed": processed,
            "failed": failed,
            "results": results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Batch processing error: {str(e)}"
        }), 500

@app.route('/api/discovery/mapping-test', methods=['POST'])
def api_test_data_mapping():
    """
    Test data mapping functionality without creating CRM records
    
    Useful for testing how voice data maps to CRM fields
    """
    
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        raw_data = request.get_json()
        
        # Import mapping classes
        from ai_sdr_discovery_integration import DiscoveryDataMapper, LeadScoringEngine, DiscoveryData
        
        mapper = DiscoveryDataMapper()
        scorer = LeadScoringEngine()
        
        # Test data mapping
        mapped_data = {
            "project_types": {
                "raw": raw_data.get('project_types', []),
                "mapped": mapper.normalize_project_types(raw_data.get('project_types', []))
            },
            "budget_range": {
                "raw": raw_data.get('budget_range', ''),
                "mapped": mapper.normalize_budget_range(raw_data.get('budget_range', ''))
            },
            "industry": {
                "raw": raw_data.get('industry', ''),
                "mapped": mapper.normalize_industry(raw_data.get('industry', ''))
            },
            "integrations": {
                "raw": raw_data.get('integrations', []),
                "mapped": mapper.normalize_integrations(raw_data.get('integrations', []))
            }
        }
        
        # Create discovery data object for scoring
        discovery_data = DiscoveryData(
            project_types=mapped_data["project_types"]["mapped"],
            budget_range=mapped_data["budget_range"]["mapped"],
            budget_flexibility=raw_data.get('budget_flexibility', ''),
            timeline=raw_data.get('timeline', ''),
            urgency=raw_data.get('urgency', ''),
            decision_maker=raw_data.get('decision_maker', ''),
            decision_timeline=raw_data.get('decision_timeline', ''),
            pain_points=raw_data.get('pain_points', ''),
            business_needs=raw_data.get('business_needs', [])
        )
        
        # Calculate lead score
        lead_score = scorer.calculate_lead_score(discovery_data)
        
        return jsonify({
            "success": True,
            "mapping_results": mapped_data,
            "lead_score": {
                "total": lead_score.total_score,
                "budget_score": lead_score.budget_score,
                "timeline_score": lead_score.timeline_score,
                "authority_score": lead_score.authority_score,
                "need_score": lead_score.need_score,
                "is_hot_lead": lead_score.is_hot_lead,
                "scoring_notes": lead_score.scoring_notes
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Mapping test error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Mapping test error: {str(e)}"
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "POST /api/discovery/process",
            "GET /api/discovery/score/<contact_id>",
            "GET /api/discovery/test", 
            "GET /api/discovery/health",
            "POST /api/discovery/batch",
            "POST /api/discovery/mapping-test"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("\\n" + "="*60)
    print("🤖 AI SDR DISCOVERY INTEGRATION API")
    print("="*60)
    print("Starting Flask server for Phase 2 integration...")
    print("\\nAvailable endpoints:")
    print("• POST /api/discovery/process - Process discovery data")
    print("• GET /api/discovery/score/<id> - Get lead score") 
    print("• GET /api/discovery/test - Run test")
    print("• GET /api/discovery/health - Health check")
    print("• POST /api/discovery/batch - Batch processing")
    print("• POST /api/discovery/mapping-test - Test data mapping")
    print("\\n" + "="*60)
    
    # Start the Flask development server
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5001,       # Use port 5001 (5000 might be taken by main CRM)
        debug=True,      # Enable debug mode
        threaded=True    # Handle multiple requests
    )