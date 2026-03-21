# Google Group Maker - Claude Development Guide

## Project Overview
Google Group Maker is a tool for automating the creation and management of Google Groups using the Google Admin SDK API. Available as a CLI and a FastAPI web app.

## Architecture

### Core Layer
- **groupmaker_core.py**: Extracted business logic (importable module)
  - Returns structured `OperationResult` / `ValidationResult` dataclasses
  - No print statements - designed for programmatic use
  - Used by CLI and FastAPI apps

### Interfaces
- **groupmaker.py**: CLI wrapper using argparse
- **web/**: FastAPI web app with OAuth

## Key Components

### Core Files
- **groupmaker_core.py**: Business logic (create_service, create_group, add_member, etc.)
- **groupmaker.py**: CLI wrapper importing from core
- **requirements.txt**: Base Python dependencies
- **requirements-web.txt**: FastAPI web app dependencies

### FastAPI Web App (`web/`)
- **app.py**: Main FastAPI application with OAuth
- **dependencies.py**: Shared utilities (auth, service creation, flash messages)
- **routers/**: Route handlers
  - `auth.py`: Google OAuth login/logout
  - `groups.py`: Group CRUD operations and inline editing
  - `members.py`: Member management
- **templates/**: Jinja2 + htmx templates
- **static/**: CSS/JS assets
- **Dockerfile**: Container definition

## Available Commands (CLI)
1. `create` - Create a new Google Group and add members
2. `list` - List all groups with filtering options
3. `members` - List members of a specific group
4. `add` - Add a member to a group
5. `remove` - Remove a member from a group
6. `delete` - Delete a group with confirmation
7. `rename` - Rename an existing group

## Environment Variables

### Required
- `DEFAULT_EMAIL` - Your default email address

### Optional (All Interfaces)
- `GOOGLE_GROUP_DOMAIN` - Default domain for groups
- `ADMIN_EMAIL` - Admin email for authentication
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Service account JSON string

### Web App Only (FastAPI)
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret
- `ALLOWED_DOMAIN` - Restrict login to domain
- `SESSION_SECRET` - Session signing key

## Development Workflow

### CLI Testing
```bash
source venv/bin/activate
./groupmaker.py [command] --debug
```

### Web App (FastAPI)
```bash
pip install -r requirements.txt -r requirements-web.txt
uvicorn web.app:app --reload
```

### Docker
```bash
docker-compose up -d
```

## Testing Commands
```bash
# Create test group
./groupmaker.py create test-group-delete-me trainer@example.com

# List groups
./groupmaker.py list --query test

# List members
./groupmaker.py members test-group-delete-me

# Add member
./groupmaker.py add test-group-delete-me new.member@example.com --role MEMBER

# Remove member
./groupmaker.py remove test-group-delete-me member@example.com

# Delete test group
./groupmaker.py delete test-group-delete-me
```

## Important Notes
- Service account needs domain-wide delegation
- API calls have rate limiting (delay included)
- Domain can be specified in group name, --domain parameter, or env variable
- Always test with non-production groups first
- Web app uses OAuth for user auth, service account for API calls

## Error Handling
- Authentication errors: Check service account credentials
- Permission errors: Verify OAuth scopes and admin privileges
- Rate limiting: Increase delay between operations if needed
- OAuth errors: Verify client ID/secret and redirect URIs

## Code Style
- Core module returns dataclasses, no print statements
- CLI handles user output formatting
- Use type hints throughout
- Follow PEP 8 guidelines

## Data Classes (groupmaker_core.py)
```python
@dataclass
class OperationResult:
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@dataclass
class ValidationResult:
    valid: bool
    group_name: Optional[str] = None
    domain: Optional[str] = None
    error: Optional[str] = None

@dataclass
class CredentialsResult:
    credentials: Optional[dict] = None
    source: str = "missing"
    error: Optional[str] = None
```

## Recent Changes

### Architecture Refactor
- Extracted business logic from groupmaker.py to groupmaker_core.py
- CLI now imports from core module
- Returns structured data instead of printing directly

### FastAPI Web App
- Added modern web interface with Google OAuth
- htmx for dynamic updates without full page reloads
- Tailwind CSS for styling (CDN)
- Docker support for self-hosted deployment

### Current State
- Streamlit support has been removed from the repository
- The supported interfaces are now the CLI and the FastAPI web app
