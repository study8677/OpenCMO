"""Monitoring service — schedule, run and query monitoring jobs."""

from __future__ import annotations

from opencmo import storage


async def _sync_runtime_job(job_id: int) -> None:
    from opencmo import scheduler

    job = await storage.get_scheduled_job(job_id)
    if job:
        scheduler.sync_job_record(job)


async def create_monitor(
    brand: str,
    url: str,
    category: str,
    job_type: str = "full",
    cron_expr: str = "0 9 * * *",
    keywords: list[str] | None = None,
) -> dict:
    """Create monitor + project + keywords. Returns {project_id, monitor_id, keywords_added}."""
    project_id = await storage.ensure_project(brand, url, category)
    job_id = await storage.add_scheduled_job(project_id, job_type, cron_expr)
    await _sync_runtime_job(job_id)
    kw_added: list[str] = []
    for kw in keywords or []:
        kw = kw.strip()
        if kw:
            kw_id = await storage.add_tracked_keyword(project_id, kw)
            kw_added.append(kw)
            if kw_id:
                await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
    return {"project_id": project_id, "monitor_id": job_id, "keywords_added": kw_added}


async def remove_monitor(job_id: int) -> bool:
    """Remove a scheduled job. Returns True if deleted."""
    ok = await storage.remove_scheduled_job(job_id)
    if ok:
        from opencmo import scheduler

        scheduler.unschedule_job(job_id)
    return ok


async def update_monitor(
    job_id: int,
    *,
    cron_expr: str | None = None,
    enabled: bool | None = None,
) -> bool:
    """Update a scheduled job and reconcile the in-memory scheduler."""
    ok = await storage.update_scheduled_job(job_id, cron_expr=cron_expr, enabled=enabled)
    if ok:
        await _sync_runtime_job(job_id)
    return ok


async def get_monitor(job_id: int) -> dict | None:
    """Find a single monitor by job id."""
    return await storage.get_scheduled_job(job_id)


async def list_monitors() -> list[dict]:
    """Return all scheduled jobs with project info."""
    return await storage.list_scheduled_jobs()


async def get_monitor_history(job_id: int) -> dict | None:
    """Get latest scans for a monitor's project. Returns None if monitor not found."""
    job = await get_monitor(job_id)
    if not job:
        return None
    latest = await storage.get_latest_scans(job["project_id"])
    return {"job": job, "latest": latest}


async def run_monitor(job_id: int) -> dict:
    """Run a monitor scan synchronously. Returns {ok, error?}."""
    job = await get_monitor(job_id)
    if not job:
        return {"ok": False, "error": f"Monitor #{job_id} not found."}

    from opencmo.scheduler import run_scheduled_scan

    await run_scheduled_scan(
        job["project_id"], job["job_type"], job_id, triggered_by="manual"
    )
    return {"ok": True, "job": job}


async def resolve_project(id_or_brand: str) -> tuple[int | None, str]:
    """Resolve project_id from int or brand_name. Returns (id, error_msg)."""
    try:
        pid = int(id_or_brand)
        project = await storage.get_project(pid)
        if project:
            return pid, ""
        return None, f"Project #{pid} not found."
    except ValueError:
        pass

    projects = await storage.list_projects()
    matches = [p for p in projects if p["brand_name"].lower() == id_or_brand.lower()]
    if len(matches) == 1:
        return matches[0]["id"], ""
    elif len(matches) > 1:
        ids = ", ".join(f"#{p['id']}" for p in matches)
        return None, f"Multiple projects match '{id_or_brand}': {ids}. Use project ID instead."
    return None, f"No project found for '{id_or_brand}'."


async def manage_keywords(
    project_id: int,
    action: str = "list",
    keyword: str | None = None,
    keyword_id: int | None = None,
) -> dict:
    """Manage tracked keywords. Returns {action, result}."""
    if action == "list":
        keywords = await storage.list_tracked_keywords(project_id)
        return {"action": "list", "keywords": keywords}
    elif action == "add":
        if not keyword:
            return {"action": "add", "error": "Keyword is required."}
        kw_id = await storage.add_tracked_keyword(project_id, keyword)
        if kw_id:
            await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
        return {"action": "add", "keyword_id": kw_id, "keyword": keyword}
    elif action == "rm":
        if keyword_id is None:
            return {"action": "rm", "error": "keyword_id is required."}
        ok = await storage.remove_tracked_keyword(keyword_id)
        return {"action": "rm", "removed": ok, "keyword_id": keyword_id}
    return {"action": action, "error": f"Unknown action: {action}"}


async def send_project_report(project_id: int) -> dict:
    """Send email report for a project."""
    from opencmo.tools.email_report import send_report_impl

    return await send_report_impl(project_id)


async def regenerate_project_report(project_id: int, kind: str, on_progress=None) -> dict:
    """Generate and persist a strategic or periodic report bundle."""
    project = await storage.get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    from opencmo import reports

    if kind == "strategic":
        return await reports.generate_strategic_report_bundle(project_id, on_progress=on_progress)
    if kind == "periodic":
        return await reports.generate_periodic_report_bundle(project_id, on_progress=on_progress)
    raise ValueError(f"Unsupported report kind: {kind}")


async def get_status_summary() -> list[dict]:
    """Return structured status for all projects (used by Dashboard + CLI /status)."""
    projects = await storage.list_projects()
    result = []
    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        result.append({**p, "latest": latest})
    return result
