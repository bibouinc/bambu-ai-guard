"""Gemini Decisions API (gemini-decision-1) & Image Processing engine for Bambu AI Guard."""
from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import io
import ssl
import struct
import time
from typing import Any

import aiohttp

try:
    import numpy as np
    from PIL import Image
    HAS_IMAGE_LIBS = True
except ImportError:
    np = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    HAS_IMAGE_LIBS = False

from .const import (
    BEDSLINGER_MODELS,
    KINEMATICS_BEDSLINGER,
    KINEMATICS_COREXY,
    LOGGER,
    SERIAL_PREFIX_TO_MODEL,
    STATUS_ERROR,
    STATUS_FAILURE,
    STATUS_OK,
    STATUS_WARNING,
)

DECISIONS_MODEL = "gemini-decision-1"
DECISIONS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/decisions"


@dataclass
class InspectionVerdict:
    """Result of a single Gemini Decisions API inspection checkpoint."""

    status: str
    confidence: float | None
    failure_type: str
    recommended_action: str
    details: str
    spaghetti_prob: float | None = None
    warping_prob: float | None = None
    first_layer_prob: float | None = None
    detachment_prob: float | None = None
    occluded_prob: float | None = None
    severity: float | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    layer: int | None = None
    total_layers: int | None = None
    frames_merged: int = 1
    trigger_reason: str = "layer"
    warnings: list[str] = field(default_factory=list)
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def detect_printer_model_and_kinematics(
    model_str: str | None, serial: str | None
) -> tuple[str, str]:
    """Detect printer model and kinematics (corexy vs bedslinger) from model or serial."""
    if serial:
        prefix = serial[:3].upper()
        if prefix in SERIAL_PREFIX_TO_MODEL:
            return SERIAL_PREFIX_TO_MODEL[prefix]

    if model_str:
        upper = model_str.strip().upper()
        for bm in BEDSLINGER_MODELS:
            if bm in upper:
                label = "A1 Mini" if "MINI" in upper else "A1"
                return (label, KINEMATICS_BEDSLINGER)
        if "P1S" in upper:
            return ("P1S", KINEMATICS_COREXY)
        if "P1P" in upper:
            return ("P1P", KINEMATICS_COREXY)
        if "X1E" in upper:
            return ("X1E", KINEMATICS_COREXY)
        if "X1" in upper:
            return ("X1C", KINEMATICS_COREXY)

    return (model_str or "Bambu Lab Printer", KINEMATICS_COREXY)


def compute_temporal_median_jpeg(frames: list[bytes]) -> tuple[bytes | None, int]:
    """Compute a pixel-wise 3-frame temporal median to erase the moving toolhead on CoreXY printers.

    If fewer than 3 valid images are provided or numpy/PIL is unavailable, returns the latest valid frame.
    """
    valid_frames = [f for f in frames if f and len(f) > 1000]
    if not valid_frames:
        return (None, 0)

    if len(valid_frames) < 3 or not HAS_IMAGE_LIBS:
        return (valid_frames[-1], 1)

    try:
        decoded: list[Any] = []
        target_size: tuple[int, int] | None = None
        for raw in valid_frames[-3:]:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            if target_size is None:
                target_size = img.size
            elif img.size != target_size:
                img = img.resize(target_size)
            decoded.append(np.asarray(img, dtype=np.uint8))

        stack = np.stack(decoded, axis=0)
        # Fast branchless 3-element median: max(min(a,b), min(max(a,b), c))
        a, b, c = stack[0], stack[1], stack[2]
        min_ab = np.minimum(a, b)
        max_ab = np.maximum(a, b)
        median_arr = np.maximum(min_ab, np.minimum(max_ab, c))

        out_img = Image.fromarray(median_arr, mode="RGB")
        buf = io.BytesIO()
        out_img.save(buf, format="JPEG", quality=88)
        return (buf.getvalue(), 3)
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Temporal median filter fallback to single frame: %s", err)
        return (valid_frames[-1], 1)


