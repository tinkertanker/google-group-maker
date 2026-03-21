#!/usr/bin/env python
"""
Google Groups Automation CLI

Command-line interface for managing Google Groups. Uses groupmaker_core for business logic.

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

import argparse
import sys
import time

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import groupmaker_core as core


def print_error(result: core.OperationResult) -> None:
    """Print an operation error."""
    print(f"ERROR: {result.message}")
    if result.error:
        print(f"Details: {result.error}")


def print_groups_table(groups: list) -> None:
    """Print groups in a formatted table."""
    if not groups:
        print("No groups found matching your criteria.")
        return

    separator = "-" * 120
    print(f"\nFound {len(groups)} groups:")
    print(separator)
    print(f"{'EMAIL ADDRESS':<40} {'NAME':<30} {'DESCRIPTION'}")
    print(separator)

    for group in groups:
        email = group.get('email', 'N/A')
        name = group.get('name', 'N/A')
        description = group.get('description', '')
        if description and len(description) > 30:
            description = description[:27] + "..."
        print(f"{email:<40} {name:<30} {description}")


def print_members_table(members: list, group_email: str, summary: dict) -> None:
    """Print members in a formatted table."""
    if not members:
        print("No members found in this group.")
        return

    separator = "-" * 140
    print(f"\nFound {len(members)} members in {group_email}:")
    print(separator)
    print(f"{'EMAIL ADDRESS':<45} {'NAME':<25} {'ROLE':<15} {'TYPE':<10} {'STATUS'}")
    print(separator)

    for member in members:
        email = member.get('email', 'N/A')
        role = member.get('role', 'N/A')
        member_type = member.get('type', 'N/A')
        status = member.get('status', 'N/A')

        # Extract name from email if not provided
        name = member.get('name', '')
        if not name and '@' in email:
            name_part = email.split('@')[0]
            name = name_part.replace('.', ' ').replace('-', ' ').title()

        # Mark derived members
        if member.get('isDerivedMembership', False):
            email = f"{email} (nested)"

        # Role markers
        role_marker = ''
        if role == 'OWNER':
            role_marker = '  '  # Crown emoji removed per style guide
        elif role == 'MANAGER':
            role_marker = '* '

        print(f"{email:<45} {name:<25} {role_marker}{role:<13} {member_type:<10} {status}")

    print(separator)
    print(f"Summary: {summary['owners']} owners, {summary['managers']} managers, {summary['members']} members")


def cmd_create(args, service, domain: str) -> None:
    """Handle the create command."""
    validation = core.validate_group_name(args.group_name)
    if not validation.valid:
        print(f"ERROR: {validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py create class-a-2023 external.trainer@example.com")
        print("  ./groupmaker.py create class-a-2023@example.com external.trainer@example.com")
        return

    group_domain = validation.domain or domain
    group_email = f"{validation.group_name}@{group_domain}"

    print(f"Creating group: {group_email}...")
    result = core.create_group(service, validation.group_name, domain=group_domain, description=args.description)

    if not result.success:
        print_error(result)
        print("Failed to create group. Check logs for details.")
        return

    print(result.message)
    print("Waiting for the group to be fully created in Google's system...")
    time.sleep(3)

    if not core.ensure_group_exists(service, group_email):
        print("Could not verify group creation. Proceeding anyway, but member addition might fail.")

    # Add trainer
    print(f"Adding trainer: {args.trainer_email}...")
    add_result = core.add_member(service, group_email, args.trainer_email)
    if add_result.success:
        print(add_result.message)
    else:
        print_error(add_result)

    # Add self unless skipped
    if not args.skip_self:
        print(f"Adding yourself: {args.self_email}...")
        self_result = core.add_member(service, group_email, args.self_email)
        if self_result.success:
            print(self_result.message)
        else:
            print_error(self_result)

    print(f"\nGroup setup complete. Group email: {group_email}")


def cmd_delete(args, service, domain: str) -> None:
    """Handle the delete command."""
    validation = core.validate_group_name(args.group_name)
    if not validation.valid:
        print(f"ERROR: {validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py delete class-a-2023")
        print("  ./groupmaker.py delete class-a-2023@example.com")
        return

    group_domain = validation.domain or domain
    group_email = f"{validation.group_name}@{group_domain}"

    # Check if group exists
    check = core.get_group(service, group_email)
    if not check.success:
        print(f"Error: Group {group_email} not found or cannot be accessed.")
        if check.error:
            print(f"Details: {check.error}")
        return

    # Confirm deletion
    print(f"\nABOUT TO DELETE GROUP: {group_email}")
    print("This action cannot be undone and will remove all members and content.")
    confirmation = input("Are you sure you want to delete this group? (type 'yes' to confirm): ")

    if confirmation.lower() != 'yes':
        print("Deletion cancelled.")
        return

    result = core.delete_group(service, group_email)
    if result.success:
        print(result.message)
    else:
        print_error(result)


def cmd_list(args, service, domain: str) -> None:
    """Handle the list command."""
    print(f"Fetching groups from domain: {domain}...")
    result = core.list_groups(service, domain=domain, query=args.query, max_results=args.max_results)

    if result.success:
        print_groups_table(result.data['groups'])
    else:
        print_error(result)


def cmd_members(args, service, domain: str) -> None:
    """Handle the members command."""
    validation = core.validate_group_name(args.group_name)
    if not validation.valid:
        print(f"ERROR: {validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py members class-a-2023")
        print("  ./groupmaker.py members class-a-2023@example.com")
        return

    group_domain = validation.domain or domain
    group_email = f"{validation.group_name}@{group_domain}"

    print(f"Fetching members for group: {group_email}...")
    result = core.list_members(
        service, group_email,
        include_derived=args.include_derived,
        max_results=args.max_results
    )

    if result.success:
        print_members_table(result.data['members'], group_email, result.data['summary'])
    else:
        print_error(result)


def cmd_add(args, service, domain: str) -> None:
    """Handle the add command."""
    validation = core.validate_group_name(args.group_name)
    if not validation.valid:
        print(f"ERROR: {validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py add class-a-2023 new.member@example.com")
        print("  ./groupmaker.py add class-a-2023@example.com new.member@example.com")
        print("  ./groupmaker.py add class-a-2023 new.member@example.com --role MANAGER")
        return

    group_domain = validation.domain or domain
    group_email = f"{validation.group_name}@{group_domain}"

    # Verify group exists
    if not core.ensure_group_exists(service, group_email):
        print(f"Error: Group {group_email} not found or cannot be accessed.")
        return

    result = core.add_member(service, group_email, args.member_email, role=args.role)
    if result.success:
        print(result.message)
    else:
        print_error(result)


def cmd_remove(args, service, domain: str) -> None:
    """Handle the remove command."""
    validation = core.validate_group_name(args.group_name)
    if not validation.valid:
        print(f"ERROR: {validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py remove class-a-2023 member@example.com")
        print("  ./groupmaker.py remove class-a-2023@example.com member@example.com")
        return

    group_domain = validation.domain or domain
    group_email = f"{validation.group_name}@{group_domain}"

    # Verify group exists
    if not core.ensure_group_exists(service, group_email):
        print(f"Error: Group {group_email} not found or cannot be accessed.")
        return

    # Validate member email
    if not core.validate_email(args.member_email):
        print(f"Error: Invalid email address '{args.member_email}'")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py remove class-a-2023 member@example.com")
        return

    result = core.remove_member(service, group_email, args.member_email)
    if result.success:
        print(result.message)
    else:
        print_error(result)


def cmd_rename(args, service, domain: str) -> None:
    """Handle the rename command."""
    # Validate old group name
    old_validation = core.validate_group_name(args.old_group_name)
    if not old_validation.valid:
        print(f"ERROR: {old_validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py rename old-group-name new-group-name")
        print("  ./groupmaker.py rename old-group-name@example.com new-group-name")
        return

    # Validate new group name
    new_validation = core.validate_group_name(args.new_group_name)
    if not new_validation.valid:
        print(f"ERROR: {new_validation.error}")
        print("\nUSAGE EXAMPLE:")
        print("  ./groupmaker.py rename old-group-name new-group-name")
        print("  ./groupmaker.py rename old-group-name new-group-name@example.com")
        return

    # Determine domain
    group_domain = old_validation.domain or new_validation.domain or domain
    old_email = f"{old_validation.group_name}@{group_domain}"

    result = core.rename_group(service, old_email, new_validation.group_name, new_domain=group_domain)
    if result.success:
        print(result.message)
    else:
        print_error(result)


def main():
    # Check required environment variable
    if not core.DEFAULT_EMAIL:
        print("ERROR: DEFAULT_EMAIL environment variable is required.")
        print("Please set DEFAULT_EMAIL in your .env file or environment.")
        print("Example: DEFAULT_EMAIL=your-email@tinkertanker.com")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Create, rename, list or delete Google Groups')
    parser.add_argument('--domain', '-d', dest='domain',
                        help=f'Domain for the Google Group (defaults to {core.DEFAULT_DOMAIN})')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new Google Group')
    create_parser.add_argument('group_name', help='Name for the Google Group')
    create_parser.add_argument('trainer_email', help='Email address of the external trainer')
    create_parser.add_argument('--skip-self', action='store_true',
                               help='Skip adding yourself to the group')
    create_parser.add_argument('--self-email', default=core.DEFAULT_ADMIN_EMAIL,
                               help=f'Your email address (defaults to {core.DEFAULT_ADMIN_EMAIL})')
    create_parser.add_argument('--description', default='',
                               help='Optional description for the group')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an existing Google Group')
    delete_parser.add_argument('group_name', help='Name of the Google Group to delete')

    # List command
    list_parser = subparsers.add_parser('list', help='List Google Groups in the domain')
    list_parser.add_argument('--query', help='Search query to filter groups')
    list_parser.add_argument('--max-results', type=int, default=100,
                             help='Maximum number of results per page (default: 100)')

    # Members command
    members_parser = subparsers.add_parser('members', help='List members of a Google Group')
    members_parser.add_argument('group_name', help='Name of the Google Group')
    members_parser.add_argument('--include-derived', action='store_true',
                                help='Include members from nested groups')
    members_parser.add_argument('--max-results', type=int, default=100,
                                help='Maximum number of results per page (default: 100)')

    # Add member command
    add_parser = subparsers.add_parser('add', help='Add a member to a Google Group')
    add_parser.add_argument('group_name', help='Name of the Google Group')
    add_parser.add_argument('member_email', help='Email address of the member to add')
    add_parser.add_argument('--role', choices=['OWNER', 'MANAGER', 'MEMBER'], default='MEMBER',
                            help='Role to assign (default: MEMBER)')

    # Remove member command
    remove_parser = subparsers.add_parser('remove', help='Remove a member from a Google Group')
    remove_parser.add_argument('group_name', help='Name of the Google Group')
    remove_parser.add_argument('member_email', help='Email address of the member to remove')

    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename an existing Google Group')
    rename_parser.add_argument('old_group_name', help='Current name of the Google Group')
    rename_parser.add_argument('new_group_name', help='New name for the Google Group')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create the service
    creds_result = core.load_credentials()
    if creds_result.credentials is None:
        if creds_result.source == 'invalid-env':
            print("ERROR: Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON environment variable.")
        elif creds_result.source == 'invalid-file':
            print("ERROR: The service-account-credentials.json file contains invalid JSON.")
            print("Please re-download the credentials file from Google Cloud Console.")
        else:
            print("ERROR: No service account credentials found!")
            print("Please provide credentials via:")
            print("  1. GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
            print("  2. service-account-credentials.json file (for local development)")
            print("Check the company Notion documentation for instructions on obtaining credentials.")
        sys.exit(1)

    service = core.create_service(creds_result.credentials)
    if not service:
        print("ERROR: Failed to create Google Directory API service.")
        sys.exit(1)

    domain = args.domain or core.DEFAULT_DOMAIN

    # Dispatch to command handlers
    commands = {
        'create': cmd_create,
        'delete': cmd_delete,
        'list': cmd_list,
        'members': cmd_members,
        'add': cmd_add,
        'remove': cmd_remove,
        'rename': cmd_rename,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args, service, domain)


if __name__ == "__main__":
    main()
