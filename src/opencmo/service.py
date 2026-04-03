"""Service layer — shared business logic for CLI and Web.

This module is a backward-compatible re-export layer.  The actual
implementations now live in focused domain modules under ``opencmo.services``:

- ``monitoring_service`` — monitors, keywords, reports, status
- ``approval_service``  — content approval queue and publishing
- ``intelligence_service`` — AI-powered URL analysis and competitor discovery
"""

from __future__ import annotations

# ── Approval & publishing ────────────────────────────────────────────
from opencmo.services.approval_service import (  # noqa: F401
    approve_approval,
    create_approval,
    get_approval,
    list_approvals,
    reject_approval,
)

# ── AI intelligence (URL analysis, competitor discovery) ─────────────
from opencmo.services.intelligence_service import (  # noqa: F401
    analyze_and_enrich_project,
    analyze_url_with_ai,
    discover_competitors,
)

# ── Monitoring & project management ──────────────────────────────────
from opencmo.services.monitoring_service import (  # noqa: F401
    create_monitor,
    get_monitor,
    get_monitor_history,
    get_status_summary,
    list_monitors,
    manage_keywords,
    regenerate_project_report,
    remove_monitor,
    resolve_project,
    run_monitor,
    send_project_report,
    update_monitor,
)
