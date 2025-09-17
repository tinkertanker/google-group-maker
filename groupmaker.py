#!/usr/bin/env python
"""
Google Groups Automation Script

This script creates Google Groups and adds members automatically.
Requirements:
- Google Admin SDK API access
- Service account with proper permissions
- Python 3.6+
- google-api-python-client, google-auth-httplib2, google-auth-oauthlib packages

Usage examples:
- Create a group: ./groupmaker.py create group-name trainer@example.com
- Create a group in a specific domain: ./groupmaker.py --domain example.org create group-name trainer@example.com
- Create a group (specifying domain in group name): ./groupmaker.py create group-name@example.org trainer@example.com
- List groups: ./groupmaker.py list
- List members of a group: ./groupmaker.py members group-name
- List members of a group (with domain): ./groupmaker.py members group-name@example.org
- Add a member to a group: ./groupmaker.py add group-name new.member@example.com
- Add a member as manager: ./groupmaker.py add group-name new.member@example.com --role MANAGER
- Remove a member from a group: ./groupmaker.py remove group-name member@example.com
- Remove a member (specifying domain): ./groupmaker.py remove group-name@example.org member@example.com
- Rename a group: ./groupmaker.py rename old-name new-name
- Rename a group (specifying domain): ./groupmaker.py rename old-name@example.org new-name
- Delete a group: ./groupmaker.py delete group-name
- Delete a group (specifying domain): ./groupmaker.py delete group-name@example.org

IMPORTANT: You need a service-account-credentials.json file to use this script.
           Check the company Notion documentation for instructions on obtaining this file.
           DO NOT commit this file to Git as it contains sensitive information.
"""

import os
import argparse
import re
import time
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env if it exists
except ImportError:
    pass  # dotenv is optional

# Constants - configure with environment variables or use defaults
DOMAIN = os.environ.get("GOOGLE_GROUP_DOMAIN", "tinkertanker.com")
DEFAULT_EMAIL = os.environ.get("DEFAULT_EMAIL")

# Validate that DEFAULT_EMAIL is set
if not DEFAULT_EMAIL:
    print("ERROR: DEFAULT_EMAIL environment variable is required.")
    print("Please set DEFAULT_EMAIL in your .env file or environment.")
    print("Example: DEFAULT_EMAIL=your-email@tinkertanker.com")
    sys.exit(1)

DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", DEFAULT_EMAIL)

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

def validate_group_name(group_name):
    """
    Validate that the group name is valid.
    
    This function accepts either:
    - Simple group name (e.g., 'class-a-2023')
    - Full email address (e.g., 'class-a-2023@example.com')
    
    Returns:
    - If valid, returns a tuple (is_valid, group_name, domain_from_email)
      where domain_from_email is None for simple group names
    - If invalid, returns (False, None, None)
    """
    domain_from_email = None
    
    # Check if it's an email address and extract domain if it is
    if '@' in group_name:
        parts = group_name.split('@')
        if len(parts) != 2:
            print(f"ERROR: Invalid email format '{group_name}'.")
            print("Email format should be 'group-name@domain.com'.")
            return False, None, None
        
        group_name, domain_from_email = parts
    
    # Check for valid characters (letters, numbers, hyphens, underscores, periods)
    if not re.match(r'^[a-zA-Z0-9.\-_]+$', group_name):
        print(f"ERROR: Group name '{group_name}' contains invalid characters.")
        print("Group names can only contain letters, numbers, periods, hyphens, and underscores.")
        return False, None, None
    
    return True, group_name, domain_from_email

