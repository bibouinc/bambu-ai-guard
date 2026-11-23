"""Timelapse Replay Simulator — run Bambu AI Guard on previous prints (local /media or printer SD card FTPS)."""
from __future__ import annotations

import asyncio
import base64
import ftplib
import json
from pathlib import Path
import ssl
import subprocess
import tempfile
from typing import Any

from .const import CRITICAL_CHECKPOINT_LAYERS, LOGGER, STATUS_FAILURE
from .vision import GeminiDecisionsInspector


class _ImplicitFTPS(ftplib.FTP_TLS):
    """Implicit FTPS (TLS on port 990) used by Bambu Lab printers for SD card timelapses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self) -> Any:
        return self._sock

    @sock.setter
    def sock(self, value: Any) -> None:
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

    def ntransfercmd(self, cmd: str, rest: Any = None) -> Any:
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session
            )
        return conn, size


def _list_local_timelapses_sync() -> list[dict[str, Any]]:
    """Scan Home Assistant /media directories for Bambu Lab timelapse videos."""
    candidates: list[dict[str, Any]] = []
    search_dirs = [
        Path("/media/bambu-timelapses"),
        Path("/media/timelapse"),
        Path("/media"),
    ]
    seen_paths: set[str] = set()

    for base in search_dirs:
        if not base.exists() or not base.is_dir():
            continue
        # Optional friendly print names mapping if present
        names_map: dict[str, str] = {}
        names_file = base / ".print_names.json"
        if names_file.exists():
            try:
                names_map = json.loads(names_file.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass

        for ext in ("*.mp4", "*.avi"):
            for f in base.glob(ext):
                if f.name.startswith("."):
                    continue
                real = str(f.resolve())
                if real in seen_paths:
                    continue
                seen_paths.add(real)
                try:
                    stat = f.stat()
                    if stat.st_size < 10_000:
                        continue
                    label = names_map.get(f.name) or f.stem
                    candidates.append(
                        {
                            "id": f"local:{real}",
                            "name": f.name,
                            "label": label,
                            "source": "media",
                            "path": real,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "mtime": stat.st_mtime,
                        }
                    )
                except OSError:
                    continue

    candidates.sort(key=lambda x: x["mtime"], reverse=True)
    return candidates[:40]


def _list_ftps_timelapses_sync(host: str, access_code: str) -> list[dict[str, Any]]:
    """List timelapse videos directly from Bambu Lab printer SD card via Implicit FTPS (port 990)."""
    if not host or not access_code:
        return []
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    items: list[dict[str, Any]] = []
    try:
        ftp = _ImplicitFTPS(context=ssl_ctx)
        ftp.connect(host, 990, timeout=6)
        ftp.login("bblp", access_code)
        ftp.prot_p()
        ftp.cwd("/timelapse")
        names = ftp.nlst()
        for name in sorted(names, reverse=True):
            low = name.lower()
            if low.endswith((".mp4", ".avi")) and not name.startswith("."):
                items.append(
                    {
                        "id": f"ftps:{name}",
                        "name": name,
                        "label": Path(name).stem,
                        "source": "printer_sd",
                        "path": f"/timelapse/{name}",
                        "size_mb": None,
                        "mtime": 0,
                    }
                )
        ftp.quit()
    except Exception as err:  # noqa: BLE001
        LOGGER.debug("FTPS timelapse list skipped (%s): %s", host, err)
    return items[:25]


def _download_ftps_timelapse_sync(
    host: str, access_code: str, remote_name: str, dest_path: Path
) -> bool:
    """Download a timelapse video from printer SD card via Implicit FTPS (port 990)."""
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    try:
        ftp = _ImplicitFTPS(context=ssl_ctx)
        ftp.connect(host, 990, timeout=10)
        ftp.login("bblp", access_code)
        ftp.prot_p()
        ftp.cwd("/timelapse")
        with dest_path.open("wb") as fh:
            ftp.retrbinary(f"RETR {remote_name}", fh.write)
        ftp.quit()
        return dest_path.exists() and dest_path.stat().st_size > 10_000
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("FTPS download failed for %s: %s", remote_name, err)
        return False


def _probe_and_extract_frames_sync(
    video_path: Path, layer_interval: int, max_checkpoints: int = 16
) -> tuple[int, list[tuple[int, bytes]]]:
    """Use ffprobe + ffmpeg to extract checkpoint frames from a Bambu timelapse video."""
    # 1. Probe frame count
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_packets",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_packets,nb_frames",
            "-of",
            "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    total_frames = 0
    try:
        info = json.loads(probe.stdout or "{}")
        streams = info.get("streams", [])
        if streams:
            s0 = streams[0]
            raw_n = s0.get("nb_frames") or s0.get("nb_read_packets") or "0"
            if str(raw_n).isdigit():
                total_frames = int(raw_n)
    except Exception:  # noqa: BLE001
        total_frames = 0

    if total_frames <= 0:
        total_frames = 60

    # 2. Build checkpoint frame indices (1-based layers)
    step = max(1, int(layer_interval))
    indices: list[int] = []
    for cl in (1, *CRITICAL_CHECKPOINT_LAYERS):
        if cl <= total_frames and cl not in indices:
            indices.append(cl)
    for idx in range(step, total_frames + 1, step):
        if idx not in indices:
            indices.append(idx)
    if total_frames not in indices:
        indices.append(total_frames)
    indices.sort()

    # Cap total checkpoints evenly so simulation stays snappy & quota-friendly
    if len(indices) > max_checkpoints:
        stride = len(indices) / float(max_checkpoints)
        indices = sorted({indices[min(len(indices) - 1, int(i * stride))] for i in range(max_checkpoints)})
        if total_frames not in indices:
            indices[-1] = total_frames

    # 3. Extract selected frames in a single fast ffmpeg pass using select filter
    select_expr = "+".join(f"eq(n\\,{idx - 1})" for idx in indices)
    extracted: list[tuple[int, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="bambu_replay_") as tmpdir:
        out_pattern = str(Path(tmpdir) / "frame_%04d.jpg")
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(video_path),
                "-vf",
                f"select='{select_expr}',scale=960:-1",
                "-vsync",
                "0",
                "-q:v",
                "4",
                out_pattern,
            ],
            capture_output=True,
            timeout=45,
            check=False,
        )
        jpgs = sorted(Path(tmpdir).glob("frame_*.jpg"))
        for layer_idx, jpg_path in zip(indices, jpgs, strict=False):
            raw = jpg_path.read_bytes()
            if len(raw) > 2000:
                extracted.append((layer_idx, raw))

    return (total_frames, extracted)


class PrintReplaySimulator:
    """Runs dry-run AI simulations on recorded Bambu Lab timelapse videos."""

    def __init__(self) -> None:
        self.running: bool = False
        self.progress: dict[str, Any] = {
            "running": False,
            "video_name": None,
            "total_layers": 0,
            "checked": 0,
            "total_checkpoints": 0,
            "would_pause": False,
            "pause_layer": None,
            "pause_reason": None,
            "results": [],
            "error": None,
        }

    async def async_list_timelapses(
        self, hass: Any, printer_ip: str = "", access_code: str = ""
    ) -> list[dict[str, Any]]:
        """List timelapses from local HA /media folders and optionally printer SD card."""
        local_list = await hass.async_add_executor_job(_list_local_timelapses_sync)
        if local_list:
            return local_list
        if printer_ip and access_code:
            return await hass.async_add_executor_job(
                _list_ftps_timelapses_sync, printer_ip, access_code
            )
        return []

    async def async_run_simulation(
        self,
        hass: Any,
        inspector: GeminiDecisionsInspector,
        video_id: str,
        printer_model: str,
        kinematics: str,
        layer_interval: int,
        auto_pause_threshold: int,
        printer_ip: str = "",
        access_code: str = "",
    ) -> dict[str, Any]:
        """Run a full checkpoint-by-checkpoint AI replay simulation without touching the real printer."""
        if self.running:
            return self.progress

        self.running = True
        self.progress = {
            "running": True,
            "video_name": video_id.split(":", 1)[-1],
            "total_layers": 0,
            "checked": 0,
            "total_checkpoints": 0,
            "would_pause": False,
            "pause_layer": None,
            "pause_reason": None,
            "results": [],
            "error": None,
        }

        try:
            with tempfile.TemporaryDirectory(prefix="bambu_sim_dl_") as tmp_dl:
                video_path: Path | None = None
                if video_id.startswith("local:"):
                    candidate = Path(video_id.removeprefix("local:")).resolve()
                    # Security guard: restrict to /media
                    if str(candidate).startswith("/media/") and candidate.exists():
                        video_path = candidate
                        self.progress["video_name"] = candidate.name
                elif video_id.startswith("ftps:") and printer_ip and access_code:
                    remote_name = Path(video_id.removeprefix("ftps:")).name
                    self.progress["video_name"] = remote_name
                    dest = Path(tmp_dl) / remote_name
                    ok = await hass.async_add_executor_job(
                        _download_ftps_timelapse_sync,
                        printer_ip,
                        access_code,
                        remote_name,
                        dest,
                    )
                    if ok:
                        video_path = dest

                if not video_path:
                    self.progress["error"] = "Selected timelapse video could not be opened."
                    return self.progress

                total_layers, frames = await hass.async_add_executor_job(
                    _probe_and_extract_frames_sync, video_path, layer_interval, 14
                )
                self.progress["total_layers"] = total_layers
                self.progress["total_checkpoints"] = len(frames)

                if not frames:
                    self.progress["error"] = "No frames could be extracted from this timelapse."
                    return self.progress

                for layer_num, jpeg_bytes in frames:
                    verdict = await inspector.async_inspect_frame(
                        jpeg_bytes=jpeg_bytes,
                        printer_model=printer_model,
                        kinematics=kinematics,
                        layer=layer_num,
                        total_layers=total_layers,
                        frames_merged=1,
                        trigger_reason=f"replay_layer_{layer_num}",
                    )
                    conf_pct = round((verdict.confidence or 0.0) * 100.0, 1)
                    would_trigger_pause = (
                        verdict.status == STATUS_FAILURE
                        and conf_pct >= auto_pause_threshold
                    )

                    # Lightweight base64 thumbnail for replay UI
                    thumb_b64 = base64.b64encode(jpeg_bytes).decode("ascii")
                    step_item = {
                        "layer": layer_num,
                        "total_layers": total_layers,
                        "status": verdict.status,
                        "failure_type": verdict.failure_type,
                        "confidence_pct": conf_pct,
                        "spaghetti_pct": round((verdict.spaghetti_prob or 0.0) * 100.0, 1),
                        "warping_pct": round((verdict.warping_prob or 0.0) * 100.0, 1),
                        "detachment_pct": round((verdict.detachment_prob or 0.0) * 100.0, 1),
                        "first_layer_pct": round((verdict.first_layer_prob or 0.0) * 100.0, 1),
                        "severity": verdict.severity,
                        "latency_ms": verdict.latency_ms,
                        "would_pause": would_trigger_pause,
                        "details": verdict.details,
                        "image_data_url": f"data:image/jpeg;base64,{thumb_b64}",
                    }
                    self.progress["results"].append(step_item)
                    self.progress["checked"] = len(self.progress["results"])

                    if would_trigger_pause and not self.progress["would_pause"]:
                        self.progress["would_pause"] = True
                        self.progress["pause_layer"] = layer_num
                        self.progress["pause_reason"] = (
                            f"{verdict.failure_type} ({conf_pct:.0f}% >= {auto_pause_threshold}%)"
                        )
                        # Stop replay right where real Auto-Pause would have stopped the print!
                        break

                    await asyncio.sleep(0.15)
        except Exception as err:  # noqa: BLE001
            LOGGER.error("Timelapse replay simulation failed: %s", err)
            self.progress["error"] = str(err)
        finally:
            self.running = False
            self.progress["running"] = False

        return self.progress
