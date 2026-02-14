# AI SDR Phase 2 - CRM Discovery Form Auto-Fill

**Mission Control Card:** 60ba5b82-db74-4d9c-b99f-6f6f22173908

Connect voice discovery data to CRM, auto-creating contacts and filling discovery forms with intelligent lead scoring.

## 🎯 Overview

Phase 2 seamlessly integrates voice-extracted discovery data from Phase 1 into the MPT-CRM system, automatically:

- **Creating contacts** with proper categorization and source attribution
- **Filling discovery forms** using existing `client_intakes` table structure  
- **Scoring leads** intelligently based on budget, timeline, authority, and need fit
- **Flagging hot leads** (score > 80) for immediate attention
- **Auto-creating deals** for qualified prospects

## 📋 Features Implemented

### ✅ 1. Discovery Data Mapping
- **Voice field normalization** - handles variations in how prospects provide info
- **Project type mapping** - "web site" → "Website Development", "crm system" → "Custom Software / CRM"
- **Budget range parsing** - "10k to 25k" → "$10,000 - $25,000"
- **Industry standardization** - "law firm" → "Legal", "real estate" → "Real Estate"
- **Integration mapping** - "quickbooks" → "QuickBooks", "email marketing" → "Mailchimp"
- **Data validation & cleaning** - truncates long text, normalizes phone/email

### ✅ 2. Auto-Create Contact
- **Contact creation** with `source="ai_discovery"` and `source_detail="AI SDR Discovery Call"`
- **Lead type assignment** - all AI discoveries marked as "lead" type
- **Duplicate prevention** - checks for existing contacts by email/phone
- **Immediate activity logging** - "AI Discovery call completed" with lead score

### ✅ 3. Discovery Form Auto-Fill
- **Uses existing CRM structure** - populates `client_intakes` table with full discovery data
- **Complete field mapping**:
  - **Contact info** → first_name, last_name, company, email, phone
  - **Business context** → industry, company_website, pain_points, current_solution, desired_outcome
  - **Project scope** → project_types, must_have_features, nice_to_have_features, integrations
  - **Timeline & Budget** → deadline_type, urgency, budget_range, budget_flexibility
  - **Decision making** → decision_maker, decision_timeline, competing_quotes
  - **Internal notes** → meeting_notes, red_flags, confidence_level, next_steps
- **Status management** - new intakes start with `status="new"`

### ✅ 4. Lead Scoring (1-100 Scale)
**Four scoring factors (25 points each):**

#### Budget Score (0-25)
- **Higher budgets = higher scores** - "$50,000+" gets 25 points, "Under $2,500" gets 10
- **Flexibility bonus** - "very flexible" adds 2 points, "firm budget" subtracts 3
- **Unknown budget** - gets neutral 15 points

#### Timeline Score (0-25) 
- **Urgency levels** - "ASAP" = 25, "Hard deadline" = 22, "Flexible" = 12
- **Deadline reasons** - mentions of "launch", "event", "compliance" add 3 points
- **Decision timeline** - "ready now" adds 5, "just exploring" subtracts 5

#### Authority Score (0-25)
- **Decision power** - "sole decision maker" = 25, "presenting to others" = 10
- **Approval process** - "needs approval" = 20, "part of team" = 15
- **Timeline to decide** - combines with decision power for final score

#### Need Score (0-25)
- **Pain point intensity** - keywords like "frustrated", "losing", "manual" add points
- **Project complexity** - custom software, integrations score higher than basic websites
- **Multiple needs** - articulating several business needs indicates serious buyer

**Hot Lead Threshold:** Score > 80 automatically creates deal in "qualified" stage

### ✅ 5. Integration Endpoint
- **REST API** - Flask server on port 5001 with comprehensive endpoints
- **Main endpoint** - `POST /api/discovery/process` for Phase 1 integration
- **Batch processing** - handle multiple discoveries at once
- **Health checks** - database connectivity and system status
- **Testing tools** - data mapping validation and scoring tests

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd "C:\Users\Patri\Metro Point Technology\Metro Point Technology - Documents\DEVELOPMENT\Metro Point Technology\Projects\MPT-CRM"
pip install flask flask-cors requests
```

### 2. Start the API Server
```bash
python ai_sdr_api.py
```
This starts the Flask server on `http://localhost:5001` with endpoints for Phase 1 integration.

### 3. Test the Integration
```bash
python ai_sdr_test.py
```
Runs comprehensive tests of data mapping, lead scoring, and API endpoints.

