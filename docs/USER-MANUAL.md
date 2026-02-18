# MPT-CRM — User Manual

> Metro Point Technology's Customer Relationship Management System

---

## MPT-CRM Ecosystem Architecture

MPT-CRM is Metro Point Technology's comprehensive customer relationship management system that handles the complete customer lifecycle from lead generation to project delivery and ongoing service.

```
              ┌─────────────────────────────────────┐
              │            MPT-CRM                  │
              │      (Sales & Service Hub)         │
              │                                     │
              │   • Contact & Company Management    │
              │   • Sales Pipeline & Deals         │
              │   • Projects & Time Tracking       │
              │   • Service Tickets & Support      │
              │   • Marketing Campaigns            │
              └─────────────────┬───────────────────┘
                                │
       ┌────────────────────────┼────────────────────────┐
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────┐         ┌─────────────┐         ┌────────────────┐
│MISSION CTRL │         │ DEVELOPMENT │         │ MPT-Accounting │
│(Operations) │         │ (Products)  │         │   (Finance)    │
│             │         │             │         │                │
│ • Tasks     │         │ • Code      │         │ • Invoices     │
│ • Time      │         │ • Builds    │         │ • Payments     │
│ • Agents    │         │ • Deploy    │         │ • Expenses     │
│ • Reports   │         │ • Monitor   │         │ • P&L          │
└─────────────┘         └─────────────┘         └────────────────┘
```

### System Role

| System | Department | Owns | Queries |
|--------|------------|------|---------|
| **MPT-CRM** | Sales + Service | Contacts, companies, deals, projects, tickets, campaigns | Mission Control for time entries, Accounting for project financials |

### Data Flow Principles

**Live Integration - No Data Duplication**

MPT-CRM queries other systems in real-time for the latest data:

- **Project financials** → Live query to MPT-Accounting invoices
- **Time tracking** → Live query to Mission Control time entries  
- **Task assignment** → Creates cards in Mission Control
- **Invoice generation** → Pushes data to MPT-Accounting

**Single Source of Truth for Customer Data**

MPT-CRM is the master system for:
- Contact and company information
- Deal pipeline and sales data
- Project definitions and client relationships
- Service ticket history
- Marketing campaign tracking

---

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| MPT-CRM Dashboard | [CRM Production URL] | Main CRM interface |
| Mission Control | https://mpt-mission-control.vercel.app | Task and time management |
| MPT-Accounting | [Accounting URL] | Financial management |

---

## 1. Getting Started & Login

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- Valid MPT-CRM account

### Login Process
MPT-CRM uses Single Sign-On (SSO) authentication for secure access.

**Step 1: Access the System**
1. Navigate to the MPT-CRM URL
2. Click "Login" button
3. You'll be redirected to the SSO provider

**Step 2: Authenticate**
1. Enter your Metro Point Technology credentials
2. Complete any multi-factor authentication if prompted
3. You'll be redirected back to MPT-CRM

**Step 3: Verify Access**
- Upon successful login, you'll see the Dashboard
- Your name and logout option appear in the top navigation
- All CRM modules become available in the sidebar

### First-Time Setup
After your first login:
1. Review your user profile in Settings
2. Familiarize yourself with the dashboard layout
3. Check the Help section for guided tutorials
4. Contact your administrator if features are missing

*[Screenshot: Login screen with SSO button]*
*[Screenshot: Successful login showing dashboard]*

---

## 2. Dashboard Overview

The Dashboard provides a real-time overview of your CRM data and serves as the central navigation hub.

### Key Metrics Section
The top of the dashboard displays critical business metrics:

**Pipeline Overview**
- **Total Pipeline Value** - Sum of all open deals
- **Active Deals** - Number of deals in progress
- **Won This Month** - Monthly closed revenue
- **Conversion Rate** - Deal success percentage

**Activity Summary**
- **New Contacts** - Recent contact additions
- **Active Projects** - Projects in development
- **Open Tickets** - Pending service requests
- **Overdue Tasks** - Items requiring attention

### Quick Actions Panel
Direct access to common workflows:
- **Add Contact** - Quick contact entry
- **Create Deal** - Start new sales opportunity
- **New Project** - Initialize client project
- **Log Service Call** - Create support ticket
- **Schedule Follow-up** - Set reminder tasks

### Recent Activity Feed
Real-time stream of CRM events:
- New contacts added
- Deal stage changes  
- Project updates
- Ticket resolutions
- Campaign activities

### Pipeline Visual
Kanban-style overview of your sales pipeline:
- Deals organized by stage
- Visual progress indicators
- Quick stage updates
- Value summaries per stage

*[Screenshot: Dashboard with key metrics highlighted]*
*[Screenshot: Pipeline visual with sample deals]*

---

## 3. Contacts Management

### Overview
The Contacts module manages all people in your business network, from initial networking contacts to long-term clients.

### Contact Types
MPT-CRM categorizes contacts into distinct types:

- **Networking** - Initial connections from events, referrals
- **Prospect** - Qualified potential customers
- **Lead** - Actively engaged sales opportunities
- **Client** - Current paying customers
- **Former Client** - Past customers for reactivation
- **Partner** - Business partners and collaborators
- **Vendor** - Service providers and suppliers

### Adding New Contacts

**Manual Entry**
1. Navigate to Contacts page
2. Click "Add Contact" button
3. Complete required fields:
   - Name (first and last)
   - Email address
   - Contact type
   - Company (optional)
4. Add optional details:
   - Phone number
   - Role/Title (in notes)
   - Tags for categorization
   - Source information
5. Click "Save Contact"

**Business Card Import**
MPT-CRM includes advanced business card processing:
1. Upload business card image (JPG/PNG)
2. System extracts contact information automatically
3. Review and correct extracted data
4. Assign contact type and tags
5. Save with business card image attached

**CSV Import**
For bulk contact uploads:
1. Download CSV template from Contacts page
2. Populate template with contact data
3. Upload CSV file using Import function
4. Review mapping between CSV columns and CRM fields
5. Process import and review results

### Contact Detail View
Click any contact to view detailed information:

**Basic Information Tab**
- Name, email, phone
- Company and role
- Contact type and source
- Tags and categories

**Business Card Tab**
- Original business card images
- Side-by-side card display
- Card image management

