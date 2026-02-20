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

        document.getElementById('preview-fields').addEventListener('click', () => {
            this.previewFields();
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
        
        // Here you would typically send this data to your backend
        // For now, we'll store it in localStorage as a demo
        localStorage.setItem('esign_field_layout', JSON.stringify(layoutData));
        
        alert(`Field layout saved! Found ${this.fields.length} fields across ${this.totalPages} pages.`);
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
}

// Initialize the editor when DOM is loaded
let editor;
document.addEventListener('DOMContentLoaded', () => {
    editor = new ESignatureFieldEditor();
});

// Expose to global scope for external access
window.ESignatureFieldEditor = ESignatureFieldEditor;