// E-Signature Field Editor JavaScript
// Implements PDF.js + Fabric.js integration for drag-drop field placement

// Global variables
let pdfDoc = null;
let pageNum = 1;
let pageCount = 0;
let scale = 1.5;
let canvas = null;
let context = null;
let fabricCanvas = null;
let isRendering = false;

// Field tracking
window.selectedFieldType = null;
let fieldCounter = {
    signature: 0,
    initials: 0,
    date: 0,
    text: 0
};

// Initialize the field editor
async function initializeFieldEditor() {
    console.log('Initializing E-Signature Field Editor...');
    
    try {
        // Get PDF.js library
        if (typeof pdfjsLib === 'undefined') {
            console.error('PDF.js library not loaded');
            showMessage('PDF.js library failed to load', 'error');
            return;
        }

        // Set PDF.js worker
        if (typeof pdfjsLib.GlobalWorkerOptions !== 'undefined') {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.js';
        }

        // Initialize canvases
        initializeCanvases();
        
        // Set up event listeners
        setupEventListeners();
        
        console.log('Field editor initialized successfully');
        showMessage('Field editor ready', 'success');
        
    } catch (error) {
        console.error('Error initializing field editor:', error);
        showMessage('Failed to initialize field editor', 'error');
    }
}

// Initialize PDF and Fabric.js canvases
function initializeCanvases() {
    // Get PDF canvas
    canvas = document.getElementById('pdfCanvas');
    context = canvas.getContext('2d');
    
    // Initialize Fabric.js canvas for annotations
    fabricCanvas = new fabric.Canvas('annotationCanvas', {
        selection: true,
        preserveObjectStacking: true
    });
    
    // Set initial canvas size
    const defaultWidth = 595; // A4 width at 72 DPI
    const defaultHeight = 842; // A4 height at 72 DPI
    
    canvas.width = defaultWidth;
    canvas.height = defaultHeight;
    
    fabricCanvas.setWidth(defaultWidth);
    fabricCanvas.setHeight(defaultHeight);
    
    // Handle canvas clicks for field placement
    fabricCanvas.on('mouse:down', function(event) {
        if (window.selectedFieldType && event.target === null) {
            // Only place field if clicking on empty area (not on existing object)
            const pointer = fabricCanvas.getPointer(event.e);
            placeField(pointer.x, pointer.y, window.selectedFieldType);
        }
    });
    
    // Handle object selection
    fabricCanvas.on('selection:created', function(event) {
        console.log('Object selected:', event.selected[0]);
    });
    
    // Make canvases responsive
    makeCanvasesResponsive();
}

// Make canvases responsive
function makeCanvasesResponsive() {
    const container = document.querySelector('.canvas-container');
    if (!container) return;
    
    // Adjust canvas position when container resizes
    const resizeObserver = new ResizeObserver(function(entries) {
        if (fabricCanvas) {
            fabricCanvas.calcOffset();
        }
    });
    
    resizeObserver.observe(container);
}

// Set up event listeners
function setupEventListeners() {
    // Page navigation
    document.getElementById('prevBtn').addEventListener('click', previousPage);
    document.getElementById('nextBtn').addEventListener('click', nextPage);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        switch(e.key) {
            case 'ArrowLeft':
                if (e.ctrlKey) {
                    e.preventDefault();
                    previousPage();
                }
                break;
            case 'ArrowRight':
                if (e.ctrlKey) {
                    e.preventDefault();
                    nextPage();
                }
                break;
            case 'Escape':
                deselectFieldType();
                break;
            case 'Delete':
                deleteSelectedField();
                break;
        }
    });
    
    // Window resize handler
    window.addEventListener('resize', function() {
        if (fabricCanvas) {
            fabricCanvas.calcOffset();
        }
    });
}

// Load PDF file
async function loadPDF() {
    const input = document.getElementById('pdfInput');
    const file = input.files[0];
    
    if (!file) {
        showMessage('Please select a PDF file', 'error');
        return;
    }
    
    if (file.type !== 'application/pdf') {
        showMessage('Please select a valid PDF file', 'error');
        return;
    }
    
    showMessage('Loading PDF...', 'info');
    
    try {
        const fileReader = new FileReader();
        fileReader.onload = async function() {
            const typedArray = new Uint8Array(this.result);
            
            // Load PDF document
            pdfDoc = await pdfjsLib.getDocument({
                data: typedArray,
                cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.0.379/cmaps/',
                cMapPacked: true
            }).promise;
            
            pageCount = pdfDoc.numPages;
            pageNum = 1;
            
            console.log(`PDF loaded: ${pageCount} pages`);
            showMessage(`PDF loaded successfully (${pageCount} pages)`, 'success');
            
            // Render first page
            await queueRenderPage(pageNum);
            
            // Update debug info
            updateDebugInfo();
            
            // Enable navigation buttons
            updateNavigationButtons();
            
        };
        fileReader.readAsArrayBuffer(file);
        
    } catch (error) {
        console.error('Error loading PDF:', error);
        showMessage('Failed to load PDF', 'error');
    }
}

