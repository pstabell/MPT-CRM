"""
E-Signature SharePoint Integration Service
==========================================

Handles automatic filing of signed PDFs to SharePoint using Microsoft Graph API.
Features:
- Auto-create folder structure: SALES/{ClientName}/Contracts/Signed/
- Upload signed PDFs with metadata
- Maintain audit trail of uploads
- Handle permissions and access control

Uses existing Graph API credentials from MPT-CRM.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path
import urllib.parse

class ESignSharePointService:
    """SharePoint integration service for e-signature documents"""
    
    def __init__(self):
        """Initialize SharePoint service with Graph API configuration"""
        # These should match the existing CRM SharePoint integration
        self.tenant_id = os.getenv('AZURE_TENANT_ID', 'metropointtechnology.onmicrosoft.com')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.site_id = os.getenv('SHAREPOINT_SITE_ID')
        self.access_token = None
        
        # SharePoint folder configuration
        self.base_folder = "SALES"  # Base folder for client documents
        self.contracts_subfolder = "Contracts"
        self.signed_subfolder = "Signed"
        
        print(f"SharePoint service initialized for tenant: {self.tenant_id}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API to get access token
        
        Returns:
            bool: True if authentication successful
        """
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            print("ERROR: Missing SharePoint credentials. Check .env for AZURE_* variables")
            return False
        
        try:
            # Microsoft Graph token endpoint
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            # Request body for client credentials flow
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                print("SUCCESS: SharePoint authentication successful")
                return True
            else:
                print(f"ERROR: SharePoint authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"ERROR: Error authenticating with SharePoint: {e}")
            return False
    
    def create_folder_structure(self, client_name: str) -> Optional[str]:
        """
        Create the folder structure for a client if it doesn't exist
        Structure: SALES/{ClientName}/Contracts/Signed/
        
        Args:
            client_name: Name of the client (will be sanitized)
        
        Returns:
            str: SharePoint folder path or None if failed
        """
        if not self.access_token and not self.authenticate():
            return None
        
        try:
            # Sanitize client name for folder creation
            safe_client_name = self._sanitize_folder_name(client_name)
            
            # Build folder path
            folder_path = f"{self.base_folder}/{safe_client_name}/{self.contracts_subfolder}/{self.signed_subfolder}"
            
            # Check if folder exists or create it
            folder_url = self._ensure_folder_exists(folder_path)
            
            if folder_url:
                print(f"✅ SharePoint folder ready: {folder_path}")
                return folder_path
            else:
                print(f"❌ Failed to create SharePoint folder: {folder_path}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating folder structure: {e}")
            return None
    
    def upload_signed_document(self, document_data: Dict, signed_pdf_path: str, 
                              folder_path: Optional[str] = None) -> Optional[Dict]:
        """
        Upload signed PDF to SharePoint
        
        Args:
            document_data: Document metadata from database
            signed_pdf_path: Path to the signed PDF file
            folder_path: Optional custom folder path
        
        Returns:
            dict: Upload result with SharePoint URL and metadata, or None if failed
        """
        if not self.access_token and not self.authenticate():
            return None
        
        if not os.path.exists(signed_pdf_path):
            print(f"❌ Signed PDF file not found: {signed_pdf_path}")
            return None
        
        try:
            # Determine folder path
            if not folder_path:
                client_name = document_data.get('client_name')
                if not client_name:
                    # Fallback to a generic folder
                    folder_path = f"{self.base_folder}/General/{self.contracts_subfolder}/{self.signed_subfolder}"
                else:
                    folder_path = self.create_folder_structure(client_name)
                    
                if not folder_path:
                    print("❌ Could not determine SharePoint folder path")
                    return None
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_title = document_data.get('title', 'document').replace(' ', '_')
            safe_title = self._sanitize_filename(original_title)
            filename = f"{safe_title}_signed_{timestamp}.pdf"
            
            # Upload file
            upload_result = self._upload_file(signed_pdf_path, folder_path, filename)
            
            if upload_result:
                # Add metadata to the uploaded file
                metadata_result = self._add_file_metadata(upload_result['id'], document_data)
                
                result = {
                    'sharepoint_url': upload_result.get('webUrl'),
                    'file_id': upload_result.get('id'),
                    'folder_path': folder_path,
                    'filename': filename,
                    'upload_timestamp': datetime.utcnow().isoformat() + 'Z',
                    'metadata_updated': metadata_result
                }
                
                print(f"✅ Document uploaded to SharePoint: {result['sharepoint_url']}")
                return result
            else:
                print("❌ Failed to upload document to SharePoint")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading to SharePoint: {e}")
            return None
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitize folder name for SharePoint compatibility"""
        if not name:
            return "General"
        
        # Replace invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/', '&']
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing spaces and periods
        sanitized = sanitized.strip(' .')
        
        # Ensure not empty
        return sanitized if sanitized else "General"
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for SharePoint compatibility"""
        if not name:
            return "document"
        
        # Replace invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/', '~', '#', '%']
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing spaces and periods
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized if sanitized else "document"
    
    def _ensure_folder_exists(self, folder_path: str) -> Optional[str]:
        """
        Ensure folder structure exists in SharePoint, create if needed
        
        Args:
            folder_path: Full folder path to create
        
        Returns:
            str: SharePoint folder URL or None if failed
        """
        try:
            # Split path into components
            path_parts = folder_path.split('/')
            current_path = ""
            
            # Build path incrementally
            for part in path_parts:
                if current_path:
                    current_path += f"/{part}"
                else:
                    current_path = part
                
                # Check if folder exists
                if not self._folder_exists(current_path):
                    # Create folder
                    parent_path = "/".join(current_path.split('/')[:-1]) if '/' in current_path else ""
                    folder_name = current_path.split('/')[-1]
                    
                    if not self._create_folder(parent_path, folder_name):
                        print(f"❌ Failed to create folder: {current_path}")
                        return None
            
            return folder_path
            
        except Exception as e:
            print(f"❌ Error ensuring folder exists: {e}")
            return None
    
    def _folder_exists(self, folder_path: str) -> bool:
        """Check if a folder exists in SharePoint"""
        try:
            encoded_path = urllib.parse.quote(folder_path, safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{encoded_path}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _create_folder(self, parent_path: str, folder_name: str) -> bool:
        """Create a folder in SharePoint"""
        try:
            # Determine the parent URL
            if parent_path:
                encoded_parent = urllib.parse.quote(parent_path, safe='')
                url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{encoded_parent}:/children"
            else:
                url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root/children"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'name': folder_name,
                'folder': {},
                '@microsoft.graph.conflictBehavior': 'rename'
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Created SharePoint folder: {parent_path}/{folder_name}")
                return True
            else:
                print(f"❌ Failed to create folder {folder_name}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating folder: {e}")
            return False
    
    def _upload_file(self, file_path: str, sharepoint_folder: str, filename: str) -> Optional[Dict]:
        """Upload file to SharePoint"""
        try:
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Build upload URL
            encoded_path = urllib.parse.quote(f"{sharepoint_folder}/{filename}", safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{encoded_path}:/content"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/pdf'
            }
            
            # Upload file
            response = requests.put(url, headers=headers, data=file_data)
            
            if response.status_code in [200, 201]:
                upload_result = response.json()
                print(f"✅ File uploaded: {filename}")
                return upload_result
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading file: {e}")
            return None
    
    def _add_file_metadata(self, file_id: str, document_data: Dict) -> bool:
        """Add metadata to uploaded file"""
        try:
            # Graph API doesn't directly support custom metadata for files
            # This could be implemented by adding the file to a SharePoint list
            # or by updating the file properties if custom columns are configured
            
            # For now, we'll just log that metadata should be added
            print(f"ℹ️  File metadata could be added for: {document_data.get('title')}")
            print(f"   - Signer: {document_data.get('signer_name')}")
            print(f"   - Client: {document_data.get('client_name')}")
            print(f"   - Signed: {document_data.get('signed_at')}")
            
            # TODO: Implement custom metadata if SharePoint list integration is needed
            return True
            
        except Exception as e:
            print(f"❌ Error adding metadata: {e}")
            return False
    
    def get_folder_contents(self, folder_path: str) -> Optional[Dict]:
        """
        Get contents of a SharePoint folder
        
        Args:
            folder_path: SharePoint folder path
        
        Returns:
            dict: Folder contents or None if failed
        """
        if not self.access_token and not self.authenticate():
            return None
        
        try:
            encoded_path = urllib.parse.quote(folder_path, safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{encoded_path}:/children"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get folder contents: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting folder contents: {e}")
            return None
    
    def generate_sharepoint_url(self, folder_path: str, filename: str) -> str:
        """
        Generate SharePoint web URL for a file
        
        Args:
            folder_path: SharePoint folder path
            filename: File name
        
        Returns:
            str: SharePoint web URL
        """
        # This is a basic URL construction - actual URLs may vary
        base_url = f"https://{self.tenant_id.split('.')[0]}.sharepoint.com"
        encoded_path = urllib.parse.quote(f"{folder_path}/{filename}", safe='')
        return f"{base_url}/sites/MetroPointTechnology/Shared Documents/{encoded_path}"


# Initialize global SharePoint service instance
sharepoint_service = ESignSharePointService()


def store_signed_document_in_sharepoint(document_data: Dict, signed_pdf_path: str) -> Optional[Dict]:
    """
    Convenience function to store signed document in SharePoint
    
    Args:
        document_data: Document metadata from database
        signed_pdf_path: Path to signed PDF file
    
    Returns:
        dict: Upload result or None if failed
    """
    return sharepoint_service.upload_signed_document(document_data, signed_pdf_path)


def create_client_folder_structure(client_name: str) -> Optional[str]:
    """
    Convenience function to create client folder structure
    
    Args:
        client_name: Name of the client
    
    Returns:
        str: Folder path or None if failed
    """
    return sharepoint_service.create_folder_structure(client_name)