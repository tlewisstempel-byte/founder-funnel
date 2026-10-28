"""Command line: run the bot, and jobs a scheduler can trigger.

  founder-engine run                 start the bot (Socket Mode if SLACK_APP_TOKEN is set, else HTTP)
  founder-engine draft-buffer --n 3  draft the N oldest waiting ideas (weekly job)
  founder-engine edits-summary [--month 2026-11]
                                     write voice/edits/YYYY-MM.md from Floris's edits (monthly job)
  founder-engine check               validate config files without connecting to anything
  founder-engine scan                news scan into the ideas board (daily job)
  founder-engine metrics-check      DM the owner any posts whose 24h/7d numbers are due (daily job)
  founder-engine board-digest        send the Wednesday ideas board to the owner (weekly job, Wednesday morning)
  founder-engine board-export [--md F] [--csv F]
                                     write the board as Markdown (Obsidian) and/or CSV (Notion import)
  founder-engine notion-setup --parent-page ID
                                     create the Notion board database; prints NOTION_DATABASE_ID
  founder-engine notion-sync         push the whole board to Notion
  founder-engine visual SPEC.yaml OUT.png
                                     render an on-brand chart/stat/quote card (see brand/visuals/README.md)
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import Settings, load_funnels, load_team


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="founder-engine")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run")
    sub.add_parser("check")
    d = sub.add_parser("draft-buffer")
    d.add_argument("--n", type=int, default=3)
    e = sub.add_parser("edits-summary")
    e.add_argument("--month", default="")
    sub.add_parser("scan")
    sub.add_parser("board-digest")
    sub.add_parser("metrics-check")
    sub.add_parser("notion-sync")
    bx = sub.add_parser("board-export")
    bx.add_argument("--md", default="")
    bx.add_argument("--csv", default="")
    ns = sub.add_parser("notion-setup")
    ns.add_argument("--parent-page", required=True)
    v = sub.add_parser("visual")
    v.add_argument("spec")
    v.add_argument("out")
    args = p.parse_args(argv)

    if args.cmd == "visual":
        from pathlib import Path

        import yaml

        from .visuals import render_spec

        path, alt = render_spec(yaml.safe_load(Path(args.spec).read_text()), Path(args.out))
        print(f"Wrote {path}\nAlt text (paste into LinkedIn): {alt}")
        return 0

    if args.cmd == "check":
        team, funnels = load_team(), load_funnels()
        people = [team.owner, team.founder, *team.amplifiers.values()]
        missing = list(dict.fromkeys(p.key for p in people if not p.slack_id or p.slack_id.startswith("U0000")))
        print(f"Team: {', '.join(dict.fromkeys(p.key for p in people))}")
        print(f"Funnels: {', '.join(funnels)}")
        for pt, steps in funnels.items():
            for s in steps:
                if not team.person(s.who):
                    print(f"  ! funnel {pt} names unknown person '{s.who}'")
        if missing:
            print(f"  ! placeholder Slack IDs for: {', '.join(missing)} (fill in config/team.yaml)")
        return 0

    from .app import build

    settings = Settings.from_env()
    app, engine = build(settings)

    if args.cmd == "run":
        if settings.slack_app_token:
            from slack_bolt.adapter.socket_mode import SocketModeHandler

            SocketModeHandler(app, settings.slack_app_token).start()
        else:
            app.start(port=settings.port)
        return 0

    if args.cmd == "draft-buffer":
        from .models import Idea

        for idea in engine.store.find(Idea, status="new")[: args.n]:
            engine.draft_idea(idea.id)
            print(f"Drafted {idea.id}")
        return 0

    if args.cmd == "scan":
        added = engine.scan_news()
        print(f"Added {len(added)} ideas ({sum(1 for i in added if i.urgent)} urgent)")
        return 0

    if args.cmd == "metrics-check":
        print(f"{engine.request_metrics()} post checkpoint(s) due")
        return 0

    if args.cmd == "board-digest":
        print(f"Sent board digest with {engine.send_board_digest()} candidates")
        return 0

    if args.cmd == "board-export":
        import csv
        from pathlib import Path

        from . import board

        rows = engine.board_rows()
        if args.md:
            Path(args.md).write_text(board.to_markdown(rows, board.next_cycle_week()))
            print(f"Wrote {args.md}")
        if args.csv:
            with open(args.csv, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=board.CSV_FIELDS)
                w.writeheader()
                w.writerows(board.to_csv_rows(rows))
            print(f"Wrote {args.csv}")
        return 0

    if args.cmd == "notion-setup":
        from .notion_sync import NotionClient

        db = NotionClient(settings.notion_token).create_database(args.parent_page)
        print(f"Created. Set NOTION_DATABASE_ID={db}")
        return 0

    if args.cmd == "notion-sync":
        print(f"Synced {engine.sync_notion()} rows" if engine.notion else "Set NOTION_TOKEN and NOTION_DATABASE_ID first")
        return 0

    if args.cmd == "edits-summary":
        from .flows import default_month

        month = args.month or default_month()
        path = engine.write_edit_summary(month)
        print(f"Wrote {path}" if path else f"No Floris edits found for {month}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
