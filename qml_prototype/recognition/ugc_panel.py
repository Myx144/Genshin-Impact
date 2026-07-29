"""Recognise the fixed Genshin UGC character panel from a screenshot.

The panel is registered by four large white square markers.  The marker centres
are mapped to a canonical 1240 x 740 coordinate system, then four fixed value
columns are split into four text rows each.  OCR is intentionally limited to
numbers and a decimal point.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

CANONICAL_WIDTH = 1240
CANONICAL_HEIGHT = 740
FIELD_ORDER = ("atk", "basic_atk", "crit_rate", "crit_damage")
SCALES = {
    "atk": Decimal("10000"),
    "basic_atk": Decimal("10000"),
    "crit_rate": Decimal("10000"),
    "crit_damage": Decimal("10000000"),
}

# Broad value-column regions in marker-relative canonical coordinates.  Row
# positions are found dynamically from the white-pixel horizontal projection.
VALUE_BLOCKS = {
    1: (260, 102, 300, 136),
    2: (850, 102, 300, 136),
    3: (260, 284, 300, 136),
    4: (850, 284, 300, 136),
}


class RecognitionError(RuntimeError):
    """A user-facing recognition failure."""


class NumberOcrBackend(Protocol):
    name: str

    def recognise(self, image: np.ndarray) -> str: ...


@dataclass(frozen=True)
class Marker:
    center: tuple[float, float]
    box: tuple[int, int, int, int]
    area: int
    fill_ratio: float


class TesseractNumberOcr:
    """Small subprocess wrapper; no pytesseract dependency is required."""

    name = "tesseract"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or find_tesseract()
        if not self.executable:
            raise RecognitionError(
                "未找到本地 Tesseract OCR。请安装 Tesseract，或设置 "
                "GENSHIN_TESSERACT 指向 tesseract.exe。"
            )

    def recognise(self, image: np.ndarray) -> str:
        with tempfile.TemporaryDirectory(prefix="genshin_ugc_ocr_") as tmp:
            input_path = Path(tmp) / "number.png"
            if not cv2.imwrite(str(input_path), image):
                raise RecognitionError("无法创建 OCR 临时图片")

            outputs: list[str] = []
            for psm in (8, 13):
                command = [
                    self.executable,
                    str(input_path),
                    "stdout",
                    "--psm", str(psm),
                    "--oem", "1",
                    "-l", "eng",
                    "-c", "tessedit_char_whitelist=0123456789.",
                ]
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                if completed.returncode != 0:
                    message = completed.stderr.strip() or "Tesseract OCR 执行失败"
                    raise RecognitionError(message)
                outputs.append(completed.stdout.strip())

            cleaned = [clean_number_text(output) for output in outputs]
            if cleaned[0] != cleaned[1]:
                raise RecognitionError(
                    f"数字 OCR 双重校验不一致：{cleaned[0]} / {cleaned[1]}"
                )
            return cleaned[0]


def find_tesseract() -> str | None:
    configured = os.environ.get("GENSHIN_TESSERACT", "").strip()
    candidates = [
        configured,
        shutil.which("tesseract") or "",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return None


def _read_image(path: str | Path) -> np.ndarray:
    path = Path(path)
    if not path.is_file():
        raise RecognitionError(f"截图文件不存在：{path}")
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise RecognitionError("无法读取截图，请选择 PNG、JPG 或 BMP 文件")
    return image


def _white_mask(image: np.ndarray, threshold: int = 238) -> np.ndarray:
    low = np.array([threshold, threshold, threshold], dtype=np.uint8)
    return cv2.inRange(image, low, np.array([255, 255, 255], dtype=np.uint8))


def locate_square_markers(image: np.ndarray) -> list[Marker]:
    height, width = image.shape[:2]
    min_dim = min(width, height)
    mask = _white_mask(image)
    count, _labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    candidates: list[Marker] = []
    min_side = max(24, int(min_dim * 0.045))
    max_side = int(min_dim * 0.14)

    for index in range(1, count):
        x, y, box_w, box_h, area = (int(v) for v in stats[index])
        if not (min_side <= box_w <= max_side and min_side <= box_h <= max_side):
            continue
        aspect = box_w / max(box_h, 1)
        fill_ratio = area / max(box_w * box_h, 1)
        if not (0.84 <= aspect <= 1.16 and fill_ratio >= 0.86):
            continue
        cx, cy = (float(v) for v in centroids[index])
        candidates.append(Marker((cx, cy), (x, y, box_w, box_h), area, fill_ratio))

    if len(candidates) < 4:
        raise RecognitionError(f"只找到 {len(candidates)} 个白色定位方块，需要 4 个")

    # Large, solid squares outrank circular UI icons and text fragments.
    candidates.sort(key=lambda marker: (marker.area * marker.fill_ratio), reverse=True)
    markers = candidates[:4]
    markers.sort(key=lambda marker: marker.center[1])
    top = sorted(markers[:2], key=lambda marker: marker.center[0])
    bottom = sorted(markers[2:], key=lambda marker: marker.center[0])
    ordered = [top[0], top[1], bottom[0], bottom[1]]
    _validate_markers(ordered, width, height)
    return ordered


def _validate_markers(markers: list[Marker], width: int, height: int) -> None:
    tl, tr, bl, br = markers
    horizontal_top = tr.center[0] - tl.center[0]
    horizontal_bottom = br.center[0] - bl.center[0]
    vertical_left = bl.center[1] - tl.center[1]
    vertical_right = br.center[1] - tr.center[1]
    if min(horizontal_top, horizontal_bottom) < width * 0.35:
        raise RecognitionError("左右定位方块距离过近，截图可能被裁剪")
    if min(vertical_left, vertical_right) < height * 0.35:
        raise RecognitionError("上下定位方块距离过近，截图可能被裁剪")
    if abs(horizontal_top - horizontal_bottom) > max(horizontal_top, horizontal_bottom) * 0.12:
        raise RecognitionError("上下两组定位方块宽度不一致")
    if abs(vertical_left - vertical_right) > max(vertical_left, vertical_right) * 0.12:
        raise RecognitionError("左右两组定位方块高度不一致")
    sides = [marker.box[2] for marker in markers] + [marker.box[3] for marker in markers]
    if max(sides) - min(sides) > max(sides) * 0.24:
        raise RecognitionError("四个定位方块大小差异过大")


def normalise_marker_frame(image: np.ndarray, markers: list[Marker]) -> np.ndarray:
    source = np.float32([marker.center for marker in markers])
    destination = np.float32([
        [0, 0],
        [CANONICAL_WIDTH - 1, 0],
        [0, CANONICAL_HEIGHT - 1],
        [CANONICAL_WIDTH - 1, CANONICAL_HEIGHT - 1],
    ])
    matrix = cv2.getPerspectiveTransform(source, destination)
    return cv2.warpPerspective(image, matrix, (CANONICAL_WIDTH, CANONICAL_HEIGHT))


def validate_blue_canvas(frame: np.ndarray) -> float:
    blue, green, red = cv2.split(frame)
    blue_pixels = (blue >= 170) & (green <= 110) & (red <= 110) & (blue > green * 1.6) & (blue > red * 1.6)
    ratio = float(np.count_nonzero(blue_pixels) / blue_pixels.size)
    if ratio < 0.62:
        raise RecognitionError(
            f"定位区蓝色背景占比只有 {ratio * 100:.1f}%，不是支持的 UGC 面板"
        )
    return ratio


def _projection_ranges(mask: np.ndarray) -> list[tuple[int, int]]:
    projection = np.count_nonzero(mask, axis=1)
    active = projection >= max(3, int(mask.shape[1] * 0.012))
    ranges: list[list[int]] = []
    for row, enabled in enumerate(active):
        if enabled:
            if not ranges or row - ranges[-1][1] > 3:
                ranges.append([row, row])
            else:
                ranges[-1][1] = row
    filtered = [(start, end) for start, end in ranges if end - start + 1 >= 6]
    if len(filtered) == 4:
        return filtered
    # If antialiasing split a line, merge the closest neighbours until four remain.
    while len(filtered) > 4:
        gaps = [filtered[i + 1][0] - filtered[i][1] for i in range(len(filtered) - 1)]
        at = int(np.argmin(gaps))
        filtered[at:at + 2] = [(filtered[at][0], filtered[at + 1][1])]
    return filtered


def _crop_numeric_glyphs(row: np.ndarray, position: int) -> np.ndarray:
    """Drop the leading colon while retaining the complete decimal number.

    The UGC layout places a colon immediately before every value. At higher
    resolutions its two dots survive normalization clearly enough for
    Tesseract to interpret them as a leading 1 or 2. Real digits have a tall
    connected component, so the first tall glyph is a stable number boundary.
    """
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(row, 8)
    if count <= 1:
        raise RecognitionError(f"{position} 号位存在空白数值行")

    components = stats[1:]
    max_height = int(np.max(components[:, cv2.CC_STAT_HEIGHT]))
    minimum_digit_height = max(6, int(round(max_height * 0.62)))
    digit_components = [
        component
        for component in components
        if int(component[cv2.CC_STAT_HEIGHT]) >= minimum_digit_height
    ]
    if not digit_components:
        raise RecognitionError(f"{position} 号位无法定位数值起点")

    first_digit_x = min(int(component[cv2.CC_STAT_LEFT]) for component in digit_components)
    columns = np.flatnonzero(np.count_nonzero(row, axis=0) > 0)
    columns = columns[columns >= first_digit_x]
    if columns.size == 0:
        raise RecognitionError(f"{position} 号位存在空白数值行")

    left = max(0, first_digit_x - 2)
    right = min(row.shape[1], int(columns[-1]) + 3)
    return row[:, left:right]


def extract_number_rows(frame: np.ndarray, position: int) -> list[np.ndarray]:
    x, y, width, height = VALUE_BLOCKS[position]
    block = frame[y:y + height, x:x + width]
    mask = _white_mask(block, 170)
    ranges = _projection_ranges(mask)
    if len(ranges) != 4:
        raise RecognitionError(f"{position} 号位找到 {len(ranges)} 行数字，预期 4 行")

    rows: list[np.ndarray] = []
    for start, end in ranges:
        start = max(0, start - 2)
        end = min(mask.shape[0] - 1, end + 2)
        row = mask[start:end + 1]
        row = _crop_numeric_glyphs(row, position)
        row = cv2.copyMakeBorder(row, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=0)
        row = cv2.resize(row, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        _threshold, row = cv2.threshold(row, 110, 255, cv2.THRESH_BINARY)
        # Tesseract is more stable on document-like black glyphs over white.
        row = cv2.bitwise_not(row)
        rows.append(row)
    return rows


_OCR_SUBSTITUTIONS = str.maketrans({
    "O": "0", "o": "0", "Q": "0", "D": "0",
    "I": "1", "l": "1", "|": "1",
    "S": "5", "s": "5", "B": "8", ",": ".",
})


def clean_number_text(text: str) -> str:
    text = text.translate(_OCR_SUBSTITUTIONS).replace(" ", "")
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    if not matches:
        raise RecognitionError(f"OCR 未识别出数字：{text!r}")
    value = max(matches, key=len)
    if value.count(".") > 1:
        raise RecognitionError(f"数字格式无效：{value}")
    return value


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def decode_character(raw_values: dict[str, str], position: int) -> dict:
    decoded: dict[str, str] = {}
    for field in FIELD_ORDER:
        try:
            raw = Decimal(raw_values[field])
        except InvalidOperation as error:
            raise RecognitionError(f"{position} 号位 {field} 不是有效数字") from error
        if raw < 0:
            raise RecognitionError(f"{position} 号位 {field} 不能为负数")
        decoded[field] = _decimal_text(raw / SCALES[field])

    for field in ("atk", "basic_atk"):
        if Decimal(decoded[field]) >= Decimal("10000"):
            label = "ATK" if field == "atk" else "白值"
            raise RecognitionError(
                f"{position} 号位 {label} 识别为 {decoded[field]}，超过四位数上限，请重新截图"
            )

    return {
        "position": position,
        "name": f"{position}号位角色",
        "raw": raw_values,
        "decoded": decoded,
        "display": {
            "atk": decoded["atk"],
            "basicAtk": decoded["basic_atk"],
            "critRatePercent": _decimal_text(Decimal(decoded["crit_rate"]) * 100),
            "critDamagePercent": _decimal_text(Decimal(decoded["crit_damage"]) * 100),
        },
    }


def recognise_frame(frame: np.ndarray, backend: NumberOcrBackend) -> list[dict]:
    characters: list[dict] = []
    for position in range(1, 5):
        rows = extract_number_rows(frame, position)
        raw_values: dict[str, str] = {}
        for field, row in zip(FIELD_ORDER, rows, strict=True):
            raw_values[field] = clean_number_text(backend.recognise(row))
        characters.append(decode_character(raw_values, position))
    return characters


def recognise_ugc_panel(
    image_path: str | Path,
    backend: NumberOcrBackend | None = None,
) -> dict:
    image = _read_image(image_path)
    markers = locate_square_markers(image)
    frame = normalise_marker_frame(image, markers)
    blue_ratio = validate_blue_canvas(frame)
    backend = backend or TesseractNumberOcr()
    characters = recognise_frame(frame, backend)
    return {
        "ok": True,
        "screenType": "ugc_character_panel_v1",
        "ocrBackend": backend.name,
        "blueRatio": blue_ratio,
        "imageSize": {"width": int(image.shape[1]), "height": int(image.shape[0])},
        "markers": [
            {
                "x": marker.center[0], "y": marker.center[1],
                "box": list(marker.box), "fillRatio": marker.fill_ratio,
            }
            for marker in markers
        ],
        "characters": characters,
    }
