"""
ai_sdr_discovery_integration.py — AI SDR Phase 2 - CRM Discovery Form Auto-Fill
=================================================================================

Connects voice discovery data from Phase 1 to CRM, auto-creating contacts and 
filling discovery forms with intelligent lead scoring.

Features:
1. Discovery Data Mapping - voice fields → CRM discovery form fields
2. Auto-Create Contact - from discovery completion with AI Discovery source
3. Discovery Form Auto-Fill - populate existing client_intakes structure
4. Lead Scoring - score leads 1-100 based on discovery answers
5. Integration Endpoint - API for Phase 1 to call when discovery completes

Database: Uses existing MPT-CRM Supabase structure via db_service.py patterns
"""

import json
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Import existing CRM database service
from db_service import (
    db_create_contact, db_update_contact, db_get_contact,
    db_create_intake, db_update_intake, db_get_intake,
    db_log_activity, db_create_deal
)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DiscoveryData:
    """Structured discovery data from voice extraction"""
    # Contact Info
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    industry: str = ""
    
    # Business Context
    business_needs: List[str] = None
    current_solutions: str = ""
    pain_points: str = ""
    desired_outcome: str = ""
    
    # Project Details
    project_types: List[str] = None
    must_have_features: str = ""
    nice_to_have_features: str = ""
    integrations: List[str] = None
    
    # Budget & Timeline
    budget_range: str = ""
    budget_flexibility: str = ""
    timeline: str = ""
    urgency: str = ""
    deadline_reason: str = ""
    
    # Decision Making
    decision_maker: str = ""
    decision_timeline: str = ""
    stakeholders: str = ""
    competition: str = ""
    
    # Additional Context
    meeting_notes: str = ""
    next_steps: str = ""
    confidence_indicators: List[str] = None
    red_flags: List[str] = None
    
    def __post_init__(self):
        """Initialize list fields if None"""
        if self.business_needs is None:
            self.business_needs = []
        if self.project_types is None:
            self.project_types = []
        if self.integrations is None:
            self.integrations = []
        if self.confidence_indicators is None:
            self.confidence_indicators = []
        if self.red_flags is None:
            self.red_flags = []

@dataclass
class LeadScore:
    """Lead scoring result with breakdown"""
    total_score: int  # 1-100
    budget_score: int  # 0-25
    timeline_score: int  # 0-25
    authority_score: int  # 0-25
    need_score: int  # 0-25
    is_hot_lead: bool  # score > 80
    scoring_notes: str = ""

@dataclass
class ProcessingResult:
    """Result of processing discovery data into CRM"""
    success: bool
    contact_id: Optional[str] = None
    intake_id: Optional[str] = None
    deal_id: Optional[str] = None
    lead_score: Optional[LeadScore] = None
    error_message: str = ""
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

# ============================================================================
# DATA MAPPING & CLEANING
# ============================================================================

