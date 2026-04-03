import asyncio
import shlex

from agents import Runner
from dotenv import load_dotenv

from opencmo.agents.cmo import cmo_agent


async def _handle_monitor(args: list[str]) -> str:
    """Handle /monitor subcommands."""
    from opencmo import service

    if not args:
        return "Usage: /monitor add|list|remove|run|history ..."

    sub = args[0]

    if sub == "add":
        # /monitor add <brand> <url> <category> [--type full] [--cron "0 9 * * *"] [--keywords "kw1,kw2"]
        if len(args) < 4:
            return "Usage: /monitor add <brand_name> <url> <category> [--type full|seo|geo|community] [--cron '0 9 * * *'] [--keywords 'kw1,kw2']"
        brand, url, category = args[1], args[2], args[3]
        job_type = "full"
        cron_expr = "0 9 * * *"
        keywords_str = ""
        i = 4
        while i < len(args):
            if args[i] == "--type" and i + 1 < len(args):
                job_type = args[i + 1]
                i += 2
            elif args[i] == "--cron" and i + 1 < len(args):
                cron_expr = args[i + 1]
                i += 2
            elif args[i] == "--keywords" and i + 1 < len(args):
                keywords_str = args[i + 1]
                i += 2
            else:
                i += 1

        kw_list = [k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else []
        result = await service.create_monitor(brand, url, category, job_type, cron_expr, kw_list)
        kw_msg = f"\n  Keywords tracked: {', '.join(result['keywords_added'])}" if result["keywords_added"] else ""
        return (
            f"Monitor #{result['monitor_id']} created (project #{result['project_id']}): {brand} ({url}) — "
            f"{job_type} scan, cron: {cron_expr}{kw_msg}"
        )

    elif sub == "list":
        jobs = await service.list_monitors()
        if not jobs:
            return "No monitors configured. Use /monitor add to create one."
        lines = ["| ID | PID | Brand | URL | Type | Cron | Enabled | Last Run |",
                 "|----|-----|-------|-----|------|------|---------|----------|"]
        for j in jobs:
            lines.append(
                f"| {j['id']} | {j['project_id']} | {j['brand_name']} | {j['url'][:30]} | {j['job_type']} "
                f"| {j['cron_expr']} | {'Yes' if j['enabled'] else 'No'} | {j['last_run_at'] or 'never'} |"
            )
        return "\n".join(lines)

    elif sub == "remove":
        if len(args) < 2:
            return "Usage: /monitor remove <id>"
        job_id = int(args[1])
        ok = await service.remove_monitor(job_id)
        return f"Monitor #{job_id} removed." if ok else f"Monitor #{job_id} not found."

    elif sub == "run":
        if len(args) < 2:
            return "Usage: /monitor run <id>"
        job_id = int(args[1])
        result = await service.run_monitor(job_id)
        if not result["ok"]:
            return result["error"]
        print(f"Running {result['job']['job_type']} scan for {result['job']['brand_name']}...")
        return f"Scan complete for monitor #{job_id}."

    elif sub == "history":
        job_id = int(args[1]) if len(args) > 1 else None
        if not job_id:
            return "Usage: /monitor history <id>"
        data = await service.get_monitor_history(job_id)
        if not data:
            return f"Monitor #{job_id} not found."
        job = data["job"]
        latest = data["latest"]
        lines = [f"Latest scans for {job['brand_name']}:"]
        for scan_type, scan_data in latest.items():
            if scan_type == "serp":
                if scan_data:
                    lines.append(f"  serp: {len(scan_data)} keyword(s) tracked")
                else:
                    lines.append("  serp: no data")
            elif scan_data:
                lines.append(f"  {scan_type}: {scan_data}")
            else:
                lines.append(f"  {scan_type}: no data")
        return "\n".join(lines)

    return f"Unknown subcommand: {sub}"


async def _handle_keywords(args: list[str]) -> str:
    """Handle /keywords <id_or_brand> [list|add|rm] subcommands."""
    from opencmo import service

    if not args:
        return "Usage: /keywords <project_id_or_brand> [list|add \"keyword\"|rm <keyword_id>]"

    pid, err = await service.resolve_project(args[0])
    if err:
        return err

    sub = args[1] if len(args) > 1 else "list"

    if sub == "list":
        result = await service.manage_keywords(pid, "list")
        keywords = result["keywords"]
        if not keywords:
            return f"No tracked keywords for project #{pid}. Use: /keywords {pid} add \"keyword\""
        lines = [f"Tracked keywords for project #{pid}:"]
        for kw in keywords:
            lines.append(f"  [{kw['id']}] {kw['keyword']} (since {kw['created_at'][:10]})")
        return "\n".join(lines)

    elif sub == "add":
        if len(args) < 3:
            return "Usage: /keywords <id> add \"keyword\""
        keyword = " ".join(args[2:])
        result = await service.manage_keywords(pid, "add", keyword=keyword)
        return f"Keyword '{result['keyword']}' added (id: {result['keyword_id']}) to project #{pid}."

    elif sub == "rm":
        if len(args) < 3:
            return "Usage: /keywords <id> rm <keyword_id>"
        kw_id = int(args[2])
        result = await service.manage_keywords(pid, "rm", keyword_id=kw_id)
        return f"Keyword #{kw_id} removed." if result["removed"] else f"Keyword #{kw_id} not found."

    return f"Unknown subcommand: {sub}. Use list, add, or rm."


async def _handle_report(args: list[str]) -> str:
    """Handle /report <project_id> — send email report."""
    from opencmo import service

    if not args:
        return "Usage: /report <project_id>"

    pid, err = await service.resolve_project(args[0])
    if err:
        return err

    print(f"Generating report for project #{pid}...")
    result = await service.send_project_report(pid)
    if result["ok"]:
        return f"Report sent to {result['recipient']}"
    else:
        return f"Failed: {result['error']}"


async def _handle_status() -> str:
    """Handle /status command."""
    from opencmo import service

    projects = await service.get_status_summary()
    if not projects:
        return "No projects tracked yet. Use /monitor add to start."

    lines = ["# Project Status\n"]
    for p in projects:
        latest = p["latest"]
        lines.append(f"## [#{p['id']}] {p['brand_name']} ({p['url']})")
        seo = latest.get("seo")
        geo = latest.get("geo")
        comm = latest.get("community")
        serp = latest.get("serp", [])
        if seo and seo.get("score") is not None:
            seo_str = f"score {seo['score']:.0%}, last {seo['scanned_at'][:10]}"
        elif seo:
            seo_str = f"last {seo['scanned_at'][:10]}"
        else:
            seo_str = "no data"
        geo_str = f"score {geo['score']}/100, last {geo['scanned_at'][:10]}" if geo else "no data"
        comm_str = f"{comm['total_hits']} hits, last {comm['scanned_at'][:10]}" if comm else "no data"
        lines.append(f"  SEO: {seo_str}")
        lines.append(f"  GEO: {geo_str}")
        lines.append(f"  Community: {comm_str}")
        if serp:
            serp_parts = []
            for s in serp:
                pos = f"#{s['position']}" if s['position'] else "n/r"
                serp_parts.append(f"{s['keyword']}={pos}")
            lines.append(f"  SERP: {', '.join(serp_parts)}")
        lines.append("")

    return "\n".join(lines)


def _handle_web(args: list[str]) -> None:
    """Handle /web command — start web dashboard."""
    try:
        from opencmo.web.app import run_server
    except ImportError:
        print("Web dashboard requires additional dependencies. Install with: pip install opencmo[web]")
        return

    port = 8080
    for i, a in enumerate(args):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    print(f"Starting web dashboard on http://localhost:{port}")
    run_server(port=port)


async def run_cli():
    print("=" * 60)
    print("  OpenCMO - Your AI Chief Marketing Officer")
    print("  Type a product URL and what you need, or 'quit' to exit.")
    print("  Commands: /monitor, /status, /keywords, /report, /web")
    print("=" * 60)
    print()

    input_items = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # Handle CLI commands
        if user_input.startswith("/"):
            try:
                parts = shlex.split(user_input)
            except ValueError:
                parts = user_input.split()

            cmd = parts[0].lower()

            if cmd == "/monitor":
                try:
                    result = await _handle_monitor(parts[1:])
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
                continue

            elif cmd == "/status":
                try:
                    result = await _handle_status()
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
                continue

            elif cmd == "/keywords":
                try:
                    result = await _handle_keywords(parts[1:])
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
                continue

            elif cmd == "/report":
                try:
                    result = await _handle_report(parts[1:])
                    print(f"\n{result}\n")
                except Exception as e:
                    print(f"\nError: {e}\n")
                continue

            elif cmd == "/web":
                _handle_web(parts[1:])
                continue

            else:
                print(f"\nUnknown command: {cmd}. Available: /monitor, /status, /keywords, /report, /web\n")
                continue

        input_items.append({"role": "user", "content": user_input})

        print("\nCMO is working...\n")
        result = await Runner.run(cmo_agent, input_items, max_turns=15)

        print(f"[{result.last_agent.name}]")
        print(result.final_output)
        print()

        input_items = result.to_input_list()
        # Truncate history to prevent context explosion with search/SEO/GEO reports
        MAX_HISTORY = 20
        if len(input_items) > MAX_HISTORY:
            input_items = input_items[:1] + input_items[-(MAX_HISTORY - 1):]


def main():
    load_dotenv()

    # Disable tracing for non-OpenAI providers (avoids 401 noise)
    from opencmo.config import is_custom_provider
    if is_custom_provider():
        from agents import set_tracing_disabled
        set_tracing_disabled(True)

    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
