from __future__ import annotations

import unittest

import cv2
import numpy as np

from .ugc_panel import (
    extract_number_rows,
    locate_square_markers,
    normalise_marker_frame,
    recognise_frame,
    validate_blue_canvas,
)

VALUES = [
    ["30321280.00", "10163600.00", "6814.00", "23012240.00"],
    ["7735264.00", "5107260.00", "1200.00", "6552000.00"],
    ["5272077.00", "1699997.00", "2483.00", "14484000.00"],
    ["7735264.00", "5107260.00", "1200.00", "6552000.00"],
]


def build_panel() -> np.ndarray:
    image = np.zeros((1110, 1920, 3), np.uint8)
    image[:] = (255, 0, 0)
    marker_centres = [(287, 103), (1525, 103), (287, 841), (1525, 841)]
    for cx, cy in marker_centres:
        cv2.rectangle(image, (cx - 48, cy - 48), (cx + 48, cy + 48), (255, 255, 255), -1)

    def source(x: float, y: float) -> tuple[int, int]:
        return round(287 + x * (1238 / 1239)), round(103 + y * (738 / 739))

    blocks = [(260, 102), (850, 102), (260, 284), (850, 284)]
    for values, (block_x, block_y) in zip(VALUES, blocks, strict=True):
        for index, text in enumerate(values):
            cv2.putText(
                image,
                text,
                source(block_x, block_y + 25 + index * 30),
                cv2.FONT_HERSHEY_DUPLEX,
                0.72,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
    return image


class FakeOcr:
    name = "fake"

    def __init__(self) -> None:
        self.index = 0

    def recognise(self, _image: np.ndarray) -> str:
        flattened = sum(VALUES, [])
        value = flattened[self.index]
        self.index += 1
        return value


class UgcPanelRecognitionTests(unittest.TestCase):
    def test_markers_rows_and_decoding(self) -> None:
        image = build_panel()
        markers = locate_square_markers(image)
        self.assertEqual(4, len(markers))
        frame = normalise_marker_frame(image, markers)
        self.assertGreater(validate_blue_canvas(frame), 0.9)
        self.assertEqual([4, 4, 4, 4], [len(extract_number_rows(frame, p)) for p in range(1, 5)])
        characters = recognise_frame(frame, FakeOcr())
        self.assertEqual("3032.128", characters[0]["decoded"]["atk"])
        self.assertEqual("1016.36", characters[0]["decoded"]["basic_atk"])
        self.assertEqual("0.6814", characters[0]["decoded"]["crit_rate"])
        self.assertEqual("2.301224", characters[0]["decoded"]["crit_damage"])

    def test_scaled_and_padded_panel(self) -> None:
        scaled = cv2.resize(build_panel(), None, fx=0.72, fy=0.72, interpolation=cv2.INTER_AREA)
        image = cv2.copyMakeBorder(scaled, 40, 65, 90, 35, cv2.BORDER_CONSTANT, value=(30, 30, 30))
        frame = normalise_marker_frame(image, locate_square_markers(image))
        self.assertEqual([4, 4, 4, 4], [len(extract_number_rows(frame, p)) for p in range(1, 5)])


if __name__ == "__main__":
    unittest.main()