// Queue page rendering (prevents multiple simultaneous renders)
async function queueRenderPage(num) {
    if (isRendering) {
        console.log('Already rendering, skipping...');
        return;
    }
    
    isRendering = true;
    
    try {
        await renderPage(num);
    } finally {
        isRendering = false;
    }
}

// Render PDF page
async function renderPage(num) {
    if (!pdfDoc) {
        console.log('No PDF document loaded');
        return;
    }
    
    console.log(`Rendering page ${num}`);
    
    try {
        // Get page
        const page = await pdfDoc.getPage(num);
        
        // Calculate viewport
        const viewport = page.getViewport({ scale: scale });
        
        // Set canvas dimensions
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        // Update Fabric.js canvas to match
        fabricCanvas.setDimensions({
            width: viewport.width,
            height: viewport.height
        });
        
        // Clear previous content
        context.clearRect(0, 0, canvas.width, canvas.height);
        
        // Render page
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        // Update page info
        document.getElementById('pageInfo').textContent = `Page ${pageNum} of ${pageCount}`;
        
        // Update debug info
        updateDebugInfo();
        
        console.log(`Page ${num} rendered successfully`);
        
    } catch (error) {
        console.error('Error rendering page:', error);
        showMessage('Failed to render page', 'error');
    }
}