class DiscoveryDataMapper:
    """Maps voice-extracted fields to CRM discovery form fields"""
    
    # Standard project type mappings
    PROJECT_TYPE_MAPPINGS = {
        # Common variations -> standard CRM values
        'website': 'Website Development',
        'web site': 'Website Development', 
        'web development': 'Website Development',
        'new website': 'Website Development',
        'build website': 'Website Development',
        'website redesign': 'Website Redesign',
        'redesign': 'Website Redesign',
        'web app': 'Web Application',
        'application': 'Web Application',
        'mobile app': 'Mobile App',
        'app': 'Mobile App',
        'crm': 'Custom Software / CRM',
        'custom software': 'Custom Software / CRM',
        'software': 'Custom Software / CRM',
        'ecommerce': 'E-commerce Store',
        'e-commerce': 'E-commerce Store',
        'online store': 'E-commerce Store',
        'shop': 'E-commerce Store',
        'api': 'API Integration',
        'integration': 'API Integration',
        'data migration': 'Data Migration',
        'automation': 'Automation / Workflow',
        'workflow': 'Automation / Workflow',
        'consulting': 'Consulting / Strategy',
        'strategy': 'Consulting / Strategy',
        'maintenance': 'Maintenance / Support',
        'support': 'Maintenance / Support'
    }
    
    # Budget range normalization
    BUDGET_MAPPINGS = {
        'under 2500': 'Under $2,500',
        'under $2500': 'Under $2,500',
        'under 2.5k': 'Under $2,500',
        'less than 2500': 'Under $2,500',
        '2500 to 5000': '$2,500 - $5,000',
        '2.5k to 5k': '$2,500 - $5,000',
        '5000 to 10000': '$5,000 - $10,000',
        '5k to 10k': '$5,000 - $10,000',
        '10000 to 25000': '$10,000 - $25,000',
        '10k to 25k': '$10,000 - $25,000',
        '25000 to 50000': '$25,000 - $50,000',
        '25k to 50k': '$25,000 - $50,000',
        'over 50000': '$50,000+',
        'over 50k': '$50,000+',
        'more than 50k': '$50,000+',
        'not sure': 'Not sure / Need quote',
        'dont know': 'Not sure / Need quote',
        'need quote': 'Not sure / Need quote',
        'wont say': 'Prefers not to say',
        'prefer not to say': 'Prefers not to say'
    }
    
    # Industry standardization
    INDUSTRY_MAPPINGS = {
        'health': 'Healthcare',
        'medical': 'Healthcare',
        'doctor': 'Healthcare',
        'insurance': 'Insurance',
        'real estate': 'Real Estate',
        'realtor': 'Real Estate',
        'property': 'Real Estate',
        'law': 'Legal',
        'lawyer': 'Legal',
        'attorney': 'Legal',
        'legal': 'Legal',
        'accounting': 'Finance / Accounting',
        'finance': 'Finance / Accounting',
        'cpa': 'Finance / Accounting',
        'bookkeeping': 'Finance / Accounting',
        'construction': 'Construction',
        'contractor': 'Construction',
        'building': 'Construction',
        'restaurant': 'Hospitality / Restaurant',
        'food': 'Hospitality / Restaurant',
        'hotel': 'Hospitality / Restaurant',
        'hospitality': 'Hospitality / Restaurant',
        'retail': 'Retail / E-commerce',
        'store': 'Retail / E-commerce',
        'shop': 'Retail / E-commerce',
        'ecommerce': 'Retail / E-commerce',
        'nonprofit': 'Non-Profit',
        'non-profit': 'Non-Profit',
        'charity': 'Non-Profit',
        'school': 'Education',
        'university': 'Education',
        'education': 'Education',
        'tech': 'Technology',
        'technology': 'Technology',
        'software': 'Technology',
        'manufacturing': 'Manufacturing',
        'factory': 'Manufacturing'
    }
    
    def normalize_project_types(self, raw_types: List[str]) -> List[str]:
        """Convert voice-extracted project types to standard CRM values"""
        normalized = []
        
        for raw_type in raw_types:
            if not raw_type:
                continue
                
            # Clean up the input
            clean_type = raw_type.lower().strip()
            
            # Check for direct mapping
            if clean_type in self.PROJECT_TYPE_MAPPINGS:
                mapped = self.PROJECT_TYPE_MAPPINGS[clean_type]
                if mapped not in normalized:
                    normalized.append(mapped)
                continue
            
            # Check for partial matches
            matched = False
            for key, value in self.PROJECT_TYPE_MAPPINGS.items():
                if key in clean_type or clean_type in key:
                    if value not in normalized:
                        normalized.append(value)
                    matched = True
                    break
            
            # If no match found, add as "Other"
            if not matched and "Other" not in normalized:
                normalized.append("Other")
        
        return normalized if normalized else ["Other"]
    
    def normalize_budget_range(self, raw_budget: str) -> str:
        """Convert voice-extracted budget to standard CRM budget range"""
        if not raw_budget:
            return "Not sure / Need quote"
        
        clean_budget = raw_budget.lower().strip()
        
        # Remove currency symbols and normalize
        clean_budget = re.sub(r'[\$,]', '', clean_budget)
        clean_budget = re.sub(r'\s+', ' ', clean_budget)
        
        # Check direct mappings
        if clean_budget in self.BUDGET_MAPPINGS:
            return self.BUDGET_MAPPINGS[clean_budget]
        
        # Try to extract numbers and categorize
        numbers = re.findall(r'\\d+', clean_budget)
        if len(numbers) >= 1:
            amount = int(numbers[0])
            if amount < 2500:
                return "Under $2,500"
            elif amount < 5000:
                return "$2,500 - $5,000"
            elif amount < 10000:
                return "$5,000 - $10,000"
            elif amount < 25000:
                return "$10,000 - $25,000"
            elif amount < 50000:
                return "$25,000 - $50,000"
            else:
                return "$50,000+"
        
        # Default fallback
        return "Not sure / Need quote"
    
    def normalize_industry(self, raw_industry: str) -> str:
        """Convert voice-extracted industry to standard CRM industry"""
        if not raw_industry:
            return "-- Select --"
        
        clean_industry = raw_industry.lower().strip()
        
        # Check direct mappings
        if clean_industry in self.INDUSTRY_MAPPINGS:
            return self.INDUSTRY_MAPPINGS[clean_industry]
        
        # Check partial matches
        for key, value in self.INDUSTRY_MAPPINGS.items():
            if key in clean_industry or clean_industry in key:
                return value
        
        return "Other"
    
    def normalize_integrations(self, raw_integrations: List[str]) -> List[str]:
        """Normalize integration names to match CRM options"""
        integration_mappings = {
            'quickbooks': 'QuickBooks',
            'qb': 'QuickBooks',
            'xero': 'Xero', 
            'stripe': 'Stripe / Payments',
            'payment': 'Stripe / Payments',
            'square': 'Square',
            'salesforce': 'Salesforce',
            'hubspot': 'HubSpot',
            'mailchimp': 'Mailchimp',
            'google': 'Google Workspace',
            'gmail': 'Google Workspace',
            'microsoft': 'Microsoft 365',
            'office 365': 'Microsoft 365',
            'zapier': 'Zapier',
            'sms': 'SMS / Twilio',
            'text': 'SMS / Twilio',
            'twilio': 'SMS / Twilio',
            'docusign': 'DocuSign',
            'calendly': 'Calendly',
            'zoom': 'Zoom',
            'social': 'Social Media',
            'facebook': 'Social Media',
            'instagram': 'Social Media',
            'api': 'Custom API',
            'custom': 'Custom API'
        }
        
        normalized = []
        for raw_int in raw_integrations:
            if not raw_int:
                continue
                
            clean_int = raw_int.lower().strip()
            
            # Check for direct or partial matches
            matched = False
            for key, value in integration_mappings.items():
                if key in clean_int or clean_int in key:
                    if value not in normalized:
                        normalized.append(value)
                    matched = True
                    break
            
            if not matched and "None / Not sure" not in normalized:
                normalized.append("None / Not sure")
        
        return normalized if normalized else ["None / Not sure"]
    
    def clean_text_field(self, text: str) -> str:
        """Clean and normalize text fields"""
        if not text:
            return ""
        
        # Basic cleanup
        cleaned = text.strip()
        cleaned = re.sub(r'\\s+', ' ', cleaned)
        cleaned = re.sub(r'[\\n\\r]+', '\\n', cleaned)
        
        return cleaned[:1000]  # Truncate to reasonable length

