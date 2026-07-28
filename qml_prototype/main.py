"""Primary PySide6/QML frontend for the damage calculator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

ATK_SAVE_FILE = Path.home() / ".genshin_atk_artifacts.json"
ATK_SLOT_FIELDS = {
    "flower": ("sub_flat", "sub_pct"),
    "plume": ("main_flat", "sub_pct"),
    "sands": ("main_pct", "sub_flat", "sub_pct"),
    "goblet": ("main_pct", "sub_flat", "sub_pct"),
    "circlet": ("main_pct", "sub_flat", "sub_pct"),
}

try:
    from .recognition.ugc_panel import RecognitionError, recognise_ugc_panel
except ImportError:  # Direct execution: python qml_prototype/main.py
    from recognition.ugc_panel import RecognitionError, recognise_ugc_panel

from damage_calculator import (
    INPUT_FIELDS,
    NUM_SLOTS,
    _get_meta_slot,
    _save_meta_slot,
    _slot_file,
    calculate_from_values,
    load_saved_gui_state,
)


class UgcRecognitionTask(QRunnable):
    """Run the CPU/subprocess-heavy OCR pipeline away from the QML GUI thread."""

    def __init__(self, bridge: "CalculatorBridge", image_url: str) -> None:
        super().__init__()
        self.bridge = bridge
        self.image_url = image_url

    @Slot()
    def run(self) -> None:
        self.bridge.ugcRecognitionFinished.emit(
            self.bridge._recognize_ugc_response(self.image_url)
        )


class CalculatorBridge(QObject):
    ugcRecognitionFinished = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._recognition_pool = QThreadPool(self)
        self._recognition_pool.setMaxThreadCount(1)

    @staticmethod
    def _default_atk_config() -> dict:
        config = {"base_atk": "", "weapon_secondary": "0"}
        for slot, fields in ATK_SLOT_FIELDS.items():
            config[slot] = {}
            for field in fields:
                always_on = slot == "plume" and field == "main_flat"
                config[slot][field] = {
                    "checked": always_on,
                    "value": "311" if always_on else "0",
                }
        return config

    @staticmethod
    def _normalise_atk_config(saved: dict | None) -> dict:
        config = CalculatorBridge._default_atk_config()
        if not isinstance(saved, dict):
            return config
        config["base_atk"] = str(saved.get("base_atk", ""))
        config["weapon_secondary"] = str(saved.get("weapon_secondary", "0"))
        for slot, fields in ATK_SLOT_FIELDS.items():
            saved_slot = saved.get(slot, {})
            if not isinstance(saved_slot, dict):
                continue
            for field in fields:
                entry = saved_slot.get(field, {})
                if not isinstance(entry, dict):
                    continue
                config[slot][field]["checked"] = bool(entry.get("checked", False))
                config[slot][field]["value"] = str(entry.get("value", "0"))
        config["plume"]["main_flat"] = {"checked": True, "value": "311"}
        return config

    @Slot(result=str)
    def loadAtkConfig(self) -> str:
        saved = None
        if ATK_SAVE_FILE.exists():
            try:
                saved = json.loads(ATK_SAVE_FILE.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                saved = None
        return json.dumps({"ok": True, "config": self._normalise_atk_config(saved)}, ensure_ascii=False)

    @Slot(str, result=str)
    def saveAtkConfig(self, config_json: str) -> str:
        try:
            config = self._normalise_atk_config(json.loads(config_json))
            ATK_SAVE_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            return json.dumps({"ok": True}, ensure_ascii=False)
        except (OSError, TypeError, json.JSONDecodeError) as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)

    @Slot(str, bool, result=str)
    def calculateAtk(self, config_json: str, percent_mode: bool) -> str:
        try:
            config = self._normalise_atk_config(json.loads(config_json))
            base = float(config.get("base_atk", 0) or 0)
            weapon_percent = float(config.get("weapon_secondary", 0) or 0)
            if percent_mode:
                weapon_percent /= 100.0

            total_flat = 0.0
            artifact_percent = 0.0
            details = []
            for slot, fields in ATK_SLOT_FIELDS.items():
                slot_flat = 0.0
                slot_percent = 0.0
                for field in fields:
                    entry = config[slot][field]
                    if not entry["checked"]:
                        continue
                    value = float(entry["value"] or 0)
                    if "flat" in field:
                        slot_flat += value
                    else:
                        slot_percent += value / 100.0 if percent_mode else value
                total_flat += slot_flat
                artifact_percent += slot_percent
                if slot_flat or slot_percent:
                    details.append({"slot": slot, "flat": slot_flat, "percent": slot_percent})

            total_percent = weapon_percent + artifact_percent
            final_atk = base * (1 + total_percent) + total_flat
            return json.dumps({
                "ok": True,
                "baseAtk": base,
                "weaponPercent": weapon_percent,
                "artifactPercent": artifact_percent,
                "totalPercent": total_percent,
                "totalFlat": total_flat,
                "finalAtk": final_atk,
                "details": details,
            }, ensure_ascii=False)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)

    @staticmethod
    def _read_raw_slot(slot: int) -> dict:
        path = _slot_file(slot)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @Slot(result=str)
    def listSlots(self) -> str:
        slots = []
        for slot in range(1, NUM_SLOTS + 1):
            raw = self._read_raw_slot(slot)
            raw_values = raw.get("values", {})
            name = str(raw_values.get("__slot_name__", f"配置 {slot}"))
            slots.append({"id": slot, "name": name, "hasData": _slot_file(slot).exists()})
        return json.dumps({"ok": True, "currentSlot": _get_meta_slot(), "slots": slots}, ensure_ascii=False)

    @Slot(int, result=str)
    def loadSlot(self, slot: int) -> str:
        if slot < 1 or slot > NUM_SLOTS:
            return json.dumps({"ok": False, "error": "无效的配置槽"}, ensure_ascii=False)
        raw = self._read_raw_slot(slot)
        state = load_saved_gui_state(_slot_file(slot))
        values = state["values"]
        raw_cond_bonuses = raw.get("cond_bonuses", {})
        if not isinstance(raw_cond_bonuses, dict):
            raw_cond_bonuses = {}
        # Before static artifact-set ATK had its own field, the only set field
        # was commonly used for the permanent 2-piece bonus. Move that legacy
        # value once into the new static field so UGC panel ATK does not add it
        # a second time after import.
        if "set_bonus_permanent" not in raw_cond_bonuses:
            legacy_set_bonus = state["cond_bonuses"].get("set_bonus", ("0", False))
            if bool(legacy_set_bonus[1]):
                state["cond_bonuses"]["set_bonus_permanent"] = (
                    str(legacy_set_bonus[0]), True,
                )
                state["cond_bonuses"]["set_bonus"] = ("0", False)
        return json.dumps({
            "ok": True,
            "slot": slot,
            "values": values,
            "mode": state["mode"],
            "mainPctMode": bool(state.get("main_pct_mode", False)),
            "autoSave": str(values.get("__auto_save__", "True")).lower() != "false",
            "condBonuses": {
                key: [str(entry[0]), bool(entry[1])]
                for key, entry in state.get("cond_bonuses", {}).items()
            },
            "name": values.get("__slot_name__", f"配置 {slot}"),
        }, ensure_ascii=False)

    @Slot(int, str, result=str)
    def saveSlot(self, slot: int, state_json: str) -> str:
        if slot < 1 or slot > NUM_SLOTS:
            return json.dumps({"ok": False, "error": "无效的配置槽"}, ensure_ascii=False)
        try:
            incoming = json.loads(state_json)
            raw = self._read_raw_slot(slot)
            raw_values = raw.get("values", {})
            if not isinstance(raw_values, dict):
                raw_values = {}
            incoming_values = incoming.get("values", {})
            if not isinstance(incoming_values, dict):
                incoming_values = {}
            for key, value in incoming_values.items():
                raw_values[key] = str(value)
            raw["values"] = raw_values
            raw["mode"] = incoming.get("mode", "期望")
            raw["main_pct_mode"] = bool(incoming.get("mainPctMode", False))

            incoming_cond = incoming.get("condBonuses")
            if isinstance(incoming_cond, dict):
                cond_defaults = {
                    "weapon_passive_permanent": ["0", True],
                    "set_bonus_permanent": ["0", True],
                    "weapon_passive": ["0", False],
                    "set_bonus": ["0", False],
                    "other_pct": ["0", False],
                    "other_flat": ["0", False],
                }
                saved_cond = raw.get("cond_bonuses", {})
                if not isinstance(saved_cond, dict):
                    saved_cond = {}
                for key, default in cond_defaults.items():
                    entry = incoming_cond.get(key, default)
                    if isinstance(entry, dict):
                        value = entry.get("value", default[0])
                        enabled = entry.get("enabled", default[1])
                    elif isinstance(entry, (list, tuple)):
                        value = entry[0] if len(entry) > 0 else default[0]
                        enabled = entry[1] if len(entry) > 1 else default[1]
                    else:
                        value, enabled = default
                    saved_cond[key] = [str(value), bool(enabled)]
                raw["cond_bonuses"] = saved_cond

            _slot_file(slot).write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            _save_meta_slot(slot)
            return json.dumps({"ok": True}, ensure_ascii=False)
        except (OSError, TypeError, json.JSONDecodeError) as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)

    @Slot(int, result=str)
    def setCurrentSlot(self, slot: int) -> str:
        if slot < 1 or slot > NUM_SLOTS:
            return json.dumps({"ok": False, "error": "无效的配置槽"}, ensure_ascii=False)
        _save_meta_slot(slot)
        return json.dumps({"ok": True}, ensure_ascii=False)

    @Slot(str, bool, result=str)
    def calculate(self, values_json: str, crit_damage_only: bool) -> str:
        try:
            values = json.loads(values_json)
            result = calculate_from_values(values, crit_damage_only=crit_damage_only)
            return json.dumps({
                "ok": True,
                "expectedDamage": result["expected_damage"],
                "coefficients": result,
            }, ensure_ascii=False)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)

    @staticmethod
    def _recognize_ugc_response(image_url: str) -> str:
        try:
            url = QUrl(image_url)
            image_path = url.toLocalFile() if url.isLocalFile() else image_url
            result = recognise_ugc_panel(image_path)
            return json.dumps(result, ensure_ascii=False)
        except RecognitionError as error:
            return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
        except Exception as error:
            return json.dumps({
                "ok": False,
                "error": f"UGC 截图识别失败：{error}",
            }, ensure_ascii=False)

    @Slot(str, result=str)
    def recognizeUgcScreenshot(self, image_url: str) -> str:
        """Synchronous compatibility entrypoint used by older callers/tests."""
        return self._recognize_ugc_response(image_url)

    @Slot(str)
    def recognizeUgcScreenshotAsync(self, image_url: str) -> None:
        self._recognition_pool.start(UgcRecognitionTask(self, image_url))


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("GenshinImpact")
    app.setApplicationName("GenshinDamageCalculator")

    bridge = CalculatorBridge()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("calculatorBridge", bridge)
    engine.rootContext().setContextProperty(
        "inputFields",
        [
            {
                "key": key,
                "label": label,
                "required": required,
                "defaultValue": default,
            }
            for key, label, required, default in INPUT_FIELDS
        ],
    )

    qml_file = Path(__file__).with_name("Main.qml")
    engine.load(qml_file)
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
