# Google Group Maker

A command-line utility for automating the creation and management of Google Groups.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up service account credentials
cp service-account-credentials.example.json service-account-credentials.json
# Edit service-account-credentials.json with your actual credentials

# Make script executable
chmod +x groupmaker.py

# Create a new group with an external trainer
./groupmaker.py create python-class-feb2023 external_trainer@example.com

# Create a group in a specific domain (using --domain parameter)
./groupmaker.py --domain example.org create python-class-feb2023 external_trainer@example.com

# Create a group in a specific domain (specifying domain in group name)
./groupmaker.py create python-class-feb2023@example.org external_trainer@example.com

# List all groups
./groupmaker.py list
```

## Overview

This script automates the process of:

1. Creating new Google Groups in your organization
2. Adding members to groups
3. Listing existing groups with filtering options
4. Deleting groups with confirmation
5. Renaming existing Google Groups

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

4. **Configuration Options:**

    You can set default values using environment variables or a `.env` file:
    ```
    GOOGLE_GROUP_DOMAIN=yourdomain.com
    ADMIN_EMAIL=admin@yourdomain.com
    ```
    
    Create a `.env` file in the same directory as the script to automatically load these settings.

## Usage

The script supports multiple commands with different functionality:

### Creating a Group

```bash
./groupmaker.py create GROUP_NAME TRAINER_EMAIL [options]
```

Example:

```bash
# Basic usage
./groupmaker.py create python-class-feb2023 external_trainer@example.com

# Specify the domain as part of the group name
./groupmaker.py create python-class-feb2023@example.org external_trainer@example.com

# Using the --domain parameter
./groupmaker.py --domain example.org create python-class-feb2023 external_trainer@example.com
```

**Expected Output:**
```
Creating group: python-class-feb2023@tinkertanker.com
Group created successfully
Adding trainer external_trainer@example.com to group
Adding admin yjsoon@tinkertanker.com to group
All members added successfully
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

**Expected Output:**
```
Found 23 groups:
------------------------------------------------------------------------------------------------------------------------
EMAIL ADDRESS                            NAME                          DESCRIPTION
------------------------------------------------------------------------------------------------------------------------
python-class-feb2023@tinkertanker.com    python-class-feb2023          Python class February 2023    
java-workshop-apr2023@tinkertanker.com   java-workshop-apr2023         Java workshop April 2023      
```

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

### Listing Group Members

```bash
./groupmaker.py members GROUP_NAME [options]
```

This will display all members of a specific Google Group with detailed information.

**Expected Output:**
```
Found 5 members in python-class-feb2023@tinkertanker.com:
--------------------------------------------------------------------------------------------------------------------------------------------
EMAIL ADDRESS                                 NAME                      ROLE            TYPE       STATUS
--------------------------------------------------------------------------------------------------------------------------------------------
yjsoon@tinkertanker.com                      Yjsoon                    👑 OWNER        USER       ACTIVE
trainer@example.com                          Trainer                   ⭐ MANAGER      USER       ACTIVE
alice.johnson@tinkertanker.com               Alice Johnson             MEMBER          USER       ACTIVE
bob.smith@tinkertanker.com                   Bob Smith                 MEMBER          USER       ACTIVE
charlie.chen@tinkertanker.com                Charlie Chen              MEMBER          USER       ACTIVE
--------------------------------------------------------------------------------------------------------------------------------------------
Summary: 1 owners, 1 managers, 3 members
```

**Features:**
- Members are sorted by role (owners first, then managers, then regular members)
- Names are extracted and displayed for better identification
- Visual markers (👑 for owners, ⭐ for managers) help identify roles at a glance
- Summary shows total count by role

**Options:**
-   `--include-derived`: Include members from nested groups
-   `--max-results NUMBER`: Maximum number of results to return per page (default: 100)

Example:

```bash
# List members of a group
./groupmaker.py members python-class-feb2023

# Include nested group members
./groupmaker.py members python-class-feb2023 --include-derived
```