**Activity History**
- Email interactions
- Meeting records
- Deal associations
- Service tickets

**Projects & Deals**
- Active projects for this contact
- Deal pipeline history
- Project roles and involvement

### Contact Tagging System
Organize contacts with a flexible tagging system:

**Source Tags**
- Networking Event
- Referral
- Website
- Cold Outreach
- Social Media

**Industry Tags**
- Technology
- Healthcare
- Finance
- Manufacturing
- Retail

**Interest Tags**
- Web Development
- Mobile Apps
- CRM Systems
- E-commerce
- Automation

**Status Tags**
- Hot Lead
- Needs Follow-up
- Not Interested
- Future Opportunity

### Email Status Management
Track email deliverability for each contact:
- **Active** - Receiving emails successfully
- **Unsubscribed** - Opted out of communications
- **Bounced** - Email address invalid
- **Suppressed** - Temporarily blocked

*[Screenshot: Contacts list with filters applied]*
*[Screenshot: Contact detail view with all tabs visible]*
*[Screenshot: Business card import process]*

---

## 4. Companies Management

### Overview
The Companies module manages business entities and their associated addresses, serving as the organizational hub for multiple contacts.

### Company Information
Each company record includes:

**Basic Details**
- Company name
- Website URL
- Industry classification
- Primary phone number

**Address Management**
Companies support three address types:
- **Physical Address** - Main office location
- **Mailing Address** - Correspondence delivery
- **Billing Address** - Invoice and payment processing

**Contact Associations**
- Link multiple contacts to each company
- Assign contact roles (Owner, Billing, Technical, Project Manager, General)
- Maintain organizational hierarchy

### Creating Companies

**New Company Setup**
1. Navigate to Companies page
2. Click "Add Company" button
3. Enter company name (required)
4. Add website and industry
5. Configure addresses as needed:
   - Physical address for visits
   - Mailing address if different
   - Billing address for invoicing
6. Save company record

**Contact Assignment**
1. Select company from companies list
2. Click "View Details"
3. In Associated Contacts section, click "Link Contact"
4. Choose existing contact or create new
5. Assign appropriate role
6. Save association

### Company Detail View
Comprehensive company information display:

**Company Profile**
- Name, website, industry
- Contact information
- Notes and important details

**Addresses Section**
Collapsible sections for each address type:
- Complete address information
- Visual indicators for configured addresses
- Edit capabilities for each address type

**Associated Contacts**
- List all contacts for this company
- Contact roles and responsibilities
- Direct links to contact details
- Quick contact creation

**Projects & Deals**
- Active projects for this company
- Deal pipeline history
- Revenue tracking

### Company-Contact Relationships
The system enforces proper data organization:

**Individual vs Corporate Contacts**
- Individual contacts: No company association
- Corporate contacts: Linked to company record
- Address inheritance: Corporate contacts use company addresses

**Role Management**
Clearly defined contact roles within companies:
- **Owner** - Decision maker, primary contact
- **Billing** - Handles invoicing and payments
- **Technical** - Project implementation contact
- **Project Manager** - Day-to-day project coordination
- **General** - Standard business contact

*[Screenshot: Companies list with search and filters]*
*[Screenshot: Company detail view showing addresses and contacts]*
*[Screenshot: Contact role assignment interface]*

---

## 5. Projects Management

### Overview
The Projects module manages client work from contract to delivery, ensuring every project is properly linked to a won sales opportunity.

### Project Creation Workflow
MPT-CRM enforces strict business rules for project integrity:

**BUSINESS RULE: Every project MUST link to a Won deal**

**Step 1: Deal Must Be Won**
1. Navigate to Sales Pipeline
2. Move deal to "Closed Won" stage
3. Deal becomes available for project creation

**Step 2: Create Project**
1. Go to Projects page
2. Click "New Project"
3. Select company (only companies with Won deals shown)
4. Select Won deal (only unlinked Won deals available)
5. Project details auto-populate from deal

**Step 3: Project Configuration**
- Project name and description
- Start and end dates
- Budget and billing type
- SharePoint folder URL for documents
- Team assignments

### Project Types
Projects are categorized by type:

**Development Projects**
- Custom software development
- Web application builds
- Mobile app development
- System integrations

**Consulting Projects**
- Business analysis
- Process optimization
- Technology planning
- Training and support

**Support Projects**
- Ongoing maintenance
- System administration
- User support
- Emergency fixes

### Project Status Tracking
Projects progress through defined stages:

- **Planning** - Initial setup and requirements
- **Active** - Development in progress
- **Testing** - Quality assurance phase
- **Staging** - Client review and approval
- **Complete** - Project delivered and accepted
- **On Hold** - Temporarily suspended
- **Cancelled** - Project terminated

### Time Tracking Integration
Projects integrate with Mission Control for time management:

**Time Entry Process**
1. Work performed on project tasks
2. Time logged in Mission Control
3. Entries automatically linked to project
4. Project dashboard shows total time
5. Data feeds to invoicing system

**Billing Integration**
- Time entries flow to MPT-Accounting
- Automatic invoice generation
- Project profitability tracking
- Budget vs. actual reporting

### Project Detail View
Comprehensive project management interface:

**Project Overview**
- Basic project information
- Status and progress indicators
- Budget and time summaries
- Source deal information

**Tasks & Milestones**
- Project task breakdown
- Milestone tracking
- Dependency management
- Team assignments

**Time & Billing**
- Time entry summaries
- Billing rate information
- Invoice status
- Profitability metrics

**Documents & Communication**
- SharePoint folder access
- Project documentation
- Client communication history
- Change order tracking

*[Screenshot: Projects list showing source deals]*
*[Screenshot: New project form with deal selection]*
*[Screenshot: Project detail view with time tracking]*

---

## 6. Deals/Pipeline

### Overview
The Sales Pipeline manages revenue opportunities from initial discovery through contract closure using a visual Kanban board interface.

### Pipeline Stages
Deals progress through five defined stages:

**Discovery**
- Initial client meetings
- Requirements gathering
- Opportunity qualification
- Preliminary scope definition

**Proposal**
- Formal proposal preparation
- Scope documentation
- Pricing and timeline
- Client presentation

