# MPT-CRM Design Document
## Metro Point Technology - Customer Relationship Management System

---

## Overview

MPT-CRM is a custom CRM application built with Streamlit for Metro Point Technology, designed to manage software development sales, networking contacts, and marketing campaigns.

---

## Current Implementation (Phase 1 - Prototype)

### Completed Features

#### 1. Dashboard (app.py)
- Pipeline overview with deal counts and values
- Quick stats for contacts, leads, and active deals
- Navigation hub to all CRM sections

#### 2. Contacts Page (pages/02_Contacts.py)
- Contact types: Networking, Prospect, Lead, Client, Former Client, Partner, Vendor
- Tag system: Source tags, Industry tags, Interest tags, Status tags
- Contact detail view with inline editing
- Search and filtering by type and tag
- Email status tracking (Active, Unsubscribed, Bounced)

#### 3. Pipeline Page (pages/03_Pipeline.py)
- Kanban-style visual pipeline (similar to Microsoft Planner)
- Stages: Discovery, Proposal, Negotiation, Closed Won, Closed Lost
- Deal cards with value, contact, and expected close date
- Drag concept (click-to-move between stages)

#### 4. Marketing Page (pages/07_Marketing.py)
- Email template library with 6 templates:
  - Networking Follow-Up - New Contact
  - Networking Follow-Up - Reconnection
  - Proposal Follow-Up
  - Check-In After Meeting
  - Thank You for Referral
  - Welcome New Client
- Drip campaign builder (UI ready)
- Campaign analytics placeholders

#### 5. Shared Navigation (shared/navigation.py)
- Custom sidebar with Metro Point Technology logo
- Consistent navigation across all pages
- CSS to hide default Streamlit navigation

---

## Completed (Phase 2)

### Database Setup ✅
- [x] Supabase project created and configured
- [x] Database schema created with all tables:
  - contacts, deals, deal_tasks, deal_comments
  - projects, tasks, time_entries, invoices
  - email_templates, email_campaigns, email_sends, activities
- [x] Created `services/database.py` - Supabase wrapper class
- [x] Credentials stored in `.env` file

### Email Integration ✅
- [x] SendGrid API configured
- [x] Created `services/email_service.py` - SendGrid wrapper with template merging
- [x] Three domains verified: agentcommissiontracker.com, metropointtech.com, metropointtechnology.com
- [x] Test email functionality added to Marketing page

### Additional Pages ✅
- [x] Projects page (pages/04_Projects.py) - Project management with time tracking
- [x] Tasks page (pages/05_Tasks.py) - Task management with priorities
- [x] Time & Billing page (pages/06_Time_Billing.py) - Time entries and invoicing
- [x] Reports page (pages/08_Reports.py) - Pipeline analytics, revenue tracking
- [x] Settings page (pages/09_Settings.py) - Company info, integrations config

---

## Next Steps (Phase 3 - Enhancement)

### Priority 1: Migrate Pages to Supabase
**IMPORTANT:** All pages currently use session state with sample data. The database is configured but pages need to be updated to use `services/database.py` for persistence.

Pages requiring migration:
- [ ] Dashboard (app.py) - Load real data from Supabase
- [ ] Contacts page - CRUD operations via database.py
- [ ] Pipeline page - Save deal stage changes to database
- [ ] Projects page - Persist projects and time entries
- [ ] Tasks page - Save tasks to database
- [ ] Time & Billing page - Persist invoices
- [ ] Marketing page - Load/save templates from database

### Priority 2: Real Kanban Drag-and-Drop
Current pipeline uses click-to-move. Options for true drag-and-drop:
- [ ] **streamlit-sortables** - Native drag-and-drop sortable containers
- [ ] **streamlit-elements** - Material UI components with drag support
- [ ] **Custom JS component** - Full control with streamlit.components.v1
- [ ] **MS Graph Sync** - Sync with Microsoft Planner for Kanban in M365

### Priority 3: UI Improvements
- [ ] Fix deprecation warnings (use_container_width -> width)
- [ ] Add empty label text to form fields (accessibility)
- [ ] Responsive design improvements
- [ ] Dark/light mode toggle

### Priority 4: Advanced Features
- [ ] Import contacts from CSV/Excel
- [ ] Export reports to PDF
- [ ] Email automation rules
- [ ] Lead scoring
- [ ] Integration with calendar (Google/Outlook)
- [ ] User authentication via Supabase Auth

