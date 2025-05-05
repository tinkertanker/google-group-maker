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

# List all groups
./groupmaker.py list
```

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
./groupmaker.py create python-class-feb2023 external_trainer@example.com
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
+--------------------------------+-----------------------------+-------------------------------+
| Group Email                    | Name                        | Description                   |
+--------------------------------+-----------------------------+-------------------------------+
| python-class-feb2023@...com    | python-class-feb2023        | Python class February 2023    |
| java-workshop-apr2023@...com   | java-workshop-apr2023       | Java workshop April 2023      |
+--------------------------------+-----------------------------+-------------------------------+
Total groups: 2
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

The script uses the following default values that can be configured using environment variables:

-   Domain: tinkertanker.com (can be set with `GOOGLE_GROUP_DOMAIN` environment variable)
-   Default admin email: yjsoon@tinkertanker.com (can be set with `ADMIN_EMAIL` environment variable)

Example of using environment variables:

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