**Negotiation**
- Contract terms discussion
- Pricing adjustments
- Timeline refinements
- Legal review

**Closed Won**
- Contract signed and executed
- Project setup initiated
- Available for project creation
- Revenue recognized

**Closed Lost**
- Opportunity did not convert
- Reasons documented
- Contact maintained for future
- Lessons learned captured

### Creating New Deals

**Deal Setup**
1. Navigate to Sales Pipeline
2. Click "Add Deal" button
3. Enter deal information:
   - Deal title/name
   - Associated contact
   - Deal value (revenue potential)
   - Expected close date
   - Initial stage (usually Discovery)
4. Add notes and context
5. Save deal

**Deal Qualification**
Ensure deals meet qualification criteria:
- Identified decision maker
- Budget confirmed or estimated
- Timeline established
- Business need validated

### Managing Deal Flow

**Moving Between Stages**
1. Locate deal card on pipeline board
2. Click deal to open detail view
3. Use stage dropdown to select new stage
4. Add notes explaining stage change
5. Update expected close date if needed
6. Save changes

**Deal Activities**
Track all deal-related activities:
- Client meetings and calls
- Proposal submissions
- Follow-up communications
- Stakeholder interactions
- Competitive intelligence

### Deal Detail View
Complete deal management interface:

**Deal Information**
- Basic deal details
- Contact and company
- Value and probability
- Stage and progression

**Activity Timeline**
- Chronological activity log
- Meeting records
- Communication history
- Document sharing

**Proposal Management**
- Proposal version tracking
- Client feedback incorporation
- Pricing evolution
- Terms negotiation

**Competitive Analysis**
- Competitor identification
- Competitive advantages
- Threat assessment
- Differentiation strategy

### Pipeline Analytics
Track sales performance metrics:

**Pipeline Value**
- Total pipeline value by stage
- Weighted pipeline (probability-adjusted)
- Monthly pipeline trends
- Stage conversion rates

**Performance Metrics**
- Average deal size
- Sales cycle length
- Win rate analysis
- Loss reason tracking

*[Screenshot: Pipeline Kanban board with deals]*
*[Screenshot: Deal detail view with activity timeline]*
*[Screenshot: Pipeline analytics dashboard]*

---

## 7. Service Tickets

### Overview
The Service module manages customer support requests, technical issues, and service delivery from initial request through resolution.

### Ticket Types
Service tickets are categorized by type:

**Technical Support**
- Software bugs and issues
- System performance problems
- Integration difficulties
- User access problems

**Feature Requests**
- New functionality requests
- Enhancement suggestions
- Workflow improvements
- Integration requests

**Training & Consultation**
- User training requests
- Best practice guidance
- Process optimization
- Strategic consultation

**Emergency Support**
- Critical system outages
- Security incidents
- Data recovery needs
- Urgent business issues

### Creating Service Tickets

**Ticket Submission Process**
1. Navigate to Service page
2. Click "New Ticket" button
3. Complete ticket form:
   - Ticket title/summary
   - Client/company selection
   - Priority level (Low, Medium, High, Critical)
   - Category/type
   - Detailed description
   - Affected systems/users
4. Attach relevant files or screenshots
5. Submit ticket

**Priority Levels**
- **Critical** - System down, business stopped (2-hour response)
- **High** - Major functionality impacted (4-hour response)
- **Medium** - Minor functionality affected (1-day response)  
- **Low** - General questions, nice-to-have (3-day response)

### Service Workflow

**Ticket Lifecycle**
Tickets progress through standardized states:

1. **New** - Recently submitted, awaiting review
2. **Assigned** - Assigned to technician
3. **In Progress** - Work actively underway
4. **Waiting Customer** - Awaiting client response/input
5. **Testing** - Solution implemented, under review
6. **Resolved** - Issue fixed, awaiting confirmation
7. **Closed** - Customer confirmed resolution

**Escalation Process**
Automatic escalation triggers:
- Critical tickets not acknowledged within 2 hours
- High priority tickets not assigned within 4 hours
- Any ticket approaching SLA breach
- Customer escalation requests

### Service Level Agreements (SLA)
Commitment to response and resolution times:

| Priority | Response Time | Resolution Target |
|----------|---------------|------------------|
| Critical | 2 hours | 8 hours |
| High | 4 hours | 24 hours |
| Medium | 1 business day | 3 business days |
| Low | 3 business days | 1 week |

### Ticket Management Interface

**Service Dashboard**
- Open ticket queue
- SLA status indicators
- Technician workloads
- Performance metrics

**Ticket Detail View**
- Complete ticket history
- Customer communication log
- Time tracking
- Resolution documentation

**Knowledge Base Integration**
- Link tickets to knowledge articles
- Create articles from resolved tickets
- Search existing solutions
- Best practice documentation

### Client Communication
Maintain professional client communication throughout the service process:

**Automated Notifications**
- Ticket confirmation emails
- Status change notifications
- Resolution confirmations
- Satisfaction surveys

**Communication Log**
- All client interactions recorded
- Email correspondence tracked
- Phone call summaries
- Meeting notes attached

*[Screenshot: Service ticket list with priority indicators]*
*[Screenshot: New ticket creation form]*
*[Screenshot: Ticket detail view with communication history]*

---

## 8. Change Orders

### Overview
The Change Orders module manages project scope changes, additional work requests, and contract modifications with full approval workflows.

### Change Order Types

**Scope Changes**
- Additional features or functionality
- Modified requirements
- Technology platform changes
- Timeline adjustments

**Resource Changes**
- Team member additions
- Skill set modifications
- Equipment or tool requirements
- Third-party service needs

**Budget Modifications**
- Cost increases or decreases
- Payment term changes
- Billing rate adjustments
- Currency or tax changes

### Creating Change Orders

**Change Order Initiation**
1. Navigate to project detail page
2. Click "Request Change Order"
3. Complete change order form:
   - Project reference
   - Change description
   - Business justification
   - Impact assessment
   - Cost estimate
   - Timeline implications
4. Submit for approval

**Impact Assessment**
Document all change impacts:
- **Scope Impact** - What changes in deliverables
- **Schedule Impact** - Timeline adjustments required
- **Budget Impact** - Cost increase/decrease
- **Resource Impact** - Team or tool changes
- **Risk Impact** - New risks introduced