---

## Branding & Domain Strategy

### Current Situation
- **Two Domains:**
  - `MetroPointTech.com` - Currently used for products/SaaS
  - `MetroPointTechnology.com` - Available for services/custom development
- **One Email:** `Support@MetroPointTech.com` used for all communication
- **Challenge:** How to market software development services without confusing clients who know the product brand

### Recommended Strategy

#### Option A: Domain Separation (Recommended)

| Domain | Purpose | Email |
|--------|---------|-------|
| **MetroPointTech.com** | Products, SaaS, existing tools | support@metropointtech.com |
| **MetroPointTechnology.com** | Custom software development, consulting | patrick@metropointtechnology.com |

**Business Card Design for Software Development:**
```
FRONT:
Patrick [Last Name]
Founder & Software Developer

Metro Point Technology, LLC
Custom Software | Web Applications | Business Automation

BACK:
www.MetroPointTechnology.com
patrick@metropointtechnology.com
(239) XXX-XXXX

Specializing in:
- Custom Business Software
- Web Application Development
- Insurance Industry Solutions
- Process Automation
```

**Email Strategy:**
1. Create `patrick@metropointtechnology.com` for personal/sales communication
2. Create `hello@metropointtechnology.com` for general inquiries
3. Keep `support@metropointtech.com` for product support only
4. Use email signatures that match the domain you're communicating from

**Website Strategy:**
- Add a "Custom Development" or "Services" page to MetroPointTech.com that links to MetroPointTechnology.com
- MetroPointTechnology.com focuses on:
  - Custom software development services
  - Portfolio of projects
  - Case studies
  - Contact form for consultations
  - Your background and expertise

#### Option B: Single Domain with Clear Sections

If managing two websites feels like too much, use one domain with clear navigation:

```
MetroPointTech.com
├── Products (your SaaS tools)
├── Services (custom development)
├── About
└── Contact
```

**Pros:** Simpler to maintain, builds single brand
**Cons:** May confuse users who came for products vs services

### Implementation Checklist

- [ ] Decide on domain strategy (Option A or B)
- [ ] Set up email addresses for the chosen strategy
- [ ] Update email signatures
- [ ] Design and order business cards
- [ ] Create/update website content for services
- [ ] Update CRM email templates with correct sender addresses

---

## Technical Architecture

### Current Stack
- **Frontend:** Streamlit
- **State Management:** Streamlit session_state
- **Styling:** Custom CSS via st.markdown

### Planned Stack
- **Database:** Supabase (PostgreSQL)
- **Email:** SendGrid API
- **Authentication:** Supabase Auth
- **File Storage:** Supabase Storage (for attachments)
- **Hosting:** Streamlit Cloud or self-hosted

---

## File Structure

```
MPT-CRM/
├── app.py                     # Dashboard/home page
├── pages/
│   ├── 02_Contacts.py         # Contact management
│   ├── 03_Pipeline.py         # Sales pipeline (Kanban)
│   ├── 04_Projects.py         # Project management
│   ├── 05_Tasks.py            # Task management
│   ├── 06_Time_Billing.py     # Time tracking & invoices
│   ├── 07_Marketing.py        # Email templates & campaigns
│   ├── 08_Reports.py          # Analytics & reports
│   └── 09_Settings.py         # Configuration
├── services/
│   ├── database.py            # Supabase wrapper class
│   └── email_service.py       # SendGrid wrapper class
├── database/
│   └── schema.sql             # Full database schema for Supabase
├── shared/
│   └── navigation.py          # Shared sidebar component
├── assets/
│   └── MetroPointTechnology-Logo.jpg
├── .env                       # API keys (not in git)
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
├── .venv/                     # Python virtual environment
└── MPT-CRM Design Document.md # This file
```

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-23 | 0.1.0 | Initial prototype with Dashboard, Contacts, Pipeline, Marketing |
| 2026-01-24 | 0.1.1 | Fixed sidebar navigation, added logo, imported email templates |
| 2026-01-24 | 0.2.0 | Added Supabase database, SendGrid email, Projects, Tasks, Time & Billing, Reports, Settings pages |

---

## Architecture: Centralized Database Service Layer

### THE PROBLEM