async def capture_direct_bambu_camera_frame(
    host: str, access_code: str, port: int = 6000, timeout_secs: float = 10.0
) -> bytes | None:
    """Capture a single JPEG frame directly from Bambu Lab P1P/P1S/A1/A1 Mini TLS port 6000."""
    if not host or not access_code:
        return None

    header = struct.pack("<IIII", 0x40, 0x3000, 0, 0)
    user_bytes = b"bblp".ljust(32, b"\x00")[:32]
    pass_bytes = access_code.encode("utf-8").ljust(32, b"\x00")[:32]
    auth_packet = header + user_bytes + pass_bytes

    # Non-blocking TLS context (avoids blocking load_default_certs in HA event loop)
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(
                host, port, ssl=ssl_ctx, server_hostname="bambulab.local"
            ),
            timeout=timeout_secs,
        )
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("Direct camera TLS connect to %s:%s failed: %s", host, port, err)
        return None

    try:
        writer.write(auth_packet)
        await writer.drain()

        buf = bytearray()
        started = time.monotonic()
        jpeg_start = -1

        while (time.monotonic() - started) < timeout_secs:
            chunk = await asyncio.wait_for(reader.read(8192), timeout=4.0)
            if not chunk:
                break
            buf.extend(chunk)

            if jpeg_start < 0:
                idx = buf.find(b"\xff\xd8")
                if idx >= 0:
                    del buf[:idx]
                    jpeg_start = 0

            if jpeg_start >= 0:
                end_idx = buf.find(b"\xff\xd9")
                if end_idx >= 0:
                    frame = bytes(buf[: end_idx + 2])
                    if len(frame) > 10000:
                        return frame
                    del buf[: end_idx + 2]
                    jpeg_start = -1
    except Exception as err:  # noqa: BLE001
        LOGGER.debug("Direct camera read error: %s", err)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass

    return None


def parse_decisions_api_payload(payload: dict[str, Any]) -> InspectionVerdict:
    """Parse calibrated probabilities from Google Gemini Decisions API (v1beta/decisions)."""
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("Missing 'answers' object in Decisions API response")

    p_spaghetti = float(answers.get("spaghetti", {}).get("noul", 0.0))
    p_warping = float(answers.get("warping", {}).get("noul", 0.0))
    p_first_layer = float(answers.get("first_layer_defect", {}).get("noul", 0.0))
    p_detachment = float(answers.get("detachment", {}).get("noul", 0.0))
    p_occluded = float(answers.get("occluded", {}).get("noul", 0.0))
    severity = float(answers.get("severity", {}).get("score", 1.0))
    severity_conf = float(answers.get("severity", {}).get("confidence", 0.8))

    defects = [
        ("spaghetti", p_spaghetti),
        ("warping", p_warping),
        ("first_layer_defect", p_first_layer),
        ("detachment", p_detachment),
    ]
    top_defect, max_prob = max(defects, key=lambda item: item[1])

    if max_prob >= 0.80 or severity >= 2.5:
        status = STATUS_FAILURE
        action = "pause"
        failure_type = top_defect
        confidence = max(max_prob, severity_conf)
    elif max_prob >= 0.50 or severity >= 1.5:
        status = STATUS_WARNING
        action = "inspect"
        failure_type = top_defect
        confidence = max(max_prob, severity_conf)
    else:
        status = STATUS_OK
        action = "continue"
        failure_type = "none"
        confidence = max(0.0, min(1.0, min(1.0 - max_prob, severity_conf)))

    occ_note = f" | occluded={p_occluded * 100:.0f}%" if p_occluded >= 0.60 else ""
    details = (
        f"Decisions API: severity={severity:.2f}/3, "
        f"spaghetti={p_spaghetti * 100:.0f}%, "
        f"warping={p_warping * 100:.0f}%, "
        f"first_layer={p_first_layer * 100:.0f}%, "
        f"detachment={p_detachment * 100:.0f}%{occ_note}"
    )

    return InspectionVerdict(
        status=status,
        confidence=round(confidence, 4),
        failure_type=failure_type,
        recommended_action=action,
        details=details,
        spaghetti_prob=round(p_spaghetti, 4),
        warping_prob=round(p_warping, 4),
        first_layer_prob=round(p_first_layer, 4),
        detachment_prob=round(p_detachment, 4),
        occluded_prob=round(p_occluded, 4),
        severity=round(severity, 3),
        provider="gemini_decisions",
        model=DECISIONS_MODEL,
    )


