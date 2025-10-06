# Google Group Maker - Streamlit Web Interface

A user-friendly web interface for the Google Group Maker CLI tool, built with Streamlit.

## Features

- **Dashboard**: Configuration overview and quick actions
- **Create Group**: Create new groups with trainer and member management
- **List Groups**: Browse and search existing groups with action buttons
- **Group Members**: View detailed member lists with role indicators and export options
- **Add Members**: Batch add members via text input or CSV upload
- **Rename Group**: Change group names with preview
- **Delete Group**: Safe deletion with double confirmation
- **Settings**: Configure environment variables and upload credentials

## Prerequisites

Before using the Streamlit interface, ensure you have:

1. **Google Workspace Admin Access**
   - Admin credentials for your Google Workspace domain
   - Permissions to create and manage groups

2. **Service Account Credentials**
   - Service account with Google Admin SDK API access
   - Credentials configured in **Streamlit Secrets** (recommended) or as JSON file
   - See [docs/CREDENTIALS.md](CREDENTIALS.md) for detailed setup instructions

3. **Python Environment**
   - Python 3.6 or higher
   - pip package manager

## Setup

1. **Virtual Environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Credentials Setup (Streamlit Secrets - Recommended)

The application uses **Streamlit Secrets** for credential management, which works seamlessly in both local development and Streamlit Cloud:

**For Local Development:**
1. Copy the example secrets file: `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`
2. Edit `.streamlit/secrets.toml` with your actual service account credentials
3. The app will automatically load credentials from this file

**For Streamlit Cloud:**
1. Go to your app's Settings → Secrets in the Streamlit Cloud dashboard
2. Paste your credentials in TOML format (see Settings page in the app for formatted output)
3. Save and reboot the app

**Legacy JSON File (Optional):**
- You can still use `service-account-credentials.json` for local CLI usage
- The app will fall back to this file if secrets are not configured

For comprehensive credential setup instructions, see [docs/CREDENTIALS.md](CREDENTIALS.md).

### Environment Variables

## Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Start the Streamlit app
streamlit run streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## First-Time Setup Checklist

1. ✅ **Configure Credentials**
   - Go to the **⚙️ Settings** page
   - Navigate to the "Streamlit Secrets (Recommended)" tab
   - Upload your service account JSON file
   - Click "Save to Local Secrets" (local) or copy TOML for Streamlit Cloud
   - See [docs/CREDENTIALS.md](CREDENTIALS.md) for detailed instructions

2. ✅ **Set Environment Variables**
   - In Settings, configure:
     - `DEFAULT_EMAIL`: Your admin email address
     - `GOOGLE_GROUP_DOMAIN`: Your domain (e.g., `tinkertanker.com`)
     - `ADMIN_EMAIL`: Admin email for API authentication (optional, uses DEFAULT_EMAIL)

3. ✅ **Test Authentication**
   - Click "Test Connection" in Settings
   - Or go to Dashboard and click "Test Authentication"
   - Verify you see a success message

4. ✅ **Create Test Group**
   - Go to "➕ Create Group"
   - Create a test group (e.g., `test-group-delete-me`)
   - Verify it appears in "📋 List Groups"
   - Delete it when done testing

## Usage Tips

### Group Names
- Use letters, numbers, hyphens, underscores, and periods only
- Can specify full email (e.g., `group@domain.com`) or just name part
- Domain hierarchy: Group email → Command line → Environment variable → Default

### Adding Members
- Supports multiple formats: one per line, comma-separated, semicolon-separated
- Can upload CSV files with an `email` column
- Duplicate emails are automatically removed
- Invalid emails are filtered out

### Batch Operations
- Progress bars show status for long-running operations
- Small delays are built in to respect API rate limits
- Detailed error reporting for failed operations

### Caching
- Group lists and member data are cached for 1 minute
- Use refresh buttons to clear cache and reload
- Cache automatically cleared after modifications

## Security Notes

### Credential Storage

**Streamlit Secrets (Recommended):**
- The `.streamlit/secrets.toml` file is automatically gitignored
- Never committed to version control
- Works seamlessly for both local development and Streamlit Cloud
- Encrypted and secure when deployed to Streamlit Cloud

**For Streamlit Cloud Users:**
- Use the **Secrets UI** in your app settings (Settings → Secrets)
- Paste your credentials in TOML format
- Credentials are encrypted at rest and never exposed in logs
- The Settings page in the app provides a formatted TOML snippet you can copy

**Legacy JSON File:**
- The `service-account-credentials.json` file is also gitignored
- Supported for local CLI usage and development
- **Does not work on Streamlit Cloud** (files don't persist)
- If using this method locally, ensure it's never committed to Git

### Best Practices

1. **Never commit credentials** to version control
2. **Use Streamlit Secrets** for cloud deployments
3. **Rotate credentials** regularly via Google Cloud Console
4. **Limit permissions** - only grant necessary API scopes
5. **Monitor usage** - review service account activity periodically

For detailed security guidance, see [docs/CREDENTIALS.md](CREDENTIALS.md).

### Other Security Considerations

- Environment variables are stored in `.env` file (also gitignored)
- All sensitive operations require confirmation
- Debug mode shows detailed error information (use carefully)

## Troubleshooting

### Authentication Issues
- Verify service account has domain-wide delegation
- Check that `DEFAULT_EMAIL` matches your admin account
- Ensure proper OAuth scopes are configured

### Group Operations Fail
- Groups may take time to propagate in Google's system
- Use refresh buttons to reload data
- Check debug logs for detailed error messages

### Performance Issues
- Large group lists may take time to load
- Use search/query filters to limit results
- Consider increasing timeout values if needed

## Features Overview

### Dashboard 🏠
- Configuration summary with status indicators
- Quick access to common actions
- Authentication testing
- Getting started guidance

### Create Group ➕
- Guided form with validation
- Domain specification options
- Optional description field
- Skip self-addition option

### List Groups 📋
- Search and filter capabilities
- Domain-specific filtering
- Quick action buttons for each group
- Refresh and cache management

### Group Members 👥
- Role-based member display with emoji indicators
- Member statistics and summaries
- Email list export for copy/paste
- CSV download functionality

### Add Members 👤
- Bulk member addition
- Multiple input methods (text, CSV upload)
- Email validation and deduplication
- Progress tracking and error reporting

### Rename Group ✏️
- Preview functionality
- Domain preservation
- Validation and confirmation

### Delete Group 🗑️
- Double confirmation safety
- Clear warning about permanence
- Type-to-confirm validation

### Settings ⚙️
- Environment variable management
- Credentials file upload
- Authentication testing
- Security guidance

## Development Notes

The web interface is built as a wrapper around the existing CLI tool:

- **config_utils.py**: Environment and credentials management
- **web_utils.py**: API wrapper for CLI commands with parsing
- **streamlit_app.py**: Main application with all pages

The implementation prioritizes safety and user experience while maintaining full compatibility with the existing CLI functionality.