### Approval Process

**Approval Workflow**
Change orders follow a structured approval process:

1. **Submitted** - Initial change order created
2. **Review** - Technical team evaluates feasibility
3. **Estimation** - Cost and timeline analysis
4. **Client Review** - Presented to client for approval
5. **Approved** - Client accepts change order
6. **Rejected** - Client declines change order
7. **Implemented** - Changes incorporated into project

**Approval Authorities**
- **Technical Lead** - Technical feasibility review
- **Project Manager** - Impact assessment
- **Client Stakeholder** - Business approval
- **Account Manager** - Commercial terms

### Change Order Tracking

**Status Monitoring**
Track change order progress:
- Approval workflow position
- Outstanding approvals needed
- Implementation progress
- Budget and timeline impact

**Financial Impact**
- Original project budget
- Approved change order value
- Pending change order value
- Total project value (current)

### Implementation Management

**Change Implementation**
Once approved, change orders are implemented:

1. **Project Plan Update** - Scope and timeline revision
2. **Resource Allocation** - Team and tool adjustments
3. **Contract Amendment** - Legal documentation
4. **Client Communication** - Implementation notification
5. **Progress Tracking** - Regular status updates

**Version Control**
Maintain clear project version history:
- Original project scope (v1.0)
- Change order modifications (v1.1, v1.2, etc.)
- Current approved scope
- Implementation status

*[Screenshot: Change order creation form]*
*[Screenshot: Change order approval workflow]*
*[Screenshot: Project with change order history]*

---

## 9. Marketing/Campaigns/Drip Sequences

### Overview
The Marketing module manages email campaigns, drip sequences, and marketing automation to nurture leads and maintain client relationships.

### Email Templates
Pre-built email templates for common scenarios:

**Networking Templates**
- **New Contact Follow-up** - Initial connection after meeting
- **Reconnection** - Re-engaging past contacts
- **Event Follow-up** - Post-networking event communication
- **Referral Thank You** - Acknowledging referrals

**Sales Templates**
- **Proposal Follow-up** - After proposal submission
- **Meeting Follow-up** - Post-meeting summary
- **Check-in** - Regular prospect touch-base
- **Welcome New Client** - Onboarding communication

**Service Templates**
- **Project Kickoff** - Welcome to new project
- **Status Updates** - Progress communications
- **Project Completion** - Delivery confirmation
- **Satisfaction Survey** - Post-project feedback

### Campaign Management

**Creating Email Campaigns**
1. Navigate to Marketing page
2. Click "New Campaign"
3. Configure campaign:
   - Campaign name and description
   - Target audience (contact lists)
   - Email template selection
   - Send schedule (immediate or scheduled)
4. Preview and test email
5. Launch campaign

**Audience Targeting**
Segment contacts for targeted messaging:
- **By Contact Type** - Prospects, clients, partners
- **By Industry** - Technology, healthcare, finance
- **By Tag** - Custom categorization
- **By Activity** - Recent interactions
- **By Deal Stage** - Pipeline position

### Drip Sequences
Automated email sequences for lead nurturing:

**Lead Nurturing Sequence**
- Day 1: Welcome and introduction
- Day 3: Company overview and services
- Day 7: Case study and testimonials
- Day 14: Free consultation offer
- Day 30: Re-engagement attempt

**Client Onboarding Sequence**
- Day 0: Welcome to the team
- Day 1: Project overview and timeline
- Day 3: Team introductions
- Day 7: First milestone check-in
- Day 14: Progress update

**Reactivation Sequence**
- Day 1: "We miss you" message
- Day 7: New services announcement
- Day 14: Special offer or discount
- Day 30: Final re-engagement attempt

### Campaign Analytics

**Performance Metrics**
Track campaign effectiveness:
- **Open Rates** - Email open percentage
- **Click Rates** - Link click percentage
- **Response Rates** - Reply percentage
- **Conversion Rates** - Goal completion percentage
- **Unsubscribe Rates** - Opt-out percentage

**Engagement Tracking**
Monitor individual contact engagement:
- Email opens and clicks
- Website visits from emails
- Form submissions
- Meeting bookings
- Deal progression

### Marketing Automation

**Trigger-Based Campaigns**
Automatically send emails based on contact behavior:
- **New Contact Added** - Welcome sequence
- **Deal Won** - Project onboarding
- **Deal Lost** - Stay-in-touch sequence
- **Service Ticket Resolved** - Satisfaction survey
- **Project Completed** - Feedback request

**Lead Scoring**
Automatically score leads based on engagement:
- Email opens (+1 point)
- Link clicks (+2 points)
- Website visits (+2 points)
- Form submissions (+5 points)
- Meeting bookings (+10 points)

*[Screenshot: Email template library]*
*[Screenshot: Campaign creation interface]*
*[Screenshot: Drip sequence configuration]*

---

## 10. Reports

### Overview
The Reports module provides comprehensive analytics and insights into sales performance, project profitability, and business trends.

### Sales Reports

**Pipeline Analysis**
- Pipeline value by stage
- Stage conversion rates
- Average deal size trends
- Sales cycle analysis
- Win/loss ratios

**Performance Metrics**
- Revenue by time period
- Target vs. actual performance
- Individual salesperson metrics
- Lead source effectiveness
- Customer acquisition costs

**Forecasting**
- Revenue projections
- Pipeline probability analysis
- Seasonal trend identification
- Growth rate calculations
- Target achievement predictions

### Project Reports

**Project Profitability**
- Budget vs. actual costs
- Time tracking analysis
- Resource utilization
- Margin analysis
- Project ROI calculations

**Delivery Performance**
- On-time delivery rates
- Budget adherence
- Scope creep analysis
- Change order frequency
- Client satisfaction scores

**Resource Management**
- Team utilization rates
- Skill demand analysis
- Capacity planning
- Overtime tracking
- Cost per hour analysis

### Financial Reports

**Revenue Analysis**
- Monthly recurring revenue (MRR)
- Annual contract value (ACV)
- Revenue by client
- Service line profitability
- Geographic revenue distribution

**Collections Tracking**
- Outstanding invoice amounts
- Days sales outstanding (DSO)
- Collection success rates
- Aging analysis
- Payment trend tracking