# ============================================================================
# LEAD SCORING ENGINE
# ============================================================================

class LeadScoringEngine:
    """Intelligent lead scoring based on discovery answers"""
    
    def calculate_lead_score(self, data: DiscoveryData) -> LeadScore:
        """Calculate comprehensive lead score (1-100) with factor breakdown"""
        
        budget_score = self._score_budget_fit(data.budget_range, data.budget_flexibility)
        timeline_score = self._score_timeline_urgency(data.timeline, data.urgency, data.deadline_reason)
        authority_score = self._score_decision_authority(data.decision_maker, data.decision_timeline)
        need_score = self._score_need_match(data.business_needs, data.pain_points, data.project_types)
        
        total_score = budget_score + timeline_score + authority_score + need_score
        is_hot_lead = total_score > 80
        
        # Generate scoring notes
        notes = self._generate_scoring_notes(budget_score, timeline_score, authority_score, need_score, data)
        
        return LeadScore(
            total_score=total_score,
            budget_score=budget_score,
            timeline_score=timeline_score,
            authority_score=authority_score,
            need_score=need_score,
            is_hot_lead=is_hot_lead,
            scoring_notes=notes
        )
    
    def _score_budget_fit(self, budget_range: str, flexibility: str) -> int:
        """Score budget fit (0-25 points)"""
        if not budget_range or budget_range in ["Not sure / Need quote", "Prefers not to say"]:
            return 15  # Neutral score for unknown budget
        
        # Budget range scoring (higher budgets = higher scores)
        budget_scores = {
            "Under $2,500": 10,
            "$2,500 - $5,000": 15,
            "$5,000 - $10,000": 20,
            "$10,000 - $25,000": 22,
            "$25,000 - $50,000": 24,
            "$50,000+": 25
        }
        
        base_score = budget_scores.get(budget_range, 15)
        
        # Flexibility bonus
        if flexibility and "flexible" in flexibility.lower():
            base_score = min(25, base_score + 2)
        elif flexibility and "firm" in flexibility.lower():
            base_score = max(base_score - 3, 5)
        
        return base_score
    
    def _score_timeline_urgency(self, timeline: str, urgency: str, deadline_reason: str) -> int:
        """Score timeline urgency (0-25 points)"""
        score = 15  # Base score
        
        # Timeline scoring
        timeline_scores = {
            "ASAP": 25,
            "Hard deadline": 22,
            "Soft target date": 18,
            "Flexible": 12,
            "Not sure": 10
        }
        
        if timeline:
            for key, value in timeline_scores.items():
                if key.lower() in timeline.lower():
                    score = value
                    break
        
        # Urgency modifier
        urgency_modifiers = {
            "critical": 5,
            "urgent": 3,
            "important": 2,
            "moderate": 0,
            "not urgent": -3
        }
        
        if urgency:
            for key, modifier in urgency_modifiers.items():
                if key.lower() in urgency.lower():
                    score += modifier
                    break
        
        # Deadline reason bonus
        if deadline_reason:
            deadline_keywords = ["launch", "event", "deadline", "contract", "compliance"]
            if any(keyword in deadline_reason.lower() for keyword in deadline_keywords):
                score += 3
        
        return max(5, min(25, score))
    
    def _score_decision_authority(self, decision_maker: str, decision_timeline: str) -> int:
        """Score decision-making authority (0-25 points)"""
        score = 15  # Base score
        
        # Decision maker scoring
        authority_scores = {
            "Yes - sole decision maker": 25,
            "Yes - but needs approval": 20,
            "Part of a team": 15,
            "No - presenting to others": 10,
            "Not sure": 8
        }
        
        if decision_maker:
            for key, value in authority_scores.items():
                if key.lower() in decision_maker.lower():
                    score = value
                    break
        
        # Timeline modifier
        timeline_modifiers = {
            "ready now": 5,
            "1-2 weeks": 3,
            "1 month": 1,
            "2-3 months": 0,
            "just exploring": -5
        }
        
        if decision_timeline:
            for key, modifier in timeline_modifiers.items():
                if key.lower() in decision_timeline.lower():
                    score += modifier
                    break
        
        return max(5, min(25, score))
    
    def _score_need_match(self, business_needs: List[str], pain_points: str, project_types: List[str]) -> int:
        """Score how well their needs match our services (0-25 points)"""
        score = 15  # Base score
        
        # Strong need indicators
        strong_need_keywords = [
            "frustrated", "broken", "manual", "inefficient", "time-consuming",
            "error-prone", "losing", "competitive", "growth", "scaling"
        ]
        
        # Check pain points for strong needs
        if pain_points:
            keyword_count = sum(1 for keyword in strong_need_keywords 
                              if keyword in pain_points.lower())
            score += min(5, keyword_count * 2)
        
        # Project type alignment (higher value projects = higher scores)
        high_value_projects = [
            "Custom Software / CRM", "Web Application", "E-commerce Store", 
            "API Integration", "Automation / Workflow"
        ]
        
        if project_types:
            if any(proj in high_value_projects for proj in project_types):
                score += 5
            if len(project_types) > 1:  # Multiple project types indicate bigger scope
                score += 3
        
        # Business needs depth
        if business_needs and len(business_needs) > 2:
            score += 2  # Well-articulated needs
        
        return max(10, min(25, score))
    
    def _generate_scoring_notes(self, budget_score: int, timeline_score: int, 
                               authority_score: int, need_score: int, 
                               data: DiscoveryData) -> str:
        """Generate human-readable scoring explanation"""
        notes = []
        
        # Budget notes
        if budget_score >= 22:
            notes.append("Strong budget fit")
        elif budget_score <= 12:
            notes.append("Budget may be tight")
        
        # Timeline notes  
        if timeline_score >= 22:
            notes.append("High urgency/clear timeline")
        elif timeline_score <= 12:
            notes.append("Timeline flexible/unclear")
        
        # Authority notes
        if authority_score >= 22:
            notes.append("Strong decision authority")
        elif authority_score <= 12:
            notes.append("Limited decision authority")
        
        # Need notes
        if need_score >= 22:
            notes.append("Excellent service fit")
        elif need_score <= 12:
            notes.append("Needs assessment required")
        
        # Red flags check
        if data.red_flags:
            notes.append("Red flags noted")
        
        # Confidence indicators
        if data.confidence_indicators and len(data.confidence_indicators) > 2:
            notes.append("Multiple positive indicators")
        
        return " | ".join(notes) if notes else "Standard lead"

