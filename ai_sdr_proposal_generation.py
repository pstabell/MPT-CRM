"""
ai_sdr_proposal_generation.py — AI SDR Phase 3: Auto Proposal Generation
========================================================================

Generates proposals automatically from CRM discovery data.
Integrates with Phase 2 to pull discovery data and create professional proposals.

Features:
1. Pull discovery data from CRM
2. Evaluate needs and recommend services/products
3. Generate proposal document (PDF)
4. Calculate pricing based on discovery answers
5. Create draft proposal ready for review

Usage:
    from ai_sdr_proposal_generation import generate_proposal_from_discovery
    
    result = generate_proposal_from_discovery(contact_id="uuid-here")
    print(f"Proposal created: {result['proposal_path']}")
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# CRM integration
from db_service import CRMDataAccess

# ============================================================================
# CONFIGURATION & DATA MODELS
# ============================================================================

@dataclass
class MPTService:
    """MPT service offering"""
    name: str
    description: str
    base_price: int
    price_factors: Dict[str, float]  # Multipliers based on complexity
    timeline_weeks: Tuple[int, int]  # Min, max weeks
    category: str
    
@dataclass
class ProposalRecommendation:
    """Service recommendation with pricing"""
    service: MPTService
    reasoning: str
    estimated_price: int
    estimated_timeline: str
    priority: int  # 1=primary, 2=secondary, 3=nice-to-have

@dataclass
class ClientProposal:
    """Complete proposal for client"""
    contact_id: str
    client_name: str
    company: str
    recommendations: List[ProposalRecommendation]
    total_investment: int
    total_timeline: str
    proposal_date: datetime
    valid_until: datetime

# MPT Service Catalog
MPT_SERVICES = {
    "website_basic": MPTService(
        name="Professional Website",
        description="Custom responsive website with CMS, SEO optimization, and mobile design",
        base_price=5000,
        price_factors={"ecommerce": 1.5, "custom_design": 1.3, "integrations": 1.2},
        timeline_weeks=(4, 8),
        category="Web Development"
    ),
    "website_ecommerce": MPTService(
        name="E-Commerce Website",
        description="Full e-commerce solution with payment processing, inventory management, and analytics",
        base_price=8000,
        price_factors={"custom_design": 1.3, "complex_products": 1.4, "integrations": 1.5},
        timeline_weeks=(6, 12),
        category="E-Commerce"
    ),
    "crm_system": MPTService(
        name="Custom CRM System",
        description="Tailored customer relationship management system with automation and reporting",
        base_price=15000,
        price_factors={"integrations": 1.4, "custom_workflows": 1.3, "mobile_app": 1.5},
        timeline_weeks=(8, 16),
        category="Custom Software"
    ),
    "accounting_system": MPTService(
        name="Accounting System Integration", 
        description="Connect and automate your accounting workflows with QuickBooks, Xero, or custom solutions",
        base_price=3500,
        price_factors={"custom_reports": 1.3, "multiple_integrations": 1.5, "automation": 1.4},
        timeline_weeks=(3, 6),
        category="Integrations"
    ),
    "mobile_app": MPTService(
        name="Mobile Application",
        description="Native iOS and Android app with backend API and admin dashboard",
        base_price=25000,
        price_factors={"complex_features": 1.4, "real_time": 1.3, "integrations": 1.2},
        timeline_weeks=(12, 24),
        category="Mobile Development"
    ),
    "automation_suite": MPTService(
        name="Business Process Automation",
        description="Automate repetitive tasks, workflows, and data entry with custom integrations",
        base_price=7500,
        price_factors={"complex_workflows": 1.5, "multiple_systems": 1.4, "custom_logic": 1.3},
        timeline_weeks=(4, 10),
        category="Automation"
    ),
    "consulting_audit": MPTService(
        name="Technology Audit & Consulting",
        description="Comprehensive review of current systems with recommendations and implementation roadmap",
        base_price=2500,
        price_factors={"large_organization": 1.5, "complex_systems": 1.3},
        timeline_weeks=(2, 4),
        category="Consulting"
    )
}

# ============================================================================
# PROPOSAL GENERATION ENGINE
# ============================================================================

class ProposalGenerationEngine:
    """Main engine for generating proposals from CRM discovery data"""
    
    def __init__(self):
        self.db = CRMDataAccess()
        self.logger = logging.getLogger(__name__)
        
    def generate_proposal_from_discovery(self, contact_id: str) -> Dict[str, Any]:
        """
        Main method to generate proposal from CRM discovery data
        
        Returns:
            Dict containing proposal details and file paths
        """
        try:
            # 1. Pull discovery data from CRM
            discovery_data = self._get_discovery_data(contact_id)
            if not discovery_data:
                return {"success": False, "error": "No discovery data found"}
            
            # 2. Evaluate needs and recommend services
            recommendations = self._evaluate_needs_and_recommend(discovery_data)
            if not recommendations:
                return {"success": False, "error": "No suitable services found"}
            
            # 3. Create proposal object
            proposal = self._create_proposal_object(contact_id, discovery_data, recommendations)
            
            # 4. Generate PDF document
            pdf_path = self._generate_pdf_proposal(proposal)
            
            # 5. Save proposal to CRM
            proposal_record = self._save_proposal_to_crm(proposal, pdf_path)
            
            return {
                "success": True,
                "contact_id": contact_id,
                "proposal_id": proposal_record.get("id"),
                "proposal_path": pdf_path,
                "total_investment": proposal.total_investment,
                "recommendations_count": len(recommendations),
                "valid_until": proposal.valid_until.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Proposal generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_discovery_data(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Pull discovery data from CRM for the contact"""
        try:
            # Get contact info
            contact = self.db.get_contact(contact_id)
            if not contact:
                return None
            
            # Get latest discovery intake
            query = """
                SELECT * FROM client_intakes 
                WHERE contact_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            intakes = self.db.query(query, (contact_id,))
            
            if not intakes:
                return None
            
            intake = intakes[0]
            
            # Combine contact and intake data
            discovery_data = {
                "contact": contact,
                "intake": intake,
                "contact_id": contact_id
            }
            
            return discovery_data
            
        except Exception as e:
            self.logger.error(f"Error retrieving discovery data: {str(e)}")
            return None
    
    def _evaluate_needs_and_recommend(self, discovery_data: Dict[str, Any]) -> List[ProposalRecommendation]:
        """Analyze discovery data and recommend appropriate services"""
        
        contact = discovery_data["contact"]
        intake = discovery_data["intake"]
        recommendations = []
        
        # Extract key data
        project_types = (intake.get("project_types") or "").lower()
        budget_range = intake.get("budget_range", "")
        must_have_features = (intake.get("must_have_features") or "").lower()
        nice_to_have_features = (intake.get("nice_to_have_features") or "").lower()
        integrations = (intake.get("integrations") or "").lower()
        pain_points = (intake.get("pain_points") or "").lower()
        
        # Website needs
        if any(term in project_types for term in ["website", "web", "site"]):
            if any(term in project_types + must_have_features for term in ["ecommerce", "e-commerce", "shop", "store", "sell", "products"]):
                # E-commerce website
                service = MPT_SERVICES["website_ecommerce"]
                price_multiplier = 1.0
                
                if "custom" in must_have_features:
                    price_multiplier *= 1.3
                if any(term in integrations for term in ["payment", "inventory", "shipping"]):
                    price_multiplier *= 1.5
                
                estimated_price = int(service.base_price * price_multiplier)
                timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
                
                recommendations.append(ProposalRecommendation(
                    service=service,
                    reasoning="E-commerce functionality needed for online sales and product management",
                    estimated_price=estimated_price,
                    estimated_timeline=timeline,
                    priority=1
                ))
            else:
                # Basic website
                service = MPT_SERVICES["website_basic"]
                price_multiplier = 1.0
                
                if "custom" in must_have_features:
                    price_multiplier *= 1.3
                if "integration" in integrations:
                    price_multiplier *= 1.2
                
                estimated_price = int(service.base_price * price_multiplier)
                timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
                
                recommendations.append(ProposalRecommendation(
                    service=service,
                    reasoning="Professional web presence to enhance credibility and reach new customers",
                    estimated_price=estimated_price,
                    estimated_timeline=timeline,
                    priority=1
                ))
        
        # CRM needs
        if any(term in project_types for term in ["crm", "customer", "contact", "lead"]):
            service = MPT_SERVICES["crm_system"]
            price_multiplier = 1.0
            
            if "integration" in integrations:
                price_multiplier *= 1.4
            if "automation" in must_have_features + nice_to_have_features:
                price_multiplier *= 1.3
            if "mobile" in must_have_features + nice_to_have_features:
                price_multiplier *= 1.5
            
            estimated_price = int(service.base_price * price_multiplier)
            timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
            
            recommendations.append(ProposalRecommendation(
                service=service,
                reasoning="Centralized customer management to improve sales efficiency and customer relationships",
                estimated_price=estimated_price,
                estimated_timeline=timeline,
                priority=1
            ))
        
        # Mobile app needs
        if any(term in project_types + must_have_features for term in ["mobile", "app", "ios", "android"]):
            service = MPT_SERVICES["mobile_app"]
            price_multiplier = 1.0
            
            if "real-time" in must_have_features + nice_to_have_features:
                price_multiplier *= 1.3
            if "integration" in integrations:
                price_multiplier *= 1.2
            
            estimated_price = int(service.base_price * price_multiplier)
            timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
            
            recommendations.append(ProposalRecommendation(
                service=service,
                reasoning="Mobile presence for better customer engagement and accessibility",
                estimated_price=estimated_price,
                estimated_timeline=timeline,
                priority=1
            ))
        
        # Accounting/Integration needs
        if any(term in integrations for term in ["quickbooks", "xero", "accounting", "bookkeeping"]):
            service = MPT_SERVICES["accounting_system"]
            price_multiplier = 1.0
            
            if "automation" in must_have_features + nice_to_have_features:
                price_multiplier *= 1.4
            if "custom" in must_have_features:
                price_multiplier *= 1.3
            
            estimated_price = int(service.base_price * price_multiplier)
            timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
            
            recommendations.append(ProposalRecommendation(
                service=service,
                reasoning="Streamline financial processes and improve accuracy with automated integrations",
                estimated_price=estimated_price,
                estimated_timeline=timeline,
                priority=2
            ))
        
        # Automation needs
        if any(term in pain_points + must_have_features for term in ["manual", "repetitive", "automation", "workflow"]):
            service = MPT_SERVICES["automation_suite"]
            price_multiplier = 1.0
            
            if "complex" in must_have_features:
                price_multiplier *= 1.5
            if "integration" in integrations:
                price_multiplier *= 1.4
            
            estimated_price = int(service.base_price * price_multiplier)
            timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
            
            recommendations.append(ProposalRecommendation(
                service=service,
                reasoning="Eliminate manual work and improve efficiency with automated business processes",
                estimated_price=estimated_price,
                estimated_timeline=timeline,
                priority=2
            ))
        
        # Always recommend consulting for complex needs
        if len(recommendations) >= 2 or any(term in must_have_features for term in ["complex", "integration", "custom"]):
            service = MPT_SERVICES["consulting_audit"]
            price_multiplier = 1.0
            
            if len(recommendations) >= 3:
                price_multiplier *= 1.5  # Large organization
            
            estimated_price = int(service.base_price * price_multiplier)
            timeline = f"{service.timeline_weeks[0]}-{service.timeline_weeks[1]} weeks"
            
            recommendations.append(ProposalRecommendation(
                service=service,
                reasoning="Strategic planning to ensure optimal implementation and integration across all systems",
                estimated_price=estimated_price,
                estimated_timeline=timeline,
                priority=3
            ))
        
        # Sort by priority
        recommendations.sort(key=lambda x: x.priority)
        
        return recommendations
    
    def _create_proposal_object(self, contact_id: str, discovery_data: Dict[str, Any], recommendations: List[ProposalRecommendation]) -> ClientProposal:
        """Create complete proposal object"""
        
        contact = discovery_data["contact"]
        
        # Calculate totals
        total_investment = sum(rec.estimated_price for rec in recommendations)
        
        # Estimate overall timeline
        max_weeks = max(
            int(rec.estimated_timeline.split('-')[1].split(' ')[0]) 
            for rec in recommendations
        )
        total_timeline = f"Estimated {max_weeks} weeks for complete implementation"
        
        # Create proposal
        proposal = ClientProposal(
            contact_id=contact_id,
            client_name=f"{contact['first_name']} {contact['last_name']}",
            company=contact.get("company", ""),
            recommendations=recommendations,
            total_investment=total_investment,
            total_timeline=total_timeline,
            proposal_date=datetime.now(),
            valid_until=datetime.now() + timedelta(days=30)
        )
        
        return proposal
    
    def _generate_pdf_proposal(self, proposal: ClientProposal) -> str:
        """Generate PDF proposal document"""
        
        # Create output directory
        output_dir = Path("C:/Users/Patri/clawd/proposals")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        safe_name = "".join(c for c in proposal.client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_name}_{proposal.proposal_date.strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}.pdf"
        pdf_path = output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#003B5C')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#003B5C')
        )
        
        # Title page
        elements.append(Paragraph("Technology Solutions Proposal", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Client info
        client_info = [
            ["Prepared for:", f"{proposal.client_name}"],
            ["Company:", proposal.company] if proposal.company else None,
            ["Proposal Date:", proposal.proposal_date.strftime("%B %d, %Y")],
            ["Valid Until:", proposal.valid_until.strftime("%B %d, %Y")],
            ["", ""],
            ["Prepared by:", "Metro Point Technology"],
            ["Contact:", "Patrick Grant"],
            ["Email:", "patrick@metropointtechnology.com"],
            ["Phone:", "(239) 600-8159"]
        ]
        
        # Filter out None entries
        client_info = [row for row in client_info if row is not None]
        
        client_table = Table(client_info, colWidths=[2*inch, 4*inch])
        client_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(client_table)
        elements.append(PageBreak())
        
        # Executive summary
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        summary_text = f"""
        Based on our discovery consultation, we have identified {len(proposal.recommendations)} key technology solutions 
        to address your business needs and accelerate growth. Our recommended approach focuses on:
        
        • Implementing core systems to improve operational efficiency
        • Integrating solutions that scale with your business
        • Providing ongoing support and maintenance
        
        <b>Total Investment:</b> ${proposal.total_investment:,}<br/>
        <b>Implementation Timeline:</b> {proposal.total_timeline}
        """
        
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Recommendations overview table
        elements.append(Paragraph("Recommended Solutions", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        overview_data = [["Solution", "Investment", "Timeline"]]
        for rec in proposal.recommendations:
            overview_data.append([
                rec.service.name,
                f"${rec.estimated_price:,}",
                rec.estimated_timeline
            ])
        overview_data.append(["", "", ""])
        overview_data.append(["Total Investment", f"${proposal.total_investment:,}", ""])
        
        overview_table = Table(overview_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003B5C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('LINEBELOW', (0, -2), (-1, -2), 2, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(overview_table)
        elements.append(PageBreak())
        
        # Detailed recommendations
        for i, rec in enumerate(proposal.recommendations):
            elements.append(Paragraph(f"{i+1}. {rec.service.name}", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            # Service details
            details_text = f"""
            <b>Category:</b> {rec.service.category}<br/>
            <b>Investment:</b> ${rec.estimated_price:,}<br/>
            <b>Timeline:</b> {rec.estimated_timeline}<br/>
            <br/>
            <b>Description:</b><br/>
            {rec.service.description}
            <br/><br/>
            <b>Why We Recommend This:</b><br/>
            {rec.reasoning}
            """
            
            elements.append(Paragraph(details_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
        
        # Next steps
        elements.append(PageBreak())
        elements.append(Paragraph("Next Steps", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        next_steps_text = """
        To move forward with these recommendations:
        
        1. <b>Review this proposal</b> and let us know if you have any questions
        2. <b>Schedule a technical consultation</b> to discuss implementation details
        3. <b>Finalize scope and timeline</b> for your priority solutions
        4. <b>Begin development</b> with our proven project management process
        
        We're excited to partner with you on these technology initiatives and help drive your business forward.
        
        <br/>
        <b>Contact Information:</b><br/>
        Patrick Grant<br/>
        Metro Point Technology<br/>
        Email: patrick@metropointtechnology.com<br/>
        Phone: (239) 600-8159<br/>
        <br/>
        This proposal is valid until """ + proposal.valid_until.strftime("%B %d, %Y") + """.
        """
        
        elements.append(Paragraph(next_steps_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        return str(pdf_path)
    
    def _save_proposal_to_crm(self, proposal: ClientProposal, pdf_path: str) -> Dict[str, Any]:
        """Save proposal record to CRM"""
        
        try:
            # Create proposal record
            proposal_data = {
                "id": str(uuid.uuid4()),
                "contact_id": proposal.contact_id,
                "title": f"Technology Solutions Proposal - {proposal.client_name}",
                "total_amount": proposal.total_investment,
                "status": "draft",
                "proposal_date": proposal.proposal_date.isoformat(),
                "valid_until": proposal.valid_until.isoformat(),
                "file_path": pdf_path,
                "services": json.dumps([{
                    "name": rec.service.name,
                    "category": rec.service.category,
                    "price": rec.estimated_price,
                    "timeline": rec.estimated_timeline,
                    "reasoning": rec.reasoning
                } for rec in proposal.recommendations]),
                "created_at": datetime.now().isoformat()
            }
            
            # Insert into proposals table (create table if needed)
            create_table_query = """
                CREATE TABLE IF NOT EXISTS proposals (
                    id UUID PRIMARY KEY,
                    contact_id UUID REFERENCES contacts(id),
                    title TEXT NOT NULL,
                    total_amount INTEGER,
                    status TEXT DEFAULT 'draft',
                    proposal_date TIMESTAMP,
                    valid_until TIMESTAMP,
                    file_path TEXT,
                    services JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """
            
            self.db.execute(create_table_query)
            
            # Insert proposal
            insert_query = """
                INSERT INTO proposals (id, contact_id, title, total_amount, status, 
                                    proposal_date, valid_until, file_path, services, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute(insert_query, (
                proposal_data["id"],
                proposal_data["contact_id"],
                proposal_data["title"],
                proposal_data["total_amount"],
                proposal_data["status"],
                proposal_data["proposal_date"],
                proposal_data["valid_until"],
                proposal_data["file_path"],
                proposal_data["services"],
                proposal_data["created_at"]
            ))
            
            # Log activity
            activity_data = {
                "contact_id": proposal.contact_id,
                "activity_type": "proposal_generated",
                "notes": f"AI-generated proposal created: ${proposal.total_investment:,} total investment",
                "created_at": datetime.now().isoformat()
            }
            
            activity_query = """
                INSERT INTO activities (id, contact_id, activity_type, notes, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            self.db.execute(activity_query, (
                str(uuid.uuid4()),
                activity_data["contact_id"],
                activity_data["activity_type"],
                activity_data["notes"],
                activity_data["created_at"]
            ))
            
            return proposal_data
            
        except Exception as e:
            self.logger.error(f"Error saving proposal to CRM: {str(e)}")
            raise

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def generate_proposal_from_discovery(contact_id: str) -> Dict[str, Any]:
    """
    Generate proposal from CRM discovery data
    
    Args:
        contact_id: UUID of contact with discovery data
        
    Returns:
        Dict with success status and proposal details
    """
    engine = ProposalGenerationEngine()
    return engine.generate_proposal_from_discovery(contact_id)

def get_service_recommendations(contact_id: str) -> List[Dict[str, Any]]:
    """
    Get service recommendations without generating full proposal
    
    Args:
        contact_id: UUID of contact with discovery data
        
    Returns:
        List of service recommendations
    """
    engine = ProposalGenerationEngine()
    
    # Get discovery data
    discovery_data = engine._get_discovery_data(contact_id)
    if not discovery_data:
        return []
    
    # Get recommendations
    recommendations = engine._evaluate_needs_and_recommend(discovery_data)
    
    # Convert to dict format
    return [{
        "service_name": rec.service.name,
        "service_category": rec.service.category,
        "estimated_price": rec.estimated_price,
        "estimated_timeline": rec.estimated_timeline,
        "reasoning": rec.reasoning,
        "priority": rec.priority
    } for rec in recommendations]

def list_available_services() -> List[Dict[str, Any]]:
    """
    List all available MPT services
    
    Returns:
        List of service definitions
    """
    return [{
        "name": service.name,
        "description": service.description,
        "base_price": service.base_price,
        "category": service.category,
        "timeline_weeks": service.timeline_weeks
    } for service in MPT_SERVICES.values()]

# ============================================================================
# TESTING & VALIDATION
# ============================================================================

def test_proposal_generation():
    """Test proposal generation with sample data"""
    print("🧪 Testing AI SDR Phase 3 - Proposal Generation")
    print("=" * 60)
    
    # Test service catalog
    print(f"✅ Service catalog loaded: {len(MPT_SERVICES)} services")
    
    # List services
    print("\n📋 Available Services:")
    for name, service in MPT_SERVICES.items():
        print(f"  • {service.name} ({service.category}) - ${service.base_price:,}")
    
    # Test would require a real contact ID with discovery data
    print(f"\n⚠️  Full testing requires contact ID with discovery data")
    print(f"   Use: generate_proposal_from_discovery(contact_id)")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_proposal_generation()