# Group Maker

A command-line utility for automating the creation of Google Groups and adding members.

## Overview

This script automates the process of:

1. Creating a new Google Group in your organization
2. Adding an external trainer to the group
3. Optionally adding yourself to the group

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

Basic usage:

```bash
./groupmaker.py group_name trainer_email
```

Example:

```bash
./groupmaker.py python-class-feb2023 external_trainer@example.com
```

### Command Line Arguments

-   `group_name`: Name for the Google Group (what goes before @domain.com)
-   `trainer_email`: Email address of the external trainer
-   `--skip-self`: Optional flag to skip adding yourself to the group
-   `--self-email`: Your email address (defaults to the admin email in the script)
-   `--description`: Optional description for the group

## Configuration

The script uses the following default values that can be modified in the code:

-   Domain: tinkertanker.com
-   Default admin email: yjsoon@tinkertanker.com

## Permissions

The service account needs the following OAuth scopes:

-   https://www.googleapis.com/auth/admin.directory.group
-   https://www.googleapis.com/auth/admin.directory.group.member
