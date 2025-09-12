"""
Configuration constants and settings for Google Group Maker Streamlit app.
"""

from typing import List

# Page configuration
APP_TITLE = "Google Group Maker"
APP_ICON = "👥"
LAYOUT = "wide"

# Page definitions
PAGES: List[str] = [
    "🏠 Dashboard",
    "➕ Create Group",
    "📋 List Groups", 
    "👥 Group Members",
    "👤 Add Members",
    "✏️ Rename Group",
    "🗑️ Delete Group",
    "⚙️ Settings"
]

# UI Constants
DEFAULT_DOMAIN = "tinkertanker.com"
MAX_RESULTS_DEFAULT = 100
CACHE_TTL_SECONDS = 60  # Cache for 1 minute
MEMBER_BATCH_DELAY = 0.1  # Delay between batch member operations

# Role definitions
VALID_ROLES = ["MEMBER", "MANAGER", "OWNER"]
ROLE_EMOJIS = {
    "OWNER": "👑",
    "MANAGER": "⭐",
    "MEMBER": "👤"
}

# Messages
SUCCESS_MESSAGES = {
    "auth_success": "✅ Authentication successful!",
    "auth_failed": "❌ Authentication failed. Check your configuration.",
    "group_created": "🎉 Successfully created group: {group_email}",
    "group_deleted": "🗑️ Successfully deleted group: {group_email}",
    "group_renamed": "✅ Successfully renamed group to: {new_name}",
    "members_added": "✅ Successfully added {count} members",
    "settings_saved": "✅ Environment settings saved successfully!",
    "credentials_saved": "✅ Credentials file saved successfully!"
}

ERROR_MESSAGES = {
    "group_name_required": "Group name is required",
    "trainer_email_required": "Valid trainer email is required",
    "domain_required": "Domain is required",
    "no_credentials": "❌ No credentials file found. Please upload credentials first.",
    "no_default_email": "❌ DEFAULT_EMAIL not set. Please configure environment variables first.",
    "invalid_json": "❌ Invalid JSON file. Please upload a valid service account credentials file."
}

# Getting started guide
GETTING_STARTED_INFO = """
**First time setup:**
1. Go to **Settings** to configure your environment variables
2. Upload your service account credentials file
3. Test authentication
4. Create your first group for testing (use a safe name like `test-group-delete-me`)

**Testing commands from CLI:**
- `./groupmaker.py create test-group-delete-me trainer@example.com`
- `./groupmaker.py list --query test`
- `./groupmaker.py delete test-group-delete-me`
"""

# Security warnings
DELETE_WARNING = """
**You are about to permanently delete: {group_email}**

This will:
- Remove all members from the group
- Delete all group content and history  
- Make the group email address unusable
- Cannot be undone
"""

RENAME_WARNING = "⚠️ **Warning**: Renaming a group changes its email address. Update any references accordingly."

CREDENTIALS_WARNING = """
**Security Note**: The credentials file is saved locally and should never be committed to version control.
Make sure your `.gitignore` includes `service-account-credentials.json`.
"""