"""
SMS Webhook Handler for MPT-CRM
===============================

Lightweight Flask app to handle Twilio SMS webhooks.
Receives inbound messages and status updates.

Usage:
    python sms_webhook.py

Webhook URL: http://your-domain.com:5555/sms-webhook

Deploy to production:
    - Use gunicorn or similar WSGI server
    - Set up reverse proxy with nginx
    - Configure Twilio webhook URL
"""

from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from twilio_sms_service import handle_sms_webhook
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/sms-webhook', methods=['POST'])
def sms_webhook():
    """Handle Twilio SMS webhook events"""
    try:
        # Get webhook data from Twilio
        webhook_data = request.form.to_dict()
        
        # Log the incoming webhook for debugging
        logger.info(f"SMS Webhook received: {webhook_data}")
        
        # Handle the webhook using our SMS service
        success = handle_sms_webhook(webhook_data)
        
        if success:
            logger.info("SMS webhook processed successfully")
            return jsonify({"status": "success"}), 200
        else:
            logger.error("Failed to process SMS webhook")
            return jsonify({"status": "error", "message": "Failed to process webhook"}), 400
            
    except Exception as e:
        logger.error(f"SMS webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "MPT-CRM SMS Webhook",
        "version": "1.0.0"
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Basic info endpoint"""
    return jsonify({
        "service": "MPT-CRM SMS Webhook Handler",
        "endpoints": {
            "/sms-webhook": "POST - Twilio SMS webhook endpoint",
            "/health": "GET - Health check",
        },
        "status": "running"
    }), 200

if __name__ == '__main__':
    # Development server settings
    port = int(os.environ.get('SMS_WEBHOOK_PORT', 5555))
    host = os.environ.get('SMS_WEBHOOK_HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'on')
    
    logger.info(f"Starting SMS webhook server on {host}:{port}")
    logger.info("Webhook URL: http://localhost:5555/sms-webhook")
    logger.info("Configure this URL in Twilio Console > Phone Numbers > [Your Number] > Webhooks")
    
    app.run(host=host, port=port, debug=debug)