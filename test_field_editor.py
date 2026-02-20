#!/usr/bin/env python3
"""
Test the E-Signature Field Editor integration
"""

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="E-Signature Field Editor Test",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 E-Signature Field Editor Test")

# Test the embedded field editor
st.markdown("### Testing PDF Field Editor Integration")

# Simple embedded HTML test
test_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Field Editor Test</title>
    
    <!-- PDF.js CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.min.js"></script>
    
    <!-- Fabric.js CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.0/fabric.min.js"></script>
    
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            display: flex;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .controls {
            width: 200px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .viewer {
            flex: 1;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .field-btn {
            background: #3498db;
            color: white;
        }
        .field-btn:hover {
            background: #2980b9;
        }
        .field-btn.active {
            background: #e74c3c;
        }
        #pdfCanvas, #annotationCanvas {
            border: 1px solid #ddd;
            max-width: 100%;
        }
        .canvas-container {
            position: relative;
            display: inline-block;
        }
        #annotationCanvas {
            position: absolute;
            top: 0;
            left: 0;
            z-index: 10;
        }
        .status {
            margin: 10px 0;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 4px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="controls">
            <h3>Field Types</h3>
            <button class="field-btn" onclick="selectField('signature')">✍️ Signature</button>
            <button class="field-btn" onclick="selectField('initials')">🔤 Initials</button>
            <button class="field-btn" onclick="selectField('date')">📅 Date</button>
            <button class="field-btn" onclick="selectField('text')">📝 Text</button>
            
            <div class="status">
                <strong>Selected:</strong> <span id="selectedType">None</span>
            </div>
            
            <input type="file" id="pdfFile" accept=".pdf" onchange="loadPDF()" style="margin: 10px 0;">
            <button onclick="clearFields()" style="background: #e74c3c; color: white;">Clear Fields</button>
        </div>
        
        <div class="viewer">
            <h3>PDF Viewer</h3>
            <div id="status">Ready - Please load a PDF</div>
            
            <div class="canvas-container">
                <canvas id="pdfCanvas"></canvas>
                <canvas id="annotationCanvas"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let pdfDoc = null;
        let canvas = null;
        let fabricCanvas = null;
        let selectedFieldType = null;
        
        // Set PDF.js worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.js';
        
        function init() {
            canvas = document.getElementById('pdfCanvas');
            
            // Initialize Fabric.js canvas
            fabricCanvas = new fabric.Canvas('annotationCanvas', {
                selection: true
            });
            
            // Handle clicks for field placement
            fabricCanvas.on('mouse:down', function(event) {
                if (selectedFieldType && !event.target) {
                    const pointer = fabricCanvas.getPointer(event.e);
                    placeField(pointer.x, pointer.y, selectedFieldType);
                }
            });
            
            updateStatus('Initialized - Ready to load PDF');
        }
        
        function selectField(type) {
            selectedFieldType = type;
            
            // Update button states
            document.querySelectorAll('.field-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            document.getElementById('selectedType').textContent = type;
            updateStatus('Selected field type: ' + type);
        }
        
        async function loadPDF() {
            const file = document.getElementById('pdfFile').files[0];
            if (!file) return;
            
            updateStatus('Loading PDF...');
            
            try {
                const arrayBuffer = await file.arrayBuffer();
                pdfDoc = await pdfjsLib.getDocument({data: arrayBuffer}).promise;
                
                updateStatus('PDF loaded, rendering page 1...');
                await renderPage(1);
                
            } catch (error) {
                updateStatus('Error loading PDF: ' + error.message);
            }
        }
        
        async function renderPage(pageNum) {
            if (!pdfDoc) return;
            
            try {
                const page = await pdfDoc.getPage(pageNum);
                const viewport = page.getViewport({scale: 1.5});
                
                // Set canvas dimensions
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                
                // Update Fabric canvas to match
                fabricCanvas.setDimensions({
                    width: viewport.width,
                    height: viewport.height
                });
                
                // Render PDF page
                const context = canvas.getContext('2d');
                await page.render({
                    canvasContext: context,
                    viewport: viewport
                }).promise;
                
                updateStatus('Page rendered successfully');
                
            } catch (error) {
                updateStatus('Error rendering page: ' + error.message);
            }
        }
        
        function placeField(x, y, type) {
            const colors = {
                signature: '#e74c3c',
                initials: '#3498db', 
                date: '#27ae60',
                text: '#f39c12'
            };
            
            const sizes = {
                signature: {width: 200, height: 60},
                initials: {width: 80, height: 60},
                date: {width: 120, height: 30},
                text: {width: 180, height: 30}
            };
            
            const size = sizes[type];
            const color = colors[type];
            
            const rect = new fabric.Rect({
                left: x - size.width/2,
                top: y - size.height/2,
                width: size.width,
                height: size.height,
                fill: color + '40', // Add transparency
                stroke: color,
                strokeWidth: 2,
                cornerStyle: 'circle'
            });
            
            const text = new fabric.Text(type.toUpperCase(), {
                left: x - size.width/2 + 5,
                top: y - size.height/2 + 5,
                fontSize: 12,
                fill: '#333',
                selectable: false
            });
            
            const group = new fabric.Group([rect, text], {
                fieldType: type
            });
            
            fabricCanvas.add(group);
            fabricCanvas.setActiveObject(group);
            
            updateStatus('Placed ' + type + ' field');
        }
        
        function clearFields() {
            if (fabricCanvas) {
                fabricCanvas.clear();
                updateStatus('All fields cleared');
            }
        }
        
        function updateStatus(message) {
            document.getElementById('status').textContent = message;
            console.log(message);
        }
        
        // Initialize when loaded
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
"""

# Display the test field editor
components.html(test_html, height=600, scrolling=True)

st.markdown("""
**Test Instructions:**
1. Click "Choose File" to upload a PDF
2. Select a field type (Signature, Initials, Date, Text) 
3. Click on the PDF to place fields
4. Use "Clear Fields" to remove all placed fields

This is a simplified test version of the field editor.
""")

# Test file upload
st.markdown("### Test with Sample PDFs")
if st.button("Create Sample PDFs"):
    import subprocess
    import os
    
    try:
        # Run the PDF creation script
        subprocess.run(["python", "create_test_pdf.py"], check=True)
        st.success("✅ Sample PDFs created: test_contract.pdf and simple_test.pdf")
        st.info("You can now upload these PDFs to test the field editor above.")
    except Exception as e:
        st.error(f"Error creating sample PDFs: {e}")

# Display current files
st.markdown("### Available Test Files")
test_files = []
for filename in ["test_contract.pdf", "simple_test.pdf"]:
    if os.path.exists(filename):
        test_files.append(filename)

if test_files:
    st.success(f"Found test files: {', '.join(test_files)}")
else:
    st.info("No test PDFs found. Click 'Create Sample PDFs' to generate them.")