### 4. Process Discovery Data
**From Phase 1 (or any Python code):**
```python
import requests

discovery_data = {
    "first_name": "Sarah",
    "last_name": "Johnson", 
    "company": "Johnson Real Estate",
    "email": "sarah@johnsonrealty.com",
    "phone": "239-555-0123",
    "industry": "real estate",
    "project_types": ["crm", "website"],
    "budget_range": "10k to 25k",
    "timeline": "hard deadline - new office launch in 3 months",
    "decision_maker": "Yes - sole decision maker",
    "pain_points": "Losing leads, manual follow-up is time-consuming"
}

response = requests.post(
    'http://localhost:5001/api/discovery/process',
    json=discovery_data
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Contact ID: {result['contact_id']}")
print(f"Lead Score: {result['lead_score']['total']}/100")
print(f"Hot Lead: {result['lead_score']['is_hot_lead']}")
```

## 📡 API Endpoints

### `POST /api/discovery/process`
**Main integration endpoint for processing discovery data**

**Request:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "company": "Doe Industries", 
    "email": "john@doeindustries.com",
    "phone": "239-555-0123",
    "project_types": ["website", "crm"],
    "budget_range": "10k to 25k",
    "decision_maker": "Yes - sole decision maker",
    "pain_points": "Manual processes are inefficient",
    "timeline": "ASAP - launching new service"
}
```

**Response:**
```json
{
    "success": true,
    "contact_id": "550e8400-e29b-41d4-a716-446655440000",
    "intake_id": "550e8400-e29b-41d4-a716-446655440001", 
    "deal_id": "550e8400-e29b-41d4-a716-446655440002",
    "lead_score": {
        "total": 85,
        "budget": 22,
        "timeline": 25,
        "authority": 25,
        "need": 13,
        "is_hot_lead": true,
        "notes": "Strong budget fit | High urgency/clear timeline | Strong decision authority"
    },
    "warnings": [],
    "timestamp": "2026-02-07T14:30:00"
}
```

### `GET /api/discovery/score/<contact_id>`
**Get detailed lead score breakdown for existing contact**

### `GET /api/discovery/health` 
**Health check - database connectivity and system status**

### `POST /api/discovery/batch`
**Process multiple discoveries at once**

### `POST /api/discovery/mapping-test`
**Test data mapping without creating CRM records**

### `GET /api/discovery/test`
**Run integration test with sample data**

## 🗂️ File Structure

```
MPT-CRM/
├── ai_sdr_discovery_integration.py    # Main integration logic
├── ai_sdr_api.py                      # Flask API endpoints  
├── ai_sdr_test.py                     # Comprehensive test suite
├── AI_SDR_PHASE_2_README.md           # This documentation
└── db_service.py                      # Existing CRM database layer
```

## 🔄 Data Flow

```
Phase 1 Voice Processing
          ↓
Voice-Extracted Discovery Data (JSON)
          ↓  
POST /api/discovery/process
          ↓
┌─────────────────────────────────┐
│ Data Mapping & Validation       │
│ • Normalize project types       │
│ • Clean budget ranges          │
│ • Standardize industries       │
│ • Validate contact info        │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Contact Creation/Update         │
│ • Create new contact record     │
│ • Set source="ai_discovery"    │ 
│ • Mark as "lead" type          │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Discovery Form Population       │
│ • Create client_intakes record  │
│ • Map all discovery fields     │
│ • Set status="new"             │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Lead Scoring                    │
│ • Calculate 4 factor scores     │
│ • Generate total (1-100)       │
│ • Identify hot leads (>80)     │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│ Deal Creation (Hot Leads Only)  │
│ • Auto-create qualified deal    │
│ • Estimate value from budget    │
│ • Set high priority            │
└─────────────────────────────────┘
          ↓
Response with IDs & Lead Score
```

## 🧪 Testing & Validation

The integration includes comprehensive testing:

### Unit Tests
- **Data mapping validation** - ensures voice fields map correctly to CRM
- **Lead scoring accuracy** - validates scoring logic with various scenarios
- **Edge case handling** - tests missing data, invalid formats, etc.

### Integration Tests  
- **API endpoint testing** - validates all REST endpoints
- **Database connectivity** - ensures CRM integration works
- **Performance testing** - measures processing speed

### Test Cases Included
1. **Hot Lead** - High budget, urgent timeline, sole decision maker → Score 85-100
2. **Medium Lead** - Moderate budget, flexible timeline → Score 50-75  
3. **Low Lead** - Small budget, price shopping, no urgency → Score 20-45
4. **Edge Cases** - Missing data, unusual formats
5. **Data Mapping** - Voice variations that need normalization

**Run tests:**
```bash
python ai_sdr_test.py
```

## 🔧 Configuration & Customization

### Lead Scoring Weights
Modify scoring factors in `LeadScoringEngine` class:

```python
# Current weights (25 points each)
budget_score = self._score_budget_fit(...)      # 0-25
timeline_score = self._score_timeline_urgency(...)  # 0-25  
authority_score = self._score_decision_authority(...) # 0-25
need_score = self._score_need_match(...)        # 0-25

