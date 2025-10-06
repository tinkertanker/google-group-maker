# Google Service Account Credentials Setup

This guide covers how to configure Google Service Account credentials for the Google Group Maker application.

## Overview

The application supports multiple credential sources in priority order:

1. **Streamlit Secrets** (Recommended) - Cloud-ready, encrypted storage
2. **Local Secrets File** (`.streamlit/secrets.toml`) - For local development
3. **Legacy JSON File** (`service-account-credentials.json`) - Fallback for CLI/local dev

**Why Streamlit Secrets?**
- ✅ Works on Streamlit Cloud (persistent, encrypted)
- ✅ Never committed to Git
- ✅ Same format for local and cloud deployment
- ✅ Integrated with Streamlit's security model

## Quick Start

### Option 1: Streamlit Secrets (Recommended)

#### For Local Development

1. **Copy the example file:**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml`** with your service account credentials:
   ```toml
   [google_service_account]
   type = "service_account"
   project_id = "your-project-123"
   private_key_id = "abc123..."
   private_key = """-----BEGIN PRIVATE KEY-----
   Your actual private key here...
   -----END PRIVATE KEY-----
   """
   client_email = "your-sa@your-project.iam.gserviceaccount.com"
   # ... other fields
   ```

3. **The file is automatically gitignored** - safe from accidental commits

4. **Run the app:**
   ```bash
   streamlit run streamlit_app.py
   ```

#### For Streamlit Cloud

1. **Prepare your credentials:**
   - Go to the app's **Settings** page
   - Upload your service account JSON file
   - Click "📋 Copy for Streamlit Cloud"

2. **Configure in Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Open your app
   - Click **Settings** (⚙️) → **Secrets**
   - Paste the TOML configuration
   - Click **Save**
   - Reboot the app

3. **Verify:**
   - App should load credentials automatically
   - Test authentication in Settings or Dashboard

### Option 2: Legacy JSON File (CLI/Local Only)

⚠️ **Warning:** This method does NOT work on Streamlit Cloud (files don't persist)

1. **Place your JSON file:**
   ```bash
   cp /path/to/your/credentials.json service-account-credentials.json
   ```

2. **The app will use it as a fallback** if secrets aren't configured

3. **For CLI usage:**
   ```bash
   ./groupmaker.py list
   ```

## Obtaining Service Account Credentials

If you don't have a service account yet:

1. **Go to [Google Cloud Console](https://console.cloud.google.com)**

2. **Create/Select a Project**

3. **Enable APIs:**
   - Admin SDK API
   - Google Groups API

4. **Create Service Account:**
   - IAM & Admin → Service Accounts → Create
   - Grant necessary permissions
   - Create a key (JSON format)
   - Download the JSON file

5. **Domain-wide Delegation:**
   - In Google Workspace Admin Console
   - Security → API Controls → Domain-wide Delegation
   - Add your service account client ID
   - Grant scopes:
     - `https://www.googleapis.com/auth/admin.directory.group`
     - `https://www.googleapis.com/auth/admin.directory.group.member`

For detailed Google Cloud setup, check your organization's internal documentation.

## Migration Guide

### From JSON File to Streamlit Secrets

If you're currently using `service-account-credentials.json`:

1. **Open the Streamlit app** and go to **⚙️ Settings**

2. **In the "Streamlit Secrets" tab:**
   - Upload your existing JSON file
   - Review the preview
   - Click "💾 Save to Local Secrets"

3. **For Streamlit Cloud:**
   - Use the "📋 Copy for Streamlit Cloud" button
   - Paste into Streamlit Cloud Secrets UI

4. **Verify the migration:**
   - Check Dashboard → Configuration Summary
   - Should show "Credentials Source: Streamlit Secrets"

5. **Optional: Remove the old JSON file:**
   ```bash
   rm service-account-credentials.json
   ```
   (Keep a backup copy somewhere safe, outside the repo)

### From Streamlit Cloud Environment Variables

If you previously used environment variables:

1. The new secrets format is more secure and easier to manage
2. Follow the "For Streamlit Cloud" setup above
3. Remove old environment variables after verifying secrets work

