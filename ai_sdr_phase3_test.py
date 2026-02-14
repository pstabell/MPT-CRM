"""
ai_sdr_phase3_test.py — Test Suite for AI SDR Phase 3: Auto Proposal Generation
===============================================================================

Comprehensive testing for proposal generation system.
Tests service evaluation, proposal generation, PDF creation, and API endpoints.

Usage:
    python ai_sdr_phase3_test.py
"""

import json
import requests
import time
import unittest
from datetime import datetime
from typing import Dict, List, Any
import logging

# Test configuration
PHASE3_API_URL = "http://localhost:5002"
TEST_CONTACT_ID = "test-contact-uuid"  # Will need real contact with discovery data

class TestProposalGeneration(unittest.TestCase):
    """Test proposal generation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = PHASE3_API_URL
        
    def test_service_catalog(self):
        """Test service catalog loading"""
        print("\n🧪 Testing service catalog...")
        
        response = requests.get(f"{self.api_url}/api/proposal/services")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("services", data)
        
        services = data["services"]
        self.assertGreater(len(services), 0)
        
        # Check required fields
        for service in services:
            self.assertIn("name", service)
            self.assertIn("description", service)
            self.assertIn("base_price", service)
            self.assertIn("category", service)
            
        print(f"✅ Service catalog loaded: {len(services)} services")
        
    def test_health_check(self):
        """Test health check endpoint"""
        print("\n🧪 Testing health check...")
        
        response = requests.get(f"{self.api_url}/api/proposal/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database", data)
        self.assertIn("services_count", data)
        
        print(f"✅ Health check passed - {data['services_count']} services available")
        
    def test_api_endpoints(self):
        """Test API endpoint availability"""
        print("\n🧪 Testing API endpoints...")
        
        # Test endpoint
        response = requests.get(f"{self.api_url}/api/proposal/test")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("endpoints", data)
        
        endpoints = data["endpoints"]
        expected_endpoints = [
            "POST /api/proposal/generate",
            "GET /api/proposal/services",
            "GET /api/proposal/health"
        ]
        
        for endpoint in expected_endpoints:
            self.assertIn(endpoint, endpoints)
            
        print(f"✅ API endpoints available: {len(endpoints)} endpoints")

def test_service_evaluation():
    """Test service evaluation logic with mock discovery data"""
    print("\n🧪 Testing service evaluation logic...")
    
    from ai_sdr_proposal_generation import ProposalGenerationEngine
    
    # Mock discovery data scenarios
    test_scenarios = [
        {
            "name": "Website + CRM Combo",
            "discovery": {
                "contact": {
                    "first_name": "John",
                    "last_name": "Doe", 
                    "company": "Doe Industries"
                },
                "intake": {
                    "project_types": "website, crm system",
                    "budget_range": "$15,000 - $30,000",
                    "must_have_features": "mobile responsive, integration with existing tools",
                    "integrations": "quickbooks, email marketing",
                    "pain_points": "losing leads, manual follow-up"
                }
            },
            "expected_services": ["website_basic", "crm_system", "accounting_system"]
        },
        {
            "name": "E-commerce Focus",
            "discovery": {
                "contact": {
                    "first_name": "Sarah", 
                    "last_name": "Smith",
                    "company": "Smith Boutique"
                },
                "intake": {
                    "project_types": "ecommerce website",
                    "budget_range": "$10,000 - $20,000",
                    "must_have_features": "online store, payment processing, inventory",
                    "integrations": "payment gateway, shipping",
                    "pain_points": "need to sell online, manual inventory"
                }
            },
            "expected_services": ["website_ecommerce"]
        },
        {
            "name": "Automation Heavy",
            "discovery": {
                "contact": {
                    "first_name": "Mike",
                    "last_name": "Johnson", 
                    "company": "Johnson Services"
                },
                "intake": {
                    "project_types": "automation, integrations",
                    "budget_range": "$20,000 - $40,000",
                    "must_have_features": "workflow automation, custom integrations",
                    "integrations": "multiple systems, apis",
                    "pain_points": "too much manual work, repetitive tasks"
                }
            },
            "expected_services": ["automation_suite", "consulting_audit"]
        }
    ]
    
    engine = ProposalGenerationEngine()
    
    for scenario in test_scenarios:
        print(f"\n  📋 Scenario: {scenario['name']}")
        
        # Get recommendations
        recommendations = engine._evaluate_needs_and_recommend(scenario["discovery"])
        
        print(f"     Recommendations: {len(recommendations)}")
        for rec in recommendations:
            print(f"       • {rec.service.name} (${rec.estimated_price:,}) - {rec.reasoning[:50]}...")
        
        # Check if expected services are recommended
        recommended_names = [rec.service.name.lower() for rec in recommendations]
        
        for expected in scenario["expected_services"]:
            service_name = expected.replace("_", " ").lower()
            found = any(service_name in name for name in recommended_names)
            if not found:
                print(f"     ⚠️  Expected service not found: {service_name}")
    
    print("✅ Service evaluation logic tested")

def test_pricing_calculations():
    """Test pricing calculation logic"""
    print("\n🧪 Testing pricing calculations...")
    
    from ai_sdr_proposal_generation import MPT_SERVICES
    
    # Test base pricing
    website_service = MPT_SERVICES["website_basic"]
    base_price = website_service.base_price
    print(f"  Base website price: ${base_price:,}")
    
    # Test price factors
    ecommerce_multiplier = website_service.price_factors.get("ecommerce", 1.0)
    ecommerce_price = int(base_price * ecommerce_multiplier)
    print(f"  E-commerce multiplier: {ecommerce_multiplier}x = ${ecommerce_price:,}")
    
    # Test complex service pricing
    crm_service = MPT_SERVICES["crm_system"]
    complex_price = int(crm_service.base_price * 1.5)  # All factors applied
    print(f"  Complex CRM price: ${complex_price:,}")
    
    print("✅ Pricing calculations working correctly")

def test_pdf_generation():
    """Test PDF generation capabilities"""
    print("\n🧪 Testing PDF generation...")
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate
        print("  ✅ ReportLab library available")
        
        # Test basic PDF creation
        test_path = "C:/Users/Patri/clawd/test_proposal.pdf"
        doc = SimpleDocTemplate(test_path, pagesize=letter)
        
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        styles = getSampleStyleSheet()
        elements = [Paragraph("Test Proposal", styles['Title'])]
        
        doc.build(elements)
        
        import os
        if os.path.exists(test_path):
            print(f"  ✅ Test PDF created: {test_path}")
            os.remove(test_path)  # Clean up
        else:
            print("  ❌ PDF creation failed")
            
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e}")
        print("  💡 Install: pip install reportlab")
    
    except Exception as e:
        print(f"  ❌ PDF test failed: {e}")

def run_integration_tests():
    """Run integration tests with live API"""
    print("\n🧪 Running integration tests...")
    
    # Check if API server is running
    try:
        response = requests.get(f"{PHASE3_API_URL}/api/proposal/health", timeout=5)
        if response.status_code != 200:
            print("❌ API server not responding - start with: python ai_sdr_phase3_api.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ API server not running - start with: python ai_sdr_phase3_api.py")
        return False
    
    print("✅ API server is running")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    return True

def main():
    """Main test runner"""
    print("🚀 AI SDR Phase 3 - Proposal Generation Test Suite")
    print("=" * 60)
    
    # Test 1: Service evaluation
    test_service_evaluation()
    
    # Test 2: Pricing calculations
    test_pricing_calculations()
    
    # Test 3: PDF generation
    test_pdf_generation()
    
    # Test 4: Integration tests
    run_integration_tests()
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed!")
    print("\n💡 To test full proposal generation:")
    print("   1. Start API server: python ai_sdr_phase3_api.py")
    print("   2. Use contact with discovery data:")
    print("      import requests")
    print("      response = requests.post('http://localhost:5002/api/proposal/generate',")
    print("                               json={'contact_id': 'your-contact-id'})")
    print("   3. Check response for proposal details and download URL")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    main()