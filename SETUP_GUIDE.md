# SETUP GUIDE

Complete setup guide for the Pinterest to YouTube Shorts Automation Agent.

## Step 1: Set Up Google Cloud Project (YouTube API)

### 1.1 Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it (e.g., "YouTube Shorts Automation")
4. Click "Create"

### 1.2 Enable YouTube Data API v3
1. In your project, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### 1.3 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: YouTube Shorts Uploader
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip this step
   - Test users: Add your email
   - Click "Save and Continue"
4. Back to creating credentials:
   - Application type: Desktop app
   - Name: YouTube Shorts Client
   - Click "Create"
5. Download the JSON file and save it as `client_secret.json`

### 1.4 Get Your Refresh Token
Run the following command locally:
```bash
pip install google-auth google-auth-oauthlib google-api-python-client
python get_refresh_token.py
```

This will:
- Open your browser for authentication
- Ask you to log in with your Google account
- Grant permissions to upload videos
- Display your refresh token in the terminal

**SAVE THESE THREE VALUES:**
- Client ID
- Client Secret  
- Refresh Token

---

## Step 2: Set Up Pinterest Developer Account

### 2.1 Create Pinterest Developer Account
1. Go to [Pinterest Developer Portal](https://developers.pinterest.com/)
2. Log in with your Pinterest account
3. Click "Create App" or go to your apps

### 2.2 Create a New App
1. Fill in app details:
   - App name: YouTube Shorts Automation
   - App description: Automating food video uploads
   - Website: Your GitHub repo URL (optional)
2. Agree to terms and create

### 2.3 Generate Access Token
1. Go to your app dashboard
2. Find "Access Token" section
3. Generate a new token with these permissions:
   - `pins:read` - Read pins
   - `boards:read` - Read boards
4. Copy the access token

**Note:** Pinterest API has limitations. The agent includes fallback web scraping if API access is limited.

---

## Step 3: Configure GitHub Repository

### 3.1 Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Pinterest to YouTube Shorts Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 3.2 Add GitHub Secrets
1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "+ New secret" for each of these:

| Secret Name | Value |
|------------|-------|
| `YOUTUBE_CLIENT_ID` | From Google Cloud Console |
| `YOUTUBE_CLIENT_SECRET` | From Google Cloud Console |
| `YOUTUBE_REFRESH_TOKEN` | From get_refresh_token.py script |
| `PINTEREST_ACCESS_TOKEN` | From Pinterest Developer Portal |
| `TIMEZONE` | Your timezone (e.g., `America/New_York`) |

### 3.3 Enable GitHub Actions
1. Go to "Actions" tab in your repository
2. If prompted, enable workflows
3. The workflow will run automatically at scheduled times

---

## Step 4: Test Locally (Optional but Recommended)

### 4.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 4.2 Create .env File
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### 4.3 Run Tests
```bash
# Check schedule
python src/main.py --schedule

# Force a test upload (if credentials are set)
python src/main.py --force

# Check channel status
python src/main.py --status
```

---

## Step 5: Customize Upload Schedule

The default schedule uses EST timezone. Adjust the cron times in `.github/workflows/upload-short.yml`:

### Cron Time Converter
Use this formula: `UTC = Your_Time + UTC_Offset`

Examples:
- **EST (UTC-5)**: 8AM EST = 13:00 UTC
- **PST (UTC-8)**: 8AM PST = 16:00 UTC
- **GMT (UTC+0)**: 8AM GMT = 08:00 UTC
- **IST (UTC+5:30)**: 8AM IST = 02:30 UTC

Edit the cron values:
```yaml
schedule:
  - cron: '0 13 * * *'  # First upload time
  - cron: '0 17 * * *'  # Second upload time
  - cron: '0 0 * * *'   # Third upload time
```

---

## Step 6: Monitor and Optimize

### 6.1 Check Workflow Runs
1. Go to "Actions" tab in GitHub
2. Click on workflow runs to see logs
3. Check for successful uploads

### 6.2 Monitor YouTube Analytics
1. Go to YouTube Studio
2. Check "Analytics" for Shorts performance
3. Monitor:
   - Views
   - Watch time
   - Subscriber growth
   - Traffic sources

### 6.3 Monetization Requirements
To monetize your YouTube channel, you need:
- 1,000 subscribers
- 4,000 watch hours in past 12 months OR 10M Shorts views in 90 days
- Follow all YouTube policies

**Tips for Monetization:**
- Post consistently (3x daily as configured)
- Use trending audio/music
- Create engaging thumbnails
- Respond to comments
- Cross-promote on other platforms

---

## Troubleshooting

### Common Issues

**1. Authentication Failed**
- Check that all credentials are correct
- Ensure refresh token hasn't expired (regenerate if needed)
- Verify OAuth consent screen is configured

**2. No Videos Downloaded**
- Check Pinterest access token
- Pinterest may have rate limits - wait and retry
- Check network connectivity in GitHub Actions

**3. Video Upload Fails**
- Verify video format meets YouTube Shorts requirements
- Check file size (max 256MB or 1 hour)
- Ensure category ID is valid (26 for Howto & Style)

**4. Workflow Not Running**
- Check GitHub Actions is enabled
- Verify cron syntax
- Check repository settings for workflow permissions

---

## Important Legal Notes

⚠️ **Content Rights**: 
- Only use content you have rights to
- Transform downloaded content sufficiently
- Consider creating original content instead

⚠️ **YouTube Policies**:
- Follow Community Guidelines
- Avoid copyright strikes
- Don't reupload others' content without permission

⚠️ **Pinterest Terms**:
- Respect Pinterest's Terms of Service
- Don't abuse their API
- Use data responsibly

---

## Support

For issues:
1. Check GitHub Actions logs
2. Review error messages
3. Verify all credentials
4. Test locally first

Good luck with your YouTube Shorts channel! 🚀