### Marketing Reports

**Campaign Performance**
- Email open and click rates
- Lead generation effectiveness
- Cost per lead
- Campaign ROI
- Audience growth rates

**Lead Analysis**
- Lead source effectiveness
- Lead quality scoring
- Conversion funnel analysis
- Lead nurturing performance
- Customer journey mapping

### Custom Reports

**Report Builder**
Create custom reports with:
- Flexible date ranges
- Multiple data sources
- Custom field combinations
- Various chart types
- Export capabilities

**Scheduled Reports**
- Automatic report generation
- Email delivery schedules
- Dashboard updates
- Stakeholder distribution
- Performance alerts

*[Screenshot: Sales pipeline report dashboard]*
*[Screenshot: Project profitability analysis]*
*[Screenshot: Custom report builder interface]*

---

## 11. Workflow Documentation

### Lead → Contact → Customer Journey

This workflow documents the complete customer lifecycle from initial lead generation through long-term client relationship management.

#### Phase 1: Lead Generation
**Lead Sources**
- Networking events and referrals
- Website contact forms
- Social media engagement
- Cold outreach campaigns
- Partner introductions

**Lead Qualification Process**
1. **Initial Contact** - First interaction with prospect
2. **BANT Assessment** - Budget, Authority, Need, Timeline
3. **Discovery Questions** - Business challenges, goals, constraints
4. **Fit Analysis** - Service alignment, cultural fit, capacity
5. **Qualification Decision** - Accept, nurture, or disqualify

#### Phase 2: Contact Development
**Contact Categorization**
```
Lead (qualified) → Prospect (engaged) → Client (contracted)
```

**Development Activities**
1. **Networking Contact Creation**
   - Add contact to CRM system
   - Assign networking contact type
   - Tag with source information
   - Add to appropriate nurturing sequence

2. **Prospect Advancement**
   - Schedule discovery call
   - Conduct needs assessment
   - Create sales opportunity (deal)
   - Begin formal sales process

3. **Lead Nurturing**
   - Assign to drip campaign sequence
   - Track engagement and interactions
   - Score based on activity level
   - Schedule periodic check-ins

#### Phase 3: Sales Process
**Deal Pipeline Management**
1. **Discovery Stage**
   - Conduct discovery call
   - Document requirements
   - Assess technical feasibility
   - Create preliminary scope

2. **Proposal Stage**
   - Prepare formal proposal
   - Define scope and deliverables
   - Establish timeline and budget
   - Present to client stakeholders

3. **Negotiation Stage**
   - Discuss terms and conditions
   - Handle objections
   - Negotiate pricing and timeline
   - Finalize contract terms

4. **Closure**
   - Execute contract documents
   - Move deal to "Closed Won"
   - Initiate client onboarding
   - Create project record

#### Phase 4: Customer Onboarding
**Project Initiation**
1. **Project Setup**
   - Create project from won deal
   - Define project team
   - Establish communication channels
   - Set up project documentation

2. **Client Onboarding**
   - Send welcome email sequence
   - Schedule kickoff meeting
   - Introduce project team
   - Review project timeline

3. **Service Integration**
   - Configure support channels
   - Establish SLA agreements
   - Set up monitoring systems
   - Create knowledge base access

#### Phase 5: Ongoing Relationship
**Client Retention Activities**
- Regular check-in meetings
- Proactive support monitoring
- Service expansion discussions
- Feedback collection and implementation
- Renewal and upsell opportunities

### Service Request → Ticket → Resolution → Invoice

This workflow documents the complete service delivery process from initial client request through billing completion.

#### Phase 1: Service Request Intake
**Request Channels**
- Direct client phone calls
- Email support requests
- Online support portal
- Project-related requests
- Emergency hotline calls

**Initial Assessment**
1. **Request Classification**
   - Technical support
   - Feature enhancement
   - Training/consultation
   - Emergency support
   - Billing questions

2. **Priority Assignment**
   - Critical: System down (2-hour response)
   - High: Major functionality (4-hour response)
   - Medium: Minor issues (1-day response)
   - Low: General questions (3-day response)

#### Phase 2: Ticket Creation
**Ticket Setup Process**
1. **Information Collection**
   - Client/company identification
   - Contact person details
   - Issue description
   - Affected systems/users
   - Business impact assessment

2. **Ticket Documentation**
   - Generate unique ticket ID
   - Assign priority level
   - Categorize by type
   - Set SLA response target
   - Create initial communication

3. **Resource Assignment**
   - Assign to appropriate technician
   - Consider skill requirements
   - Check availability and workload
   - Set escalation contacts
   - Define approval authorities

#### Phase 3: Resolution Process
**Technical Resolution**
1. **Issue Investigation**
   - Reproduce issue if possible
   - Review system logs and data
   - Identify root cause
   - Evaluate solution options
   - Assess implementation impact

2. **Solution Implementation**
   - Develop solution approach
   - Test in non-production environment
   - Implement in production
   - Validate resolution
   - Document solution steps

3. **Client Communication**
   - Regular status updates
   - Solution explanation
   - Testing instructions
   - Implementation scheduling
   - Resolution confirmation

#### Phase 4: Quality Assurance
**Resolution Validation**
1. **Client Testing**
   - Client confirms issue resolution
   - Acceptance of solution
   - Sign-off on implementation
   - Feedback collection
   - Satisfaction measurement

2. **Documentation Updates**
   - Update knowledge base
   - Create troubleshooting guides
   - Document lessons learned
   - Update procedures if needed
   - Train other team members

#### Phase 5: Billing Process
**Time and Cost Tracking**
1. **Time Entry Management**
   - Log all work time to Mission Control
   - Link time entries to client project
   - Include detailed work descriptions
   - Assign appropriate billing rates
   - Get approval for billing

2. **Invoice Generation**
   - Export time data to MPT-Accounting
   - Generate client invoice
   - Include detailed work breakdown
   - Apply contracted rates
   - Send invoice to client

3. **Payment Processing**
   - Track invoice status
   - Follow up on overdue payments
   - Process payments received
   - Update client account
   - Close ticket financial cycle

### Change Order Approval Process

This workflow ensures proper authorization and documentation for all project scope changes.