# Hot lead threshold (default 80)
is_hot_lead = total_score > 80
```

### Data Mapping Rules
Add new mappings in `DiscoveryDataMapper` class:

```python
PROJECT_TYPE_MAPPINGS = {
    'your_term': 'Standard CRM Value',
    # Add custom mappings
}

BUDGET_MAPPINGS = {
    'custom_budget_phrase': '$10,000 - $25,000',
    # Add budget variations
}
```

### API Configuration
Modify server settings in `ai_sdr_api.py`:

```python
app.run(
    host='0.0.0.0',     # Listen address
    port=5001,          # Port number
    debug=True,         # Debug mode
    threaded=True       # Multi-threading
)
```

## 🔗 Phase 1 Integration

**From your Phase 1 voice processing code:**

```python
import requests
import json

# After voice processing extracts discovery data
discovery_data = {
    # Your extracted fields from voice processing
}

# Send to Phase 2 for CRM integration
try:
    response = requests.post(
        'http://localhost:5001/api/discovery/process',
        json=discovery_data,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        
        if result['success']:
            print(f"✅ CRM integration successful!")
            print(f"Contact ID: {result['contact_id']}")
            print(f"Lead Score: {result['lead_score']['total']}/100")
            
            if result['lead_score']['is_hot_lead']:
                print(f"🔥 HOT LEAD DETECTED! Deal created: {result['deal_id']}")
                # Trigger immediate notification/follow-up
                
        else:
            print(f"❌ CRM integration failed: {result['error']}")
            
    else:
        print(f"❌ API error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Integration error: {str(e)}")
```

## 📊 Lead Score Interpretation

**Score Ranges:**
- **85-100**: 🔥 **Hot Lead** - High priority, auto-creates deal
- **70-84**: 🔸 **Warm Lead** - Strong potential, follow up soon  
- **50-69**: 🔹 **Medium Lead** - Standard follow-up process
- **30-49**: 🔸 **Cool Lead** - Nurture campaign, longer timeline
- **1-29**: ❄️ **Cold Lead** - Qualification needed

**Factor Breakdown:**
- **Budget Score** - Higher budgets and flexibility increase score
- **Timeline Score** - Urgency and clear deadlines increase score
- **Authority Score** - Decision-making power increases score  
- **Need Score** - Pain points and service fit increase score

## 🚨 Hot Lead Workflow

When a lead scores > 80:

1. **Deal Auto-Creation** - Creates deal in "qualified" stage with high priority
2. **Value Estimation** - Uses budget range to estimate deal value
3. **Activity Logging** - Records "AI Discovery completed (HOT LEAD 🔥)"
4. **Immediate Attention** - Flagged for same-day follow-up

**Recommended Actions:**
- Send personalized proposal within 24 hours
- Schedule discovery call confirmation  
- Prioritize in daily task list
- Consider expedited pricing/timeline

## 🔍 Monitoring & Analytics

**Key Metrics to Track:**
- **Lead scores distribution** - Are most leads scoring appropriately?
- **Hot lead conversion rate** - How many 80+ scores actually close?
- **Processing time** - Is integration keeping up with call volume?
- **Data quality** - Are mappings working correctly?

**Available in CRM:**
- Lead score visible in contact activities
- Discovery intake records with full details
- Deal pipeline with AI-sourced deals marked
- Activity timeline showing processing steps

## ❗ Troubleshooting

### Common Issues

**"Database not connected"**
- Check Supabase credentials in `.env` file
- Verify `db_service.py` is working correctly
- Test with `GET /api/discovery/health`

**"Contact creation failed"**  
- Check for duplicate emails (CRM constraint)
- Verify required fields (first_name, last_name)
- Check database permissions

**"Low lead scores"**
- Review scoring factors - budget, timeline, authority, need
- Consider adjusting weights for your business
- Check if data mapping is working correctly

**"API timeout"**
- Database queries may be slow
- Check Supabase performance
- Consider optimizing queries in `db_service.py`

### Debug Mode
Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Mode
Use test endpoint to validate without creating records:

```bash
curl -X GET http://localhost:5001/api/discovery/test
```

## 🔮 Future Enhancements

**Potential Phase 3 Features:**
- **ML-based scoring** - Train on conversion history for better predictions
- **Automated follow-up** - Schedule emails/calls based on lead score
- **Real-time notifications** - Slack/Teams alerts for hot leads
- **Advanced analytics** - Lead score trends, conversion analysis
- **Custom scoring models** - Industry-specific scoring algorithms

## 📞 Support

**For issues or questions:**
- Run test suite first: `python ai_sdr_test.py`  
- Check API health: `GET /api/discovery/health`
- Review logs in terminal where API server is running
- Validate input data with mapping test endpoint

**Mission Control Card:** 60ba5b82-db74-4d9c-b99f-6f6f22173908

---

*AI SDR Phase 2 completed - Discovery data now flows automatically into CRM with intelligent lead scoring! 🚀*