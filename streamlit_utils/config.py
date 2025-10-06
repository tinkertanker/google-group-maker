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
    "credentials_saved_secrets": "✅ Credentials saved to .streamlit/secrets.toml!",
    "credentials_saved_file": "✅ Credentials saved to local JSON file!",
    "credentials_copied": "📋 TOML configuration copied to clipboard!"
}

ERROR_MESSAGES = {
    "group_name_required": "Group name is required",
    "trainer_email_required": "Valid trainer email is required",
    "domain_required": "Domain is required",
    "no_credentials": "❌ No credentials configured. Please add credentials in the Settings page.",
    "no_default_email": "❌ DEFAULT_EMAIL not set. Please configure environment variables first.",
    "invalid_json": "❌ Invalid JSON file. Please upload a valid service account credentials file.",
    "secrets_write_failed": "❌ Failed to write secrets file. Check file permissions."
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
**🔐 Credentials Best Practices:**

**For Streamlit Cloud (Recommended):**
- Use Streamlit Secrets for encrypted, cloud-ready storage
- Navigate to: App Settings → Secrets → Paste TOML configuration
- Credentials are never committed to version control

**For Local Development:**
- Use `.streamlit/secrets.toml` (recommended) or fallback to `service-account-credentials.json`
- Both files are automatically gitignored

**Security:** Never commit credentials to Git!
"""

CLOUD_SECRETS_INSTRUCTIONS = """
**📋 Streamlit Cloud Setup:**

1. Copy the TOML configuration above using the copy button
2. Go to your Streamlit Cloud dashboard
3. Select your app → Settings (⚙️) → Secrets
4. Paste the TOML configuration into the text area
5. Click "Save" and reboot your app

Your app will now use encrypted Streamlit secrets for authentication!
"""