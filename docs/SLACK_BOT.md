# Slack bot: what it does and how to set it up

## What it does

| Step | In Slack | Who |
|---|---|---|
| Ideas | Post in `#content-inbox` (💡 confirms) or `/idea <text>` | Anyone |
| Draft | `/draft <text>` (fast lane) or `/draft` (oldest waiting idea). Optional type prefix: `/draft policy-take: ...` | B2B lead |
| Review | DM card: **Send to Floris · Edit · Other variant · Redraft · Drop**, with alternative hooks and a claims checklist | B2B lead |
| Approve | DM card: **Approve · Edit · Reject**. Edits are saved as before/after | Floris |
| Publish | After approving, Floris posts on LinkedIn and taps **I've posted it**: pastes the link, and the final text if he changed it | Floris |
| Amplify | Each teammate in that post type's funnel (`config/funnels.yaml`) gets a DM: what to do, by when, a suggested comment in their voice, **Done / Skip** | Team |
| Comments | Paste LinkedIn link + post text into `#comment-queue` (👀 confirms). `/comments` ranks them and drafts Floris's comments; you check, then **Send to Floris** | B2B lead, Floris |
| News scan | Daily job (or `/scan`): GOV.UK and news feeds → relevant items land on the ideas board. Only urgent items DM the B2B lead (**Draft now / Keep for Wednesday / Drop**) | Bot, B2B lead |
| Ideas board | Wednesday morning (or `/board`): top 10 ideas from every source, scored, with tick boxes → **Confirm picks** → **Draft all picked now**. Mirrored to Notion (`docs/NOTION.md`) | B2B lead, Floris |
| Status | `/buffer`: ideas waiting, drafts in review, with Floris, approved, published, and the share approved without edits | Anyone |
| Learn | `founder-engine edits-summary` writes `voice/edits/YYYY-MM.md` from Floris's edits (monthly) | Scheduled job |

Only the B2B lead can draft and send; only Floris can approve. Errors are DMed to the B2B lead.

## Set up a free test workspace (about 15 minutes)

1. **Create the workspace:** https://slack.com/get-started > create a new workspace (free plan is fine). Invite a second account of yours if you want to play Floris; otherwise you can be both (put your own ID as owner and founder).
2. **Create two channels:** `#content-inbox` and `#comment-queue`.
3. **Create the app:** https://api.slack.com/apps > **Create New App** > **From a manifest** > pick the test workspace > paste `slack/manifest.yaml` > Create.
4. **App-level token (for Socket Mode):** Basic Information > App-Level Tokens > Generate > name it `socket`, add scope `connections:write`. Copy the `xapp-...` token.
5. **Install:** Install App > Install to Workspace > Allow. Copy the **Bot User OAuth Token** (`xoxb-...`).
6. **Signing secret:** Basic Information > App Credentials > Signing Secret.
7. **Invite the bot** to both channels: in each, type `/invite @Stairpay Content`.
8. **Fill in `config/team.yaml`** (copy `config/team.example.yaml`): Slack member IDs (profile > ⋯ > Copy member ID) and the two channel IDs (channel name > About > bottom).
9. **Anthropic API key:** https://console.anthropic.com > API keys. Set a low monthly spend limit for testing.

Never commit tokens. Hand them over through a password manager or set them as environment variables; for the test workspace, rotate them after testing.

## Run it

```bash
pip install -e ".[dev]"
export SLACK_BOT_TOKEN=xoxb-... SLACK_APP_TOKEN=xapp-... SLACK_SIGNING_SECRET=...
export ANTHROPIC_API_KEY=sk-ant-... LLM_MODEL=<current model name>
founder-engine check      # validates config/team.yaml and funnels
founder-engine run        # Socket Mode while SLACK_APP_TOKEN is set
```

Tests (no network, simulated Slack and model): `pytest`

## Moving to production (Stairpay Slack + Cloud Run)

1. Create the app in Stairpay's Slack from the same manifest, with `socket_mode_enabled: false`, and set the Request URL for slash commands, interactivity and events to `https://<cloud-run-url>/slack/events`.
2. Deploy: `gcloud run deploy founder-engine --source . --region europe-west2 --no-cpu-throttling --min-instances 1` (the bot keeps working after acknowledging Slack, so CPU must stay allocated).
3. Secrets in Secret Manager, mounted as env vars: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `ANTHROPIC_API_KEY`. Set `LLM_MODEL`, `GCP_PROJECT_ID`; `STORAGE=firestore` is the image default.
4. `config/team.yaml` with real IDs: mount as a secret file or bake into the image from a private config.
5. Cloud Scheduler jobs (as Cloud Run jobs): daily 07:00 `founder-engine scan`; Wednesday 08:00 `founder-engine board-digest`; monthly `founder-engine edits-summary`.

## Code map

| File | What it does |
|---|---|
| `src/founder_engine/flows.py` | Every pipeline step (the logic) |
| `src/founder_engine/app.py` | Slack wiring and permissions |
| `src/founder_engine/blocks.py` | Every card and form layout |
| `src/founder_engine/writer.py` | Every prompt; built from `voice/` and `playbooks/` |
| `src/founder_engine/llm.py` | The only file that calls a model provider |
| `src/founder_engine/scanner.py`, `board.py`, `notion_sync.py` | News scan, ideas board, Notion mirror |
| `src/founder_engine/store.py` | Storage: SQLite (local) or Firestore (Cloud Run) |
| `config/team.yaml`, `config/funnels.yaml` | Who's who; who amplifies which post type |

## Not built yet
- Metrics at 24h and 7 days (waiting on the LinkedIn metrics decision)
- Company-page versions for key posts
- Reminder if Floris hasn't approved within 24h, and buffer swap-in
- SQL ingestion, meeting transcript ingestion, chart rendering