def validate_email(email):
    """
    Validate that an email address is valid.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def create_group(service, group_name, group_description="", domain=None):
    """Create a new Google Group."""
    # Use provided domain or default
    domain_to_use = domain or DOMAIN
    email = f"{group_name}@{domain_to_use}"
    
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

def add_member(service, group_email, member_email, role="MEMBER", retry=True):
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
        if retry and "Resource Not Found: groupKey" in str(e):
            print(f"Group not found yet. Waiting a moment before retrying...")
            # Wait a moment for the group to propagate
            time.sleep(5)
            return add_member(service, group_email, member_email, role, retry=False)
        else:
            print(f"Error adding member: {e}")
            print(f"HINT: If the error mentions 'groupKey', the group may still be propagating in Google's system.")
            return None

def remove_member(service, group_email, member_email):
    """Remove a member from a Google Group."""
    try:
        service.members().delete(
            groupKey=group_email,
            memberKey=member_email
        ).execute()
        print(f"Removed {member_email} from {group_email}")
        return True
    except Exception as e:
        error_str = str(e)
        if "Resource Not Found" in error_str:
            if "memberKey" in error_str:
                print(f"Error: {member_email} is not a member of {group_email}")
            else:
                print(f"Error: Group {group_email} not found")
        else:
            print(f"Error removing member: {e}")
        return False

def ensure_group_exists(service, group_email, max_attempts=3, delay=3):
    """Check if a group exists and wait for it to be available."""
    for attempt in range(max_attempts):
        try:
            group = service.groups().get(groupKey=group_email).execute()
            print(f"Confirmed group exists: {group_email}")
            return True
        except Exception as e:
            if "Resource Not Found" in str(e) and attempt < max_attempts - 1:
                print(f"Group not found yet (attempt {attempt+1}/{max_attempts}). Waiting {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Error checking group: {e}")
                return False

    return False

def delete_group(service, group_email):
    """Delete a Google Group after confirmation."""
    # First check if the group exists
    try:
        service.groups().get(groupKey=group_email).execute()
    except Exception as e:
        print(f"Error: Group {group_email} not found or cannot be accessed.")
        print(f"Details: {e}")
        return False
    
    # Ask for confirmation
    print(f"\nABOUT TO DELETE GROUP: {group_email}")
    print("This action cannot be undone and will remove all members and content.")
    confirmation = input("Are you sure you want to delete this group? (type 'yes' to confirm): ")
    
    if confirmation.lower() != 'yes':
        print("Deletion cancelled.")
        return False
    
    # Proceed with deletion
    try:
        service.groups().delete(groupKey=group_email).execute()
        print(f"Group {group_email} has been successfully deleted.")
        return True
    except Exception as e:
        print(f"Error deleting group: {e}")
        return False

def list_groups(service, domain=DOMAIN, query=None, max_results=100):
    """List Google Groups in the domain with optional filtering."""
    groups = []
    page_token = None
    
    print(f"Fetching groups from domain: {domain}...")
    
    try:
        while True:
            # Prepare request parameters
            params = {
                'domain': domain,
                'maxResults': max_results
            }
            
            # Add page token if we're on subsequent pages
            if page_token:
                params['pageToken'] = page_token
            
            # Execute the API request to list groups
            results = service.groups().list(**params).execute()
            
            # Add groups from this page to our collection
            if 'groups' in results:
                # If a query is provided, filter the results locally
                if query:
                    filtered_groups = [
                        group for group in results['groups']
                        if (query.lower() in group.get('email', '').lower() or
                            query.lower() in group.get('name', '').lower() or
                            query.lower() in group.get('description', '').lower())
                    ]
                    groups.extend(filtered_groups)
                else:
                    groups.extend(results['groups'])
                
            # Check if there are more pages
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        # Print results in a formatted way
        if groups:
            separator_line = "-" * 120
            print(f"\nFound {len(groups)} groups:")
            print(separator_line)
            print(f"{'EMAIL ADDRESS':<40} {'NAME':<30} {'DESCRIPTION'}")
            print(separator_line)
            
            for group in groups:
                email = group.get('email', 'N/A')
                name = group.get('name', 'N/A')
                description = group.get('description', '')
                
                # Truncate long descriptions for display
                if description and len(description) > 30:
                    description = description[:27] + "..."
                    
                print(f"{email:<40} {name:<30} {description}")
        else:
            print("No groups found matching your criteria.")
            
        return groups
            
    except Exception as e:
        print(f"Error listing groups: {e}")
        return []

def list_members(service, group_email, include_derived_membership=False, max_results=100):
    """List members of a Google Group with optional parameters."""
    members = []
    page_token = None
    
    print(f"Fetching members for group: {group_email}...")
    
    try:
        while True:
            # Prepare request parameters
            params = {
                'groupKey': group_email,
                'maxResults': max_results,
                'includeDerivedMembership': include_derived_membership
            }
            
            # Add page token if we're on subsequent pages
            if page_token:
                params['pageToken'] = page_token
            
            # Execute the API request to list members
            results = service.members().list(**params).execute()
            
            # Add members from this page to our collection
            if 'members' in results:
                members.extend(results['members'])
                
            # Check if there are more pages
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        # Sort members by role (OWNER first, then MANAGER, then MEMBER)
        role_order = {'OWNER': 0, 'MANAGER': 1, 'MEMBER': 2}
        members.sort(key=lambda m: (role_order.get(m.get('role', 'MEMBER'), 3), m.get('email', '')))
        
        # Print results in a formatted way
        if members:
            separator_line = "-" * 140
            print(f"\nFound {len(members)} members in {group_email}:")
            print(separator_line)
            print(f"{'EMAIL ADDRESS':<45} {'NAME':<25} {'ROLE':<15} {'TYPE':<10} {'STATUS'}")
            print(separator_line)
            
            for member in members:
                email = member.get('email', 'N/A')
                role = member.get('role', 'N/A')
                member_type = member.get('type', 'N/A')
                status = member.get('status', 'N/A')
                
                # Extract name if available (try to get from email if not provided separately)
                name = member.get('name', '')
                if not name and '@' in email:
                    # Extract name part from email address
                    name_part = email.split('@')[0]
                    # Replace dots and dashes with spaces for better readability
                    name = name_part.replace('.', ' ').replace('-', ' ').title()
                
                # Highlight derived members if they're included
                derived = member.get('isDerivedMembership', False)
                if derived:
                    email = f"{email} (nested)"
                
                # Highlight different roles with markers
                role_marker = ''
                if role == 'OWNER':
                    role_marker = '👑 '
                elif role == 'MANAGER':
                    role_marker = '⭐ '
                    
                print(f"{email:<45} {name:<25} {role_marker}{role:<13} {member_type:<10} {status}")
            
            # Print summary
            print(separator_line)
            owners = sum(1 for m in members if m.get('role') == 'OWNER')
            managers = sum(1 for m in members if m.get('role') == 'MANAGER')
            regular_members = sum(1 for m in members if m.get('role') == 'MEMBER')
            print(f"Summary: {owners} owners, {managers} managers, {regular_members} members")
            
        else:
            print("No members found in this group.")
            
        return members
            
    except Exception as e:
        print(f"Error listing members: {e}")
        return []

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Create, rename, list or delete Google Groups')
    parser.add_argument('--domain', '-d', dest='domain',
                        help=f'Domain for the Google Group (defaults to {DOMAIN})')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new Google Group')
    create_parser.add_argument('group_name', help='Name for the Google Group (e.g., "class-a-2023" or "class-a-2023@example.com")')
    create_parser.add_argument('trainer_email', help='Email address of the external trainer')
    create_parser.add_argument('--skip-self', action='store_true', 
                        help='Skip adding yourself to the group')
    create_parser.add_argument('--self-email', default=DEFAULT_ADMIN_EMAIL,
                        help=f'Your email address (defaults to {DEFAULT_ADMIN_EMAIL})')
    create_parser.add_argument('--description', default='',
                        help='Optional description for the group')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an existing Google Group')
    delete_parser.add_argument('group_name', help='Name of the Google Group to delete (e.g., "class-a-2023" or "class-a-2023@example.com")')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List Google Groups in the domain')
    list_parser.add_argument('--query', help='Search query to filter groups (e.g., "class" to find all class groups)')
    list_parser.add_argument('--max-results', type=int, default=100, 
                      help='Maximum number of results to return per page (default: 100)')
    
    # Members command
    members_parser = subparsers.add_parser('members', help='List members of a Google Group')
    members_parser.add_argument('group_name', help='Name of the Google Group to list members from (e.g., "class-a-2023" or "class-a-2023@example.com")')
    members_parser.add_argument('--include-derived', action='store_true',
                          help='Include members from nested groups')
    members_parser.add_argument('--max-results', type=int, default=100,
                          help='Maximum number of results to return per page (default: 100)')

    # Add member command
    add_parser = subparsers.add_parser('add', help='Add a member to a Google Group')
    add_parser.add_argument('group_name', help='Name of the Google Group to add a member to (e.g., "class-a-2023" or "class-a-2023@example.com")')
    add_parser.add_argument('member_email', help='Email address of the member to add')
    add_parser.add_argument('--role', choices=['OWNER', 'MANAGER', 'MEMBER'], default='MEMBER',
                      help='Role to assign to the member (default: MEMBER)')

    # Remove member command
    remove_parser = subparsers.add_parser('remove', help='Remove a member from a Google Group')
    remove_parser.add_argument('group_name', help='Name of the Google Group to remove a member from (e.g., "class-a-2023" or "class-a-2023@example.com")')
    remove_parser.add_argument('member_email', help='Email address of the member to remove')

    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename an existing Google Group')
    rename_parser.add_argument('old_group_name', help='Current name of the Google Group (e.g., "class-a-2023" or "class-a-2023@example.com")')
    rename_parser.add_argument('new_group_name', help='New name for the Google Group (e.g., "class-b-2023" or "class-b-2023@example.com")')
    
    args = parser.parse_args()
    
    # If no command is specified, show help
    if not args.command:
        parser.print_help()
        return
    
    # Create the service
    service = create_service()
    if not service:
        return
    
    # Use the domain from command line if specified, otherwise use default
    domain = args.domain or DOMAIN
    
    if args.command == 'create':
        # Validate the group_name
        is_valid, group_name, email_domain = validate_group_name(args.group_name)
        if not is_valid:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py create class-a-2023 external.trainer@example.com")
            print(f"  ./groupmaker.py create class-a-2023@example.com external.trainer@example.com")
            return
        
        # Use domain from email if provided, otherwise use command line parameter or default
        group_domain = email_domain or domain
        
        # Create the Google Group
        group_email = f"{group_name}@{group_domain}"
        print(f"Creating group: {group_email}...")
        group = create_group(service, group_name, args.description, domain=group_domain)
        
        if group:
            # Wait a moment for the group to propagate through Google's system
            print("Waiting for the group to be fully created in Google's system...")
            time.sleep(3)
            
            # Verify the group exists before proceeding
            if not ensure_group_exists(service, group_email):
                print("Could not verify group creation. Proceeding anyway, but member addition might fail.")
            
            # Add the external trainer
            print(f"Adding trainer: {args.trainer_email}...")
            add_member(service, group_email, args.trainer_email)
            
            # Add yourself by default unless --skip-self is specified
            if not args.skip_self:
                print(f"Adding yourself: {args.self_email}...")
                add_member(service, group_email, args.self_email)
            
            print(f"\nGroup setup complete. Group email: {group_email}")
        else:
            print("Failed to create group. Check logs for details.")
            
    elif args.command == 'delete':
        # Validate the group_name
        is_valid, group_name, email_domain = validate_group_name(args.group_name)
        if not is_valid:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py delete class-a-2023")
            print(f"  ./groupmaker.py delete class-a-2023@example.com")
            return
        
        # Use domain from email if provided, otherwise use command line parameter or default
        group_domain = email_domain or domain
        
        # Delete the Google Group
        group_email = f"{group_name}@{group_domain}"
        delete_group(service, group_email)
    
    elif args.command == 'list':
        # List Google Groups in the domain with optional filtering
        list_groups(service, domain=domain, query=args.query, max_results=args.max_results)
    
    elif args.command == 'members':
        # Validate the group_name
        is_valid, group_name, email_domain = validate_group_name(args.group_name)
        if not is_valid:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py members class-a-2023")
            print(f"  ./groupmaker.py members class-a-2023@example.com")
            return
        
        # Use domain from email if provided, otherwise use command line parameter or default
        group_domain = email_domain or domain
        
        # List members of the Google Group
        group_email = f"{group_name}@{group_domain}"
        list_members(service, group_email, include_derived_membership=args.include_derived, max_results=args.max_results)
    
    elif args.command == 'add':
        # Validate the group_name
        is_valid, group_name, email_domain = validate_group_name(args.group_name)
        if not is_valid:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py add class-a-2023 new.member@example.com")
            print(f"  ./groupmaker.py add class-a-2023@example.com new.member@example.com")
            print(f"  ./groupmaker.py add class-a-2023 new.member@example.com --role MANAGER")
            return

        # Use domain from email if provided, otherwise use command line parameter or default
        group_domain = email_domain or domain

        # Add member to the Google Group
        group_email = f"{group_name}@{group_domain}"

        # Verify the group exists before proceeding
        if not ensure_group_exists(service, group_email):
            print(f"Error: Group {group_email} not found or cannot be accessed.")
            return

        # Add the member
        add_member(service, group_email, args.member_email, role=args.role)

    elif args.command == 'remove':
        # Validate the group_name
        is_valid, group_name, email_domain = validate_group_name(args.group_name)
        if not is_valid:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py remove class-a-2023 member@example.com")
            print(f"  ./groupmaker.py remove class-a-2023@example.com member@example.com")
            return

        # Use domain from email if provided, otherwise use command line parameter or default
        group_domain = email_domain or domain

        # Remove member from the Google Group
        group_email = f"{group_name}@{group_domain}"

        # Verify the group exists before proceeding
        if not ensure_group_exists(service, group_email):
            print(f"Error: Group {group_email} not found or cannot be accessed.")
            return

        # Validate member email
        if not validate_email(args.member_email):
            print(f"Error: Invalid email address '{args.member_email}'")
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py remove class-a-2023 member@example.com")
            return

        # Remove the member
        remove_member(service, group_email, args.member_email)

    elif args.command == 'rename':
        # Validate old group name
        is_valid_old, old_group_name, old_email_domain = validate_group_name(args.old_group_name)
        if not is_valid_old:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py rename old-group-name new-group-name")
            print(f"  ./groupmaker.py rename old-group-name@example.com new-group-name")
            return
            
        # Validate new group name
        is_valid_new, new_group_name, new_email_domain = validate_group_name(args.new_group_name)
        if not is_valid_new:
            print("\nUSAGE EXAMPLE:")
            print(f"  ./groupmaker.py rename old-group-name new-group-name")
            print(f"  ./groupmaker.py rename old-group-name new-group-name@example.com")
            return
        
        # Determine which domain to use (prioritize email domains)
        group_domain = old_email_domain or new_email_domain or domain
        
        old_group_email = f"{old_group_name}@{group_domain}"
        new_group_email = f"{new_group_name}@{group_domain}"
        
        # Check if old group exists
        if not ensure_group_exists(service, old_group_email):
            print(f"Error: Group {old_group_email} not found.")
            return
        
        # Check if new group name already exists
        if ensure_group_exists(service, new_group_email):
            print(f"Error: Group {new_group_email} already exists.")
            return
        
        # Get current group settings
        try:
            group = service.groups().get(groupKey=old_group_email).execute()
            
            # Update group settings
            group['email'] = new_group_email
            group['name'] = args.new_group_name
            
            # Update the group
            service.groups().update(groupKey=old_group_email, body=group).execute()
            print(f"Successfully renamed group from {old_group_email} to {new_group_email}")
            
        except Exception as e:
            print(f"Error renaming group: {e}")
            return

if __name__ == "__main__":
    main()