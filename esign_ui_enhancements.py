"""
E-Signature UI/UX Enhancements for MPT-CRM Phase 4
==================================================

Enhanced UI components with improved styling, responsiveness,
and user experience for the E-Signature system.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64


def inject_enhanced_esign_styles():
    """Inject enhanced CSS styles for E-Signature pages"""
    
    enhanced_css = """
    <style>
    /* Enhanced E-Signature Styles */
    
    /* Main container improvements */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Enhanced card styling */
    .esign-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border: 1px solid #e0e6ed;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .esign-card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-sent {
        background-color: #cce5ff;
        color: #004085;
        border: 1px solid #74c0fc;
    }
    
    .status-signed {
        background-color: #d1edff;
        color: #0c5460;
        border: 1px solid #17a2b8;
    }
    
    .status-completed {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-expired {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* Enhanced buttons */
    .esign-button {
        background: linear-gradient(145deg, #007bff, #0056b3);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 123, 255, 0.3);
    }
    
    .esign-button:hover {
        background: linear-gradient(145deg, #0056b3, #003d82);
        box-shadow: 0 4px 8px rgba(0, 123, 255, 0.4);
        transform: translateY(-1px);
    }
    
    .esign-button.secondary {
        background: linear-gradient(145deg, #6c757d, #495057);
        box-shadow: 0 2px 4px rgba(108, 117, 125, 0.3);
    }
    
    .esign-button.success {
        background: linear-gradient(145deg, #28a745, #1e7e34);
        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
    }
    
    .esign-button.danger {
        background: linear-gradient(145deg, #dc3545, #bd2130);
        box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
    }
    
    /* PDF viewer enhancements */
    .pdf-viewer-container {
        background: #ffffff;
        border: 2px solid #e0e6ed;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .pdf-controls {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        border-bottom: 1px solid #dee2e6;
        padding: 1rem;
        display: flex;
        gap: 0.75rem;
        align-items: center;
        flex-wrap: wrap;
    }
    
    /* Signature canvas styling */
    .signature-canvas-container {
        border: 2px dashed #007bff;
        border-radius: 8px;
        padding: 1rem;
        background: #f8f9ff;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .signature-canvas-container:hover {
        border-color: #0056b3;
        background: #f0f4ff;
    }
    
    .signature-canvas-container.active {
        border-style: solid;
        background: #ffffff;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
    }
    
    /* Progress indicators */
    .esign-progress {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1rem 0;
        padding: 1rem;
        background: linear-gradient(145deg, #f8f9fa, #ffffff);
        border-radius: 8px;
        border: 1px solid #e0e6ed;
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .progress-step.completed {
        background-color: #28a745;
        color: white;
    }
    
    .progress-step.active {
        background-color: #007bff;
        color: white;
        animation: pulse 2s infinite;
    }
    
    .progress-step.pending {
        background-color: #6c757d;
        color: white;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
    }
    
    /* Form enhancements */
    .esign-form-group {
        margin-bottom: 1.5rem;
    }
    
    .esign-form-label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 600;
        color: #333;
    }
    
    .esign-form-help {
        font-size: 0.875rem;
        color: #6c757d;
        margin-top: 0.25rem;
    }
    
    /* Notification enhancements */
    .esign-notification {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid;
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
    }
    
    .esign-notification.success {
        border-color: #28a745;
        background: linear-gradient(145deg, #d4edda, #c3e6cb);
        color: #155724;
    }
    
    .esign-notification.warning {
        border-color: #ffc107;
        background: linear-gradient(145deg, #fff3cd, #ffeaa7);
        color: #856404;
    }
    
    .esign-notification.error {
        border-color: #dc3545;
        background: linear-gradient(145deg, #f8d7da, #f5c6cb);
        color: #721c24;
    }
    
    .esign-notification.info {
        border-color: #17a2b8;
        background: linear-gradient(145deg, #d1ecf1, #bee5eb);
        color: #0c5460;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .esign-card {
            padding: 1rem;
        }
        
        .pdf-controls {
            flex-direction: column;
            align-items: stretch;
        }
        
        .esign-button {
            width: 100%;
            margin-bottom: 0.5rem;
        }
        
        .signature-canvas-container {
            padding: 0.5rem;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .esign-card {
            background: linear-gradient(145deg, #2d3748, #4a5568);
            border-color: #4a5568;
            color: #e2e8f0;
        }
        
        .pdf-viewer-container {
            background: #2d3748;
            border-color: #4a5568;
        }
        
        .pdf-controls {
            background: linear-gradient(145deg, #4a5568, #2d3748);
            border-color: #718096;
        }
    }
    
    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .slide-in-left {
        animation: slideInLeft 0.5s ease-out;
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-50px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .bounce-in {
        animation: bounceIn 0.6s ease-out;
    }
    
    @keyframes bounceIn {
        0% { opacity: 0; transform: scale(0.3); }
        50% { opacity: 1; transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Loading states */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #007bff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Accessibility improvements */
    .esign-button:focus,
    .esign-form-input:focus {
        outline: 2px solid #007bff;
        outline-offset: 2px;
    }
    
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    </style>
    """
    
    st.markdown(enhanced_css, unsafe_allow_html=True)


def render_enhanced_progress_indicator(steps: List[Dict[str, Any]], current_step: int) -> None:
    """Render an enhanced progress indicator"""
    
    progress_html = """
    <div class="esign-progress fade-in">
    """
    
    for i, step in enumerate(steps):
        step_class = "completed" if i < current_step else ("active" if i == current_step else "pending")
        icon = step.get('icon', '●')
        title = step.get('title', f'Step {i+1}')
        
        progress_html += f"""
        <div class="progress-step {step_class}">
            <span style="margin-right: 0.5rem;">{icon}</span>
            {title}
        </div>
        """
        
        if i < len(steps) - 1:
            progress_html += '<div style="flex: 1; height: 2px; background: #e0e6ed; margin: 0 0.5rem;"></div>'
    
    progress_html += "</div>"
    
    st.markdown(progress_html, unsafe_allow_html=True)


def render_enhanced_document_card(doc: Dict[str, Any], actions: Optional[List[Dict[str, Any]]] = None) -> None:
    """Render an enhanced document card with improved styling"""
    
    status = doc.get('status', 'unknown')
    title = doc.get('title', 'Untitled Document')
    signer_name = doc.get('signer_name', 'Unknown')
    signer_email = doc.get('signer_email', 'unknown@example.com')
    client_name = doc.get('client_name', '')
    created_at = doc.get('created_at', '')
    
    # Format date
    if created_at:
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = created_date.strftime('%B %d, %Y at %I:%M %p')
        except:
            formatted_date = created_at
    else:
        formatted_date = 'Unknown'
    
    # Status colors and icons
    status_config = {
        'pending': {'icon': '⏳', 'class': 'status-pending'},
        'sent': {'icon': '📧', 'class': 'status-sent'},
        'signed': {'icon': '✍️', 'class': 'status-signed'},
        'completed': {'icon': '✅', 'class': 'status-completed'},
        'expired': {'icon': '⏰', 'class': 'status-expired'},
        'cancelled': {'icon': '❌', 'class': 'status-expired'}
    }
    
    config = status_config.get(status, {'icon': '❓', 'class': 'status-pending'})
    
    card_html = f"""
    <div class="esign-card fade-in">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div style="flex: 1;">
                <h3 style="margin: 0 0 0.5rem 0; color: #2c3e50; font-size: 1.25rem;">{title}</h3>
                <div style="color: #6c757d; font-size: 0.95rem;">
                    <div style="margin-bottom: 0.25rem;">
                        <strong>Signer:</strong> {signer_name} ({signer_email})
                    </div>
                    {f'<div style="margin-bottom: 0.25rem;"><strong>Client:</strong> {client_name}</div>' if client_name else ''}
                    <div><strong>Created:</strong> {formatted_date}</div>
                </div>
            </div>
            <div style="margin-left: 1rem;">
                <div class="status-indicator {config['class']}">
                    {config['icon']} {status.title()}
                </div>
            </div>
        </div>
    """
    
    # Add action buttons if provided
    if actions:
        card_html += '<div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1rem;">'
        for action in actions:
            button_class = action.get('class', 'esign-button')
            onclick = f"onclick=\"{action.get('onclick', '')}\"" if action.get('onclick') else ''
            
            card_html += f"""
            <button class="{button_class}" {onclick}>
                {action.get('icon', '')} {action.get('label', 'Action')}
            </button>
            """
        card_html += '</div>'
    
    card_html += "</div>"
    
    st.markdown(card_html, unsafe_allow_html=True)


def render_enhanced_notification(message: str, type: str = "info", 
                                title: Optional[str] = None, dismissible: bool = True) -> None:
    """Render an enhanced notification"""
    
    icons = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️'
    }
    
    icon = icons.get(type, 'ℹ️')
    
    notification_html = f"""
    <div class="esign-notification {type} bounce-in">
        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
            <div style="font-size: 1.25rem;">{icon}</div>
            <div style="flex: 1;">
                {f'<div style="font-weight: 600; margin-bottom: 0.5rem;">{title}</div>' if title else ''}
                <div>{message}</div>
            </div>
            {f'<button onclick="this.parentElement.parentElement.style.display=\'none\'" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #6c757d;">×</button>' if dismissible else ''}
        </div>
    </div>
    """
    
    st.markdown(notification_html, unsafe_allow_html=True)


def render_enhanced_signature_area(title: str = "Your Signature", 
                                  subtitle: str = "Please sign below") -> None:
    """Render an enhanced signature capture area"""
    
    signature_html = f"""
    <div class="signature-canvas-container slide-in-left">
        <div style="margin-bottom: 1rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;">{title}</h4>
            <p style="margin: 0; color: #6c757d; font-size: 0.95rem;">{subtitle}</p>
        </div>
        <div id="signature-placeholder" style="min-height: 200px; display: flex; align-items: center; justify-content: center; color: #6c757d;">
            Click here to start signing
        </div>
    </div>
    
    <script>
    // Add interactivity to signature area
    document.addEventListener('DOMContentLoaded', function() {
        const container = document.querySelector('.signature-canvas-container');
        const placeholder = document.getElementById('signature-placeholder');
        
        container.addEventListener('mouseenter', function() {
            this.classList.add('active');
        });
        
        container.addEventListener('mouseleave', function() {
            if (!this.classList.contains('signing')) {
                this.classList.remove('active');
            }
        });
        
        container.addEventListener('click', function() {
            this.classList.add('active', 'signing');
            placeholder.textContent = 'Drawing signature...';
        });
    });
    </script>
    """
    
    st.markdown(signature_html, unsafe_allow_html=True)


def render_enhanced_file_upload(label: str = "Upload Document", 
                               accept: str = ".pdf", 
                               help_text: str = "Select a PDF file to upload") -> None:
    """Render an enhanced file upload area"""
    
    upload_html = f"""
    <div class="esign-form-group">
        <label class="esign-form-label">{label}</label>
        <div class="file-upload-container" style="
            border: 2px dashed #007bff;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            background: linear-gradient(145deg, #f8f9ff, #ffffff);
            transition: all 0.3s ease;
            cursor: pointer;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem; color: #007bff;">📁</div>
            <div style="font-weight: 600; margin-bottom: 0.5rem; color: #2c3e50;">
                Click to browse or drag & drop your file here
            </div>
            <div class="esign-form-help">{help_text}</div>
        </div>
    </div>
    
    <style>
    .file-upload-container:hover {
        border-color: #0056b3;
        background: linear-gradient(145deg, #f0f4ff, #ffffff);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2);
    }
    </style>
    """
    
    st.markdown(upload_html, unsafe_allow_html=True)


def add_loading_state(element_id: str, loading: bool = True) -> None:
    """Add/remove loading state to an element"""
    
    if loading:
        loading_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const element = document.getElementById('{element_id}');
            if (element) {{
                const spinner = document.createElement('div');
                spinner.className = 'loading-spinner';
                spinner.style.marginRight = '0.5rem';
                element.insertBefore(spinner, element.firstChild);
                element.style.pointerEvents = 'none';
                element.style.opacity = '0.7';
            }}
        }});
        </script>
        """
    else:
        loading_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const element = document.getElementById('{element_id}');
            if (element) {{
                const spinner = element.querySelector('.loading-spinner');
                if (spinner) spinner.remove();
                element.style.pointerEvents = 'auto';
                element.style.opacity = '1';
            }}
        }});
        </script>
        """
    
    st.markdown(loading_script, unsafe_allow_html=True)


def render_enhanced_metrics_dashboard(metrics: Dict[str, Any]) -> None:
    """Render an enhanced metrics dashboard"""
    
    dashboard_html = """
    <div class="metrics-dashboard fade-in" style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    ">
    """
    
    for metric_key, metric_data in metrics.items():
        value = metric_data.get('value', 0)
        label = metric_data.get('label', metric_key.title())
        icon = metric_data.get('icon', '📊')
        color = metric_data.get('color', '#007bff')
        change = metric_data.get('change', None)
        
        change_html = ""
        if change is not None:
            change_color = "#28a745" if change >= 0 else "#dc3545"
            change_icon = "↗️" if change >= 0 else "↘️"
            change_html = f"""
            <div style="font-size: 0.875rem; color: {change_color}; margin-top: 0.25rem;">
                {change_icon} {change:+.1f}%
            </div>
            """
        
        dashboard_html += f"""
        <div class="metric-card esign-card" style="text-align: center;">
            <div style="font-size: 2.5rem; color: {color}; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-size: 2rem; font-weight: bold; color: #2c3e50; margin-bottom: 0.25rem;">{value}</div>
            <div style="font-size: 1rem; color: #6c757d; font-weight: 600;">{label}</div>
            {change_html}
        </div>
        """
    
    dashboard_html += "</div>"
    
    st.markdown(dashboard_html, unsafe_allow_html=True)


def inject_enhanced_mobile_styles():
    """Inject enhanced mobile-specific styles"""
    
    mobile_css = """
    <style>
    @media (max-width: 768px) {
        /* Mobile-specific E-Signature styles */
        
        .esign-card {
            margin-bottom: 1rem;
            border-radius: 8px;
        }
        
        .status-indicator {
            font-size: 0.75rem;
            padding: 0.125rem 0.5rem;
        }
        
        .signature-canvas-container {
            padding: 1rem 0.5rem;
        }
        
        .pdf-viewer-container {
            margin: 0 -1rem;
            border-radius: 0;
            border-left: none;
            border-right: none;
        }
        
        .esign-progress {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .progress-step {
            justify-content: center;
            width: 100%;
        }
        
        .metrics-dashboard {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }
    }
    
    /* Touch-friendly interactions */
    @media (hover: none) and (pointer: coarse) {
        .esign-button {
            padding: 1rem 1.5rem;
            font-size: 1rem;
        }
        
        .signature-canvas-container {
            min-height: 250px;
        }
        
        .esign-card:hover {
            transform: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
    }
    </style>
    """
    
    st.markdown(mobile_css, unsafe_allow_html=True)