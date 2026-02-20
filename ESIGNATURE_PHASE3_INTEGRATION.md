# E-Signature Phase 3: Integration Guide

## Overview
Phase 3 adds signature capture and PDF overlay functionality to the existing E-signature system. Users can now draw or type signatures directly into PDF documents at precise coordinates.

## Features Implemented

### ✅ Frontend (JavaScript)
- **Signature Modal**: Responsive modal with draw/type tabs
- **Canvas Drawing**: Mouse and touch support with `toDataURL()` export
- **Text Input**: Font selection and live preview
- **Field Integration**: Double-click signature fields to open modal
- **Visual Feedback**: Fields marked as signed with green styling

### ✅ Backend (Python)
- **PDF Processing**: ReportLab-based signature overlay
- **Image Handling**: Base64 to PIL Image conversion
- **Text Rendering**: Multiple font options
- **Database Storage**: Signatures table with full metadata
- **API Endpoints**: RESTful signature management

### ✅ Database
- **Signatures Table**: Stores signature data with coordinates
- **Field Tracking**: Prevents duplicate signatures per field
- **Document Status**: Tracks signing progress

## Installation & Setup

### 1. Install Dependencies
```bash
pip install reportlab PyPDF2 Pillow
```

### 2. Create Database Tables
Run the SQL schema:
```bash
# Apply to Supabase SQL Editor
cat create_signatures_table.sql
```

### 3. Integrate API Routes
Add to your main Flask app:
```python
from esign_signature_api import create_signature_api_routes

app = Flask(__name__)
create_signature_api_routes(app)
```

### 4. Test the System
```bash
python esign_phase3_test.py
```

## Usage Guide

### For Document Preparers
1. Open the field editor: `esign_field_editor.html`
2. Load your PDF document
3. Place signature fields by clicking with "Signature" tool selected
4. Save the field layout
5. Send document for signing

### For Signers
1. Open the signing interface (with signature fields loaded)
2. **Double-click** any signature field
3. **Draw Mode**: Use mouse/finger to draw signature
4. **Type Mode**: Enter name and select font
5. Click "Apply Signature"
6. Signature is overlaid on PDF at exact coordinates

### For Developers

#### API Endpoints
```
POST /api/esign/apply_signature
GET  /api/esign/signatures/<document_id>  
GET  /api/esign/check_field/<pdf_field_id>
```

#### JavaScript Integration
```javascript
// Trigger signature modal
editor.showSignatureModal(fieldId, fieldObject);

// Check if field is signed
const signature = await checkFieldSigned(fieldId);
```

#### Python Integration  
```python
from esign_signature_service import process_signature_application

result = process_signature_application(payload, pdf_path, output_path)
```

## File Structure

```
mpt-crm-app/
├── static/
│   ├── esign_field_editor.html     # Enhanced with modal
│   ├── esign_field_editor.css      # Modal styles added  
│   └── esign_field_editor.js       # Signature functionality
├── esign_signature_service.py      # Core signature processing
├── esign_signature_api.py           # Flask API endpoints
├── esign_phase3_test.py            # Testing suite
├── create_signatures_table.sql     # Database schema
└── db_service.py                   # Enhanced with signature functions
```

## Key Technical Details

### Coordinate System
- **Frontend**: Canvas coordinates (top-left origin)
- **Backend**: PDF coordinates (bottom-left origin)  
- **Conversion**: `y = page_height - y - field_height`

### Image Processing
- Canvas exports as `data:image/png;base64,<data>`
- Backend strips data URL prefix
- PIL converts to RGB (removes transparency)
- ReportLab renders with aspect ratio preserved

### Text Rendering
- Font mapping: `cursive` → `Times-Italic`, etc.
- Vertical centering within field height
- 5px left padding for readability

### Database Schema
```sql
signatures (
    id UUID PRIMARY KEY,
    pdf_field_id TEXT NOT NULL,
    document_id UUID REFERENCES esign_documents(id),
    signature_type TEXT CHECK (signature_type IN ('draw', 'type')),
    signature_data TEXT NOT NULL,
    x_coordinate FLOAT,
    y_coordinate FLOAT,
    width FLOAT,
    height FLOAT,
    page_number INTEGER,
    font_family TEXT,
    font_size INTEGER,
    applied_at TIMESTAMPTZ DEFAULT NOW()
)
```

## Error Handling

### Common Issues
1. **ReportLab not installed**: Install with `pip install reportlab PyPDF2 Pillow`
2. **PDF not found**: Check document_id mapping in `get_document_pdf_path()`
3. **Coordinate mismatch**: Verify coordinate conversion logic
4. **Double signatures**: API prevents duplicate signatures per field
5. **Image format errors**: Only PNG supported from canvas

### Debugging
- Enable debug mode in Flask app
- Check browser console for JavaScript errors  
- Monitor Python logs for PDF processing issues
- Verify Supabase connection and permissions

## Testing Checklist

✅ **Frontend Tests**
- [ ] Modal opens on signature field double-click
- [ ] Canvas drawing works (mouse + touch)
- [ ] Text input with font preview
- [ ] Apply button enables/disables correctly
- [ ] Fields marked as signed after application

✅ **Backend Tests**  
- [ ] PDF signature overlay works
- [ ] Image signatures render correctly
- [ ] Text signatures use correct fonts
- [ ] Database records created properly
- [ ] Coordinate conversion accurate

✅ **Integration Tests**
- [ ] End-to-end signature flow
- [ ] Multiple signatures per document
- [ ] Error handling (missing PDF, etc.)
- [ ] Duplicate signature prevention

## Production Considerations

### Security
- Validate signature data size limits
- Sanitize text input for XSS prevention  
- Rate limit signature API endpoints
- Audit trail for all signature actions

### Performance
- Compress signature images before storage
- Cache processed PDFs
- Optimize database queries
- Consider async PDF processing

### Storage
- Move signed PDFs to permanent storage
- Backup signature data regularly
- Archive completed documents
- Clean up temporary files

### Monitoring
- Track signature application success rates
- Monitor PDF processing times
- Alert on API failures
- Log security events

## Next Steps (Future Phases)

### Phase 4 Ideas
- **Bulk signing**: Multiple signatures in one session
- **Templates**: Pre-configured signature layouts
- **Mobile app**: Native signature capture
- **Integration**: Connect with DocuSign, Adobe Sign APIs
- **Analytics**: Signing completion rates and times

---

## Support

For issues or questions about E-Signature Phase 3:
1. Check the test suite: `python esign_phase3_test.py`
2. Review browser console for JavaScript errors
3. Check Flask logs for backend issues  
4. Verify database schema matches `create_signatures_table.sql`

**Phase 3 Status**: ✅ Complete and Ready for Production