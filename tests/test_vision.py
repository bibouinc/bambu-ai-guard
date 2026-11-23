"""Unit tests for Bambu AI Guard dynamic scoring, kinematics detection, and median filtering."""
from __future__ import annotations

import io
import unittest
from PIL import Image

from custom_components.bambu_ai_guard.const import (
    KINEMATICS_BEDSLINGER,
    KINEMATICS_COREXY,
    STATUS_FAILURE,
    STATUS_OK,
    STATUS_WARNING,
)
from custom_components.bambu_ai_guard.vision import (
    compute_temporal_median_jpeg,
    detect_printer_model_and_kinematics,
    parse_decisions_api_payload,
)


class TestBambuAIGuardVision(unittest.TestCase):
    """Test suite verifying dynamic scoring, model detection, and median filtering."""

    def test_detect_printer_model_and_kinematics(self) -> None:
        """Verify CoreXY vs Bed-Slinger auto-detection for P1P, P1S, X1C, A1, A1 Mini."""
        self.assertEqual(
            detect_printer_model_and_kinematics(None, "01S00A000000001"),
            ("P1P", KINEMATICS_COREXY),
        )
        self.assertEqual(
            detect_printer_model_and_kinematics(None, "01P00A123456"),
            ("P1S", KINEMATICS_COREXY),
        )
        self.assertEqual(
            detect_printer_model_and_kinematics(None, "03900A123456"),
            ("A1", KINEMATICS_BEDSLINGER),
        )
        self.assertEqual(
            detect_printer_model_and_kinematics(None, "03000A123456"),
            ("A1 Mini", KINEMATICS_BEDSLINGER),
        )
        self.assertEqual(
            detect_printer_model_and_kinematics("Bambu Lab A1", None),
            ("A1", KINEMATICS_BEDSLINGER),
        )
        self.assertEqual(
            detect_printer_model_and_kinematics("A1 Mini", None),
            ("A1 Mini", KINEMATICS_BEDSLINGER),
        )
        self.assertEqual(
            detect_printer_model_and_kinematics("X1C", None),
            ("X1C", KINEMATICS_COREXY),
        )

    def test_parse_decisions_api_dynamic_ranking(self) -> None:
        """Verify dynamic defect ranking across healthy, warning, and failure synthetic payloads."""
        healthy_payload = {
            "answers": {
                "spaghetti": {"noul": 0.02, "confidence": 0.98},
                "warping": {"noul": 0.04, "confidence": 0.96},
                "first_layer_defect": {"noul": 0.01, "confidence": 0.99},
                "detachment": {"noul": 0.01, "confidence": 0.99},
                "occluded": {"noul": 0.08, "confidence": 0.92},
                "severity": {"score": 0.15, "confidence": 0.95},
            }
        }
        v_ok = parse_decisions_api_payload(healthy_payload)
        self.assertEqual(v_ok.status, STATUS_OK)
        self.assertEqual(v_ok.failure_type, "none")
        self.assertEqual(v_ok.recommended_action, "continue")
        self.assertGreater(v_ok.confidence or 0.0, 0.90)

        warning_payload = {
            "answers": {
                "spaghetti": {"noul": 0.03, "confidence": 0.95},
                "warping": {"noul": 0.64, "confidence": 0.85},
                "first_layer_defect": {"noul": 0.12, "confidence": 0.88},
                "detachment": {"noul": 0.05, "confidence": 0.94},
                "occluded": {"noul": 0.72, "confidence": 0.88},
                "severity": {"score": 1.65, "confidence": 0.82},
            }
        }
        v_warn = parse_decisions_api_payload(warning_payload)
        self.assertEqual(v_warn.status, STATUS_WARNING)
        self.assertEqual(v_warn.failure_type, "warping")
        self.assertEqual(v_warn.recommended_action, "inspect")
        self.assertIn("occluded=72%", v_warn.details)

        spaghetti_payload = {
            "answers": {
                "spaghetti": {"noul": 0.93, "confidence": 0.96},
                "warping": {"noul": 0.11, "confidence": 0.90},
                "first_layer_defect": {"noul": 0.15, "confidence": 0.88},
                "detachment": {"noul": 0.42, "confidence": 0.84},
                "occluded": {"noul": 0.05, "confidence": 0.95},
                "severity": {"score": 2.91, "confidence": 0.94},
            }
        }
        v_fail = parse_decisions_api_payload(spaghetti_payload)
        self.assertEqual(v_fail.status, STATUS_FAILURE)
        self.assertEqual(v_fail.failure_type, "spaghetti")
        self.assertEqual(v_fail.recommended_action, "pause")
        self.assertAlmostEqual(v_fail.spaghetti_prob or 0.0, 0.93, places=2)

    def test_parse_decisions_api_detachment_ranking(self) -> None:
        """Verify dynamic detachment ranking without placeholder overwrites."""
        detachment_payload = {
            "answers": {
                "spaghetti": {"noul": 0.12, "confidence": 0.90},
                "warping": {"noul": 0.35, "confidence": 0.85},
                "first_layer_defect": {"noul": 0.05, "confidence": 0.95},
                "detachment": {"noul": 0.89, "confidence": 0.92},
                "occluded": {"noul": 0.10, "confidence": 0.91},
                "severity": {"score": 2.85, "confidence": 0.90},
            }
        }
        verdict = parse_decisions_api_payload(detachment_payload)
        self.assertEqual(verdict.status, STATUS_FAILURE)
        self.assertEqual(verdict.failure_type, "detachment")
        self.assertEqual(verdict.recommended_action, "pause")
        self.assertAlmostEqual(verdict.detachment_prob or 0.0, 0.89, places=2)
        self.assertEqual(verdict.model, "gemini-decision-1")

    def test_temporal_median_nozzle_erasing(self) -> None:
        """Verify 3-frame temporal median erases transient toolhead pixels."""
        frames = []
        # Create 3 frames where background is (40, 40, 40) and a bright toolhead (250, 250, 250)
        # occupies a different X strip in each frame
        for idx in range(3):
            img = Image.new("RGB", (120, 90), color=(40, 40, 40))
            for x in range(idx * 40, (idx + 1) * 40):
                for y in range(20, 50):
                    img.putpixel((x, y), (250, 250, 250))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=100)
            frames.append(buf.getvalue())

        composite_bytes, merged_count = compute_temporal_median_jpeg(frames)
        self.assertEqual(merged_count, 3)
        self.assertIsNotNone(composite_bytes)
        out_img = Image.open(io.BytesIO(composite_bytes or b"")).convert("RGB")
        # All three toolhead positions should be restored near the (40, 40, 40) background
        for check_x in (20, 60, 100):
            r, g, b = out_img.getpixel((check_x, 35))
            self.assertLess(r, 60)
            self.assertLess(g, 60)
            self.assertLess(b, 60)


if __name__ == "__main__":
    unittest.main()
