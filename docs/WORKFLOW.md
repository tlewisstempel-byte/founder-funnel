# Workflow at a glance

Purple = people, teal = Slack bot. Obsidian renders this diagram.

```mermaid
flowchart TD
    classDef people fill:#f4f1fe,stroke:#7847ff,color:#1f0b56
    classDef bot fill:#e1f5ee,stroke:#0f6e56,color:#04342c
    classDef neutral fill:#f1f0f4,stroke:#b4b0bf,color:#3d3946

    IN["Inputs<br/>ideas, weekly meeting, news, data"]:::neutral --> D["Bot drafts the post<br/>2 versions, hooks, claims to check"]:::bot
    D --> R["You review and edit<br/>then 'Send to Floris'"]:::people
    R --> F["Floris approves and posts<br/>within 24h, on his own account"]:::people
    F --> T["Bot sends team tasks<br/>team copies, tweaks, posts"]:::bot
    T --> L["Learn from Floris's edits<br/>monthly voice-file update"]:::bot
    L -. improves future drafts .-> D

    C0["Daily comments<br/>weekdays, alongside"]:::neutral --> C1["You pick 3-5 posts<br/>from watchlist alerts"]:::people
    C1 --> C2["Bot drafts comments<br/>ranked, in Floris's voice"]:::bot
    C2 --> C3["Floris comments<br/>copy, tweak, post"]:::people
```

Details: `ARCHITECTURE.md` (design), `docs/SLACK_BOT.md` (bot), `playbooks/` (per post type), `playbooks/daily-comments.md`.