// Field type selection
function selectFieldType(fieldType) {
    window.selectedFieldType = fieldType;
    
    // Update UI
    document.querySelectorAll('.field-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.querySelector(`[data-field-type="${fieldType}"]`).classList.add('active');
    
    // Update selected field display
    document.getElementById('selectedField').textContent = fieldType.charAt(0).toUpperCase() + fieldType.slice(1);
    
    // Change cursor style
    if (fabricCanvas) {
        fabricCanvas.defaultCursor = 'crosshair';
    }
    
    console.log(`Selected field type: ${fieldType}`);
}

// Deselect field type
function deselectFieldType() {
    window.selectedFieldType = null;
    
    // Update UI
    document.querySelectorAll('.field-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById('selectedField').textContent = 'None';
    
    // Reset cursor
    if (fabricCanvas) {
        fabricCanvas.defaultCursor = 'default';
    }
    
    console.log('Field type deselected');
}

// Place field on canvas
function placeField(x, y, fieldType) {
    if (!fabricCanvas || !fieldType) return;
    
    fieldCounter[fieldType]++;
    
    // Field dimensions based on type
    const fieldDimensions = {
        signature: { width: 200, height: 60 },
        initials: { width: 80, height: 60 },
        date: { width: 120, height: 30 },
        text: { width: 180, height: 30 }
    };
    
    const dim = fieldDimensions[fieldType];
    
    // Create rectangle with semi-transparent fill and black border
    const rect = new fabric.Rect({
        left: x - dim.width / 2,
        top: y - dim.height / 2,
        width: dim.width,
        height: dim.height,
        fill: getFieldFillColor(fieldType),
        stroke: getFieldStrokeColor(fieldType),
        strokeWidth: 2,
        cornerStyle: 'circle',
        cornerColor: '#666',
        cornerSize: 8,
        transparentCorners: false,
        hasRotatingPoint: false
    });
    
    // Add metadata to the field
    rect.set({
        fieldType: fieldType,
        fieldId: `${fieldType}_${fieldCounter[fieldType]}`,
        pageNumber: pageNum
    });
    
    // Add text label
    const label = new fabric.Text(`${fieldType.toUpperCase()} ${fieldCounter[fieldType]}`, {
        left: x - dim.width / 2 + 5,
        top: y - dim.height / 2 + 5,
        fontSize: 12,
        fill: '#333',
        selectable: false,
        evented: false,
        fontFamily: 'Arial, sans-serif'
    });
    
    // Group rectangle and label
    const group = new fabric.Group([rect, label], {
        fieldType: fieldType,
        fieldId: `${fieldType}_${fieldCounter[fieldType]}`,
        pageNumber: pageNum,
        selectable: true,
        hasControls: true
    });
    
    // Add to canvas
    fabricCanvas.add(group);
    fabricCanvas.setActiveObject(group);
    
    console.log(`Placed ${fieldType} field at (${x}, ${y})`);
    
    // Update debug info
    updateDebugInfo();
    
    // Auto-deselect after placing (optional)
    // deselectFieldType();
}

// Get field fill color
function getFieldFillColor(fieldType) {
    const colors = {
        signature: 'rgba(231, 76, 60, 0.3)',
        initials: 'rgba(52, 152, 219, 0.3)', 
        date: 'rgba(39, 174, 96, 0.3)',
        text: 'rgba(243, 156, 18, 0.3)'
    };
    return colors[fieldType] || 'rgba(128, 128, 128, 0.3)';
}

// Get field stroke color
function getFieldStrokeColor(fieldType) {
    const colors = {
        signature: '#e74c3c',
        initials: '#3498db',
        date: '#27ae60', 
        text: '#f39c12'
    };
    return colors[fieldType] || '#666';
}

// Delete selected field
function deleteSelectedField() {
    if (!fabricCanvas) return;
    
    const activeObject = fabricCanvas.getActiveObject();
    if (activeObject) {
        fabricCanvas.remove(activeObject);
        fabricCanvas.discardActiveObject();
        console.log('Deleted selected field');
        updateDebugInfo();
    }
}

// Clear all fields
function clearAllFields() {
    if (!fabricCanvas) return;
    
    const objects = fabricCanvas.getObjects();
    const fieldObjects = objects.filter(obj => obj.fieldType);
    
    fieldObjects.forEach(obj => {
        fabricCanvas.remove(obj);
    });
    
    // Reset counters
    fieldCounter = {
        signature: 0,
        initials: 0,
        date: 0,
        text: 0
    };
    
    console.log('Cleared all fields');
    showMessage('All fields cleared', 'info');
    updateDebugInfo();
}

// Export field data
function exportFieldData() {
    if (!fabricCanvas) return;
    
    const objects = fabricCanvas.getObjects();
    const fieldObjects = objects.filter(obj => obj.fieldType);
    
    const fieldData = fieldObjects.map(obj => ({
        id: obj.fieldId,
        type: obj.fieldType,
        page: obj.pageNumber || pageNum,
        position: {
            x: obj.left,
            y: obj.top,
            width: obj.width * (obj.scaleX || 1),
            height: obj.height * (obj.scaleY || 1)
        },
        created: new Date().toISOString()
    }));
    
    console.log('Field data:', fieldData);
    
    // Create download
    const dataStr = JSON.stringify(fieldData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `esign_fields_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    
    showMessage(`Exported ${fieldData.length} fields`, 'success');
}

// Page navigation functions
async function previousPage() {
    if (!pdfDoc || pageNum <= 1) return;
    
    pageNum--;
    await queueRenderPage(pageNum);
    updateNavigationButtons();
    console.log(`Navigated to page ${pageNum}`);
}

async function nextPage() {
    if (!pdfDoc || pageNum >= pageCount) return;
    
    pageNum++;
    await queueRenderPage(pageNum);
    updateNavigationButtons();
    console.log(`Navigated to page ${pageNum}`);
}

// Update navigation buttons state
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (prevBtn) prevBtn.disabled = (pageNum <= 1);
    if (nextBtn) nextBtn.disabled = (pageNum >= pageCount);
}

// Update debug information
function updateDebugInfo() {
    document.getElementById('debugPages').textContent = pageCount;
    document.getElementById('debugCurrentPage').textContent = pageNum;
    
    if (fabricCanvas) {
        const fieldCount = fabricCanvas.getObjects().filter(obj => obj.fieldType).length;
        document.getElementById('debugFields').textContent = fieldCount;
    }
}

// Show message to user
function showMessage(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    messageEl.textContent = message;
    
    // Add to DOM
    document.body.appendChild(messageEl);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (messageEl.parentNode) {
            messageEl.parentNode.removeChild(messageEl);
        }
    }, 3000);
}

// Toggle debug info visibility (for development)
function toggleDebugInfo() {
    const debugEl = document.getElementById('debugInfo');
    if (debugEl) {
        debugEl.style.display = debugEl.style.display === 'none' ? 'block' : 'none';
    }
}

// Export functions to global scope for HTML onclick handlers
window.initializeFieldEditor = initializeFieldEditor;
window.loadPDF = loadPDF;
window.selectFieldType = selectFieldType;
window.previousPage = previousPage;
window.nextPage = nextPage;
window.clearAllFields = clearAllFields;
window.exportFieldData = exportFieldData;
window.toggleDebugInfo = toggleDebugInfo;

// Initialize when script loads
console.log('E-Signature Field Editor JavaScript loaded');