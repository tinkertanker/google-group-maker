# Google Group Maker - Claude Development Guide

## Project Overview
Google Group Maker is a command-line utility for automating the creation and management of Google Groups using the Google Admin SDK API.

## Key Components
- **groupmaker.py**: Main script containing all functionality
- **service-account-credentials.json**: Service account credentials (not in git)
- **requirements.txt**: Python dependencies

## Available Commands
1. `create` - Create a new Google Group and add members
2. `list` - List all groups with filtering options
3. `members` - List members of a specific group
4. `delete` - Delete a group with confirmation
5. `rename` - Rename an existing group

## Environment Variables
Required:
- `DEFAULT_EMAIL` - Your default email address (required)

Optional:
- `GOOGLE_GROUP_DOMAIN` - Default domain for groups
- `ADMIN_EMAIL` - Admin email for authentication

## Development Workflow
1. Test changes with: `./groupmaker.py [command] --debug`
2. Use virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`

## Important Notes
- Service account needs domain-wide delegation
- API calls have rate limiting (delay included)
- Domain can be specified in group name, --domain parameter, or env variable
- Always test with non-production groups first

## Testing Commands
```bash
# Create test group
./groupmaker.py create test-group-delete-me trainer@example.com

# List groups
./groupmaker.py list --query test

# List members
./groupmaker.py members test-group-delete-me

# Delete test group
./groupmaker.py delete test-group-delete-me
```

## Error Handling
- Authentication errors: Check service account credentials
- Permission errors: Verify OAuth scopes and admin privileges
- Rate limiting: Increase delay between operations if needed

## Code Style
- Use Click framework for CLI
- Include proper error handling with helpful messages
- Add debug logging with --debug flag
- Follow PEP 8 guidelines