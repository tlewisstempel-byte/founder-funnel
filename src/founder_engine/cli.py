"""Command line: run the bot, and jobs a scheduler can trigger.

  founder-engine run                 start the bot (Socket Mode if SLACK_APP_TOKEN is set, else HTTP)
  founder-engine draft-buffer --n 3  draft the N oldest waiting ideas (weekly job)
  founder-engine edits-summary [--month 2026-11]
                                     write voice/edits/YYYY-MM.md from Floris's edits (monthly job)
  founder-engine check               validate config files without connecting to anything
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

    if args.cmd == "edits-summary":
        from .flows import default_month

        month = args.month or default_month()
        path = engine.write_edit_summary(month)
        print(f"Wrote {path}" if path else f"No Floris edits found for {month}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