#### Phase 1: Change Identification
**Change Request Sources**
- Client-requested modifications
- Technical requirement changes
- Timeline adjustment needs
- Resource availability changes
- External dependency impacts

**Change Documentation**
1. **Request Description**
   - Clear change definition
   - Business justification
   - Urgency assessment
   - Stakeholder identification
   - Initial impact estimate

#### Phase 2: Impact Analysis
**Technical Assessment**
1. **Scope Impact Analysis**
   - Deliverable modifications
   - Feature additions/removals
   - Quality impact assessment
   - Integration requirements
   - Testing implications

2. **Resource Impact Analysis**
   - Team member requirements
   - Skill set needs
   - Tool and equipment needs
   - Third-party service requirements
   - Training requirements

3. **Schedule Impact Analysis**
   - Timeline adjustments
   - Milestone modifications
   - Dependency changes
   - Critical path impacts
   - Delivery date changes

4. **Financial Impact Analysis**
   - Cost increase/decrease
   - Billing rate adjustments
   - Payment term modifications
   - Currency impacts
   - Tax implications

#### Phase 3: Approval Workflow
**Approval Hierarchy**
```
Technical Lead → Project Manager → Account Manager → Client Stakeholder
```

**Approval Steps**
1. **Technical Review**
   - Feasibility assessment
   - Implementation approach
   - Risk evaluation
   - Resource requirements
   - Timeline estimates

2. **Project Management Review**
   - Impact on overall project
   - Schedule adjustments needed
   - Resource reallocation
   - Communication requirements
   - Documentation updates

3. **Commercial Review**
   - Pricing adjustments
   - Contract modifications
   - Payment terms
   - Legal implications
   - Risk mitigation

4. **Client Approval**
   - Present change order
   - Explain impacts and costs
   - Negotiate terms
   - Obtain written approval
   - Update contracts

#### Phase 4: Implementation
**Change Implementation Process**
1. **Project Plan Updates**
   - Revise project scope
   - Update timeline and milestones
   - Modify resource allocations
   - Adjust deliverable definitions
   - Update quality criteria

2. **Communication Management**
   - Notify all stakeholders
   - Update project documentation
   - Revise status reports
   - Adjust meeting agendas
   - Update client communications

3. **Execution Monitoring**
   - Track implementation progress
   - Monitor cost and schedule
   - Ensure quality standards
   - Manage risks
   - Report status regularly

### Drip Campaign Enrollment

This workflow automates lead nurturing and client communication through targeted email sequences.

#### Phase 1: Enrollment Triggers
**Automatic Enrollment Events**
- New contact addition
- Contact type changes
- Deal stage progression
- Service ticket resolution
- Project completion
- Specific date anniversaries

**Manual Enrollment Options**
- Individual contact enrollment
- Bulk contact list enrollment
- Tag-based enrollment
- Custom criteria enrollment

#### Phase 2: Campaign Sequencing
**Lead Nurturing Sequence Example**
```
Day 0: Welcome and introduction
Day 2: Company overview and services  
Day 7: Case study and testimonials
Day 14: Free consultation offer
Day 30: Re-engagement attempt
```

**Sequence Management**
1. **Email Scheduling**
   - Set send timing and frequency
   - Configure time zone handling
   - Avoid weekends and holidays
   - Respect send time preferences
   - Monitor delivery rates

2. **Content Personalization**
   - Dynamic field insertion
   - Industry-specific content
   - Contact type customization
   - Geographic localization
   - Previous interaction history

#### Phase 3: Engagement Tracking
**Activity Monitoring**
1. **Email Metrics**
   - Open rates and times
   - Click-through rates
   - Reply rates
   - Forward rates
   - Unsubscribe rates

2. **Engagement Scoring**
   - Points for opens and clicks
   - Website visit tracking
   - Form submission detection
   - Meeting booking identification
   - Deal progression correlation

#### Phase 4: Response Management
**Automated Responses**
- Out-of-office detection
- Unsubscribe processing
- Bounce handling
- Engagement escalation
- Lead scoring updates

**Manual Intervention Triggers**
- High engagement scores
- Direct email replies
- Meeting requests
- Unsubscribe with feedback
- Complaint escalation

### Discovery Meeting Lifecycle (Sales Prospects)

This workflow automates the complete lifecycle for **sales discovery calls** with prospects who come through the CRM Discovery form.

#### Wire Chart: Discovery Meeting Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISCOVERY MEETING LIFECYCLE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │  DISCOVERY   │     │   PRE-MTG    │     │   MEETING    │                │
│   │    FORM      │────▶│    PREP      │────▶│  (RECORDED)  │                │
│   │  (CRM p.01)  │     │              │     │              │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│   • Auto-create       • Match to CRM       • Teams recording                 │
│     contact           • Calendar brief     • Auto-transcript                 │
│   • Drip enroll       • Full CRM context                                    │
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │  TRANSCRIPT  │     │   APPROVAL   │     │   MISSION    │                │
│   │  PROCESSING  │────▶│    QUEUE     │────▶│   CONTROL    │                │
│   │ (Metro Bot)  │     │   (Teams)    │     │    CARDS     │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│   • Summarize         • Patrick approves   • Approved items                  │
│   • Extract items       each item            become cards                    │
│   • Ownership tags    • Reject junk        • Auto-tracked                   │
│   • Update CRM                                                               │
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │   PROJECT    │     │  WAITING-ON  │     │    DAILY     │                │
│   │   PROPOSAL   │     │   TRACKING   │     │    CHECKS    │                │
│   │              │────▶│              │────▶│              │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│   • Auto-generate     • Client items       • What's overdue?                 │
│     from scope        • Follow-up dates    • Waiting on whom?                │
│   • Send for sig      • Auto-reminders     • Archive 14 days                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Workflow Steps

**1. Lead Intake**
- Prospect fills out **Discovery form** in MPT-CRM (`pages/01_Discovery.py`)
- Contact auto-created in CRM with all intake data
- Auto-enrolled in appropriate drip campaign

**2. Pre-Meeting**
- Match attendees to CRM contacts automatically
- Generate calendar briefing with full CRM relationship summary
- Include: who they are, company, product interest, message from form

**3. During Meeting**
- Patrick records in Teams (built-in, free)
- Teams auto-generates transcript