# ============================================================================
# MAIN INTEGRATION CLASS
# ============================================================================

class AISDRDiscoveryIntegration:
    """Main class for processing AI SDR discovery data into CRM"""
    
    def __init__(self):
        self.mapper = DiscoveryDataMapper()
        self.scorer = LeadScoringEngine()
        self.logger = logging.getLogger(__name__)
    
    def process_discovery_completion(self, discovery_data: Dict[str, Any]) -> ProcessingResult:
        """
        Main entry point: Process completed discovery data into CRM
        
        Args:
            discovery_data: Raw discovery data from Phase 1 voice processing
            
        Returns:
            ProcessingResult with success status, IDs, lead score, and any errors
        """
        try:
            # Parse and validate input data
            structured_data = self._parse_discovery_data(discovery_data)
            
            # Create or update contact
            contact_id, warnings = self._create_or_update_contact(structured_data)
            if not contact_id:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to create/update contact",
                    warnings=warnings
                )
            
            # Create discovery intake record
            intake_id = self._create_discovery_intake(contact_id, structured_data)
            if not intake_id:
                return ProcessingResult(
                    success=False,
                    contact_id=contact_id,
                    error_message="Failed to create intake record",
                    warnings=warnings
                )
            
            # Calculate lead score
            lead_score = self.scorer.calculate_lead_score(structured_data)
            
            # Create deal if this is a hot lead
            deal_id = None
            if lead_score.is_hot_lead:
                deal_id = self._create_deal_for_hot_lead(contact_id, structured_data, lead_score)
            
            # Log activity
            self._log_discovery_completion(contact_id, intake_id, lead_score)
            
            return ProcessingResult(
                success=True,
                contact_id=contact_id,
                intake_id=intake_id,
                deal_id=deal_id,
                lead_score=lead_score,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Error processing discovery data: {str(e)}")
            return ProcessingResult(
                success=False,
                error_message=f"Processing error: {str(e)}"
            )
    
    def _parse_discovery_data(self, raw_data: Dict[str, Any]) -> DiscoveryData:
        """Parse raw discovery data into structured format"""
        
        # Handle various input formats from Phase 1
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
        
        # Extract and clean data fields
        return DiscoveryData(
            first_name=self.mapper.clean_text_field(raw_data.get('first_name', '')),
            last_name=self.mapper.clean_text_field(raw_data.get('last_name', '')),
            company=self.mapper.clean_text_field(raw_data.get('company', '')),
            email=raw_data.get('email', '').strip().lower(),
            phone=re.sub(r'[^0-9+]', '', raw_data.get('phone', '')),
            website=raw_data.get('website', '').strip(),
            industry=self.mapper.normalize_industry(raw_data.get('industry', '')),
            
            business_needs=raw_data.get('business_needs', []) or [],
            current_solutions=self.mapper.clean_text_field(raw_data.get('current_solutions', '')),
            pain_points=self.mapper.clean_text_field(raw_data.get('pain_points', '')),
            desired_outcome=self.mapper.clean_text_field(raw_data.get('desired_outcome', '')),
            
            project_types=self.mapper.normalize_project_types(raw_data.get('project_types', [])),
            must_have_features=self.mapper.clean_text_field(raw_data.get('must_have_features', '')),
            nice_to_have_features=self.mapper.clean_text_field(raw_data.get('nice_to_have_features', '')),
            integrations=self.mapper.normalize_integrations(raw_data.get('integrations', [])),
            
            budget_range=self.mapper.normalize_budget_range(raw_data.get('budget_range', '')),
            budget_flexibility=raw_data.get('budget_flexibility', ''),
            timeline=raw_data.get('timeline', ''),
            urgency=raw_data.get('urgency', ''),
            deadline_reason=self.mapper.clean_text_field(raw_data.get('deadline_reason', '')),
            
            decision_maker=raw_data.get('decision_maker', ''),
            decision_timeline=raw_data.get('decision_timeline', ''),
            stakeholders=self.mapper.clean_text_field(raw_data.get('stakeholders', '')),
            competition=raw_data.get('competition', ''),
            
            meeting_notes=self.mapper.clean_text_field(raw_data.get('meeting_notes', '')),
            next_steps=self.mapper.clean_text_field(raw_data.get('next_steps', '')),
            confidence_indicators=raw_data.get('confidence_indicators', []) or [],
            red_flags=raw_data.get('red_flags', []) or []
        )
    
    def _create_or_update_contact(self, data: DiscoveryData) -> Tuple[Optional[str], List[str]]:
        """Create new contact or update existing one"""
        warnings = []
        
        # Look for existing contact by email or phone
        existing_contact = None
        if data.email:
            # In real implementation, would search by email
            # For now, create new contact
            pass
        
        contact_data = {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "company": data.company,
            "email": data.email,
            "phone": data.phone,
            "type": "lead",  # From AI Discovery
            "source": "ai_discovery",
            "source_detail": "AI SDR Discovery Call",
            "email_status": "active"
        }
        
        try:
            if existing_contact:
                # Update existing
                result = db_update_contact(existing_contact['id'], contact_data)
                return existing_contact['id'], warnings
            else:
                # Create new
                result = db_create_contact(contact_data)
                if result and result.get('id'):
                    return result['id'], warnings
                else:
                    return None, warnings + ["Contact creation failed"]
        except Exception as e:
            self.logger.error(f"Error creating/updating contact: {str(e)}")
            return None, warnings + [f"Database error: {str(e)}"]
    
    def _create_discovery_intake(self, contact_id: str, data: DiscoveryData) -> Optional[str]:
        """Create intake record with discovery form data"""
        
        intake_data = {
            "contact_id": contact_id,
            "intake_date": datetime.now().isoformat(),
            
            # Company details
            "company_website": data.website or None,
            "industry": data.industry if data.industry != "-- Select --" else None,
            
            # Project vision
            "project_types": data.project_types,
            "pain_points": data.pain_points or None,
            "current_solution": data.current_solutions or None,
            "desired_outcome": data.desired_outcome or None,
            "must_have_features": data.must_have_features or None,
            "nice_to_have_features": data.nice_to_have_features or None,
            "integrations": data.integrations,
            
            # Timeline & Budget
            "deadline_type": self._map_timeline_to_deadline_type(data.timeline),
            "deadline_reason": data.deadline_reason or None,
            "urgency": self._map_urgency(data.urgency),
            "budget_range": data.budget_range if data.budget_range != "-- Select --" else None,
            "budget_flexibility": data.budget_flexibility or None,
            
            # Decision making
            "decision_maker": data.decision_maker or None,
            "other_stakeholders": data.stakeholders or None,
            "decision_timeline": data.decision_timeline or None,
            "competing_quotes": self._map_competition(data.competition),
            
            # Internal notes
            "meeting_notes": data.meeting_notes or None,
            "red_flags": "\\n".join(data.red_flags) if data.red_flags else None,
            "confidence_level": self._calculate_confidence_level(data),
            "next_steps": data.next_steps or None,
            
            # Status
            "status": "new"
        }
        
        try:
            result = db_create_intake(intake_data)
            return result['id'] if result else None
        except Exception as e:
            self.logger.error(f"Error creating intake: {str(e)}")
            return None
    
    def _map_timeline_to_deadline_type(self, timeline: str) -> Optional[str]:
        """Map voice timeline to CRM deadline type"""
        if not timeline:
            return None
        
        timeline_lower = timeline.lower()
        
        if any(word in timeline_lower for word in ['asap', 'urgent', 'immediate']):
            return "ASAP"
        elif any(word in timeline_lower for word in ['hard', 'deadline', 'must']):
            return "Hard deadline (event, launch)"
        elif any(word in timeline_lower for word in ['soft', 'target', 'goal']):
            return "Soft target date"
        elif any(word in timeline_lower for word in ['flexible', 'open']):
            return "Flexible"
        else:
            return "Not sure"
    
    def _map_urgency(self, urgency: str) -> Optional[str]:
        """Map voice urgency to CRM urgency levels"""
        if not urgency:
            return "Moderate"
        
        urgency_lower = urgency.lower()
        
        if any(word in urgency_lower for word in ['critical', 'emergency']):
            return "Critical"
        elif any(word in urgency_lower for word in ['urgent', 'high']):
            return "Urgent"
        elif any(word in urgency_lower for word in ['important', 'medium']):
            return "Important"
        elif any(word in urgency_lower for word in ['low', 'not urgent']):
            return "Not urgent"
        else:
            return "Moderate"
    
    def _map_competition(self, competition: str) -> Optional[str]:
        """Map competition info to CRM competing quotes field"""
        if not competition:
            return "Didn't ask"
        
        comp_lower = competition.lower()
        
        if any(word in comp_lower for word in ['no', 'only us', 'exclusive']):
            return "No - only us"
        elif any(word in comp_lower for word in ['2-3', 'few', 'couple']):
            return "Yes - 2-3 options"
        elif any(word in comp_lower for word in ['many', 'multiple', 'several']):
            return "Yes - multiple vendors"
        elif any(word in comp_lower for word in ['existing', 'already', 'have']):
            return "Comparing to existing quotes"
        else:
            return "Yes - 2-3 options"
    
    def _calculate_confidence_level(self, data: DiscoveryData) -> str:
        """Calculate confidence level based on indicators and red flags"""
        confidence_score = 50  # Start at medium
        
        # Positive indicators
        if data.confidence_indicators:
            confidence_score += len(data.confidence_indicators) * 10
        
        # Red flags
        if data.red_flags:
            confidence_score -= len(data.red_flags) * 15
        
        # Budget clarity
        if data.budget_range and data.budget_range != "Not sure / Need quote":
            confidence_score += 10
        
        # Decision authority
        if data.decision_maker and "sole decision" in data.decision_maker.lower():
            confidence_score += 15
        
        # Timeline clarity
        if data.timeline and "not sure" not in data.timeline.lower():
            confidence_score += 10
        
        # Map to CRM confidence levels
        if confidence_score >= 80:
            return "High"
        elif confidence_score >= 65:
            return "Medium-High"
        elif confidence_score >= 35:
            return "Medium"
        elif confidence_score >= 20:
            return "Medium-Low"
        else:
            return "Low"
    
    def _create_deal_for_hot_lead(self, contact_id: str, data: DiscoveryData, lead_score: LeadScore) -> Optional[str]:
        """Create a deal for hot leads (score > 80)"""
        
        # Estimate deal value based on budget
        estimated_value = self._estimate_deal_value(data.budget_range)
        
        # Create deal title
        project_summary = ", ".join(data.project_types[:2]) if data.project_types else "Project"
        company_name = data.company or f"{data.first_name} {data.last_name}"
        title = f"{project_summary} - {company_name}"
        
        deal_data = {
            "contact_id": contact_id,
            "title": title,
            "value": estimated_value,
            "stage": "qualified",  # Hot leads start at qualified
            "description": f"Hot lead from AI Discovery (Score: {lead_score.total_score}). {data.desired_outcome or data.pain_points or 'AI-discovered opportunity'}",
            "priority": "high",
            "source": "AI Discovery",
            "labels": ["hot_lead", "ai_discovery"]
        }
        
        try:
            result = db_create_deal(deal_data)
            return result['id'] if result else None
        except Exception as e:
            self.logger.error(f"Error creating deal: {str(e)}")
            return None
    
    def _estimate_deal_value(self, budget_range: str) -> float:
        """Estimate deal value from budget range"""
        value_mappings = {
            "Under $2,500": 2000.0,
            "$2,500 - $5,000": 3750.0,
            "$5,000 - $10,000": 7500.0,
            "$10,000 - $25,000": 17500.0,
            "$25,000 - $50,000": 37500.0,
            "$50,000+": 75000.0,
            "Not sure / Need quote": 10000.0,
            "Prefers not to say": 10000.0
        }
        
        return value_mappings.get(budget_range, 10000.0)
    
    def _log_discovery_completion(self, contact_id: str, intake_id: str, lead_score: LeadScore):
        """Log the discovery completion activity"""
        
        activity_description = f"AI Discovery call completed. Lead score: {lead_score.total_score}/100"
        if lead_score.is_hot_lead:
            activity_description += " (HOT LEAD 🔥)"
        
        activity_description += f". Intake ID: {intake_id[:8]}..."
        
        try:
            db_log_activity(
                activity_type="ai_discovery_completed",
                description=activity_description,
                contact_id=contact_id
            )
        except Exception as e:
            self.logger.error(f"Error logging activity: {str(e)}")

# ============================================================================
# API ENDPOINT FUNCTIONS
# ============================================================================

def process_discovery_data(discovery_json: str) -> Dict[str, Any]:
    """
    Main API endpoint for Phase 1 to call when discovery completes
    
    Args:
        discovery_json: JSON string with structured discovery data
        
    Returns:
        Dict with processing results, contact/intake IDs, and lead score
    """
    
    try:
        # Parse JSON input
        discovery_data = json.loads(discovery_json) if isinstance(discovery_json, str) else discovery_json
        
        # Initialize processor
        processor = AISDRDiscoveryIntegration()
        
        # Process the data
        result = processor.process_discovery_completion(discovery_data)
        
        # Format response
        response = {
            "success": result.success,
            "contact_id": result.contact_id,
            "intake_id": result.intake_id,
            "deal_id": result.deal_id,
            "lead_score": {
                "total": result.lead_score.total_score if result.lead_score else 0,
                "budget": result.lead_score.budget_score if result.lead_score else 0,
                "timeline": result.lead_score.timeline_score if result.lead_score else 0,
                "authority": result.lead_score.authority_score if result.lead_score else 0,
                "need": result.lead_score.need_score if result.lead_score else 0,
                "is_hot_lead": result.lead_score.is_hot_lead if result.lead_score else False,
                "notes": result.lead_score.scoring_notes if result.lead_score else ""
            },
            "warnings": result.warnings,
            "error": result.error_message if not result.success else None,
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": f"API processing error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

def get_lead_score_breakdown(contact_id: str) -> Dict[str, Any]:
    """
    Get detailed lead scoring breakdown for a contact
    
    Args:
        contact_id: UUID of the contact
        
    Returns:
        Dict with lead scoring details and CRM data
    """
    
    try:
        # Get contact and intake data
        contact = db_get_contact(contact_id) if contact_id else None
        if not contact:
            return {"success": False, "error": "Contact not found"}
        
        # Get most recent intake for this contact
        intakes = db_get_intakes(contact_id=contact_id)
        if not intakes:
            return {"success": False, "error": "No discovery data found for contact"}
        
        recent_intake = intakes[0]  # Most recent
        
        # Reconstruct discovery data for scoring
        discovery_data = DiscoveryData(
            first_name=contact.get('first_name', ''),
            last_name=contact.get('last_name', ''),
            company=contact.get('company', ''),
            budget_range=recent_intake.get('budget_range', ''),
            budget_flexibility=recent_intake.get('budget_flexibility', ''),
            timeline=recent_intake.get('deadline_type', ''),
            urgency=recent_intake.get('urgency', ''),
            decision_maker=recent_intake.get('decision_maker', ''),
            decision_timeline=recent_intake.get('decision_timeline', ''),
            business_needs=[],  # Would need to reconstruct from notes
            pain_points=recent_intake.get('pain_points', ''),
            project_types=recent_intake.get('project_types', [])
        )
        
        # Calculate fresh score
        scorer = LeadScoringEngine()
        lead_score = scorer.calculate_lead_score(discovery_data)
        
        return {
            "success": True,
            "contact_name": f"{contact.get('first_name')} {contact.get('last_name')}",
            "company": contact.get('company'),
            "intake_id": recent_intake.get('id'),
            "intake_date": recent_intake.get('intake_date'),
            "lead_score": {
                "total": lead_score.total_score,
                "budget_score": lead_score.budget_score,
                "timeline_score": lead_score.timeline_score,
                "authority_score": lead_score.authority_score,
                "need_score": lead_score.need_score,
                "is_hot_lead": lead_score.is_hot_lead,
                "scoring_notes": lead_score.scoring_notes
            },
            "discovery_data": {
                "budget_range": recent_intake.get('budget_range'),
                "timeline": recent_intake.get('deadline_type'),
                "urgency": recent_intake.get('urgency'),
                "decision_maker": recent_intake.get('decision_maker'),
                "project_types": recent_intake.get('project_types'),
                "confidence_level": recent_intake.get('confidence_level')
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving lead score: {str(e)}"
        }

# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

def example_usage():
    """Example of how Phase 1 would call this integration"""
    
    # Example discovery data from Phase 1 voice processing
    sample_discovery = {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "company": "Johnson Real Estate",
        "email": "sarah@johnsonrealty.com",
        "phone": "239-555-0123",
        "website": "johnsonrealty.com",
        "industry": "real estate",
        
        "business_needs": ["lead generation", "client management", "property listings"],
        "current_solutions": "Using spreadsheets and manual processes",
        "pain_points": "Losing leads, manual follow-up is time-consuming, no automation",
        "desired_outcome": "Automated lead nurturing and better client management",
        
        "project_types": ["crm", "website"],
        "must_have_features": "Lead capture forms, automated follow-up, property search",
        "nice_to_have_features": "Mobile app, advanced reporting",
        "integrations": ["QuickBooks", "MLS", "email marketing"],
        
        "budget_range": "10k to 25k",
        "budget_flexibility": "some flexibility",
        "timeline": "hard deadline - new office launch in 3 months",
        "urgency": "important",
        "deadline_reason": "Grand opening event scheduled",
        
        "decision_maker": "Yes - sole decision maker",
        "decision_timeline": "1-2 weeks",
        "stakeholders": "Will discuss with business partner",
        "competition": "Getting 2-3 quotes",
        
        "meeting_notes": "Very engaged, understands value of automation, growing business",
        "next_steps": "Send proposal by Friday, schedule demo",
        "confidence_indicators": ["engaged questions", "budget confirmed", "timeline clear"],
        "red_flags": []
    }
    
    # Process the discovery data
    result = process_discovery_data(json.dumps(sample_discovery))
    
    return result

if __name__ == "__main__":
    # Test the integration
    result = example_usage()
    print("\\n" + "="*60)
    print("AI SDR DISCOVERY INTEGRATION TEST")
    print("="*60)
    print(json.dumps(result, indent=2))