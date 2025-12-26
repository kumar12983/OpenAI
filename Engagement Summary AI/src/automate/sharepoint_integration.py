# -*- coding: utf-8 -*-
"""
SharePoint Integration Module
------------------------------
Handles authentication, file download, and file upload to SharePoint using Microsoft Graph API.

Supports both:
- Delegated authentication (user interactive)
- App-only authentication (client credentials for automation)

Requirements:
    pip install msal requests
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import requests
from msal import PublicClientApplication, ConfidentialClientApplication


class SharePointClient:
    """Client for SharePoint operations via Microsoft Graph API."""
    
    def __init__(self, config_file: str = 'sharepoint_config.json'):
        """Initialize SharePoint client with configuration."""
        self.config = self._load_config(config_file)
        self.access_token = None
        self.graph_endpoint = 'https://graph.microsoft.com/v1.0'
        
    def _load_config(self, config_file: str) -> dict:
        """Load SharePoint configuration from JSON file."""
        if not Path(config_file).exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def authenticate_delegated(self) -> str:
        """Authenticate using delegated (interactive) flow."""
        app = PublicClientApplication(
            self.config['client_id'],
            authority=f"https://login.microsoftonline.com/{self.config['tenant_id']}"
        )
        
        # Try silent acquisition first
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(
                scopes=self.config['scopes'],
                account=accounts[0]
            )
            if result and 'access_token' in result:
                self.access_token = result['access_token']
                print("✓ Authenticated using cached token")
                return self.access_token
        
        # Interactive authentication
        result = app.acquire_token_interactive(scopes=self.config['scopes'])
        
        if 'access_token' in result:
            self.access_token = result['access_token']
            print("✓ Authenticated successfully")
            return self.access_token
        else:
            raise Exception(f"Authentication failed: {result.get('error_description')}")
    
    def authenticate_app_only(self) -> str:
        """Authenticate using app-only (client credentials) flow."""
        app = ConfidentialClientApplication(
            self.config['client_id'],
            authority=f"https://login.microsoftonline.com/{self.config['tenant_id']}",
            client_credential=self.config['client_secret']
        )
        
        result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
        
        if 'access_token' in result:
            self.access_token = result['access_token']
            print("✓ Authenticated using client credentials")
            return self.access_token
        else:
            raise Exception(f"Authentication failed: {result.get('error_description')}")
    
    def _get_headers(self) -> dict:
        """Get headers for Graph API requests."""
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate_delegated() or authenticate_app_only() first.")
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _get_drive_id(self, site_name: str, library_name: str = 'Documents') -> str:
        """Get drive ID for a SharePoint library."""
        # Get site ID
        site_url = f"{self.graph_endpoint}/sites/{self.config['sharepoint_domain']}:/sites/{site_name}"
        response = requests.get(site_url, headers=self._get_headers())
        response.raise_for_status()
        site_id = response.json()['id']
        
        # Get drive ID
        drives_url = f"{self.graph_endpoint}/sites/{site_id}/drives"
        response = requests.get(drives_url, headers=self._get_headers())
        response.raise_for_status()
        
        for drive in response.json()['value']:
            if drive['name'] == library_name:
                return drive['id']
        
        raise Exception(f"Library '{library_name}' not found in site '{site_name}'")
    
    def download_file(self, site_name: str, folder_path: str, filename: str, 
                     local_path: str, library_name: str = 'Documents') -> str:
        """Download a file from SharePoint to local path."""
        print(f"Downloading {filename} from SharePoint...")
        
        drive_id = self._get_drive_id(site_name, library_name)
        
        # Construct file path
        file_path = f"{folder_path}/{filename}".replace('//', '/')
        file_url = f"{self.graph_endpoint}/drives/{drive_id}/root:/{file_path}:/content"
        
        response = requests.get(file_url, headers=self._get_headers())
        response.raise_for_status()
        
        # Save to local file
        local_file = Path(local_path) / filename
        local_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded to {local_file}")
        return str(local_file)
    
    def download_latest_file(self, site_name: str, folder_path: str, 
                            pattern: str, local_path: str, 
                            library_name: str = 'Documents') -> Optional[str]:
        """Download the latest file matching a pattern from SharePoint folder."""
        print(f"Searching for latest {pattern} in {folder_path}...")
        
        drive_id = self._get_drive_id(site_name, library_name)
        
        # List files in folder
        folder_url = f"{self.graph_endpoint}/drives/{drive_id}/root:/{folder_path}:/children"
        response = requests.get(folder_url, headers=self._get_headers())
        response.raise_for_status()
        
        # Filter files matching pattern and sort by modified date
        files = [
            item for item in response.json()['value']
            if 'file' in item and pattern.lower() in item['name'].lower()
        ]
        
        if not files:
            print(f"Warning: No files matching '{pattern}' found in {folder_path}")
            return None
        
        # Get the most recently modified file
        latest_file = max(files, key=lambda x: x['lastModifiedDateTime'])
        filename = latest_file['name']
        
        return self.download_file(site_name, folder_path, filename, local_path, library_name)
    
    def upload_file(self, site_name: str, folder_path: str, local_file: str,
                   library_name: str = 'Documents', overwrite: bool = True) -> str:
        """Upload a file to SharePoint."""
        print(f"Uploading {Path(local_file).name} to SharePoint...")
        
        drive_id = self._get_drive_id(site_name, library_name)
        filename = Path(local_file).name
        
        # Construct upload path
        file_path = f"{folder_path}/{filename}".replace('//', '/')
        upload_url = f"{self.graph_endpoint}/drives/{drive_id}/root:/{file_path}:/content"
        
        headers = self._get_headers()
        headers['Content-Type'] = 'application/octet-stream'
        
        with open(local_file, 'rb') as f:
            file_content = f.read()
        
        response = requests.put(upload_url, headers=headers, data=file_content)
        response.raise_for_status()
        
        result = response.json()
        web_url = result.get('webUrl', '')
        
        print(f"✓ Uploaded successfully")
        print(f"  URL: {web_url}")
        
        return web_url
    
    def create_share_link(self, site_name: str, folder_path: str, filename: str,
                         library_name: str = 'Documents', 
                         link_type: str = 'view') -> str:
        """Create a shareable link for a file.
        
        Args:
            link_type: 'view' (read-only) or 'edit' (read-write)
        """
        print(f"Creating share link for {filename}...")
        
        drive_id = self._get_drive_id(site_name, library_name)
        file_path = f"{folder_path}/{filename}".replace('//', '/')
        
        # Get item ID
        item_url = f"{self.graph_endpoint}/drives/{drive_id}/root:/{file_path}"
        response = requests.get(item_url, headers=self._get_headers())
        response.raise_for_status()
        item_id = response.json()['id']
        
        # Create sharing link
        share_url = f"{self.graph_endpoint}/drives/{drive_id}/items/{item_id}/createLink"
        share_data = {
            "type": link_type,
            "scope": "organization"
        }
        
        response = requests.post(share_url, headers=self._get_headers(), json=share_data)
        response.raise_for_status()
        
        share_link = response.json()['link']['webUrl']
        print(f"✓ Share link created: {share_link}")
        
        return share_link
    
    def send_notification(self, recipients: List[str], subject: str, 
                         body: str, attachment_links: List[str] = None) -> None:
        """Send email notification via Microsoft Graph (requires Mail.Send permission)."""
        print(f"Sending notification to {len(recipients)} recipients...")
        
        # Build email body with attachment links
        email_body = body
        if attachment_links:
            email_body += "\n\n**Files:**\n"
            for link in attachment_links:
                email_body += f"- {link}\n"
        
        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": email_body
                },
                "toRecipients": [
                    {"emailAddress": {"address": email}} for email in recipients
                ]
            }
        }
        
        send_url = f"{self.graph_endpoint}/me/sendMail"
        response = requests.post(send_url, headers=self._get_headers(), json=email_data)
        
        if response.status_code == 202:
            print("✓ Notification sent successfully")
        else:
            print(f"Warning: Failed to send notification: {response.text}")


def main():
    """Test SharePoint integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SharePoint integration test')
    parser.add_argument('--config', default='sharepoint_config.json', help='Config file')
    parser.add_argument('--download', help='Download file: site_name:folder:filename')
    parser.add_argument('--upload', help='Upload file: site_name:folder:local_file')
    parser.add_argument('--auth-type', choices=['delegated', 'app'], default='delegated')
    
    args = parser.parse_args()
    
    client = SharePointClient(args.config)
    
    # Authenticate
    if args.auth_type == 'delegated':
        client.authenticate_delegated()
    else:
        client.authenticate_app_only()
    
    # Download test
    if args.download:
        parts = args.download.split(':')
        if len(parts) == 3:
            client.download_file(parts[0], parts[1], parts[2], '.')
        else:
            print("Download format: site_name:folder:filename")
    
    # Upload test
    if args.upload:
        parts = args.upload.split(':')
        if len(parts) == 3:
            url = client.upload_file(parts[0], parts[1], parts[2])
            link = client.create_share_link(parts[0], parts[1], Path(parts[2]).name)
        else:
            print("Upload format: site_name:folder:local_file")


if __name__ == '__main__':
    main()