Before this refactor, **every page had its own copy of the database code**. Each of the 9+ page
files (01_Discovery through 09_Settings) plus `app.py` and `mobile_scanner.py` contained:

- Its own `get_db()` / `create_client()` connection setup
- Its own `db_get_*`, `db_create_*`, `db_update_*`, `db_delete_*` functions
- Raw `.table()` and `.select()` Supabase calls inline with UI logic

This created a **"fix one page, break another"** nightmare:
- The same query existed in 3-4 different files with subtle differences
- A schema change meant hunting through every file to update every call
- Debugging a data issue meant reading thousands of lines across 10+ files
- Weeks were wasted in loops of "fix Contacts → break Pipeline → fix Pipeline → break Discovery"

### THE SOLUTION

**`db_service.py`** — a single centralized service layer that owns ALL database operations.

```
Architecture:

    ┌──────────────────────┐
    │   Streamlit Pages    │   ← UI only (layout, widgets, display)
    │  (01–09 + app.py)    │
    └──────────┬───────────┘
               │  from db_service import db_get_*, db_create_*, ...
               ▼
    ┌──────────────────────┐
    │    db_service.py     │   ← ALL database logic lives here
    │  (50+ functions)     │
    │  Single source of    │
    │  truth for DB ops    │
    └──────────┬───────────┘
               │  supabase.table(...).select/insert/update/delete
               ▼
    ┌──────────────────────┐
    │      Supabase        │   ← PostgreSQL database + Storage
    └──────────────────────┘
```

### THE RULE

> **Pages are islands.** They handle UI only.
> **`db_service.py` is the single source of truth** for ALL database operations.
> Pages NEVER import `supabase`, call `create_client`, or use raw `.table()` queries.

Every page follows this pattern:
```python
from db_service import db_get_contacts, db_create_contact, db_is_connected

# UI code only — no raw DB calls
if db_is_connected():
    contacts = db_get_contacts()
    st.dataframe(contacts)
```

### How to Add New Database Operations

1. **Add the function to `db_service.py`** in the appropriate section
2. **Follow the naming convention**: `db_get_*`, `db_create_*`, `db_update_*`, `db_delete_*`
3. **Add a docstring** with Args and Returns
4. **Use try/except** with sensible defaults (empty list, None, False)
5. **Import it in the page** that needs it: `from db_service import db_new_function`
6. **Never** put raw `.table()` calls in page files

### db_service.py Sections

| Section | Functions | Purpose |
|---------|-----------|---------|
| Connection | `get_db`, `db_is_connected`, `reset_db_connection`, `db_test_connection` | Supabase client management |
| Contacts | `db_get_contacts`, `db_get_contact`, `db_create_contact`, `db_update_contact`, `db_delete_contact`, `db_archive_contact`, `db_unarchive_contact`, `db_get_archived_contacts`, `db_check_contact_exists`, `db_check_contacts_by_company`, `db_find_duplicate_contact`, `db_find_potential_duplicates`, `db_find_potential_duplicates_by_card`, `db_merge_contacts`, `db_update_contact_type`, `db_get_contact_email` | All contact CRUD + dedup + merge |
| Deals / Pipeline | `db_get_deals`, `db_create_deal`, `db_update_deal`, `db_update_deal_stage`, `db_delete_deal`, `db_get_deal_tasks`, `db_add_deal_task`, `db_toggle_deal_task` | Pipeline management |
| Discovery / Intakes | `db_get_intakes`, `db_get_intake`, `db_create_intake`, `db_update_intake` | Client discovery forms |
| Activities | `db_get_activities`, `db_log_activity`, `db_get_contact_email_sends`, `db_get_contact_activities` | Activity tracking |
| Tasks | `db_get_tasks` | Task queries |
| Time & Billing | `db_get_time_entries`, `db_create_time_entry`, `db_get_invoices`, `db_update_invoice`, `db_create_invoice`, `db_get_projects` | Time tracking and invoicing |
| Marketing | `db_create_enrollment` | Campaign management |
| Business Cards | `upload_card_image_to_supabase`, `db_list_card_images`, `db_get_card_image_url`, `db_get_unprocessed_cards` | Card scanning storage |
| Dashboard | `db_get_dashboard_stats` | Aggregated stats |
| Settings | `db_export_all_tables` | Data export |

---

*Document maintained by Claude Code for Metro Point Technology*
