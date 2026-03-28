"""SQLite storage layer for persistent scan data.

This package re-exports all public functions from its submodules so that
existing code using ``from opencmo import storage`` followed by
``storage.some_function()`` continues to work unchanged.
"""

from __future__ import annotations

# Expose internal DB helpers (tests patch _DB_PATH and _SCHEMA_READY_FOR)
from opencmo.storage._db import (
    _SCHEMA,
    ensure_db,
    get_db,
)

# --- Projects ---
from opencmo.storage.projects import (
    ensure_project,
    update_project,
    get_project,
    list_projects,
    delete_project,
)

# --- Scans (SEO / GEO / Community) ---
from opencmo.storage.scans import (
    save_seo_scan,
    save_geo_scan,
    save_community_scan,
    get_seo_history,
    get_geo_history,
    get_community_history,
    get_latest_scans,
    get_previous_scans,
)

# --- Discussions ---
from opencmo.storage.discussions import (
    upsert_tracked_discussion,
    save_discussion_snapshot,
    get_tracked_discussions,
    get_discussion_snapshots,
)

# --- Scheduled jobs ---
from opencmo.storage.jobs import (
    add_scheduled_job,
    list_scheduled_jobs,
    get_scheduled_job,
    remove_scheduled_job,
    update_scheduled_job,
    update_job_last_run,
)

# --- SERP tracking ---
from opencmo.storage.serp import (
    add_tracked_keyword,
    list_tracked_keywords,
    remove_tracked_keyword,
    save_serp_snapshot,
    get_serp_history,
    get_all_serp_latest,
)

# --- Scan runs / findings / recommendations ---
from opencmo.storage.scan_runs import (
    create_scan_run,
    list_scan_runs_by_monitor,
    update_scan_run,
    add_scan_run_step,
    replace_scan_artifacts,
    get_task_findings,
    get_task_findings_by_project,
    get_task_recommendations,
    get_latest_monitoring_summary,
)

# --- Chat sessions ---
from opencmo.storage.chat import (
    create_chat_session,
    list_chat_sessions,
    get_chat_session,
    update_chat_session,
    delete_chat_session,
    clear_chat_sessions,
)

# --- Settings ---
from opencmo.storage.settings import (
    get_setting,
    set_setting,
    delete_setting,
)

# --- Approvals ---
from opencmo.storage.approvals import (
    create_approval,
    get_approval,
    list_approvals,
    update_approval_status,
    create_approval_with_source,
)

# --- Competitors ---
from opencmo.storage.competitors import (
    add_competitor,
    list_competitors,
    get_competitor,
    remove_competitor,
    add_competitor_keyword,
    list_competitor_keywords,
)

# --- Graph expansion ---
from opencmo.storage.graph import (
    get_or_create_expansion,
    get_expansion,
    update_expansion,
    seed_expansion_nodes,
    get_min_unexplored_wave,
    get_frontier_nodes,
    mark_node_explored,
    add_expansion_node,
    add_expansion_edge,
    reset_expansion,
    seed_node_if_expansion_exists,
    fix_stale_expansions,
    get_graph_data,
)

# --- Campaigns ---
from opencmo.storage.campaigns import (
    create_campaign_run,
    add_campaign_artifact,
    update_campaign_status,
    get_campaign_run,
    list_campaign_runs,
)

# --- Insights + autopilot ---
from opencmo.storage.insights import (
    save_insight,
    is_insight_duplicate,
    list_insights,
    mark_insight_read,
    get_insights_summary,
    get_pending_actionable_insights,
    update_insight_execution,
    snapshot_project_metrics,
    is_project_autopilot_enabled,
    count_recent_autopilot_approvals,
)

# --- GEO tools (citability / crawler / brand presence) ---
from opencmo.storage.geo_tools import (
    save_citability_scan,
    get_citability_history,
    save_ai_crawler_scan,
    get_ai_crawler_history,
    save_brand_presence_scan,
    get_brand_presence_history,
)

# --- Reports ---
from opencmo.storage.reports import (
    create_report_bundle,
    list_reports,
    get_report,
    get_latest_report,
    get_latest_reports,
)