### Deleting a Group

```bash
./groupmaker.py delete GROUP_NAME
```

This will delete a Google Group after confirmation. For safety, you must type 'yes' to confirm deletion.

**Expected Output:**
```
Are you sure you want to delete the group python-class-feb2023@tinkertanker.com? (yes/no): yes
Group python-class-feb2023@tinkertanker.com deleted successfully.
```

Example:

```bash
# Basic usage
./groupmaker.py delete python-class-feb2023

# Specify the domain as part of the group name
./groupmaker.py delete python-class-feb2023@example.org

# Using the --domain parameter
./groupmaker.py --domain example.org delete python-class-feb2023
```

### Renaming a Group

```bash
./groupmaker.py rename OLD_GROUP_NAME NEW_GROUP_NAME
```

This will rename an existing Google Group to a new name.

**Expected Output:**
```
Successfully renamed group from old-name@tinkertanker.com to new-name@tinkertanker.com
```

Example:

```bash
# Basic usage
./groupmaker.py rename python-class-feb2023 python-class-march2023

# Specify the domain in group names
./groupmaker.py rename python-class-feb2023@example.org python-class-march2023

# Using the --domain parameter
./groupmaker.py --domain example.org rename python-class-feb2023 python-class-march2023
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
./groupmaker.py rename --help
```

## Configuration

The script uses the following default values that can be configured:

-   Domain: tinkertanker.com (can be set in multiple ways)
-   Default admin email: yjsoon@tinkertanker.com (can be set with `ADMIN_EMAIL` environment variable)

### Domain Configuration Priority

When determining which domain to use, the script uses the following priority order:

1. Domain specified in the group name itself (e.g., `group@example.com`)
2. Domain specified with the `--domain` command-line parameter 
3. Domain specified with the `GOOGLE_GROUP_DOMAIN` environment variable
4. Default domain (tinkertanker.com)

### Example: Specifying Domain in Group Name

```bash
# Specify domain directly in the group name - highest priority
./groupmaker.py create new-group@example.org trainer@example.com
./groupmaker.py delete group-name@example.org
```

### Example: Using the Domain Parameter

```bash
# Set domain for a single command
./groupmaker.py --domain example.org create new-group trainer@example.com

# Using the shorthand -d option
./groupmaker.py -d example.org list
```

### Example: Using Environment Variables

```bash
# Set for a single command
GOOGLE_GROUP_DOMAIN=example.com ADMIN_EMAIL=admin@example.com ./groupmaker.py list

# Or export for the current shell session
export GOOGLE_GROUP_DOMAIN=example.com
export ADMIN_EMAIL=admin@example.com
./groupmaker.py create new-group trainer@example.com
```

## Troubleshooting

### Common Errors

1. **Authentication Failed**: 
   - Check that your service-account-credentials.json file is correctly formatted and has the proper permissions
   - Verify that the service account has been granted domain-wide delegation

2. **Permission Denied**:
   - Ensure the service account has been granted proper OAuth scopes in the Google Admin console
   - Verify the admin email specified has Admin privileges in your GSuite/Workspace

3. **Rate Limiting**:
   - The script includes a delay between operations to avoid API rate limits
   - If you encounter rate limiting errors, try increasing the delay value in the code

### Debug Mode

Run the script with the `--debug` flag to enable verbose logging:

```bash
./groupmaker.py create python-class-feb2023 external_trainer@example.com --debug
```

## Permissions

The service account needs the following OAuth scopes:

-   https://www.googleapis.com/auth/admin.directory.group
-   https://www.googleapis.com/auth/admin.directory.group.member

## Contributing

Contributions to Google Group Maker are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a pull request

Please follow these best practices:
- Include clear commit messages
- Add or update documentation as needed
- Add appropriate error handling
- Test your changes thoroughly

## Development

If you're developing new features, create a feature branch:

```bash
git checkout -b feature/group-management
```