## Credential Sources: How It Works

The application checks credentials in this order:

```
1. Streamlit Runtime Secrets (st.secrets["google_service_account"])
   ↓ (if not found)
2. Local Secrets File (.streamlit/secrets.toml)
   ↓ (if not found)
3. JSON File (service-account-credentials.json)
   ↓ (if not found)
4. Error: No credentials configured
```

**For CLI commands** (`./groupmaker.py`):
- The Streamlit app passes credentials via environment variables
- CLI can also read from `service-account-credentials.json` directly

**Credential validation:**
- All sources are validated for required fields
- Invalid credentials trigger clear error messages
- Private key format is checked

## Troubleshooting

### "No credentials configured"

**Cause:** No valid credentials found in any source

**Solution:**
1. Check if `.streamlit/secrets.toml` exists and contains `[google_service_account]`
2. Verify `service-account-credentials.json` exists (fallback)
3. On Streamlit Cloud, check App Settings → Secrets

### "Invalid JSON format"

**Cause:** Malformed JSON in uploaded file or secrets

**Solution:**
1. Validate JSON using a JSON validator
2. Re-download credentials from Google Cloud Console
3. Check for missing commas, quotes, or brackets

### "Invalid private key format"

**Cause:** Private key doesn't start with `-----BEGIN PRIVATE KEY-----`

**Solution:**
1. Ensure you downloaded the JSON key (not P12)
2. Check the `private_key` field contains the full key including headers
3. In TOML format, use triple quotes for multiline strings:
   ```toml
   private_key = """-----BEGIN PRIVATE KEY-----
   ...
   -----END PRIVATE KEY-----
   """
   ```

### "Missing required fields"

**Cause:** Incomplete credentials dictionary

**Solution:**
1. Ensure all required fields are present:
   - `type` (must be "service_account")
   - `project_id`
   - `private_key`
   - `client_email`
2. Re-download credentials from Google Cloud Console

### "Authentication failed" (after credentials are loaded)

**Cause:** Credentials are valid but authentication fails

**Solution:**
1. Verify domain-wide delegation is configured in Google Workspace Admin
2. Check that the service account has the correct scopes
3. Ensure `ADMIN_EMAIL` in Settings is a valid admin user
4. Wait a few minutes for Google's systems to propagate changes

### "TOML parser not available" (local development)

**Cause:** Missing `tomli` package for Python < 3.11

**Solution:**
```bash
pip install tomli
```

### Streamlit Cloud: Secrets not persisting

**Cause:** Using JSON file instead of Streamlit Secrets

**Solution:**
1. Files uploaded via the UI don't persist on Streamlit Cloud
2. Must use Streamlit Secrets (Settings → Secrets)
3. See "For Streamlit Cloud" setup above

### Local: Changes to secrets.toml not reflected

**Cause:** App needs to be restarted to reload secrets

**Solution:**
1. In Streamlit, click "Rerun" or press `R`
2. Or restart the app completely: `Ctrl+C` then `streamlit run streamlit_app.py`

## Security Best Practices

1. **Never commit credentials to Git:**
   - `.streamlit/secrets.toml` is gitignored
   - `service-account-credentials.json` is gitignored
   - Only `.streamlit/secrets.toml.example` should be in version control

2. **Use Streamlit Secrets for cloud deployment:**
   - Encrypted at rest
   - Only accessible to your app
   - Not exposed in logs or error messages

3. **Rotate credentials regularly:**
   - Generate new service account keys periodically
   - Delete old keys in Google Cloud Console
   - Update secrets in all environments

4. **Limit service account permissions:**
   - Only grant necessary scopes
   - Use principle of least privilege
   - Monitor service account usage

5. **For team sharing:**
   - Share via secure channels (never email or Slack)
   - Use organization's secret management system
   - Document who has access

## Additional Resources

- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google Workspace Admin SDK](https://developers.google.com/admin-sdk)

## Need Help?

- Check the Settings page in the app for credential status
- Use "Test Connection" to verify authentication
- Review app logs for detailed error messages
- Consult your organization's internal documentation for Google Cloud access