// E-Signature Field Editor JavaScript
// Handles PDF rendering, field placement, and document preparation

class ESignatureFieldEditor {
    constructor() {
        this.pdfDoc = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.canvas = null;
        this.ctx = null;
        this.fabricCanvas = null;
        this.fields = [];
        this.selectedFieldType = null;
        this.scale = 1;
        
        // Phase 2: Document and template management
        this.currentDocumentId = null;
        this.currentLayoutId = null;
        this.templates = [];
        
        this.init();
    }

    async init() {
        // Set PDF.js worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.js';
        
        // Initialize DOM elements
        this.canvas = document.getElementById('pdf-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.loadingOverlay = document.getElementById('loading-overlay');
        
        // Initialize Fabric.js canvas
        this.initFabricCanvas();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Default field type
        window.selectedFieldType = 'signature';
        this.selectFieldType('signature');
        
        // Phase 2: Load templates on startup
        this.loadTemplates();
        
        console.log('E-Signature Field Editor initialized');
    }

    initFabricCanvas() {
        // Initialize Fabric.js canvas for annotations
        this.fabricCanvas = new fabric.Canvas('annotation-canvas', {
            isDrawingMode: false,
            selection: false,
            backgroundColor: 'transparent'
        });

        // Handle click-to-place field functionality
        this.fabricCanvas.on('mouse:down', (event) => {
            if (this.selectedFieldType && event.pointer) {
                this.placeField(event.pointer.x, event.pointer.y, this.selectedFieldType);
            }
        });

        // Handle field selection
        this.fabricCanvas.on('selection:created', (event) => {
            this.updateFieldList();
        });

        this.fabricCanvas.on('selection:updated', (event) => {
            this.updateFieldList();
        });
    }

    setupEventListeners() {
        // Field palette buttons
        document.querySelectorAll('.field-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const fieldType = e.target.dataset.fieldType;
                this.selectFieldType(fieldType);
            });
        });

        // Clear all button
        document.getElementById('clear-all-btn').addEventListener('click', () => {
            this.clearAllFields();
        });

        // Page navigation
        document.getElementById('prev-page').addEventListener('click', () => {
            this.previousPage();
        });

        document.getElementById('next-page').addEventListener('click', () => {
            this.nextPage();
        });

        // Action buttons
        document.getElementById('save-fields').addEventListener('click', () => {
            this.saveFieldLayout();
        });
        
        document.getElementById('load-fields').addEventListener('click', () => {
            this.loadFieldLayout();
        });

        document.getElementById('preview-fields').addEventListener('click', () => {
            this.previewFields();
        });
        
        // Phase 2: Template management
        document.getElementById('save-as-template').addEventListener('click', () => {
            this.saveAsTemplate();
        });
        
        document.getElementById('template-name').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.saveAsTemplate();
            }
        });

        // File input for PDF upload (hidden)
        document.getElementById('pdf-file-input').addEventListener('change', (e) => {
            if (e.target.files[0]) {
                this.loadPDF(e.target.files[0]);
            }
        });
    }

    selectFieldType(fieldType) {
        // Update selected field type
        this.selectedFieldType = fieldType;
        window.selectedFieldType = fieldType;
        
        // Update button states
        document.querySelectorAll('.field-button').forEach(button => {
            button.classList.remove('active');
        });
        
        document.querySelector(`[data-field-type="${fieldType}"]`).classList.add('active');
        
        // Update cursor style
        this.fabricCanvas.defaultCursor = 'crosshair';
        
        console.log(`Selected field type: ${fieldType}`);
    }

    placeField(x, y, fieldType) {
        const fieldColors = {
            signature: '#ff6b6b',
            initials: '#4ecdc4',
            date: '#45b7d1',
            text: '#96ceb4'
        };

        const fieldLabels = {
            signature: 'SIGNATURE',
            initials: 'INITIALS',
            date: 'DATE',
            text: 'TEXT FIELD'
        };

        // Create field rectangle
        const field = new fabric.Rect({
            left: x - 60,
            top: y - 15,
            width: 120,
            height: 30,
            fill: fieldColors[fieldType] + '40', // Semi-transparent
            stroke: fieldColors[fieldType],
            strokeWidth: 2,
            rx: 4,
            ry: 4,
            selectable: true,
            moveable: true
        });

        // Add field label text
        const label = new fabric.Text(fieldLabels[fieldType], {
            left: x - 50,
            top: y - 8,
            fontSize: 12,
            fontFamily: 'Arial',
            fill: fieldColors[fieldType],
            selectable: false,
            evented: false
        });

        // Group field and label together
        const fieldGroup = new fabric.Group([field, label], {
            left: x - 60,
            top: y - 15,
            selectable: true,
            moveable: true,
            fieldType: fieldType,
            fieldId: this.generateFieldId(),
            page: this.currentPage
        });

        // Add to canvas
        this.fabricCanvas.add(fieldGroup);
        
        // Add to fields array
        this.fields.push({
            id: fieldGroup.fieldId,
            type: fieldType,
            page: this.currentPage,
            x: x,
            y: y,
            object: fieldGroup
        });

        this.updateFieldList();
        console.log(`Placed ${fieldType} field at (${x}, ${y}) on page ${this.currentPage}`);
    }

    generateFieldId() {
        return 'field_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    clearAllFields() {
        // Remove all field objects from canvas
        const objects = this.fabricCanvas.getObjects();
        objects.forEach(obj => {
            if (obj.fieldType) {
                this.fabricCanvas.remove(obj);
            }
        });

        // Clear fields array
        this.fields = [];
        
        this.updateFieldList();
        console.log('All fields cleared');
    }

    updateFieldList() {
        const fieldItems = document.getElementById('field-items');
        
        if (this.fields.length === 0) {
            fieldItems.innerHTML = '<p class="no-fields">No fields placed yet</p>';
            return;
        }

        const fieldsHtml = this.fields.map((field, index) => `
            <div class="field-item" data-field-id="${field.id}">
                <span class="field-type">${field.type.toUpperCase()}</span>
                <span class="field-page">Page ${field.page}</span>
                <button class="remove-field-btn" onclick="editor.removeField('${field.id}')">×</button>
            </div>
        `).join('');

        fieldItems.innerHTML = fieldsHtml;
    }

    removeField(fieldId) {
        // Find and remove from canvas
        const fieldIndex = this.fields.findIndex(f => f.id === fieldId);
        if (fieldIndex !== -1) {
            this.fabricCanvas.remove(this.fields[fieldIndex].object);
            this.fields.splice(fieldIndex, 1);
            this.updateFieldList();
        }
    }

    async loadPDF(file) {
        try {
            this.showLoading(true);
            
            const arrayBuffer = await file.arrayBuffer();
            this.pdfDoc = await pdfjsLib.getDocument(arrayBuffer).promise;
            this.totalPages = this.pdfDoc.numPages;
            this.currentPage = 1;
            
            await this.queueRenderPage(this.currentPage);
            this.updatePageNavigation();
            
            console.log(`PDF loaded: ${this.totalPages} pages`);
        } catch (error) {
            console.error('Error loading PDF:', error);
            alert('Error loading PDF file');
        } finally {
            this.showLoading(false);
        }
    }

    async queueRenderPage(pageNumber) {
        if (!this.pdfDoc || pageNumber < 1 || pageNumber > this.totalPages) {
            return;
        }

        try {
            this.showLoading(true);
            
            const page = await this.pdfDoc.getPage(pageNumber);
            const viewport = page.getViewport({ scale: this.scale });
            
            // Update canvas dimensions
            this.canvas.width = viewport.width;
            this.canvas.height = viewport.height;
            this.fabricCanvas.setDimensions({
                width: viewport.width,
                height: viewport.height
            });
            
            // Clear previous render
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            // Render PDF page
            await page.render({
                canvasContext: this.ctx,
                viewport: viewport
            }).promise;
            
            // Show/hide fields for current page
            this.updateFieldVisibility();
            
            console.log(`Rendered page ${pageNumber}`);
        } catch (error) {
            console.error('Error rendering page:', error);
        } finally {
            this.showLoading(false);
        }
    }

    updateFieldVisibility() {
        // Show only fields for current page
        this.fabricCanvas.getObjects().forEach(obj => {
            if (obj.fieldType) {
                obj.visible = obj.page === this.currentPage;
            }
        });
        this.fabricCanvas.renderAll();
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.queueRenderPage(this.currentPage);
            this.updatePageNavigation();
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.queueRenderPage(this.currentPage);
            this.updatePageNavigation();
        }
    }

    updatePageNavigation() {
        document.getElementById('prev-page').disabled = this.currentPage <= 1;
        document.getElementById('next-page').disabled = this.currentPage >= this.totalPages;
        document.getElementById('page-info').textContent = `Page ${this.currentPage} of ${this.totalPages}`;
    }

    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    saveFieldLayout() {
        const layoutData = {
            fields: this.fields.map(field => ({
                id: field.id,
                type: field.type,
                page: field.page,
                x: field.x,
                y: field.y,
                width: field.object.width,
                height: field.object.height
            })),
            totalPages: this.totalPages,
            timestamp: new Date().toISOString()
        };

        console.log('Field layout saved:', layoutData);
        
        // Phase 2: Save to database via Streamlit backend
        this.sendMessageToStreamlit({
            action: 'save_field_layout',
            data: layoutData,
            document_id: this.currentDocumentId
        });
    }

    previewFields() {
        const fieldCount = this.fields.length;
        const pageCount = this.totalPages;
        
        let summary = `Document Preview:\n\n`;
        summary += `• Total Pages: ${pageCount}\n`;
        summary += `• Total Fields: ${fieldCount}\n\n`;
        
        if (fieldCount > 0) {
            summary += `Fields by type:\n`;
            const fieldTypes = this.fields.reduce((acc, field) => {
                acc[field.type] = (acc[field.type] || 0) + 1;
                return acc;
            }, {});
            
            Object.entries(fieldTypes).forEach(([type, count]) => {
                summary += `• ${type.toUpperCase()}: ${count}\n`;
            });
        } else {
            summary += `No fields have been placed yet.`;
        }
        
        alert(summary);
    }

    // Public method to trigger PDF upload
    uploadPDF() {
        document.getElementById('pdf-file-input').click();
    }
    
    // =============================================================================
    // PHASE 2: DATABASE & TEMPLATE MANAGEMENT METHODS
    // =============================================================================
    
    sendMessageToStreamlit(message) {
        """Send message to Streamlit backend via postMessage"""
        console.log('Sending message to Streamlit:', message);
        
        // Store in session state for Streamlit to pick up
        if (window.parent && window.parent.postMessage) {
            window.parent.postMessage({
                type: 'field_editor_message',
                ...message
            }, '*');
        }
        
        // Also try setting directly if in same window
        if (window.streamlit_session_state) {
            window.streamlit_session_state.field_editor_message = message;
        }
    }
    
    async loadFieldLayout(documentId = null) {
        """Load field layout from database"""
        try {
            const message = {
                action: 'load_field_layout',
                document_id: documentId || this.currentDocumentId
            };
            
            this.sendMessageToStreamlit(message);
            
            // Wait for response (simplified - in real implementation, you'd use proper async handling)
            setTimeout(() => {
                this.checkForStreamlitResponse('load');
            }, 500);
            
        } catch (error) {
            console.error('Error loading field layout:', error);
            alert('Error loading field layout');
        }
    }
    
    async saveAsTemplate() {
        """Save current field layout as a reusable template"""
        const templateName = document.getElementById('template-name').value.trim();
        
        if (!templateName) {
            alert('Please enter a template name');
            return;
        }
        
        if (this.fields.length === 0) {
            alert('Please place some fields before saving as template');
            return;
        }
        
        const layoutData = {
            fields: this.fields.map(field => ({
                id: field.id,
                type: field.type,
                page: field.page,
                x: field.x,
                y: field.y,
                width: field.object.width,
                height: field.object.height
            })),
            totalPages: this.totalPages,
            timestamp: new Date().toISOString()
        };
        
        this.sendMessageToStreamlit({
            action: 'save_field_layout',
            data: layoutData,
            template_name: templateName
        });
        
        // Clear the input
        document.getElementById('template-name').value = '';
        
        // Refresh templates
        setTimeout(() => {
            this.loadTemplates();
        }, 1000);
    }
    
    async loadTemplates() {
        """Load available templates from database"""
        console.log('Loading templates...');
        
        this.sendMessageToStreamlit({
            action: 'get_templates'
        });
        
        // Wait for response
        setTimeout(() => {
            this.checkForStreamlitResponse('templates');
        }, 500);
    }
    
    checkForStreamlitResponse(type) {
        """Check if Streamlit has responded with data"""
        // This is a simplified approach - in a real implementation,
        // you'd use proper async communication or websockets
        
        if (window.streamlit_response) {
            const response = window.streamlit_response;
            
            if (type === 'load' && response.success) {
                this.applyLoadedLayout(response.data);
            } else if (type === 'templates' && response.success) {
                this.renderTemplates(response.templates);
            }
            
            // Clear response
            delete window.streamlit_response;
        }
    }
    
    applyLoadedLayout(layoutData) {
        """Apply loaded field layout to the editor"""
        try {
            // Clear existing fields
            this.clearAllFields();
            
            // Apply loaded fields
            if (layoutData.fields) {
                layoutData.fields.forEach(fieldData => {
                    this.restoreField(fieldData);
                });
            }
            
            this.updateFieldList();
            alert(`Field layout loaded! Applied ${layoutData.fields ? layoutData.fields.length : 0} fields.`);
            
        } catch (error) {
            console.error('Error applying loaded layout:', error);
            alert('Error applying loaded layout');
        }
    }
    
    restoreField(fieldData) {
        """Restore a field from saved data"""
        const fieldColors = {
            signature: '#ff6b6b',
            initials: '#4ecdc4',
            date: '#45b7d1',
            text: '#96ceb4'
        };

        const fieldLabels = {
            signature: 'SIGNATURE',
            initials: 'INITIALS',
            date: 'DATE',
            text: 'TEXT FIELD'
        };
        
        // Create field rectangle
        const field = new fabric.Rect({
            left: fieldData.x - 60,
            top: fieldData.y - 15,
            width: fieldData.width || 120,
            height: fieldData.height || 30,
            fill: fieldColors[fieldData.type] + '40',
            stroke: fieldColors[fieldData.type],
            strokeWidth: 2,
            rx: 4,
            ry: 4,
            selectable: true,
            moveable: true
        });

        // Add field label text
        const label = new fabric.Text(fieldLabels[fieldData.type], {
            left: fieldData.x - 50,
            top: fieldData.y - 8,
            fontSize: 12,
            fontFamily: 'Arial',
            fill: fieldColors[fieldData.type],
            selectable: false,
            evented: false
        });

        // Group field and label together
        const fieldGroup = new fabric.Group([field, label], {
            left: fieldData.x - 60,
            top: fieldData.y - 15,
            selectable: true,
            moveable: true,
            fieldType: fieldData.type,
            fieldId: fieldData.id,
            page: fieldData.page
        });

        // Add to canvas
        this.fabricCanvas.add(fieldGroup);
        
        // Add to fields array
        this.fields.push({
            id: fieldData.id,
            type: fieldData.type,
            page: fieldData.page,
            x: fieldData.x,
            y: fieldData.y,
            object: fieldGroup
        });
    }
    
    renderTemplates(templates) {
        """Render the list of available templates"""
        const templateList = document.getElementById('template-list');
        
        if (!templates || templates.length === 0) {
            templateList.innerHTML = '<p class="loading-templates">No templates saved yet</p>';
            return;
        }
        
        const templatesHtml = templates.map(template => `
            <div class="template-item">
                <div class="template-info">
                    <div class="template-name">${template.name}</div>
                    <div class="template-meta">${template.field_count} fields • ${this.formatDate(template.created_at)}</div>
                </div>
                <div class="template-actions">
                    <button class="template-load-btn" onclick="editor.loadTemplate('${template.name}')" title="Load Template">📂</button>
                    <button class="template-delete-btn" onclick="editor.deleteTemplate('${template.name}')" title="Delete Template">🗑️</button>
                </div>
            </div>
        `).join('');
        
        templateList.innerHTML = templatesHtml;
        this.templates = templates;
    }
    
    loadTemplate(templateName) {
        """Load a specific template"""
        if (this.fields.length > 0) {
            if (!confirm('This will replace your current field layout. Continue?')) {
                return;
            }
        }
        
        this.sendMessageToStreamlit({
            action: 'load_field_layout',
            template_name: templateName
        });
        
        setTimeout(() => {
            this.checkForStreamlitResponse('load');
        }, 500);
    }
    
    deleteTemplate(templateName) {
        """Delete a template"""
        if (confirm(`Are you sure you want to delete the template "${templateName}"?`)) {
            this.sendMessageToStreamlit({
                action: 'delete_template',
                template_name: templateName
            });
            
            // Refresh templates
            setTimeout(() => {
                this.loadTemplates();
            }, 1000);
        }
    }
    
    formatDate(dateString) {
        """Format date for display"""
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString();
        } catch (error) {
            return 'Unknown';
        }
    }
    
    setDocumentId(documentId) {
        """Set the current document ID for field association"""
        this.currentDocumentId = documentId;
        console.log('Document ID set:', documentId);
    }
}

// Initialize the editor when DOM is loaded
let editor;
document.addEventListener('DOMContentLoaded', () => {
    editor = new ESignatureFieldEditor();
});

// Expose to global scope for external access
window.ESignatureFieldEditor = ESignatureFieldEditor;