**4. Post-Meeting (Metro Bot processes transcript)**
- ✅ Summarize key points & decisions
- ✅ Extract action items with ownership (Patrick's vs. prospect's)
- ✅ **Approval queue** in Teams before creating cards
- ✅ Create Mission Control cards for approved items only
- ✅ Update CRM contact notes with meeting context
- ✅ Track "waiting on" items for prospect follow-ups
- ✅ **Generate project proposal** from discussed scope

**5. Follow-Up Automation**
- Daily completion checks (what's overdue, waiting on others)
- Auto-archive completed items after 14 days
- Temperature-based follow-up (HOT/WARM/COLD)

---

### Network Contact Meeting Lifecycle (Networking)

This workflow automates meetings with **networking contacts** from Chamber events, referrals, and professional connections.

#### Wire Chart: Network Contact Meeting Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 NETWORK CONTACT MEETING LIFECYCLE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │   CONTACT    │     │  INTEL PDF   │     │   MEETING    │                │
│   │   EXISTS     │────▶│  GENERATION  │────▶│  (RECORDED)  │                │
│   │   IN CRM     │     │              │     │              │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│   • From Chamber      • Website audit      • Teams recording                 │
│   • From referral     • PageSpeed score    • Auto-transcript                 │
│   • From event        • Competitor info                                      │
│                       • Send to contact                                      │
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │  TRANSCRIPT  │     │   SURVEYS    │     │    SMART     │                │
│   │  PROCESSING  │────▶│   (BOTH)     │────▶│  FOLLOW-UP   │                │
│   │ (Metro Bot)  │     │              │     │              │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│   • Summarize         • Contact survey     • HOT: Proposal                   │
│   • Extract items     • Patrick survey     • WARM: Nurture                   │
│   • Update CRM        • Both → CRM notes   • COLD: Stay connected            │
│                                                                              │
│                    ┌──────────────┐                                          │
│                    │  REFERRAL    │                                          │
│                    │  TRACKING    │                                          │
│                    └──────────────┘                                          │
│                          │                                                   │
│                          ▼                                                   │
│                    • Referral potential                                      │
│                    • Mutual connections                                      │
│                    • Long-term relationship                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Pre-Meeting Automation (1-2 days before)

**Intel PDF Generation**
When a networking meeting is scheduled:

1. **Website Audit**
   - Scan contact's company website
   - Identify issues (SEO, forms, mobile, etc.)
   - Document systems they may be lacking
   
2. **Generate Intel PDF**
   - Professional MPT-branded report
   - Website audit findings
   - "How MPT Can Help" soft pitch
   - Talking points for the meeting

3. **Distribution**
   - Email PDF to contact: "Looking forward to our meeting!"
   - Attach PDF to calendar event
   - Save PDF to CRM contact record

#### Post-Meeting Automation (same day)

**Survey to Contact**
```
📋 CONTACT SURVEY
• How was our meeting? (1-5 stars)
• Topics you'd like to discuss further?
• Interested in learning more about... (checkboxes)
• Best way to stay in touch?
```

**Survey to Patrick**
```
📋 INTERNAL SURVEY  
• How'd it go? (Hot / Warm / Cold)
• What were they interested in?
• Follow-up actions needed?
• Referral potential? (1-5)
```

**Smart Follow-Up Logic**
Based on survey responses:

| Lead Temp | Follow-Up Action |
|-----------|------------------|
| 🔥 Hot | Send proposal, schedule next meeting |
| 🌡️ Warm | Nurture sequence, quarterly check-in |
| ❄️ Cold | "Great meeting you" + stay connected |

#### Tools Location
- `tools/meeting-lifecycle/generate-intel-pdf.mjs`
- `tools/meeting-lifecycle/send-pre-meeting-email.mjs`
- `tools/meeting-lifecycle/attach-to-calendar.mjs`
- `tools/meeting-lifecycle/save-to-crm.mjs`
- `tools/meeting-lifecycle/smart-followup.mjs`

---

## 12. E-Signature & Contract Generation

### Overview
MPT-CRM includes a built-in e-signature system for generating, sending, and managing client contracts. This eliminates the need for external services like DocuSign and keeps the entire contract workflow within the CRM.

### Contract Package Structure

Every client contract consists of three components merged into a single PDF:

```
┌─────────────────────────────────────────────────┐
│           COMPLETE CLIENT CONTRACT              │
├─────────────────────────────────────────────────┤
│                                                 │
│  📄 MUTUAL NON-DISCLOSURE AGREEMENT (NDA)       │
│     • Confidentiality terms                     │
│     • Data protection                           │
│     • Trade secrets                             │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  📋 STATEMENT OF WORK (SOW)                     │
│     • Legal terms & liability                   │
│     • IP assignment                             │
│     • Insurance coverage ($3M Professional      │
│       Liability, Cyber Liability)               │
│     • Jurisdiction (US/Canada only)             │
│                                                 │
│     Exhibit A: [Attached Proposal]              │
│     ─────────────────────────────               │
│     • Scope & Deliverables                      │
│     • Phases & Milestones                       │
│     • Pricing & Payment Schedule                │
│     • Timeline                                  │
│     • Custom Terms                              │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ✍️ SIGNATURES                                  │
│     Client: ____________  Date: ______          │
│     MPT:    ____________  Date: ______          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Why This Structure?**
This mirrors how insurance policies incorporate applications — the proposal (with all project specifics) becomes Exhibit A of the legal contract. One signature covers the entire package.

### Contract Templates

**Template Location:** SharePoint > SALES > CONTRACTS

| Template | Purpose |
|----------|---------|
| Mutual Non-Disclosure Agreement (NDA).docx | Confidentiality protection |
| Statement of Work (SOW) TEMPLATE.docx | Legal terms and service framework |

### Auto-Fill Fields

The system automatically populates contract fields from CRM data:

| Field | Source |
|-------|--------|
| Client Company Name | contacts.company or companies.name |
| Client Contact Name | contacts.first_name + contacts.last_name |
| Client Email | contacts.email |
| Project Title | projects.name |
| Project Description | projects.description |
| Total Fee | projects.budget |
| Effective Date | Auto-generated (current date) |
| MPT Company Info | Pre-filled (Metro Point Technology LLC) |

### Contract Generation Workflow

#### Step 1: Proposal Accepted
After a client verbally or in writing accepts your proposal:
1. Ensure proposal document exists with:
   - Complete scope and deliverables
   - Phases and milestones
   - Pricing and payment schedule
   - Timeline
   - Any custom terms

#### Step 2: Generate Contract Package
1. Navigate to the Project or Deal in CRM
2. Click **"Generate Contract"** button
3. System merges:
   - NDA (pages 1-2)
   - SOW with client info auto-filled (pages 3-4)
   - Your proposal as Exhibit A (remaining pages)
4. Preview the complete PDF
5. Make any manual adjustments if needed

#### Step 3: Send for E-Signature
1. Click **"Send for Signature"**
2. Enter signer's email (auto-filled from contact)
3. Add optional message to signer
4. Click **"Send"**

The system:
- Generates a secure one-time signing link (UUID-based)
- Sends professional email via SendGrid
- Creates tracking record in esign_documents table

#### Step 4: Client Signs Electronically
The client receives an email with a signing link:
1. Client clicks the secure link
2. Views the complete contract PDF
3. Draws or types their signature
4. Clicks "Sign Document"

The system captures:
- Signature image (PNG)
- Timestamp (UTC)
- SHA-256 hash for tamper verification
- IP address and browser info (audit trail)

#### Step 5: Automatic Filing
Upon successful signature:
1. Signed PDF generated with signature overlay
2. Auto-uploaded to SharePoint: `SALES/{ClientName}/Contracts/Signed/`
3. Confirmation emails sent to:
   - Client (with signed PDF attached)
   - MPT admin (with signed PDF attached)
4. CRM project updated with "Contract Signed" status
5. Audit trail saved to database

### E-Signature Legal Compliance

**E-SIGN Act Compliance**
All electronic signatures captured through MPT-CRM comply with the Electronic Signatures in Global and National Commerce Act (E-SIGN Act):

- ✅ Intent to sign clearly captured
- ✅ Consent to electronic signature obtained
- ✅ Association of signature with document (hash verification)
- ✅ Record retention (SharePoint + database)
- ✅ Audit trail with timestamps

**Verification Features**
- SHA-256 hash of original PDF + signature + timestamp
- Tamper detection (hash mismatch alerts)
- Complete audit trail in JSON format
- Certificate of completion available

### Tracking Signed Contracts

**E-Signature Dashboard**
View all contracts and their status:

| Status | Description |
|--------|-------------|
| Pending | Contract generated, not yet sent |
| Sent | Email sent to signer, awaiting signature |
| Signed | Signer completed, awaiting processing |
| Completed | Fully processed and filed |
| Expired | 30-day signing window passed |
| Cancelled | Contract voided before signing |

**Document History**
Each contract maintains a complete history:
- Creation timestamp
- Send timestamp
- View events (when signer opens link)
- Signature timestamp
- Filing confirmation
- All email communications

### SharePoint Integration

**Automatic Folder Structure**
Signed contracts are filed to SharePoint automatically:

```
SALES/
└── {Client Company Name}/
    └── Contracts/
        └── Signed/
            └── {ProjectName}_Contract_Signed_{Date}.pdf
```

**Access from CRM**
- Direct link to SharePoint folder on Project detail page
- Quick access to all client contracts
- Version history maintained by SharePoint

### Best Practices

**Before Generating Contract**
- Ensure proposal is complete and final
- Verify all client contact information
- Confirm project budget is accurate
- Review any custom terms needed

**During Signing Process**
- Monitor for signing completion
- Follow up if not signed within 48 hours
- Be available for signer questions
- Check spam folders if client reports missing email

**After Signature**
- Verify filing to SharePoint
- Confirm receipt of signed copy
- Update project status in CRM
- Begin project onboarding sequence

---

## 13. Troubleshooting & Support

### Common Issues

**Login Problems**
- **Issue**: Cannot access CRM system
- **Solution**: Verify SSO credentials, clear browser cache, contact IT support
- **Prevention**: Use supported browsers, keep credentials updated

**Data Synchronization**
- **Issue**: Information not updating across modules
- **Solution**: Refresh browser, check network connection, verify data entry
- **Prevention**: Wait for auto-save confirmations, use reliable internet

**Performance Issues**
- **Issue**: Slow page loading or timeouts
- **Solution**: Clear browser cache, check internet speed, close unnecessary tabs
- **Prevention**: Regular browser maintenance, stable internet connection

### Contact Information

**Technical Support**
- Email: support@metropointtech.com
- Phone: [Support phone number]
- Hours: Monday-Friday, 8 AM - 6 PM EST

**Training and Documentation**
- User guides: Available in Help section
- Video tutorials: [Training portal URL]
- Best practices: Documented in knowledge base

### System Maintenance

**Scheduled Maintenance**
- Regular updates: Monthly, typically weekends
- Advance notice: 48 hours minimum
- Backup procedures: Automatic daily backups
- Recovery options: Point-in-time restoration

---

## Changelog

- **2026-02-17**: **Meeting Lifecycle Workflows** - Split into two distinct workflows with wire charts:
  - **Discovery Meeting Lifecycle** (Sales Prospects) — Full automation from CRM Discovery form through approval queue, Mission Control cards, project proposals, and daily completion checks
  - **Network Contact Meeting Lifecycle** (Networking) — Intel PDF generation, post-meeting surveys, smart follow-up based on temperature (HOT/WARM/COLD)

- **2026-02-15**: **E-Signature & Contract Generation** - Added complete documentation for the built-in e-signature system including contract package structure (NDA + SOW + Proposal), auto-fill fields, generation workflow, legal compliance (E-SIGN Act), SharePoint auto-filing, and tracking features. This workflow is the official standard for all MPT client contracts.

- **2026-02-13**: **Initial User Manual** - Complete CRM documentation including all modules, workflows, and user guidance. Covers Dashboard, Contacts, Companies, Projects, Pipeline, Service, Change Orders, Marketing, Reports with comprehensive workflow documentation for Lead→Customer journey, Service→Resolution→Invoice, Change Order approval, and Drip campaign enrollment processes.

---

*Last updated: 2026-02-17*