# ---------------------------------------------------------------------------
# Patch propagation: tests use ``patch.object(storage, "_DB_PATH", ...)``
# which sets the attribute on *this* module.  We need that change to land
# on ``_db._DB_PATH`` so that ``get_db()`` picks up the patched path.
# ---------------------------------------------------------------------------
import sys as _sys
from opencmo.storage import _db as _db_module


def __getattr__(name: str):
    if name == "_DB_PATH":
        return _db_module._DB_PATH
    if name == "_SCHEMA_READY_FOR":
        return _db_module._SCHEMA_READY_FOR
    raise AttributeError(f"module 'opencmo.storage' has no attribute {name!r}")


# Called by ``setattr(storage, "_DB_PATH", value)`` — i.e. when unittest.mock
# restores the original value as well as when it patches.
_PROPAGATED_ATTRS = {"_DB_PATH", "_SCHEMA_READY_FOR"}

_original_module = _sys.modules[__name__]


class _PatchableModule(type(_original_module)):
    """Module subclass that propagates attribute writes to _db."""
    def __setattr__(self, name, value):
        if name in _PROPAGATED_ATTRS:
            setattr(_db_module, name, value)
        super().__setattr__(name, value)

    def __getattr__(self, name):
        if name in _PROPAGATED_ATTRS:
            return getattr(_db_module, name)
        raise AttributeError(f"module 'opencmo.storage' has no attribute {name!r}")


_sys.modules[__name__].__class__ = _PatchableModule


__all__ = [
    # _db
    "_DB_PATH", "_SCHEMA", "_SCHEMA_READY_FOR", "ensure_db", "get_db",
    # projects
    "ensure_project", "update_project", "get_project", "list_projects", "delete_project",
    # scans
    "save_seo_scan", "save_geo_scan", "save_community_scan",
    "get_seo_history", "get_geo_history", "get_community_history",
    "get_latest_scans", "get_previous_scans",
    # discussions
    "upsert_tracked_discussion", "save_discussion_snapshot",
    "get_tracked_discussions", "get_discussion_snapshots",
    # jobs
    "add_scheduled_job", "list_scheduled_jobs", "get_scheduled_job",
    "remove_scheduled_job", "update_scheduled_job", "update_job_last_run",
    # serp
    "add_tracked_keyword", "list_tracked_keywords", "remove_tracked_keyword",
    "save_serp_snapshot", "get_serp_history", "get_all_serp_latest",
    # scan_runs
    "create_scan_run", "list_scan_runs_by_monitor", "update_scan_run",
    "add_scan_run_step", "replace_scan_artifacts",
    "get_task_findings", "get_task_findings_by_project",
    "get_task_recommendations", "get_latest_monitoring_summary",
    # chat
    "create_chat_session", "list_chat_sessions", "get_chat_session",
    "update_chat_session", "delete_chat_session", "clear_chat_sessions",
    # settings
    "get_setting", "set_setting", "delete_setting",
    # approvals
    "create_approval", "get_approval", "list_approvals",
    "update_approval_status", "create_approval_with_source",
    # competitors
    "add_competitor", "list_competitors", "get_competitor",
    "remove_competitor", "add_competitor_keyword", "list_competitor_keywords",
    # graph
    "get_or_create_expansion", "get_expansion", "update_expansion",
    "seed_expansion_nodes", "get_min_unexplored_wave", "get_frontier_nodes",
    "mark_node_explored", "add_expansion_node", "add_expansion_edge",
    "reset_expansion", "seed_node_if_expansion_exists", "fix_stale_expansions",
    "get_graph_data",
    # campaigns
    "create_campaign_run", "add_campaign_artifact", "update_campaign_status",
    "get_campaign_run", "list_campaign_runs",
    # insights
    "save_insight", "is_insight_duplicate", "list_insights",
    "mark_insight_read", "get_insights_summary",
    "get_pending_actionable_insights", "update_insight_execution",
    "snapshot_project_metrics", "is_project_autopilot_enabled",
    "count_recent_autopilot_approvals",
    # geo_tools
    "save_citability_scan", "get_citability_history",
    "save_ai_crawler_scan", "get_ai_crawler_history",
    "save_brand_presence_scan", "get_brand_presence_history",
    # reports
    "create_report_bundle", "list_reports", "get_report",
    "get_latest_report", "get_latest_reports",
]
