"""Persistent lifetime print history & failure snapshot manager for Bambu AI Guard."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER, STATUS_FAILURE, STATUS_WARNING
from .vision import InspectionVerdict

STORAGE_VERSION = 1


class PrintHistoryStore:
    """Manages lifetime print history in HA .storage and archives failure/warning snapshots."""

    def __init__(self, hass: HomeAssistant, printer_serial: str) -> None:
        """Initialize the persistent print history store."""
        self._hass = hass
        self._serial = printer_serial
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_history_{printer_serial}"
        )
        self._lock = asyncio.Lock()
        self.prints: list[dict[str, Any]] = []
        self.recent_inspections: list[dict[str, Any]] = []
        self._active_print: dict[str, Any] | None = None

        # Media directory for failure/warning snapshots
        self._media_dir = Path(hass.config.path("www", DOMAIN, printer_serial))

    async def async_load(self) -> None:
        """Load persisted print history from disk."""
        async with self._lock:
            data = await self._store.async_load()
            if isinstance(data, dict):
                self.prints = list(data.get("prints", []))
                self.recent_inspections = list(data.get("recent_inspections", []))

    async def _async_save(self) -> None:
        """Persist print history atomically."""
        await self._store.async_save(
            {
                "prints": self.prints,
                "recent_inspections": self.recent_inspections[-200:],
            }
        )

    def _save_snapshot_sync(self, filename: str, jpeg_bytes: bytes) -> str:
        """Write a JPEG snapshot to /config/www/bambu_ai_guard/<serial>/ and return its local URL."""
        self._media_dir.mkdir(parents=True, exist_ok=True)
        target = self._media_dir / filename
        target.write_bytes(jpeg_bytes)
        return f"/local/{DOMAIN}/{self._serial}/{filename}"

    async def async_record_inspection(
        self,
        print_name: str,
        verdict: InspectionVerdict,
        jpeg_bytes: bytes | None,
        auto_paused: bool = False,
    ) -> str | None:
        """Record a checkpoint inspection and update the active print record in lifetime history."""
        async with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            clean_name = (print_name or "Untitled Print").strip()

            # Start a new active print record if none exists or if layer reset back to 1
            if (
                self._active_print is None
                or self._active_print.get("print_name") != clean_name
                or (
                    verdict.layer is not None
                    and verdict.layer <= 2
                    and self._active_print.get("last_layer", 0) > 5
                )
            ):
                print_id = f"{int(datetime.now(timezone.utc).timestamp())}_{clean_name[:24].replace(' ', '_')}"
                self._active_print = {
                    "id": print_id,
                    "print_name": clean_name,
                    "started_at": now_iso,
                    "updated_at": now_iso,
                    "last_layer": verdict.layer or 0,
                    "total_layers": verdict.total_layers or 0,
                    "inspections_count": 0,
                    "warnings_count": 0,
                    "failures_count": 0,
                    "auto_paused": False,
                    "status": "OK",
                    "worst_defect": "none",
                    "max_spaghetti_pct": 0.0,
                    "max_warping_pct": 0.0,
                    "max_detachment_pct": 0.0,
                    "max_first_layer_pct": 0.0,
                    "max_severity": 1.0,
                    "snapshot_url": None,
                }
                self.prints.append(self._active_print)

            rec = self._active_print
            rec["updated_at"] = now_iso
            if verdict.layer is not None:
                rec["last_layer"] = verdict.layer
            if verdict.total_layers:
                rec["total_layers"] = verdict.total_layers
            rec["inspections_count"] = int(rec.get("inspections_count", 0)) + 1

            sp_pct = round((verdict.spaghetti_prob or 0.0) * 100.0, 1)
            wp_pct = round((verdict.warping_prob or 0.0) * 100.0, 1)
            dt_pct = round((verdict.detachment_prob or 0.0) * 100.0, 1)
            fl_pct = round((verdict.first_layer_prob or 0.0) * 100.0, 1)
            sev = round(verdict.severity or 1.0, 2)

            rec["max_spaghetti_pct"] = max(float(rec.get("max_spaghetti_pct", 0.0)), sp_pct)
            rec["max_warping_pct"] = max(float(rec.get("max_warping_pct", 0.0)), wp_pct)
            rec["max_detachment_pct"] = max(float(rec.get("max_detachment_pct", 0.0)), dt_pct)
            rec["max_first_layer_pct"] = max(float(rec.get("max_first_layer_pct", 0.0)), fl_pct)
            rec["max_severity"] = max(float(rec.get("max_severity", 1.0)), sev)

            snapshot_url: str | None = None
            is_defect = verdict.status in (STATUS_FAILURE, STATUS_WARNING)

            if verdict.status == STATUS_FAILURE:
                rec["failures_count"] = int(rec.get("failures_count", 0)) + 1
                rec["status"] = STATUS_FAILURE
                rec["worst_defect"] = verdict.failure_type
            elif verdict.status == STATUS_WARNING:
                rec["warnings_count"] = int(rec.get("warnings_count", 0)) + 1
                if rec.get("status") != STATUS_FAILURE:
                    rec["status"] = STATUS_WARNING
                    rec["worst_defect"] = verdict.failure_type

            if auto_paused:
                rec["auto_paused"] = True

            # Save failure/warning snapshots permanently on disk; overwrite a single "latest_ok.jpg" for clean checks
            if jpeg_bytes:
                try:
                    if is_defect:
                        fname = f"{rec['id']}_L{verdict.layer or 0}_{verdict.failure_type}.jpg"
                    else:
                        fname = "latest_clean_check.jpg"
                    snapshot_url = await self._hass.async_add_executor_job(
                        self._save_snapshot_sync, fname, jpeg_bytes
                    )
                    if is_defect:
                        rec["snapshot_url"] = snapshot_url
                except Exception as err:  # noqa: BLE001
                    LOGGER.warning("Could not save history snapshot: %s", err)

            checkpoint_item = {
                "timestamp": now_iso,
                "print_name": clean_name,
                "layer": verdict.layer,
                "total_layers": verdict.total_layers,
                "trigger": verdict.trigger_reason,
                "status": verdict.status,
                "failure_type": verdict.failure_type,
                "confidence_pct": round(verdict.confidence * 100.0, 1)
                if verdict.confidence is not None
                else None,
                "spaghetti_pct": sp_pct,
                "warping_pct": wp_pct,
                "detachment_pct": dt_pct,
                "first_layer_pct": fl_pct,
                "severity": sev,
                "latency_ms": verdict.latency_ms,
                "snapshot_url": snapshot_url if is_defect else None,
            }
            self.recent_inspections.append(checkpoint_item)
            if len(self.recent_inspections) > 200:
                self.recent_inspections = self.recent_inspections[-200:]

            await self._async_save()
            return snapshot_url

    async def async_finish_active_print(self, final_state: str) -> None:
        """Mark the currently tracked print job as completed/idle."""
        async with self._lock:
            if self._active_print is not None:
                self._active_print["ended_at"] = datetime.now(timezone.utc).isoformat()
                self._active_print["printer_final_state"] = final_state
                self._active_print = None
                await self._async_save()

    async def async_purge(
        self,
        keep_last_prints: int = 50,
        older_than_days: int | None = None,
    ) -> dict[str, int]:
        """Manually purge print records older than the last X prints (or older than Y days)."""
        async with self._lock:
            before_prints = len(self.prints)
            before_checks = len(self.recent_inspections)

            kept_prints = list(self.prints)
            if older_than_days is not None and older_than_days >= 0:
                cutoff_ts = datetime.now(timezone.utc).timestamp() - (
                    older_than_days * 86400
                )
                filtered = []
                for p in kept_prints:
                    try:
                        ts = datetime.fromisoformat(
                            str(p.get("started_at", ""))
                        ).timestamp()
                    except ValueError:
                        ts = cutoff_ts + 1
                    if ts >= cutoff_ts:
                        filtered.append(p)
                kept_prints = filtered

            if keep_last_prints <= 0:
                kept_prints = []
            elif len(kept_prints) > keep_last_prints:
                kept_prints = kept_prints[-keep_last_prints:]

            kept_ids = {p.get("id") for p in kept_prints}
            removed_prints = [
                p for p in self.prints if p.get("id") not in kept_ids
            ]
            self.prints = kept_prints

            if keep_last_prints <= 0:
                self.recent_inspections = []
                self._active_print = None
                await self._hass.async_add_executor_job(
                    self._delete_all_snapshots_sync
                )
            else:
                await self._hass.async_add_executor_job(
                    self._delete_snapshots_for_prints_sync, removed_prints
                )
                max_checks = max(20, keep_last_prints * 5)
                if len(self.recent_inspections) > max_checks:
                    self.recent_inspections = self.recent_inspections[-max_checks:]

            await self._async_save()
            return {
                "prints_removed": before_prints - len(self.prints),
                "checkpoints_removed": before_checks - len(self.recent_inspections),
                "prints_remaining": len(self.prints),
            }

    def _delete_snapshots_for_prints_sync(
        self, removed_prints: list[dict[str, Any]]
    ) -> None:
        """Delete snapshot JPEGs belonging to purged print jobs."""
        if not self._media_dir.exists():
            return
        for p in removed_prints:
            pid = p.get("id")
            if pid:
                for jpg in self._media_dir.glob(f"{pid}_*.jpg"):
                    jpg.unlink(missing_ok=True)

    def _delete_all_snapshots_sync(self) -> None:
        """Remove all saved snapshots in the printer's media folder."""
        if not self._media_dir.exists():
            return
        for jpg in self._media_dir.glob("*.jpg"):
            jpg.unlink(missing_ok=True)
