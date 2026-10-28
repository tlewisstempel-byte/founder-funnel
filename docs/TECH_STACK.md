# Tech stack

Solid = in place. Dashed = planned, not connected yet (as of 2026-10-28).

```mermaid
flowchart TB
    classDef people fill:#f4f1fe,stroke:#7847ff,color:#1f0b56
    classDef built fill:#e1f5ee,stroke:#0f6e56,color:#04342c
    classDef planned fill:#ffffff,stroke:#b4b0bf,color:#6e6a7c,stroke-dasharray:4 4

    subgraph Tools people use
      S["Slack<br/>where everyone works"]:::people
      O["Obsidian<br/>same files as the repo"]:::people
      LI["LinkedIn<br/>Floris posts by hand"]:::people
    end
    subgraph GC["Google Cloud (Stairpay project, not set up yet)"]
      B["Slack bot (Python)<br/>Cloud Run; built and tested"]:::built
      FS["Firestore<br/>post log"]:::planned
      SM["Secret Manager<br/>API keys"]:::planned
      CS["Cloud Scheduler<br/>weekly drafts, monthly lessons"]:::planned
    end
    G["GitHub repo<br/>brain + code; deploys the bot"]:::built
    C["Claude API<br/>writes; swappable"]:::built
    SQL["Anonymised SQL feed<br/>waiting on engineer"]:::planned
    MT["Meeting transcripts<br/>Google Meet"]:::planned

    S <--> B
    G --> B
    O <-. git .-> G
    B --> C
    B --> FS
    SM --> B
    CS --> B
    SQL -.-> B
    MT -.-> B
```

| Layer | Choice | Why | Swappable? |
|---|---|---|---|
| Interface | Slack (bot DMs, buttons, forms) | Where the team already works | Add Notion/Docs as extra outputs |
| Code | Python, Slack Bolt | Simple, well supported | n/a |
| Hosting | Google Cloud Run (+ Cloud Scheduler) | You already use it; scales to zero | Any container host |
| Storage | SQLite locally, Firestore on Cloud Run | No database to manage | `store.py` adapter (Postgres possible) |
| Writing | Claude API | Default model | `llm.py`: one file to change |
| Visuals | HTML + Playwright, brand tokens, Poppins | Exact numbers, on-brand | n/a |
| Source of truth | GitHub repo = Obsidian vault folder | Any LLM, any device | n/a |
