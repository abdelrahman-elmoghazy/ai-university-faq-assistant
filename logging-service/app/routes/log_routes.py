"""
Log Routes
  POST  /internal/logs          — internal endpoint (worker/auth) to write logs
  GET   /api/logs               — paginated log listing (for dashboard / admin)
  GET   /api/logs/stats         — aggregate counts per action (for monitoring)
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.log_entry import LogEntry

logs_bp = Blueprint("logs", __name__)
logger  = logging.getLogger(__name__)


# ─── Internal write endpoint ─────────────────────────────────────────────────

@logs_bp.route("/internal/logs", methods=["POST"])
def create_log():
    """Accept a structured log event from internal services (worker, auth)."""
    # Light internal auth — services share the same API key
    key = request.headers.get("X-Internal-Key") or request.json.get("_internal_key", "")
    expected = current_app.config.get("INTERNAL_API_KEY", "")
    if expected and key != expected:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}

    entry = LogEntry(
        source     = data.get("source", "unknown"),
        action     = data.get("action", "unknown"),
        user_id    = data.get("user_id"),
        user_email = data.get("user_email"),
        ip_address = data.get("ip_address"),
        status     = data.get("status"),
        details    = data.get("details"),
    )
    db.session.add(entry)
    db.session.commit()

    logger.info(f"Log saved: [{entry.action}] from {entry.source}")
    return jsonify({"id": entry.id, "saved": True}), 201


# ─── Admin / dashboard read endpoints ────────────────────────────────────────

@logs_bp.route("/api/logs", methods=["GET"])
def list_logs():
    """Return paginated log entries, newest first."""
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    action   = request.args.get("action")
    source   = request.args.get("source")
    status   = request.args.get("status")
    since    = request.args.get("since")   # ISO date

    q = LogEntry.query

    if action:
        q = q.filter(LogEntry.action == action)
    if source:
        q = q.filter(LogEntry.source == source)
    if status:
        q = q.filter(LogEntry.status == status)
    if since:
        try:
            dt = datetime.fromisoformat(since)
            q  = q.filter(LogEntry.created_at >= dt)
        except ValueError:
            pass

    pagination = q.order_by(LogEntry.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "logs":       [e.to_dict() for e in pagination.items],
        "total":      pagination.total,
        "page":       page,
        "per_page":   per_page,
        "pages":      pagination.pages,
    })


@logs_bp.route("/api/logs/stats", methods=["GET"])
def log_stats():
    """Return aggregate counts per action for the last N hours."""
    hours = int(request.args.get("hours", 24))
    since = datetime.utcnow() - timedelta(hours=hours)

    from sqlalchemy import func

    rows = (
        db.session.query(
            LogEntry.action,
            LogEntry.status,
            func.count(LogEntry.id).label("count")
        )
        .filter(LogEntry.created_at >= since)
        .group_by(LogEntry.action, LogEntry.status)
        .all()
    )

    stats = {}
    for action, status, count in rows:
        if action not in stats:
            stats[action] = {"total": 0}
        stats[action]["total"] += count
        stats[action][status or "unknown"] = count

    return jsonify({
        "window_hours": hours,
        "since":        since.isoformat(),
        "stats":        stats,
    })


@logs_bp.route("/api/logs/worker-status", methods=["GET"])
def worker_status():
    """Return latest worker / background job log entries."""
    worker_actions = ["worker_status", "background_job_status"]
    entries = (
        LogEntry.query
        .filter(LogEntry.action.in_(worker_actions))
        .order_by(LogEntry.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([e.to_dict() for e in entries])