class GeminiDecisionsInspector:
    """Async Gemini Decisions API (gemini-decision-1) inspector for Bambu Lab 3D printers."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ) -> None:
        """Initialize the Gemini Decisions inspector."""
        self._session = session
        self._api_key = api_key.strip()

    async def async_validate_api_key(self) -> tuple[bool, str | None]:
        """Validate the Gemini API key."""
        if not self._api_key:
            return (False, "missing_api_key")

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}"
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return (True, None)
                if resp.status in (400, 401, 403):
                    return (False, "invalid_api_key")
                if resp.status == 429:
                    return (True, "rate_limited")
                return (False, f"http_{resp.status}")
        except Exception as err:  # noqa: BLE001
            LOGGER.warning("Gemini API key validation connection error: %s", err)
            return (False, "cannot_connect")

    async def async_inspect_frame(
        self,
        jpeg_bytes: bytes,
        printer_model: str,
        kinematics: str,
        layer: int,
        total_layers: int,
        frames_merged: int = 1,
        trigger_reason: str = "layer",
    ) -> InspectionVerdict:
        """Inspect a JPEG frame strictly via Google Gemini Decisions API (v1beta/decisions)."""
        if not self._api_key:
            return InspectionVerdict(
                status=STATUS_ERROR,
                confidence=None,
                failure_type="none",
                recommended_action="inspect",
                details="No Gemini API key configured.",
                layer=layer,
                total_layers=total_layers,
                frames_merged=frames_merged,
                trigger_reason=trigger_reason,
                warnings=["Missing Gemini API key"],
            )

        b64_img = base64.b64encode(jpeg_bytes).decode("ascii")
        layer_info = f"Layer {layer}/{total_layers} (trigger: {trigger_reason})"
        kinematics_desc = (
            "Bed-Slinger Y-Axis Moving Bed"
            if kinematics == KINEMATICS_BEDSLINGER
            else "CoreXY Stationary X/Y Build Plate"
        )

        try:
            verdict = await self._call_decisions_api(
                key=self._api_key,
                b64_img=b64_img,
                printer_model=printer_model,
                kinematics_desc=kinematics_desc,
                layer_info=layer_info,
            )
            verdict.layer = layer
            verdict.total_layers = total_layers
            verdict.frames_merged = frames_merged
            verdict.trigger_reason = trigger_reason
            return verdict
        except Exception as err:  # noqa: BLE001
            msg = f"Gemini Decisions API error: {err}"
            LOGGER.warning(msg)
            return InspectionVerdict(
                status=STATUS_ERROR,
                confidence=None,
                failure_type="none",
                recommended_action="inspect",
                details="Upstream Gemini Decisions API error or rate-limit (HTTP 429). No fabricated score returned.",
                layer=layer,
                total_layers=total_layers,
                frames_merged=frames_merged,
                trigger_reason=trigger_reason,
                warnings=[msg],
            )

    async def _call_decisions_api(
        self,
        key: str,
        b64_img: str,
        printer_model: str,
        kinematics_desc: str,
        layer_info: str,
    ) -> InspectionVerdict:
        """Call Google Gemini Decisions API (v1beta/decisions)."""
        t0 = time.monotonic()
        payload = {
            "model": DECISIONS_MODEL,
            "input": [
                {
                    "type": "text",
                    "text": (
                        f"Bambu Lab {printer_model} ({kinematics_desc}) camera snapshot "
                        f"of a 3D print on the build plate. Checkpoint: {layer_info}"
                    ),
                },
                {
                    "type": "image",
                    "data": b64_img,
                    "mime_type": "image/jpeg",
                    "resolution": "medium",
                },
            ],
            "questions": {
                "spaghetti": {
                    "type": "noul",
                    "instructions": "Are there random loose extruded filament loops, bird's nest spaghetti, or knocked-over printed geometries?",
                },
                "warping": {
                    "type": "noul",
                    "instructions": "Is any outer corner or edge of the print peeling upwards or lifting away from the build plate?",
                },
                "first_layer_defect": {
                    "type": "noul",
                    "instructions": "Are first-layer lines, foot pads, or perimeters failing to adhere flatly, dragging, or leaving gaps?",
                },
                "detachment": {
                    "type": "noul",
                    "instructions": "Has the print or any printed part detached or shifted from the build plate?",
                },
                "occluded": {
                    "type": "noul",
                    "instructions": "Is the toolhead/extruder currently blocking the view of the main print area?",
                },
                "severity": {
                    "type": "score",
                    "instructions": "Rate the overall 3D print defect severity.",
                    "criteria": [
                        "Clean normal print, flat adhesion, no defects",
                        "Minor cosmetic flaw or slight curling",
                        "Moderate defect worth inspecting manually",
                        "Severe failure (warping >2mm, detachment, or spaghetti) requiring immediate print pause",
                    ],
                },
            },
        }

        async with self._session.post(
            DECISIONS_ENDPOINT,
            headers={"x-goog-api-key": key},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"HTTP {resp.status}: {body[:160]}")
            data = await resp.json()

        verdict = parse_decisions_api_payload(data)
        verdict.latency_ms = int((time.monotonic() - t0) * 1000)
        return verdict
