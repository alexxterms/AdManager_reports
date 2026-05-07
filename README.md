# Ad Manager Friday Report Pipeline

This service listens to a specific ad manager Slack message on Fridays, converts CAD metrics to USD, generates AI insights, overlays the values into a PDF template, and sends the output PDF via Slack DM.

## Setup (Step-by-step)

### 1. Create a Slack App and Get Tokens

**Create the app:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → choose **"From scratch"**
3. Name: `Ad Manager Reports` (or your preferred name)
4. Workspace: select your workspace
5. Click **"Create App"**

**Get the Signing Secret:**
1. Go to **"Basic Information"** (left sidebar)
2. Under **"App Credentials"**, copy the **"Signing Secret"** → paste into `.env` as `SLACK_SIGNING_SECRET`

**Get the Bot Token:**
1. Go to **"OAuth & Permissions"** (left sidebar)
2. Under **"Scopes"**, add Bot Token Scopes:
   - `app_mentions:read`
   - `channels:history`
   - `groups:history` (for private channels)
   - `im:write`
   - `files:write`
   - `chat:write:bot`
   - `users:read` (optional, for user ID lookup)
3. Scroll to top → click **"Install to Workspace"**
4. Authorize the app
5. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`) → paste into `.env` as `SLACK_BOT_TOKEN`

**Get the App Token (for Socket Mode):**
1. Go to **"Socket Mode"** (left sidebar)
2. Click **"Enable Socket Mode"**
3. A modal appears – click **"Generate"** for an app-level token
4. Name: `Socket Mode Token` (or any name)
5. Copy the token (starts with `xapp-`) → paste into `.env` as `SLACK_APP_TOKEN`

**Optional: Get Groq API key for AI insights:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign in and open **API Keys**
3. Create a new key
4. Paste it into `.env` as `GROQ_API_KEY`
5. Keep `GROQ_MODEL=llama-3.1-8b-instant` unless you want a different model

For this workflow, Groq's free tier is usually enough because the app only sends one short analysis request per report and falls back to local rules if the API is unavailable.

**Subscribe to message events:**
1. Go back to **"Socket Mode"** and ensure it's enabled
2. Go to **"Event Subscriptions"**
3. Enable events
4. Under **"Subscribe to bot events"**, add:
   - `message.channels` (for public channels)
   - `message.groups` (for private channels)
5. Save changes

### 2. Find Your Slack User and Channel IDs

**Get your ad manager's user ID:**
1. In Slack, right-click the ad manager's name → "View profile"
2. Click "…" → "Copy member ID"
3. Paste into `.env` as `SLACK_AD_MANAGER_USER_ID` (e.g., `U01234567`)

**Get recipient user IDs (who receives the PDF):**
1. Right-click each recipient → "View profile" → "…" → "Copy member ID"
2. Paste into `.env` as comma-separated `SLACK_DM_RECIPIENT_IDS` (e.g., `U22222222,U33333333`)

**Get allowed channel IDs (optional):**
1. Right-click the channel name in sidebar → "View details"
2. At the bottom, copy the channel ID
3. Paste into `.env` as comma-separated `SLACK_ALLOWED_CHANNEL_IDS`

The app only accepts messages from the allowed channels listed in `SLACK_ALLOWED_CHANNEL_IDS`.

### 3. Configure Your PDF Template Coordinates

The default coordinates in `.env` (`PDF_FIELD_COORDS_JSON`) are placeholders. To calibrate them:

1. Ensure your template PDF is in the workspace root as `(BIAB - Weekly) (5126) (2).pdf`
2. Run the calibration helper:

   ```bash
   python -m src.calibrate_pdf
   ```

3. A test PDF `calibration_test.pdf` is generated with sample values labeled at default coordinates.
4. Open `calibration_test.pdf` and check field placement visually.
5. If fields are misaligned, edit `PDF_FIELD_COORDS_JSON` in `.env`:
   - Coordinates are in **PDF points** from bottom-left origin (0,0 at bottom-left, not top-left)
   - Increase `x` to move right, increase `y` to move up
   - Reference: standard letter page is 612×792 points
6. Re-run calibration to verify, repeat until satisfied

### 4. Fill Environment Variables

Copy `.env.example` to `.env` and fill all variables:

```bash
cp .env.example .env
```

Then edit `.env` with:
- `SLACK_BOT_TOKEN` → your bot token
- `SLACK_APP_TOKEN` → your app token
- `SLACK_SIGNING_SECRET` → your signing secret
- `SLACK_AD_MANAGER_USER_ID` → ad manager user ID
- `SLACK_DM_RECIPIENT_IDS` → comma-separated recipient IDs
- `GROQ_API_KEY` → your Groq API key, if you want AI insights
- `GROQ_MODEL` → `llama-3.1-8b-instant` or another Groq model
- `PDF_FIELD_COORDS_JSON` → your calibrated coordinates (see step 3 above)

### 5. Install Python Dependencies and Run

## Message format

Expected format:

Date:24/4/2026 Spend: $4217.59 Impressions: 38.657 CTR: 0.98% Link Clicks: 379 Leads: 42 CPC: $11.13 CPM: $109.10 CPL: $100.42

Supported number separators for numeric fields are `,` and `.` in input text. Use `,` for large-number readability if possible.

## Running the Service

Once configured, start the listener (it runs continuously):

```bash
python -m src.app
```

The service will:
1. Connect to Slack via Socket Mode
2. Wait for messages from the specified ad manager on Fridays (IST)
3. Parse the metrics message
4. Fetch live CAD→USD FX rate
5. Generate AI insights using Groq when configured, otherwise use the local fallback rules
6. Generate and overlay the PDF
7. Send the PDF to configured DM recipients
8. Log all activity and errors

## Integration Tests

To dry-run the pipeline without Slack:

```bash
python -m pytest -v
```

## Coordinate mapping for PDF

Update `PDF_FIELD_COORDS_JSON` in `.env` after checking your template layout. Coordinates are in PDF points from bottom-left on page 1.

## Tests

```bash
python -m pytest -q
```

## Notes

- Idempotency is handled via sqlite in `state/idempotency.db`.
- Only messages from `SLACK_AD_MANAGER_USER_ID` are processed.
- Friday check is based on `TIMEZONE` (currently IST default).
- AI insights come from Groq when `GROQ_API_KEY` is set; otherwise the app falls back to local rule-based analysis.
