#!/usr/bin/env python3
"""Genshin Impact Spread/Aggravate damage calculator — GUI only.

Launches a Tkinter interface. Double-click or run without arguments.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import argparse
from atk_calculator import open_atk_calculator

SAVE_FILE = Path.home() / ".genshin_damage_calculator.json"
NUM_SLOTS = 5
SLOT_META_FILE = Path.home() / ".genshin_damage_calculator_meta.json"

def _slot_file(slot: int) -> Path:
    if slot == 1:
        return SAVE_FILE
    return SAVE_FILE.parent / f".genshin_damage_calculator_slot{slot}.json"

def _get_meta_slot() -> int:
    if SLOT_META_FILE.exists():
        try:
            return json.loads(SLOT_META_FILE.read_text(encoding="utf-8")).get("current_slot", 1)
        except Exception:
            pass
    return 1

def _save_meta_slot(s: int):
    try:
        SLOT_META_FILE.write_text(json.dumps({"current_slot": s}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
ROUNDING_MODES = ("off", "round", "ceil", "floor")
ROUNDING_MODE_LABELS = {
    "off": "关闭取整", "round": "四舍五入", "ceil": "向上取整", "floor": "向下取整",
}
DEBUG_VALUE_STEPS = (
    ("atk", "角色 atk / 角色面板攻击力"),
    ("elemental_mastery", "元素精通"),
    ("crit_rate", "暴击率"),
    ("crit_damage", "暴击伤害"),
    ("talent_multiplier", "天赋倍率"),
    ("reaction_bonus", "反应提升"),
    ("base_reaction_damage_bonus", "星反应基础伤害提升"),
    ("flat_damage_increase", "伤害提高"),
    ("enemy_resistance", "目标抗性"),
    ("elevation_bonus", "擢升提升"),
)
DEBUG_RESULT_STEPS = (
    ("reaction_coefficient", "反应系数计算结果"),
    ("multiplier_area", "倍率区计算结果"),
    ("elemental_mastery_bonus", "精通提升计算结果"),
    ("damage_bonus_area", "增伤区计算结果"),
    ("additive_area", "加伤区计算结果"),
    ("base_area", "基础区计算结果"),
    ("crit_rate_coefficient", "暴击率系数计算结果"),
    ("crit_area", "双暴区计算结果"),
    ("resistance_area", "抗性区计算结果"),
    ("elevation_area", "擢升区计算结果"),
    ("expected_damage", "最终伤害计算结果"),
)
DEBUG_ROUNDING_STEPS = DEBUG_RESULT_STEPS

INPUT_FIELDS = (
    ("atk",                    "角色 ATK / 角色面板攻击力", "必填", "2000"),
    ("em",                     "元素精通",                   "必填", "300"),
    ("crit_rate",              "暴击率",                     "必填", "0.7"),
    ("crit_damage",            "暴击伤害",                   "必填", "1.4"),
    ("talent_multiplier",      "天赋倍率",                   "必填", "2.5"),
    ("stacks",                 "星超导层数",                 "可选 默认 0", "0"),
    ("reaction_bonus",         "反应提升",                   "可选 默认 0", "0"),
    ("base_reaction_damage_bonus", "星反应基础伤害提升",     "可选 默认 0", "0"),
    ("flat_damage_increase",   "伤害提高",                   "可选 默认 0", "0"),
    ("enemy_resistance",       "目标抗性",                   "可选 默认 0.1", "0.1"),
    ("elevation_bonus",        "擢升提升",                   "可选 默认 0", "0"),
)

MAIN_PCT_FIELDS = {"crit_rate", "crit_damage", "talent_multiplier", "reaction_bonus",
                    "base_reaction_damage_bonus", "enemy_resistance", "elevation_bonus"}


@dataclass(frozen=True)
class CharacterInfo:
    atk: float
    elemental_mastery: float
    crit_rate: float
    crit_damage: float

@dataclass(frozen=True)
class DamageCoefficients:
    talent_multiplier: float
    catalyze_stacks: int = 0
    reaction_bonus: float = 0.0
    base_reaction_damage_bonus: float = 0.0
    flat_damage_increase: float = 0.0
    enemy_resistance: float = 0.1
    elevation_bonus: float = 0.0
@dataclass(frozen=True)
class DebugConfig:
    enabled: bool = False
    value_rounding_modes: dict[str, str] | None = None
    result_rounding_modes: dict[str, str] | None = None
    rounding_modes: dict[str, str] | None = None
    decimal_places: int = -1  # -1 = no truncation
    trunc_mode: str = "round"  # round / ceil / floor for global truncation
    em_decimal_places: int = -1  # -1 = no EM truncation
    em_trunc_mode: str = "round"  # round / ceil / floor


# --------------- rounding helpers ---------------

def default_rounding_modes(mode: str = "off",
                           steps: tuple[tuple[str, str], ...] = DEBUG_RESULT_STEPS
                           ) -> dict[str, str]:
    if mode not in ROUNDING_MODES:
        raise ValueError(f"未知取整模式：{mode}")
    return {step: mode for step, _label in steps}


def default_value_rounding_modes(mode: str = "off") -> dict[str, str]:
    return default_rounding_modes(mode, DEBUG_VALUE_STEPS)


def default_result_rounding_modes(mode: str = "off") -> dict[str, str]:
    return default_rounding_modes(mode, DEBUG_RESULT_STEPS)


def round_debug_value(value: float, mode: str) -> float:
    if mode == "off":
        return value
    if mode == "round":
        return float(math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5))
    if mode == "ceil":
        return float(math.ceil(value))
    if mode == "floor":
        return float(math.floor(value))
    raise ValueError(f"未知取整模式：{mode}")


def apply_debug_rounding(value: float, step: str,
                         debug_config: DebugConfig | None,
                         category: str = "result") -> float:
    if debug_config is None or not debug_config.enabled:
        return value
    if category == "value":
        rounding_modes = (debug_config.value_rounding_modes
                          or default_value_rounding_modes())
    else:
        rounding_modes = (debug_config.result_rounding_modes
                          or debug_config.rounding_modes
                          or default_result_rounding_modes())
    return round_debug_value(value, rounding_modes.get(step, "off"))


# --------------- damage formulas ---------------

def reaction_coefficient(catalyze_stacks: int) -> float:
    if catalyze_stacks < 0 or catalyze_stacks > 12:
        raise ValueError("星超导层数必须在 0 到 12 之间")
    if catalyze_stacks == 0:
        return 1.0
    return 0.05 * catalyze_stacks + 1.4


def elemental_mastery_bonus(elemental_mastery: float) -> float:
    if elemental_mastery < 0:
        raise ValueError("元素精通不能为负数")
    return elemental_mastery * 6 / (elemental_mastery + 2000)


def resistance_multiplier(enemy_resistance: float) -> float:
    if enemy_resistance > 0.75:
        return 1 / (1 + 4 * enemy_resistance)
    if enemy_resistance >= 0:
        return 1 - enemy_resistance
    return 1 - enemy_resistance / 2


def calculate_damage(
    character: CharacterInfo,
    coefficients: DamageCoefficients,
    crit_damage_only: bool = False,
    debug_config: DebugConfig | None = None,
) -> dict[str, float]:
    atk = apply_debug_rounding(character.atk, "atk", debug_config, "value")
    em = apply_debug_rounding(character.elemental_mastery, "elemental_mastery",
                              debug_config, "value")
    cr = apply_debug_rounding(character.crit_rate, "crit_rate", debug_config, "value")
    cd = apply_debug_rounding(character.crit_damage, "crit_damage", debug_config, "value")
    tm = apply_debug_rounding(coefficients.talent_multiplier, "talent_multiplier",
                              debug_config, "value")
    rb = apply_debug_rounding(coefficients.reaction_bonus, "reaction_bonus",
                              debug_config, "value")
    brdb = apply_debug_rounding(coefficients.base_reaction_damage_bonus,
                                "base_reaction_damage_bonus", debug_config, "value")
    fdi = apply_debug_rounding(coefficients.flat_damage_increase,
                               "flat_damage_increase", debug_config, "value")
    er = apply_debug_rounding(coefficients.enemy_resistance, "enemy_resistance",
                              debug_config, "value")
    eb = apply_debug_rounding(coefficients.elevation_bonus, "elevation_bonus",
                              debug_config, "value")

    coeff = apply_debug_rounding(reaction_coefficient(coefficients.catalyze_stacks),
                                 "reaction_coefficient", debug_config, "result")
    mult_area = apply_debug_rounding(coeff * atk * tm, "multiplier_area",
                                     debug_config, "result")
    em_bonus = apply_debug_rounding(elemental_mastery_bonus(em),
                                    "elemental_mastery_bonus", debug_config, "result")
    if debug_config is not None and debug_config.em_decimal_places >= 0:
        places = debug_config.em_decimal_places
        factor = 10 ** places
        mode = debug_config.em_trunc_mode
        if mode == "round":
            em_bonus = round(em_bonus, places)
        elif mode == "ceil":
            em_bonus = math.ceil(em_bonus * factor) / factor
        elif mode == "floor":
            em_bonus = math.floor(em_bonus * factor) / factor
    dmg_bonus = apply_debug_rounding(1 + em_bonus + rb, "damage_bonus_area",
                                     debug_config, "result")
    add_area = apply_debug_rounding(1 + brdb, "additive_area", debug_config, "result")
    base_area = apply_debug_rounding(mult_area * dmg_bonus * add_area + fdi,
                                     "base_area", debug_config, "result")
    cr_coeff = apply_debug_rounding(1.0 if crit_damage_only else cr,
                                    "crit_rate_coefficient", debug_config, "result")
    crit_area = apply_debug_rounding(1 + cr_coeff * cd, "crit_area",
                                     debug_config, "result")
    res_area = apply_debug_rounding(resistance_multiplier(er), "resistance_area",
                                    debug_config, "result")
    elev_area = apply_debug_rounding(1 + eb, "elevation_area", debug_config, "result")
    expected = apply_debug_rounding(base_area * crit_area * res_area * elev_area,
                                    "expected_damage", debug_config, "result")

    result = {
        "atk": atk, "elemental_mastery": em, "crit_rate": cr, "crit_damage": cd,
        "talent_multiplier": tm, "reaction_bonus": rb,
        "base_reaction_damage_bonus": brdb, "flat_damage_increase": fdi,
        "enemy_resistance": er, "elevation_bonus": eb,
        "reaction_coefficient": coeff, "multiplier_area": mult_area,
        "elemental_mastery_bonus": em_bonus, "damage_bonus_area": dmg_bonus,
        "additive_area": add_area, "base_area": base_area,
        "crit_rate_coefficient": cr_coeff, "crit_area": crit_area,
        "resistance_area": res_area, "elevation_area": elev_area,
        "expected_damage": expected,
    }
    if debug_config is not None and debug_config.enabled:
        result["debug_rounding_enabled"] = 1.0
    if debug_config is not None and debug_config.decimal_places >= 0:
        places = debug_config.decimal_places
        factor = 10 ** places
        mode = debug_config.trunc_mode
        if mode == "round":
            result = {k: round(v, places) for k, v in result.items()}
        elif mode == "ceil":
            result = {k: math.ceil(v * factor) / factor for k, v in result.items()}
        elif mode == "floor":
            result = {k: math.floor(v * factor) / factor for k, v in result.items()}
    return result


# --------------- GUI helpers ---------------

def parse_gui_number(value: str, field_name: str, allow_negative: bool = False) -> float:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name}不能为空")
    number = float(text)
    if not allow_negative and number < 0:
        raise ValueError(f"{field_name}不能为负数")
    return number


def calculate_from_values(
    values: dict[str, str],
    crit_damage_only: bool = False,
    debug_config: DebugConfig | None = None,
) -> dict[str, float]:
    stacks = int(parse_gui_number(values["stacks"], "星超导层数"))
    character = CharacterInfo(
        atk=parse_gui_number(values["atk"], "角色 atk / 角色面板攻击力"),
        elemental_mastery=parse_gui_number(values["em"], "元素精通"),
        crit_rate=parse_gui_number(values["crit_rate"], "暴击率"),
        crit_damage=parse_gui_number(values["crit_damage"], "暴击伤害"),
    )
    coefficients = DamageCoefficients(
        talent_multiplier=parse_gui_number(values["talent_multiplier"], "天赋倍率"),
        catalyze_stacks=stacks,
        reaction_bonus=parse_gui_number(values["reaction_bonus"], "反应提升"),
        base_reaction_damage_bonus=parse_gui_number(values["base_reaction_damage_bonus"],
                                                    "星反应基础伤害提升"),
        flat_damage_increase=parse_gui_number(values["flat_damage_increase"], "伤害提高"),
        enemy_resistance=parse_gui_number(values["enemy_resistance"], "目标抗性",
                                          allow_negative=True),
        elevation_bonus=parse_gui_number(values["elevation_bonus"], "擢升提升"),
    )
    return calculate_damage(character, coefficients,
                            crit_damage_only=crit_damage_only,
                            debug_config=debug_config)


def default_gui_values() -> dict[str, str]:
    return {key: default for key, _chinese_name, _requirement, default in INPUT_FIELDS}


# --------------- save / load ---------------

def load_saved_gui_state(save_file: Path | None = None) -> dict[str, object]:
    if save_file is None:
        save_file = SAVE_FILE
    if not save_file.exists():
        return {
            "values": default_gui_values(),
            "mode": "期望",
            "debug_enabled": False,
            "debug_value_rounding_modes": default_value_rounding_modes(),
            "debug_result_rounding_modes": default_result_rounding_modes(),
            "cond_bonuses": {"weapon_passive": ("0", False),
                             "set_bonus": ("0", False),
                             "other_pct": ("0", False),
                             "other_flat": ("0", False)},
        }
    with save_file.open("r", encoding="utf-8") as f:
        saved = json.load(f)
    saved_values = saved.get("values", {})
    values = default_gui_values()
    for key in values:
        if key in saved_values:
            values[key] = str(saved_values[key])
    if "base_atk_input" in saved_values:
        values["base_atk_input"] = str(saved_values["base_atk_input"])
    for metadata_key in (
        "__slot_name__", "__auto_save__",
        "__ugc_atk_includes_weapon_permanent__", "__ugc_weapon_permanent_at_import__",
    ):
        if metadata_key in saved_values:
            values[metadata_key] = str(saved_values[metadata_key])
    mode = saved.get("mode", "期望")
    if mode not in {"期望", "暴伤"}:
        mode = "期望"
    legacy_rm = saved.get("debug_rounding_modes", {})
    sv_rm = saved.get("debug_value_rounding_modes", {})
    sr_rm = saved.get("debug_result_rounding_modes", legacy_rm)
    dv_rm = default_value_rounding_modes()
    for step in dv_rm:
        mv = sv_rm.get(step, "off")
        if mv in ROUNDING_MODES:
            dv_rm[step] = mv
    dr_rm = default_result_rounding_modes()
    for step in dr_rm:
        mv = sr_rm.get(step, "off")
        if mv in ROUNDING_MODES:
            dr_rm[step] = mv
    cond = saved.get("cond_bonuses", {})
    cond_defaults = {"weapon_passive_permanent": ("0", True),
                     "weapon_passive": ("0", False), "set_bonus": ("0", False),
                     "other_pct": ("0", False), "other_flat": ("0", False)}
    cb = {}
    for k, dv in cond_defaults.items():
        entry = cond.get(k, list(dv))
        cb[k] = (str(entry[0]) if len(entry) > 0 else dv[0],
                 bool(entry[1]) if len(entry) > 1 else dv[1])
    return {
        "values": values, "mode": mode,
        "debug_enabled": bool(saved.get("debug_enabled", False)),
        "debug_value_rounding_modes": dv_rm,
        "debug_result_rounding_modes": dr_rm,
        "cond_bonuses": cb,
        "main_pct_mode": saved.get("main_pct_mode", False),
    }


def save_gui_state(
    values: dict[str, str],
    mode: str,
    slot: int = 1,
    debug_enabled: bool = False,
    debug_value_rounding_modes: dict[str, str] | None = None,
    debug_result_rounding_modes: dict[str, str] | None = None,
    save_file: Path | None = None,
    debug_rounding_modes: dict[str, str] | None = None,
    cond_bonuses: dict[str, tuple[str, bool]] | None = None,
    main_pct_mode: bool = False,
) -> None:
    if save_file is None:
        save_file = _slot_file(slot)
    if debug_result_rounding_modes is None and debug_rounding_modes is not None:
        debug_result_rounding_modes = debug_rounding_modes
    payload = {
        "values": values, "mode": mode, "debug_enabled": debug_enabled,
        "debug_value_rounding_modes": (debug_value_rounding_modes
                                       or default_value_rounding_modes()),
        "debug_result_rounding_modes": (debug_result_rounding_modes
                                        or default_result_rounding_modes()),
    }
    payload["main_pct_mode"] = main_pct_mode
    if cond_bonuses is not None:
        existing_cond_bonuses: dict[str, object] = {}
        if save_file.exists():
            try:
                existing_payload = json.loads(save_file.read_text(encoding="utf-8"))
                existing_cond_bonuses = existing_payload.get("cond_bonuses", {})
                if not isinstance(existing_cond_bonuses, dict):
                    existing_cond_bonuses = {}
            except (OSError, json.JSONDecodeError):
                existing_cond_bonuses = {}
        existing_cond_bonuses.update({k: list(v) for k, v in cond_bonuses.items()})
        payload["cond_bonuses"] = existing_cond_bonuses
    save_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")


# --------------- GUI ---------------

def run_gui() -> None:
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk

    root = tk.Tk()
    root.title("原神星超导角色伤害计算器")
    root.geometry("700x900")
    base_atk_var = tk.DoubleVar(value=0.0)
    base_atk_input_var = tk.StringVar(value="")

    ttk.Label(root, text="原神星超导角色伤害计算器",
              font=("Arial", 16, "bold")).pack(pady=(10, 2))
    ttk.Label(root, text="百分比请用小数输入，例如 70% 填 0.7，140% 填 1.4。",
              font=("Arial", 9)).pack(pady=(0, 8))

    main_frame = ttk.Frame(root, padding=8)
    main_frame.pack(fill="both", expand=True)

    # ---- main input ----
    input_frame = ttk.LabelFrame(main_frame, text="输入数据", padding=8)
    input_frame.pack(fill="x")

    current_slot = _get_meta_slot()
    saved_state = load_saved_gui_state(_slot_file(current_slot))
    saved_values = saved_state["values"]

    entries: dict[str, tk.StringVar] = {}
    for row, (key, chinese_name, requirement, default) in enumerate(INPUT_FIELDS):
        ttk.Label(input_frame, text=chinese_name).grid(row=row, column=0, sticky="w",
                                                        padx=4, pady=2)
        variable = tk.StringVar(value=saved_values.get(key, default))
        entries[key] = variable
        ttk.Entry(input_frame, textvariable=variable, width=16).grid(
            row=row, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(input_frame, text=requirement).grid(row=row, column=2, sticky="w",
                                                       padx=4, pady=2)
    input_frame.columnconfigure(1, weight=1)

    # Effective ATK label (column 3 of row 0, added after all vars are defined)
    effective_atk_var = tk.StringVar(value="有效 ATK: —")
    ttk.Label(input_frame, textvariable=effective_atk_var,
              font=("Arial", 10, "bold"), foreground="#c41e3a").grid(
        row=0, column=3, sticky="w", padx=8, pady=2)

    # ---- conditional bonuses ----
    cond_frame = ttk.LabelFrame(main_frame, text="条件加成（武器特效 / 套装 / 其他）", padding=6)
    cond_frame.pack(fill="x", pady=(8, 0))

    saved_cond = saved_state.get("cond_bonuses", {})

    wp_check = tk.BooleanVar(value=saved_cond.get("weapon_passive", ("0", False))[1])
    wp_var = tk.StringVar(value=saved_cond.get("weapon_passive", ("0", False))[0])
    set_check = tk.BooleanVar(value=saved_cond.get("set_bonus", ("0", False))[1])
    set_var = tk.StringVar(value=saved_cond.get("set_bonus", ("0", False))[0])
    op_check = tk.BooleanVar(value=saved_cond.get("other_pct", ("0", False))[1])
    op_var = tk.StringVar(value=saved_cond.get("other_pct", ("0", False))[0])
    of_check = tk.BooleanVar(value=saved_cond.get("other_flat", ("0", False))[1])
    of_var = tk.StringVar(value=saved_cond.get("other_flat", ("0", False))[0])

    r = 0
    cb1 = ttk.Checkbutton(cond_frame, variable=wp_check)
    cb1.grid(row=r, column=0, padx=(4, 0), pady=2)
    ttk.Label(cond_frame, text="武器特效 ATK%").grid(row=r, column=1, sticky="w", padx=2, pady=2)
    ttk.Entry(cond_frame, textvariable=wp_var, width=10).grid(row=r, column=2, padx=2, pady=2)

    cb2 = ttk.Checkbutton(cond_frame, variable=set_check)
    cb2.grid(row=r, column=3, padx=(12, 0), pady=2)
    ttk.Label(cond_frame, text="圣遗物套装 ATK%").grid(row=r, column=4, sticky="w", padx=2, pady=2)
    ttk.Entry(cond_frame, textvariable=set_var, width=10).grid(row=r, column=5, padx=2, pady=2)
    r += 1

    cb3 = ttk.Checkbutton(cond_frame, variable=op_check)
    cb3.grid(row=r, column=0, padx=(4, 0), pady=2)
    ttk.Label(cond_frame, text="其他 ATK%").grid(row=r, column=1, sticky="w", padx=2, pady=2)
    ttk.Entry(cond_frame, textvariable=op_var, width=10).grid(row=r, column=2, padx=2, pady=2)

    cb4 = ttk.Checkbutton(cond_frame, variable=of_check)
    cb4.grid(row=r, column=3, padx=(12, 0), pady=2)
    ttk.Label(cond_frame, text="其他固定 ATK").grid(row=r, column=4, sticky="w", padx=2, pady=2)
    ttk.Entry(cond_frame, textvariable=of_var, width=10).grid(row=r, column=5, padx=2, pady=2)

    r += 1
    ttk.Label(cond_frame, text="白值 (基础攻击力 = 角色基础 + 武器基础)", font=("Arial", 9)).grid(
        row=r, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 2))
    ttk.Entry(cond_frame, textvariable=base_atk_input_var, width=14).grid(
        row=r, column=4, columnspan=2, sticky="w", padx=4, pady=(6, 2))
    ttk.Label(cond_frame, text="游戏界面白色数字，用于条件加成百分比计算",
              font=("Arial", 8), foreground="gray").grid(
        row=r+1, column=0, columnspan=6, sticky="w", padx=4, pady=(0, 4))

    # ---- real-time effective ATK updater ----
    def _update_effective_atk(*_args):
        try:
            base_atk_val = float(entries["atk"].get() or 0)
            ba = base_atk_var.get() or (float(base_atk_input_var.get()) if base_atk_input_var.get().strip() else 0.0)
            cp = 0.0
            _pct_div = (lambda x: x / 100.0) if main_pct_mode_var.get() else (lambda x: x)
            if wp_check.get():
                cp += _pct_div(float(wp_var.get() or 0))
            if set_check.get():
                cp += _pct_div(float(set_var.get() or 0))
            if op_check.get():
                cp += _pct_div(float(op_var.get() or 0))
            cf = 0.0
            if of_check.get():
                cf += float(of_var.get() or 0)
            effective = base_atk_val + ba * cp + cf
            effective_atk_value.set(effective)
            if atk_decimal_var.get() >= 0:
                p = atk_decimal_var.get(); f = 10 ** p; m = atk_trunc_var.get()
                if m == "round": effective = round(effective, p)
                elif m == "ceil": effective = math.ceil(effective * f) / f
                elif m == "floor": effective = math.floor(effective * f) / f
            effective_atk_var.set(f"有效 ATK: {effective:.5f}")
        except (ValueError, tk.TclError):
            effective_atk_var.set("有效 ATK: —")

    entries["atk"].trace_add("write", _update_effective_atk)
    wp_check.trace_add("write", _update_effective_atk)
    set_check.trace_add("write", _update_effective_atk)
    op_check.trace_add("write", _update_effective_atk)
    of_check.trace_add("write", _update_effective_atk)
    wp_var.trace_add("write", _update_effective_atk)
    set_var.trace_add("write", _update_effective_atk)
    op_var.trace_add("write", _update_effective_atk)
    of_var.trace_add("write", _update_effective_atk)
    base_atk_input_var.trace_add("write", _update_effective_atk)

    # ---- mode & buttons ----
    loaded_pct_mode = bool(saved_state.get("main_pct_mode", False))
    initial_mode = str(saved_state.get("mode", "期望"))
    if initial_mode not in {"期望", "暴伤"}:
        initial_mode = "期望"
    initial_mode_label = "暴击伤害" if initial_mode == "暴伤" else "期望伤害"
    mode_var = tk.StringVar(value=initial_mode)
    debug_enabled_var = tk.BooleanVar(value=bool(saved_state.get("debug_enabled", False)))
    log_enabled_var = tk.BooleanVar(value=False)
    main_pct_mode_var = tk.BooleanVar(value=False)
    precision_var = tk.IntVar(value=-1)  # decimal places for debug truncation
    trunc_mode_var = tk.StringVar(value="round")  # global truncation mode
    em_precision_var = tk.IntVar(value=-1)  # EM precision truncation
    em_trunc_mode_var = tk.StringVar(value="round")  # EM truncation mode
    atk_decimal_var = tk.IntVar(value=-1)  # ATK decimal places
    atk_trunc_var = tk.StringVar(value="round")  # ATK truncation mode
    effective_atk_value = tk.DoubleVar(value=0.0)  # shared between _update_effective_atk and show_results

    # Apply saved pct mode after UI is built
    if loaded_pct_mode:
        root.after(10, _toggle_main_pct_mode)  # defer until UI fully initialized

    saved_vrm = saved_state.get("debug_value_rounding_modes", default_value_rounding_modes())
    saved_rrm = saved_state.get("debug_result_rounding_modes", default_result_rounding_modes())
    debug_value_rounding_vars = {
        step: tk.StringVar(value=saved_vrm.get(step, "off"))
        for step, _ in DEBUG_VALUE_STEPS
    }
    debug_result_rounding_vars = {
        step: tk.StringVar(value=saved_rrm.get(step, "off"))
        for step, _ in DEBUG_RESULT_STEPS
    }

    summary_var = tk.StringVar(
        value=f"当前模式：{initial_mode_label}。点击「计算」后显示最终伤害。")

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=(8, 0))

    summary_label = ttk.Label(main_frame, textvariable=summary_var,
                              font=("Arial", 12, "bold"), foreground="#0b6bcb")
    summary_label.pack(fill="x", pady=(8, 0))

    result_frame = ttk.LabelFrame(main_frame, text="计算结果", padding=8)
    result_frame.pack(fill="both", expand=True, pady=(8, 0))
    result_text = tk.Text(result_frame, height=12, wrap="word")
    result_text.pack(fill="both", expand=True)

    # ---- pct mode toggle ----
    pct_mode_label_var = tk.StringVar(value="当前：小数输入（0.7 = 70%）")
    def _toggle_main_pct_mode():
        factor = 100.0 if not main_pct_mode_var.get() else 0.01
        for key in MAIN_PCT_FIELDS:
            if key in entries:
                try:
                    cur = float(entries[key].get() or "0")
                    entries[key].set(f"{cur * factor:.5g}")
                except ValueError:
                    pass
        main_pct_mode_var.set(not main_pct_mode_var.get())
        if main_pct_mode_var.get():
            pct_mode_label_var.set("当前：百分比输入（70 = 70%）")
        else:
            pct_mode_label_var.set("当前：小数输入（0.7 = 70%）")
        _update_effective_atk()

    pct_label = ttk.Label(main_frame, textvariable=pct_mode_label_var, font=("Arial", 9, "bold"), foreground="#0b6bcb")
    pct_label.pack(fill="x", padx=4, pady=(4, 0))
    pct_toggle_btn = ttk.Button(main_frame, text="切换小数/百分比输入", command=_toggle_main_pct_mode)
    pct_toggle_btn.pack(padx=4, pady=(2, 0))

    # ---- save slots ----
    current_slot_var = tk.IntVar(value=1)
    current_slot_var.set(_get_meta_slot())
    current_slot = current_slot_var.get()

    slot_buttons: list[ttk.Button] = []
    def _switch_slot(new_slot: int):
        old_slot = current_slot_var.get()
        if old_slot == new_slot:
            return
        save_gui_state(
            current_values(), mode_var.get(), slot=old_slot,
            debug_enabled=debug_enabled_var.get(),
            debug_value_rounding_modes={s: v.get() for s, v in debug_value_rounding_vars.items()},
            debug_result_rounding_modes={s: v.get() for s, v in debug_result_rounding_vars.items()},
            cond_bonuses={"weapon_passive": (wp_var.get(), wp_check.get()),
                           "set_bonus": (set_var.get(), set_check.get()),
                           "other_pct": (op_var.get(), op_check.get()),
                           "other_flat": (of_var.get(), of_check.get())},
            main_pct_mode=main_pct_mode_var.get(),
        )
        current_slot_var.set(new_slot)
        _save_meta_slot(new_slot)
        saved = load_saved_gui_state(_slot_file(new_slot))
        for key, var in entries.items():
            var.set(str(saved["values"].get(key, "0")))
        mode_var.set(str(saved.get("mode", "期望")))
        debug_enabled_var.set(bool(saved.get("debug_enabled", False)))
        dv = saved.get("debug_value_rounding_modes", default_value_rounding_modes())
        dr = saved.get("debug_result_rounding_modes", default_result_rounding_modes())
        for step, var in debug_value_rounding_vars.items():
            var.set(dv.get(step, "off"))
        for step, var in debug_result_rounding_vars.items():
            drv = dr.get(step, "off")
            if drv in ROUNDING_MODES:
                var.set(drv)
        cb = saved.get("cond_bonuses", {})
        wp_check.set(bool(cb.get("weapon_passive", ("0", False))[1]) if isinstance(cb.get("weapon_passive", ("0", False)), (list, tuple)) else False)
        wp_var.set(str(cb.get("weapon_passive", ("0", False))[0]) if isinstance(cb.get("weapon_passive", ("0", False)), (list, tuple)) else "0")
        set_check.set(bool(cb.get("set_bonus", ("0", False))[1]) if isinstance(cb.get("set_bonus", ("0", False)), (list, tuple)) else False)
        set_var.set(str(cb.get("set_bonus", ("0", False))[0]) if isinstance(cb.get("set_bonus", ("0", False)), (list, tuple)) else "0")
        op_check.set(bool(cb.get("other_pct", ("0", False))[1]) if isinstance(cb.get("other_pct", ("0", False)), (list, tuple)) else False)
        op_var.set(str(cb.get("other_pct", ("0", False))[0]) if isinstance(cb.get("other_pct", ("0", False)), (list, tuple)) else "0")
        of_check.set(bool(cb.get("other_flat", ("0", False))[1]) if isinstance(cb.get("other_flat", ("0", False)), (list, tuple)) else False)
        of_var.set(str(cb.get("other_flat", ("0", False))[0]) if isinstance(cb.get("other_flat", ("0", False)), (list, tuple)) else "0")
        if saved.get("main_pct_mode", False) != main_pct_mode_var.get():
            _toggle_main_pct_mode()
        for i, btn in enumerate(slot_buttons):
            btn.configure(style="Active.TButton" if (i + 1) == new_slot else "TButton")
        summary_var.set("切换到配置槽 {}。点击\"计算\"后显示最终伤害。".format(new_slot))
        result_text.delete("1.0", tk.END)

    style = ttk.Style()
    style.configure("Active.TButton", font=("Arial", 9, "bold"), background="#0b6bcb")
    slot_frame = ttk.Frame(main_frame)
    slot_frame.pack(fill="x", padx=4, pady=(4, 0))
    ttk.Label(slot_frame, text="配置槽位:", font=("Arial", 9)).pack(side="left", padx=(0, 4))
    for i in range(1, NUM_SLOTS + 1):
        btn = ttk.Button(slot_frame, text=str(i), width=3,
                         command=lambda n=i: _switch_slot(n))
        if i == current_slot_var.get():
            btn.configure(style="Active.TButton")
        btn.pack(side="left", padx=(0, 2))
        slot_buttons.append(btn)

    def current_values() -> dict[str, str]:
        return {key: variable.get() for key, variable in entries.items()}

    def show_results() -> None:
        try:
            _update_effective_atk()  # refresh effective ATK display before calculation
            values = current_values()
            for key in MAIN_PCT_FIELDS:
                if main_pct_mode_var.get():
                    values[key] = str(float(values.get(key, "0") or 0) / 100.0)
            # Apply conditional bonuses to ATK
            base_atk = base_atk_var.get() or (float(base_atk_input_var.get()) if base_atk_input_var.get().strip() else 0.0)
            cond_pct = 0.0
            cond_flat = 0.0
            cond_detail = []
            _pct_div2 = (lambda x: x / 100.0) if main_pct_mode_var.get() else (lambda x: x)
            if wp_check.get():
                v = _pct_div2(float(wp_var.get() or 0))
                cond_pct += v
                cond_detail.append(f"  武器特效: +{v*100:.5f}%")
            if set_check.get():
                v = _pct_div2(float(set_var.get() or 0))
                cond_pct += v
                cond_detail.append(f"  圣遗物套装: +{v*100:.5f}%")
            if op_check.get():
                v = _pct_div2(float(op_var.get() or 0))
                cond_pct += v
                cond_detail.append(f"  其他ATK%: +{v*100:.5f}%")
            if of_check.get():
                v = float(of_var.get() or 0)
                cond_flat += v
                cond_detail.append(f"  其他固定ATK: +{v:.5f}")

            base_entries_atk = float(values["atk"])
            effective_atk = effective_atk_value.get()
            values["atk"] = str(effective_atk)
            if atk_decimal_var.get() >= 0:
                p = atk_decimal_var.get(); f = 10 ** p; m = atk_trunc_var.get()
                atk_val = float(values["atk"])
                if m == "round": atk_val = round(atk_val, p)
                elif m == "ceil": atk_val = math.ceil(atk_val * f) / f
                elif m == "floor": atk_val = math.floor(atk_val * f) / f
                values["atk"] = str(atk_val)

            crit_damage_only = mode_var.get() == "暴伤"
            debug_config = DebugConfig(
                enabled=debug_enabled_var.get(),
                value_rounding_modes={s: v.get() for s, v
                                      in debug_value_rounding_vars.items()},
                result_rounding_modes={s: v.get() for s, v
                                       in debug_result_rounding_vars.items()},
                decimal_places=precision_var.get(),
                trunc_mode=trunc_mode_var.get(),
                em_decimal_places=em_precision_var.get(),
                em_trunc_mode=em_trunc_mode_var.get(),
            )
            result = calculate_from_values(values, crit_damage_only=crit_damage_only,
                                           debug_config=debug_config)
        except ValueError as error:
            messagebox.showerror("输入错误", str(error))
            return

        ed = result["expected_damage"]
        mode_label = "暴击伤害" if mode_var.get() == "暴伤" else "期望伤害"
        debug_label = "Debug取整：开启" if debug_enabled_var.get() else "Debug取整：关闭"
        summary_var.set(
            f"当前模式：{mode_label}｜{debug_label}｜最终伤害：{ed:.5f}")

        lines = ["原神星超导反应角色伤害计算结果",
                 f"当前模式：{mode_label}", debug_label, "",
                 f"最终伤害 expected_damage: {ed:.5f}"]
        if cond_detail:
            lines.append("")
            lines.append("条件加成:")
            lines.extend(cond_detail)
            if base_atk > 0:
                lines.append(f"  白值: {base_atk:.5f}")
            lines.append(f"  有效 ATK: {effective_atk:.5f} "
                         f"(常驻 {base_entries_atk:.5f} + 条件 {effective_atk - base_entries_atk:.5f})")
        lines.append("")
        lines.extend(f"{key}: {value:.5f}" for key, value in result.items())


        if log_enabled_var.get():
            lines.append("")
            lines.append("=== 计算日志（逐步骤公式） ===")
            lines.append("")
            raw_atk = float(values["atk"])
            raw_em = float(values["em"])
            raw_cr = float(values["crit_rate"])
            raw_cd = float(values["crit_damage"])
            raw_tm = float(values["talent_multiplier"])
            raw_stacks = int(values["stacks"])
            raw_rb = float(values["reaction_bonus"])
            raw_brdb = float(values["base_reaction_damage_bonus"])
            raw_fdi = float(values["flat_damage_increase"])
            raw_er = float(values["enemy_resistance"])
            raw_eb = float(values["elevation_bonus"])
            lines.append(f"有效 ATK = 常驻({base_entries_atk:.5f}) + 白值({base_atk:.5f}) x 条件ATK%({cond_pct:.5f}) + 条件固定({cond_flat:.5f}) = {effective_atk:.5f}")
            lines.append("")
            rc_label = f"0.05 x {raw_stacks} + 1.4" if raw_stacks > 0 else "1"
            lines.append(f"反应系数 = {rc_label} = {result['reaction_coefficient']:.5f}")
            lines.append(f"倍率区 = 反应系数({result['reaction_coefficient']:.5f}) x ATK({result['atk']:.5f}) x 天赋倍率({result['talent_multiplier']:.5f}) = {result['multiplier_area']:.5f}")
            lines.append(f"精通提升 = 元素精通({result['elemental_mastery']:.5f}) x 6 / (元素精通({result['elemental_mastery']:.5f}) + 2000) = {result['elemental_mastery_bonus']:.5f}")
            lines.append(f"增伤区 = 1 + 精通提升({result['elemental_mastery_bonus']:.5f}) + 反应提升({result['reaction_bonus']:.5f}) = {result['damage_bonus_area']:.5f}")
            lines.append(f"加伤区 = 1 + 星反应基础伤害提升({result['base_reaction_damage_bonus']:.5f}) = {result['additive_area']:.5f}")
            lines.append(f"基础区 = 倍率区({result['multiplier_area']:.5f}) x 增伤区({result['damage_bonus_area']:.5f}) x 加伤区({result['additive_area']:.5f}) + 伤害提高({result['flat_damage_increase']:.5f}) = {result['base_area']:.5f}")
            crit_label = "1" if crit_damage_only else f"1 + 暴击率({result['crit_rate']:.5f}) x 暴击伤害({result['crit_damage']:.5f})"
            lines.append(f"双爆区 = {crit_label} = {result['crit_area']:.5f}")
            lines.append(f"抗性区 = f(目标抗性={result['enemy_resistance']:.5f}) = {result['resistance_area']:.5f}")
            lines.append(f"擢升区 = 1 + 擢升提升({result['elevation_bonus']:.5f}) = {result['elevation_area']:.5f}")
            lines.append("")
            lines.append(f"最终伤害 = 基础区({result['base_area']:.5f}) x 双爆区({result['crit_area']:.5f}) x 抗性区({result['resistance_area']:.5f}) x 擢升区({result['elevation_area']:.5f}) = {ed:.5f}")
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "\n".join(lines))

    def reset_defaults() -> None:
        for key, _cn, _req, default in INPUT_FIELDS:
            entries[key].set(default)
        mode_var.set("期望")
        debug_enabled_var.set(False)
        debug_enabled_var.set(False); log_enabled_var.set(False); result_text.configure(height=12)
        for v in [*debug_value_rounding_vars.values(),
                  *debug_result_rounding_vars.values()]:
            v.set("off")
        wp_check.set(False); wp_var.set("0")
        set_check.set(False); set_var.set("0")
        op_check.set(False); op_var.set("0")
        of_check.set(False); of_var.set("0")
        base_atk_var.set(0.0); base_atk_input_var.set("")
        summary_var.set("当前模式：期望伤害。点击「计算」后显示最终伤害。")
        result_text.delete("1.0", tk.END)
    def save_current_data() -> None:
        cb = {
            "weapon_passive": (wp_var.get(), wp_check.get()),
            "set_bonus": (set_var.get(), set_check.get()),
            "other_pct": (op_var.get(), op_check.get()),
            "other_flat": (of_var.get(), of_check.get()),
        }
        save_gui_state(
            current_values(), mode_var.get(), slot=current_slot_var.get(),
            debug_enabled=debug_enabled_var.get(),
            debug_value_rounding_modes={s: v.get() for s, v
                                        in debug_value_rounding_vars.items()},
            debug_result_rounding_modes={s: v.get() for s, v
                                         in debug_result_rounding_vars.items()},
            cond_bonuses=cb,
            main_pct_mode=main_pct_mode_var.get(),
        )
        messagebox.showinfo("保存成功",
                            f"配置槽 {current_slot_var.get()} 已保存。\n"
                            f"保存位置：{_slot_file(current_slot_var.get())}")

    # ---- debug window (unchanged internally) ----
    def open_debug_window() -> None:
        dw = tk.Toplevel(root)
        dw.title("Debug取整设置")
        dw.geometry("760x720")
        dw.transient(root)
        ttk.Checkbutton(dw, text="开启debug取整模式",
                        variable=debug_enabled_var).pack(anchor="w", padx=12, pady=(12, 6))
        ttk.Label(dw, text="数值取整：对输入数值先取整；计算结果取整：对每一步公式计算后的结果取整。",
                  wraplength=720).pack(anchor="w", padx=12, pady=(0, 6))
        prec_frame = ttk.Frame(dw)
        prec_frame.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Label(prec_frame, text="全局保留小数位 (-1=不截断):").pack(side="left", padx=(0, 6))
        ttk.Spinbox(prec_frame, from_=-1, to=10, textvariable=precision_var, width=5).pack(side="left")
        trunc_btn = ttk.Button(prec_frame)
        def _trunc_label():
            trunc_btn.configure(text=f"截断方式: {ROUNDING_MODE_LABELS[trunc_mode_var.get()]}")
        def _cycle_trunc():
            modes = ["round", "ceil", "floor"]
            ci = modes.index(trunc_mode_var.get()) if trunc_mode_var.get() in modes else 0
            trunc_mode_var.set(modes[(ci + 1) % len(modes)])
            _trunc_label()
        trunc_btn.configure(command=_cycle_trunc)
        trunc_btn.pack(side="left", padx=(12, 0))
        _trunc_label()

        em_prec_frame = ttk.Frame(dw)
        em_prec_frame.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(em_prec_frame, text="元素精通保留小数位 (-1=不截断):").pack(side="left", padx=(0, 6))
        ttk.Spinbox(em_prec_frame, from_=-1, to=10, textvariable=em_precision_var, width=5).pack(side="left")
        em_mode_btn = ttk.Button(em_prec_frame)
        def _em_mode_label():
            em_mode_btn.configure(text=f"截断方式: {ROUNDING_MODE_LABELS[em_trunc_mode_var.get()]}")
        def _cycle_em_mode():
            modes = ["round", "ceil", "floor"]
            ci = modes.index(em_trunc_mode_var.get()) if em_trunc_mode_var.get() in modes else 0
            em_trunc_mode_var.set(modes[(ci + 1) % len(modes)])
            _em_mode_label()
        em_mode_btn.configure(command=_cycle_em_mode)
        em_mode_btn.pack(side="left", padx=(12, 0))
        _em_mode_label()

        atk_prec_frame = ttk.Frame(dw)
        atk_prec_frame.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Label(atk_prec_frame, text="角色ATK保留小数位 (-1=不截断):").pack(side="left", padx=(0, 6))
        ttk.Spinbox(atk_prec_frame, from_=-1, to=10, textvariable=atk_decimal_var, width=5).pack(side="left")
        atk_btn = ttk.Button(atk_prec_frame)
        def _atk_label():
            atk_btn.configure(text=f"截断方式: {ROUNDING_MODE_LABELS[atk_trunc_var.get()]}")
        def _cycle_atk():
            modes = ["round", "ceil", "floor"]
            ci = modes.index(atk_trunc_var.get()) if atk_trunc_var.get() in modes else 0
            atk_trunc_var.set(modes[(ci + 1) % len(modes)])
            _atk_label()
        atk_btn.configure(command=_cycle_atk)
        atk_btn.pack(side="left", padx=(12, 0))
        _atk_label()

        mode_order = list(ROUNDING_MODES)

        def btn_text(label: str, mode: str) -> str:
            return f"{label}: {ROUNDING_MODE_LABELS[mode]}"

        def make_cycle_button(parent: ttk.Frame, label: str,
                              variable: tk.StringVar) -> ttk.Button:
            btn = ttk.Button(parent)
            def refresh():
                btn.configure(text=btn_text(label, variable.get()))
            def cycle():
                ci = mode_order.index(variable.get()) if variable.get() in mode_order else 0
                variable.set(mode_order[(ci + 1) % len(mode_order)])
                refresh()
            btn.configure(command=cycle)
            refresh()
            return btn

        nb = ttk.Notebook(dw)
        nb.pack(fill="both", expand=True, padx=12, pady=6)
        vf = ttk.Frame(nb, padding=12)
        rf = ttk.Frame(nb, padding=12)
        nb.add(vf, text="数值取整")
        nb.add(rf, text="计算结果取整")

        def fill_rounding_frame(frame: ttk.Frame,
                                steps: tuple[tuple[str, str], ...],
                                variables: dict[str, tk.StringVar]):
            for row, (step, label) in enumerate(steps):
                ttk.Label(frame, text=f"{label}（{step}）").grid(
                    row=row, column=0, sticky="w", padx=4, pady=3)
                make_cycle_button(frame, "取整方式", variables[step]).grid(
                    row=row, column=1, sticky="w", padx=4, pady=3)
            frame.columnconfigure(0, weight=1)

        fill_rounding_frame(vf, DEBUG_VALUE_STEPS, debug_value_rounding_vars)
        fill_rounding_frame(rf, DEBUG_RESULT_STEPS, debug_result_rounding_vars)

        def set_all(vars_: dict[str, tk.StringVar], mode: str):
            for v in vars_.values():
                v.set(mode)
            debug_enabled_var.set(mode != "off")
            dw.destroy()
            open_debug_window()

        af = ttk.LabelFrame(dw, text="一键控制", padding=8)
        af.pack(fill="x", padx=12, pady=(6, 12))
        ttk.Label(af, text="数值取整：").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Button(af, text="全部四舍五入",
                   command=lambda: set_all(debug_value_rounding_vars, "round")).grid(
            row=0, column=1, padx=3, pady=3)
        ttk.Button(af, text="全部向上取整",
                   command=lambda: set_all(debug_value_rounding_vars, "ceil")).grid(
            row=0, column=2, padx=3, pady=3)
        ttk.Button(af, text="全部向下取整",
                   command=lambda: set_all(debug_value_rounding_vars, "floor")).grid(
            row=0, column=3, padx=3, pady=3)
        ttk.Button(af, text="全部关闭取整",
                   command=lambda: set_all(debug_value_rounding_vars, "off")).grid(
            row=0, column=4, padx=3, pady=3)
        ttk.Label(af, text="计算结果取整：").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        ttk.Button(af, text="全部四舍五入",
                   command=lambda: set_all(debug_result_rounding_vars, "round")).grid(
            row=1, column=1, padx=3, pady=3)
        ttk.Button(af, text="全部向上取整",
                   command=lambda: set_all(debug_result_rounding_vars, "ceil")).grid(
            row=1, column=2, padx=3, pady=3)
        ttk.Button(af, text="全部向下取整",
                   command=lambda: set_all(debug_result_rounding_vars, "floor")).grid(
            row=1, column=3, padx=3, pady=3)
        ttk.Button(af, text="全部关闭取整",
                   command=lambda: set_all(debug_result_rounding_vars, "off")).grid(
            row=1, column=4, padx=3, pady=3)

    def toggle_damage_mode() -> None:
        if mode_var.get() == "期望":
            mode_var.set("暴伤")
            summary_var.set("当前模式：暴击伤害。暴击率系数按 1 计算，点击「计算」查看结果。")
        else:
            mode_var.set("期望")
            summary_var.set("当前模式：期望伤害。点击「计算」查看结果。")
        result_text.delete("1.0", tk.END)

    # ---- buttons ----
    ttk.Button(button_frame, text="计算", command=show_results).pack(side="left", padx=(0, 6))
    ttk.Button(button_frame, text="切换期望/暴伤",
               command=toggle_damage_mode).pack(side="left", padx=(0, 6))
    ttk.Button(button_frame, text="ATK计算器",
               command=lambda: open_atk_calculator(root, entries["atk"], base_atk_var)).pack(
        side="left", padx=(0, 6))
    ttk.Button(button_frame, text="Debug取整",
               command=open_debug_window).pack(side="left", padx=(0, 6))
    ttk.Checkbutton(button_frame, text="显示计算日志", variable=log_enabled_var,
                    command=lambda: result_text.configure(height=28 if log_enabled_var.get() else 12)).pack(side="left", padx=(0, 6))

    ttk.Button(button_frame, text="保存当前数据",
               command=save_current_data).pack(side="left", padx=(0, 6))
    ttk.Button(button_frame, text="恢复默认值",
               command=reset_defaults).pack(side="left")

    root.mainloop()


# --------------- CLI ---------------

CLI_INPUT_FIELDS = [
    ("--atk",                           "atk",                          "角色 ATK / 角色面板攻击力", True,  None),
    ("--em",                            "elemental_mastery",           "元素精通",                   True,  None),
    ("--crit-rate",                     "crit_rate",                   "暴击率",                     True,  None),
    ("--crit-damage",                   "crit_damage",                 "暴击伤害",                   True,  None),
    ("--talent-multiplier",             "talent_multiplier",           "天赋倍率",                   True,  None),
    ("--stacks",                        "stacks",                      "星超导层数",                 False, 0),
    ("--reaction-bonus",                "reaction_bonus",              "反应提升",                   False, 0.0),
    ("--base-reaction-damage-bonus",    "base_reaction_damage_bonus",  "星反应基础伤害提升",         False, 0.0),
    ("--flat-damage-increase",          "flat_damage_increase",        "伤害提高",                   False, 0.0),
    ("--enemy-resistance",              "enemy_resistance",            "目标抗性",                   False, 0.1),
    ("--elevation-bonus",              "elevation_bonus",             "擢升提升",                   False, 0.0),
]


def _parse_rounding_kv(raw: list[str], step_names: tuple[tuple[str, str], ...]) -> dict[str, str]:
    valid_steps = {s for s, _ in step_names}
    result: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"取整参数格式错误（应为 STEP=MODE）：{item}")
        step, mode = item.split("=", 1)
        if step not in valid_steps:
            raise ValueError(f"未知取整步骤：{step}")
        if mode not in ROUNDING_MODES:
            raise ValueError(f"未知取整模式：{mode}（可选：{', '.join(ROUNDING_MODES)}）")
        result[step] = mode
    return result


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="原神星超导角色伤害计算器 — 命令行模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="百分比请用小数输入，例如 80%% → 0.8，140%% → 1.4。",
    )

    for flag, dest, label, required, default in CLI_INPUT_FIELDS:
        kw: dict = {"dest": dest, "help": f"{label}"}
        if flag == "--stacks":
            kw["type"] = int
        elif default is not None:
            kw["type"] = float
        else:
            kw["type"] = float
        if required:
            kw["required"] = True
        else:
            kw["default"] = default
        parser.add_argument(flag, **kw)

    parser.add_argument("--crit-damage-only", action="store_true", help="暴伤模式（暴击率系数=1）")
    parser.add_argument("--list-inputs", action="store_true", help="列出所有输入参数及说明")
    parser.add_argument("--debug-rounding", action="store_true", help="启用 Debug 取整")
    parser.add_argument(
        "--value-rounding-mode", choices=ROUNDING_MODES, default="off",
        help="全局数值取整模式",
    )
    parser.add_argument(
        "--result-rounding-mode", choices=ROUNDING_MODES, default="off",
        help="全局计算结果取整模式",
    )
    parser.add_argument(
        "--round-value", action="append", default=[],
        help="单个数值取整，格式：STEP=MODE（如 atk=floor）；可重复使用",
    )
    parser.add_argument(
        "--round-result", action="append", default=[],
        help="单个计算结果取整，格式：STEP=MODE（如 expected_damage=floor）；可重复使用",
    )

    args = parser.parse_args()

    if args.list_inputs:
        _print_input_list()
        return

    missing = []
    for flag, dest, label, required, _default in CLI_INPUT_FIELDS:
        if required and getattr(args, dest) is None:
            missing.append(f"{flag}（{label}）")
    if missing:
        print("错误：缺少以下必填参数：")
        for m in missing:
            print(f"  {m}")
        print("请补充参数后重新运行，或使用 --help 查看帮助。")
        sys.exit(2)

    character = CharacterInfo(
        atk=args.atk,
        elemental_mastery=args.elemental_mastery,
        crit_rate=args.crit_rate,
        crit_damage=args.crit_damage,
    )
    coefficients = DamageCoefficients(
        talent_multiplier=args.talent_multiplier,
        catalyze_stacks=args.stacks,
        reaction_bonus=args.reaction_bonus,
        base_reaction_damage_bonus=args.base_reaction_damage_bonus,
        flat_damage_increase=args.flat_damage_increase,
        enemy_resistance=args.enemy_resistance,
        elevation_bonus=args.elevation_bonus,
    )

    debug_config: DebugConfig | None = None
    if args.debug_rounding or args.round_value or args.round_result:
        val_modes = default_value_rounding_modes(args.value_rounding_mode)
        res_modes = default_result_rounding_modes(args.result_rounding_mode)
        if args.round_value:
            val_modes.update(_parse_rounding_kv(args.round_value, DEBUG_VALUE_STEPS))
        if args.round_result:
            res_modes.update(_parse_rounding_kv(args.round_result, DEBUG_RESULT_STEPS))
        debug_config = DebugConfig(
            enabled=True,
            value_rounding_modes=val_modes,
            result_rounding_modes=res_modes,
        )

    result = calculate_damage(
        character, coefficients,
        crit_damage_only=args.crit_damage_only,
        debug_config=debug_config,
    )

    _print_results(result, crit_damage_only=args.crit_damage_only,
                   debug_enabled=debug_config is not None and debug_config.enabled)


def _print_input_list() -> None:
    print("原神星超导角色伤害计算器 — 输入参数列表")
    print()


def _print_results(result: dict[str, float], *,
                   crit_damage_only: bool = False,
                   debug_enabled: bool = False) -> None:
    mode_name = "暴伤模式" if crit_damage_only else "期望伤害模式"
    print(f"原神星超导角色伤害计算器 — {mode_name}")
    if debug_enabled:
        print("（Debug 取整已启用）")
    print()
    print("  ── 输入数值 ──")
    for key, label in [
        ("atk", "角色 ATK / 面板攻击力"),
        ("elemental_mastery", "元素精通"),
        ("crit_rate", "暴击率"),
        ("crit_damage", "暴击伤害"),
        ("talent_multiplier", "天赋倍率"),
        ("reaction_bonus", "反应提升"),
        ("base_reaction_damage_bonus", "星反应基础伤害提升"),
        ("flat_damage_increase", "伤害提高"),
        ("enemy_resistance", "目标抗性"),
        ("elevation_bonus", "擢升提升"),
    ]:
        val = result.get(key)
        if val is not None:
            print(f"  {label:<24} {val:>12.4f}")
    print()
    print("  ── 分步计算 ──")
    for key, label in [
        ("reaction_coefficient", "反应系数"),
        ("multiplier_area", "倍率区"),
        ("elemental_mastery_bonus", "精通提升"),
        ("damage_bonus_area", "增伤区（1+精通+反应）"),
        ("additive_area", "加伤区（1+基础伤害提升）"),
        ("base_area", "基础区"),
        ("crit_rate_coefficient", "暴击率系数"),
        ("crit_area", "双暴区"),
        ("resistance_area", "抗性区"),
        ("elevation_area", "擢升区"),
    ]:
        val = result.get(key)
        if val is not None:
            print(f"  {label:<24} {val:>12.4f}")
    print()
    expected = result.get("expected_damage")
    if expected is not None:
        print(f"  {'>>> 最终期望伤害':<24} {expected:>12.2f}")
    print()


if __name__ == "__main__":
    run_gui()
