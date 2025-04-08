# Google Group Maker

A command-line utility for automating the creation and management of Google Groups.

## Overview

This script automates the process of:

1. Creating new Google Groups in your organization
2. Adding members to groups
3. Listing existing groups with filtering options
4. Deleting groups with confirmation

## Requirements

-   Python 3.6+
-   Google Admin SDK API access
-   Service account with proper permissions
-   Required Python packages:
    -   google-api-python-client
    -   google-auth-httplib2
    -   google-auth-oauthlib

## Setup

1. Install required packages:

    ```bash
    pip install -r requirements.txt
    ```

2. **Service Account Credentials:**

    - You need a `service-account-credentials.json` file with appropriate permissions
    - **Note:** Check the company Notion documentation for instructions on obtaining this file
    - This file contains sensitive information and should not be committed to Git
    - See `service-account-credentials.example.json` for the expected format

3. Make the script executable:
    ```bash
    chmod +x groupmaker.py
    ```

## Usage

The script now supports multiple commands with different functionality:

### Creating a Group

```bash
./groupmaker.py create GROUP_NAME TRAINER_EMAIL [options]
```

Example:

```bash
./groupmaker.py create python-class-feb2023 external_trainer@example.com
```

**Options:**
-   `--skip-self`: Optional flag to skip adding yourself to the group
-   `--self-email`: Your email address (defaults to the admin email in the script)
-   `--description`: Optional description for the group

### Listing Groups

```bash
./groupmaker.py list [options]
```

This will display all Google Groups in your domain in a formatted table.

**Options:**
-   `--query TEXT`: Filter groups containing this text in their email, name, or description
-   `--max-results NUMBER`: Maximum number of results to return per page (default: 100)

Example:

```bash
# List all groups
./groupmaker.py list

# List groups with "class" in their name, email or description
./groupmaker.py list --query class
```

### Deleting a Group

```bash
./groupmaker.py delete GROUP_NAME
```

This will delete a Google Group after confirmation. For safety, you must type 'yes' to confirm deletion.

Example:

```bash
./groupmaker.py delete python-class-feb2023
```

### Getting Help

```bash
./groupmaker.py --help
```

To get help for specific commands:

```bash
./groupmaker.py create --help
./groupmaker.py list --help
./groupmaker.py delete --help
```

## Configuration

The script uses the following default values that can be modified in the code:

-   Domain: tinkertanker.com
-   Default admin email: yjsoon@tinkertanker.com

## Permissions

The service account needs the following OAuth scopes:

-   https://www.googleapis.com/auth/admin.directory.group
-   https://www.googleapis.com/auth/admin.directory.group.member

## Git Branch for Development

If you're developing new features, create a feature branch:

```bash
git checkout -b feature/group-management
```
