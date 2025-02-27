#!/usr/bin/env python
"""
Google Groups Automation Script

This script creates Google Groups and adds members automatically.
Requirements:
- Google Admin SDK API access
- Service account with proper permissions
- Python 3.6+
- google-api-python-client, google-auth-httplib2, google-auth-oauthlib packages

IMPORTANT: You need a service-account-credentials.json file to use this script.
           Check the company Notion documentation for instructions on obtaining this file.
           DO NOT commit this file to Git as it contains sensitive information.
"""

import os
import argparse
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Constants - replace with your domain
DOMAIN = "tinkertanker.com"  # Replace with your actual domain
DEFAULT_ADMIN_EMAIL = "yjsoon@tinkertanker.com"  # Default admin email

def create_service():
    """Create and return an authorized service object for the Google Directory API."""
    # Path to your service account credentials JSON file
    SERVICE_ACCOUNT_FILE = 'service-account-credentials.json'
    
    # Check if credentials file exists
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"ERROR: {SERVICE_ACCOUNT_FILE} not found!")
        print("Please check the company Notion documentation for instructions on obtaining this file.")
        return None
    
    # If you're using a service account to authenticate
    SCOPES = [
        'https://www.googleapis.com/auth/admin.directory.group',
        'https://www.googleapis.com/auth/admin.directory.group.member'
    ]
    
    # The service account needs to be delegated for a G Suite admin user
    DELEGATED_EMAIL = DEFAULT_ADMIN_EMAIL
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Delegate credentials
    delegated_credentials = credentials.with_subject(DELEGATED_EMAIL)
    
    # Build the service
    service = build('admin', 'directory_v1', credentials=delegated_credentials)
    return service

def create_group(service, group_name, group_description=""):
    """Create a new Google Group."""
    email = f"{group_name}@{DOMAIN}"
    
    group_body = {
        "email": email,
        "name": group_name,
        "description": group_description,
        # Setting basic permissions: only members can post
        "allowExternalMembers": True,
        "whoCanJoin": "INVITED_CAN_JOIN",
        "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",
        "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
        "whoCanPostMessage": "ALL_MEMBERS_CAN_POST",
        "allowWebPosting": True,
        "includeInGlobalAddressList": True
    }
    
    try:
        result = service.groups().insert(body=group_body).execute()
        print(f"Group '{email}' created successfully!")
        return result
    except Exception as e:
        print(f"Error creating group: {e}")
        return None

def add_member(service, group_email, member_email, role="MEMBER"):
    """Add a member to the specified Google Group."""
    member_body = {
        "email": member_email,
        "role": role,  # Options: OWNER, MANAGER, MEMBER
        "delivery_settings": "ALL_MAIL"  # Ensure they receive all emails
    }
    
    try:
        result = service.members().insert(
            groupKey=group_email,
            body=member_body
        ).execute()
        print(f"Added {member_email} to {group_email} as {role}")
        return result
    except Exception as e:
        print(f"Error adding member: {e}")
        return None

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Create a Google Group and add members')
    parser.add_argument('group_name', help='Name for the Google Group (what goes before @domain.com)')
    parser.add_argument('trainer_email', help='Email address of the external trainer')
    parser.add_argument('--skip-self', action='store_true', 
                        help='Skip adding yourself to the group')
    parser.add_argument('--self-email', default=DEFAULT_ADMIN_EMAIL,
                        help=f'Your email address (defaults to {DEFAULT_ADMIN_EMAIL})')
    parser.add_argument('--description', default='',
                        help='Optional description for the group')
    
    args = parser.parse_args()
    
    # Create the service
    service = create_service()
    
    # Create the Google Group
    group_email = f"{args.group_name}@{DOMAIN}"
    group = create_group(service, args.group_name, args.description)
    
    if group:
        # Add the external trainer
        add_member(service, group_email, args.trainer_email)
        
        # Add yourself by default unless --skip-self is specified
        if not args.skip_self:
            add_member(service, group_email, args.self_email)
        
        print(f"Group setup complete. Group email: {group_email}")
    else:
        print("Failed to create group. Check logs for details.")

if __name__ == "__main__":
    main()