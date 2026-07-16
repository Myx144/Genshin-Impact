#!/usr/bin/env python3
"""Genshin Impact Spread/Aggravate damage calculator.

This program implements the formula shown in the prompt image:

星超导反应角色伤害 = 基础区 × 双爆区 × 抗性区 × 擢升区

基础区 = 倍率区 × 增伤区 × 加伤区 + 伤害提高
倍率区 = 反应系数 × 角色 atk × 天赋倍率
增伤区 = 1 + 精通提升 + 反应提升
加伤区 = 1 + 星反应基础伤害提升
双爆区(期望) = 1 + 暴击率 × 暴击伤害
擢升区 = 1 + 擢升提升

The prompt specifically states that “角色面板” in 基础区 means character atk,
and “倍率” means talent multiplier.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path


SAVE_FILE = Path.home() / ".genshin_damage_calculator.json"
ROUNDING_MODES = ("off", "round", "ceil", "floor")
ROUNDING_MODE_LABELS = {
    "off": "关闭取整",
    "round": "四舍五入",
    "ceil": "向上取整",
    "floor": "向下取整",
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
    ("crit_area", "双爆区计算结果"),
    ("resistance_area", "抗性区计算结果"),
    ("elevation_area", "擢升区计算结果"),
    ("expected_damage", "最终伤害计算结果"),
)
DEBUG_ROUNDING_STEPS = DEBUG_RESULT_STEPS


INPUT_FIELDS = (
    ("atk", "--atk", "角色 atk / 角色面板攻击力", "必填", "基础区中的角色面板，直接填角色攻击力数值", "2000"),
    ("em", "--em", "元素精通", "必填", "用于计算精通提升：元素精通 × 6 / (元素精通 + 2000)", "300"),
    ("crit_rate", "--crit-rate", "暴击率", "必填", "用小数输入，例如 70% 填 0.7", "0.7"),
    ("crit_damage", "--crit-damage", "暴击伤害", "必填", "用小数输入，例如 140% 填 1.4", "1.4"),
    ("talent_multiplier", "--talent-multiplier", "天赋倍率", "必填", "基础区中的倍率，例如 250% 填 2.5", "2.5"),
    ("stacks", "--stacks", "星超导层数", "可选，默认 0", "0 到 12，用于计算反应系数", "0"),
    ("reaction_bonus", "--reaction-bonus", "反应提升", "可选，默认 0", "增伤区中的反应提升，用小数输入", "0"),
    ("base_reaction_damage_bonus", "--base-reaction-damage-bonus", "星反应基础伤害提升", "可选，默认 0", "加伤区中的基础伤害提升，用小数输入", "0"),
    ("flat_damage_increase", "--flat-damage-increase", "伤害提高", "可选，默认 0", "基础区末尾直接相加的固定伤害值", "0"),
    ("enemy_resistance", "--enemy-resistance", "目标抗性", "可选，默认 0.1", "抗性区输入，可为负数；10% 填 0.1", "0.1"),
    ("elevation_bonus", "--elevation-bonus", "擢升提升", "可选，默认 0", "擢升区提升，用小数输入", "0"),
)


@dataclass(frozen=True)
class CharacterInfo:
    """Character stats needed by the calculator.

    All rates are decimals. For example, 46.6% is entered as 0.466.
    """

    atk: float
    elemental_mastery: float
    crit_rate: float
    crit_damage: float


@dataclass(frozen=True)
class DamageCoefficients:
    """Additional coefficients from buffs, enemy stats, and reaction setup."""

    talent_multiplier: float
    catalyze_stacks: int = 0
    reaction_bonus: float = 0.0
    base_reaction_damage_bonus: float = 0.0
    flat_damage_increase: float = 0.0
    enemy_resistance: float = 0.1
    elevation_bonus: float = 0.0


@dataclass(frozen=True)
class DebugConfig:
    """Rounding controls for debug calculations.

    value_rounding_modes controls raw numeric values before they enter formulas.
    result_rounding_modes controls results after each calculation step.
    rounding_modes is kept as a backward-compatible alias for result_rounding_modes.
    """

    enabled: bool = False
    value_rounding_modes: dict[str, str] | None = None
    result_rounding_modes: dict[str, str] | None = None
    rounding_modes: dict[str, str] | None = None


def default_rounding_modes(mode: str = "off", steps: tuple[tuple[str, str], ...] = DEBUG_RESULT_STEPS) -> dict[str, str]:
    """Return a rounding-mode mapping for the selected debug steps."""

    if mode not in ROUNDING_MODES:
        raise ValueError(f"未知取整模式：{mode}")
    return {step: mode for step, _label in steps}


def default_value_rounding_modes(mode: str = "off") -> dict[str, str]:
    """Return value rounding modes for all raw numeric values."""

    return default_rounding_modes(mode, DEBUG_VALUE_STEPS)


def default_result_rounding_modes(mode: str = "off") -> dict[str, str]:
    """Return result rounding modes for all calculation-step results."""

    return default_rounding_modes(mode, DEBUG_RESULT_STEPS)


def round_debug_value(value: float, mode: str) -> float:
    """Round one debug value according to the selected mode."""

    if mode == "off":
        return value
    if mode == "round":
        return float(math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5))
    if mode == "ceil":
        return float(math.ceil(value))
    if mode == "floor":
        return float(math.floor(value))
    raise ValueError(f"未知取整模式：{mode}")


def apply_debug_rounding(value: float, step: str, debug_config: DebugConfig | None, category: str = "result") -> float:
    """Apply debug rounding to one value or calculation result when enabled."""

    if debug_config is None or not debug_config.enabled:
        return value
    if category == "value":
        rounding_modes = debug_config.value_rounding_modes or default_value_rounding_modes()
    else:
        rounding_modes = debug_config.result_rounding_modes or debug_config.rounding_modes or default_result_rounding_modes()
    return round_debug_value(value, rounding_modes.get(step, "off"))


def reaction_coefficient(catalyze_stacks: int) -> float:
    """Return reaction coefficient for 星超导层数.

    Image formula:
    - layers = 0: 1
    - layers = 1..12: 0.05 × layers + 1.4
    """

    if catalyze_stacks < 0 or catalyze_stacks > 12:
        raise ValueError("星超导层数必须在 0 到 12 之间")
    if catalyze_stacks == 0:
        return 1.0
    return 0.05 * catalyze_stacks + 1.4


def elemental_mastery_bonus(elemental_mastery: float) -> float:
    """Calculate 精通提升 = EM × 6 / (EM + 2000)."""

    if elemental_mastery < 0:
        raise ValueError("元素精通不能为负数")
    return elemental_mastery * 6 / (elemental_mastery + 2000)


def resistance_multiplier(enemy_resistance: float) -> float:
    """Calculate 抗性区 using the piecewise formula from the image."""

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
    """Calculate damage and expose each formula area for review.

    When crit_damage_only is True, the crit-rate coefficient is treated as 1,
    so the crit area becomes 1 + crit damage.
    """

    atk = apply_debug_rounding(character.atk, "atk", debug_config, "value")
    elemental_mastery = apply_debug_rounding(character.elemental_mastery, "elemental_mastery", debug_config, "value")
    crit_rate = apply_debug_rounding(character.crit_rate, "crit_rate", debug_config, "value")
    crit_damage = apply_debug_rounding(character.crit_damage, "crit_damage", debug_config, "value")
    talent_multiplier = apply_debug_rounding(coefficients.talent_multiplier, "talent_multiplier", debug_config, "value")
    reaction_bonus = apply_debug_rounding(coefficients.reaction_bonus, "reaction_bonus", debug_config, "value")
    base_reaction_damage_bonus = apply_debug_rounding(
        coefficients.base_reaction_damage_bonus,
        "base_reaction_damage_bonus",
        debug_config,
        "value",
    )
    flat_damage_increase = apply_debug_rounding(
        coefficients.flat_damage_increase,
        "flat_damage_increase",
        debug_config,
        "value",
    )
    enemy_resistance = apply_debug_rounding(coefficients.enemy_resistance, "enemy_resistance", debug_config, "value")
    elevation_bonus = apply_debug_rounding(coefficients.elevation_bonus, "elevation_bonus", debug_config, "value")

    coefficient = apply_debug_rounding(
        reaction_coefficient(coefficients.catalyze_stacks),
        "reaction_coefficient",
        debug_config,
        "result",
    )
    multiplier_area = apply_debug_rounding(
        coefficient * atk * talent_multiplier,
        "multiplier_area",
        debug_config,
        "result",
    )
    em_bonus = apply_debug_rounding(
        elemental_mastery_bonus(elemental_mastery),
        "elemental_mastery_bonus",
        debug_config,
        "result",
    )
    damage_bonus_area = apply_debug_rounding(
        1 + em_bonus + reaction_bonus,
        "damage_bonus_area",
        debug_config,
        "result",
    )
    additive_area = apply_debug_rounding(
        1 + base_reaction_damage_bonus,
        "additive_area",
        debug_config,
        "result",
    )
    base_area = apply_debug_rounding(
        multiplier_area * damage_bonus_area * additive_area + flat_damage_increase,
        "base_area",
        debug_config,
        "result",
    )
    crit_rate_coefficient = apply_debug_rounding(
        1.0 if crit_damage_only else crit_rate,
        "crit_rate_coefficient",
        debug_config,
        "result",
    )
    crit_area = apply_debug_rounding(
        1 + crit_rate_coefficient * crit_damage,
        "crit_area",
        debug_config,
        "result",
    )
    resistance_area = apply_debug_rounding(
        resistance_multiplier(enemy_resistance),
        "resistance_area",
        debug_config,
        "result",
    )
    elevation_area = apply_debug_rounding(
        1 + elevation_bonus,
        "elevation_area",
        debug_config,
        "result",
    )
    expected_damage = apply_debug_rounding(
        base_area * crit_area * resistance_area * elevation_area,
        "expected_damage",
        debug_config,
        "result",
    )

    result = {
        "atk": atk,
        "elemental_mastery": elemental_mastery,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "talent_multiplier": talent_multiplier,
        "reaction_bonus": reaction_bonus,
        "base_reaction_damage_bonus": base_reaction_damage_bonus,
        "flat_damage_increase": flat_damage_increase,
        "enemy_resistance": enemy_resistance,
        "elevation_bonus": elevation_bonus,
        "reaction_coefficient": coefficient,
        "multiplier_area": multiplier_area,
        "elemental_mastery_bonus": em_bonus,
        "damage_bonus_area": damage_bonus_area,
        "additive_area": additive_area,
        "base_area": base_area,
        "crit_rate_coefficient": crit_rate_coefficient,
        "crit_area": crit_area,
        "resistance_area": resistance_area,
        "elevation_area": elevation_area,
        "expected_damage": expected_damage,
    }
    if debug_config is not None and debug_config.enabled:
        result["debug_rounding_enabled"] = 1.0
    return result

def non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("该参数不能为负数")
    return number


def print_input_fields() -> None:
    """Print all supported input names with Chinese labels and notes."""

    print("所需输入数据名称（百分比统一用小数输入）：")
    for _key, cli_name, chinese_name, requirement, note, _default in INPUT_FIELDS:
        print(f"{cli_name}: {chinese_name}｜{requirement}｜{note}")



def parse_gui_number(value: str, field_name: str, allow_negative: bool = False) -> float:
    """Parse a GUI entry value and return a validated float."""

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
    """Build data objects from GUI text values and calculate damage."""

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
        base_reaction_damage_bonus=parse_gui_number(values["base_reaction_damage_bonus"], "星反应基础伤害提升"),
        flat_damage_increase=parse_gui_number(values["flat_damage_increase"], "伤害提高"),
        enemy_resistance=parse_gui_number(values["enemy_resistance"], "目标抗性", allow_negative=True),
        elevation_bonus=parse_gui_number(values["elevation_bonus"], "擢升提升"),
    )
    return calculate_damage(
        character,
        coefficients,
        crit_damage_only=crit_damage_only,
        debug_config=debug_config,
    )



def default_gui_values() -> dict[str, str]:
    """Return default GUI entry values keyed by input field key."""

    return {key: default for key, _cli_name, _chinese_name, _requirement, _note, default in INPUT_FIELDS}


def load_saved_gui_state(save_file: Path = SAVE_FILE) -> dict[str, object]:
    """Load saved GUI values and mode from disk if available."""

    if not save_file.exists():
        return {
            "values": default_gui_values(),
            "mode": "期望",
            "debug_enabled": False,
            "debug_value_rounding_modes": default_value_rounding_modes(),
            "debug_result_rounding_modes": default_result_rounding_modes(),
        }

    with save_file.open("r", encoding="utf-8") as file:
        saved_state = json.load(file)

    saved_values = saved_state.get("values", {})
    values = default_gui_values()
    for key in values:
        if key in saved_values:
            values[key] = str(saved_values[key])

    mode = saved_state.get("mode", "期望")
    if mode not in {"期望", "暴伤"}:
        mode = "期望"

    legacy_rounding_modes = saved_state.get("debug_rounding_modes", {})
    saved_value_rounding_modes = saved_state.get("debug_value_rounding_modes", {})
    saved_result_rounding_modes = saved_state.get("debug_result_rounding_modes", legacy_rounding_modes)

    debug_value_rounding_modes = default_value_rounding_modes()
    for step in debug_value_rounding_modes:
        mode_value = saved_value_rounding_modes.get(step, "off")
        if mode_value in ROUNDING_MODES:
            debug_value_rounding_modes[step] = mode_value

    debug_result_rounding_modes = default_result_rounding_modes()
    for step in debug_result_rounding_modes:
        mode_value = saved_result_rounding_modes.get(step, "off")
        if mode_value in ROUNDING_MODES:
            debug_result_rounding_modes[step] = mode_value

    return {
        "values": values,
        "mode": mode,
        "debug_enabled": bool(saved_state.get("debug_enabled", False)),
        "debug_value_rounding_modes": debug_value_rounding_modes,
        "debug_result_rounding_modes": debug_result_rounding_modes,
    }


def save_gui_state(
    values: dict[str, str],
    mode: str,
    debug_enabled: bool = False,
    debug_value_rounding_modes: dict[str, str] | None = None,
    debug_result_rounding_modes: dict[str, str] | None = None,
    save_file: Path = SAVE_FILE,
    debug_rounding_modes: dict[str, str] | None = None,
) -> None:
    """Save current GUI values, mode, and debug settings to disk for the next launch."""

    if debug_result_rounding_modes is None and debug_rounding_modes is not None:
        debug_result_rounding_modes = debug_rounding_modes

    save_file.write_text(
        json.dumps(
            {
                "values": values,
                "mode": mode,
                "debug_enabled": debug_enabled,
                "debug_value_rounding_modes": debug_value_rounding_modes or default_value_rounding_modes(),
                "debug_result_rounding_modes": debug_result_rounding_modes or default_result_rounding_modes(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

def run_gui() -> None:
    """Open a Tkinter visual input interface for the damage calculator."""

    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk

    root = tk.Tk()
    root.title("原神星超导角色伤害计算器")
    root.geometry("900x720")

    ttk.Label(
        root,
        text="原神星超导角色伤害计算器",
        font=("Arial", 18, "bold"),
    ).pack(pady=(16, 4))
    ttk.Label(
        root,
        text="百分比请用小数输入，例如 70% 填 0.7，140% 填 1.4。",
    ).pack(pady=(0, 12))

    main_frame = ttk.Frame(root, padding=12)
    main_frame.pack(fill="both", expand=True)

    input_frame = ttk.LabelFrame(main_frame, text="输入数据", padding=12)
    input_frame.pack(fill="x")

    saved_state = load_saved_gui_state()
    saved_values = saved_state["values"]

    entries: dict[str, tk.StringVar] = {}
    for row, (key, cli_name, chinese_name, requirement, note, default) in enumerate(INPUT_FIELDS):
        ttk.Label(input_frame, text=f"{chinese_name}（{cli_name}）").grid(row=row, column=0, sticky="w", padx=4, pady=4)
        variable = tk.StringVar(value=saved_values.get(key, default))
        entries[key] = variable
        ttk.Entry(input_frame, textvariable=variable, width=18).grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(input_frame, text=requirement).grid(row=row, column=2, sticky="w", padx=4, pady=4)
        ttk.Label(input_frame, text=note, wraplength=390).grid(row=row, column=3, sticky="w", padx=4, pady=4)

    input_frame.columnconfigure(1, weight=1)

    initial_mode = str(saved_state.get("mode", "期望"))
    if initial_mode not in {"期望", "暴伤"}:
        initial_mode = "期望"
    initial_mode_label = "暴击伤害" if initial_mode == "暴伤" else "期望伤害"
    summary_var = tk.StringVar(value=f"当前模式：{initial_mode_label}。点击“计算”后显示最终伤害")
    mode_var = tk.StringVar(value=initial_mode)
    debug_enabled_var = tk.BooleanVar(value=bool(saved_state.get("debug_enabled", False)))
    saved_value_rounding_modes = saved_state.get("debug_value_rounding_modes", default_value_rounding_modes())
    saved_result_rounding_modes = saved_state.get("debug_result_rounding_modes", default_result_rounding_modes())
    debug_value_rounding_vars = {
        step: tk.StringVar(value=saved_value_rounding_modes.get(step, "off"))
        for step, _label in DEBUG_VALUE_STEPS
    }
    debug_result_rounding_vars = {
        step: tk.StringVar(value=saved_result_rounding_modes.get(step, "off"))
        for step, _label in DEBUG_RESULT_STEPS
    }

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=(12, 0))

    summary_label = ttk.Label(
        main_frame,
        textvariable=summary_var,
        font=("Arial", 14, "bold"),
        foreground="#0b6bcb",
    )
    summary_label.pack(fill="x", pady=(10, 0))

    result_frame = ttk.LabelFrame(main_frame, text="计算结果", padding=12)
    result_frame.pack(fill="both", expand=True, pady=(8, 0))

    result_text = tk.Text(result_frame, height=14, wrap="word")
    result_text.pack(fill="both", expand=True)

    def show_results() -> None:
        try:
            values = current_values()
            crit_damage_only = mode_var.get() == "暴伤"
            debug_config = DebugConfig(
                enabled=debug_enabled_var.get(),
                value_rounding_modes={step: variable.get() for step, variable in debug_value_rounding_vars.items()},
                result_rounding_modes={step: variable.get() for step, variable in debug_result_rounding_vars.items()},
            )
            result = calculate_from_values(
                values,
                crit_damage_only=crit_damage_only,
                debug_config=debug_config,
            )
        except ValueError as error:
            messagebox.showerror("输入错误", str(error))
            return

        expected_damage = result["expected_damage"]
        mode_label = "暴击伤害" if mode_var.get() == "暴伤" else "期望伤害"
        debug_label = "Debug取整：开启" if debug_enabled_var.get() else "Debug取整：关闭"
        summary_var.set(f"当前模式：{mode_label}｜{debug_label}｜最终伤害：{expected_damage:.6f}")
        lines = ["原神星超导反应角色伤害计算结果", f"当前模式：{mode_label}", debug_label, "", f"最终伤害 expected_damage: {expected_damage:.6f}", ""]
        lines.extend(f"{key}: {value:.6f}" for key, value in result.items())
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "\n".join(lines))

    def reset_defaults() -> None:
        for key, _cli_name, _chinese_name, _requirement, _note, default in INPUT_FIELDS:
            entries[key].set(default)
        mode_var.set("期望")
        debug_enabled_var.set(False)
        for variable in [*debug_value_rounding_vars.values(), *debug_result_rounding_vars.values()]:
            variable.set("off")
        summary_var.set("当前模式：期望伤害。点击“计算”后显示最终伤害")
        result_text.delete("1.0", tk.END)

    def current_values() -> dict[str, str]:
        return {key: variable.get() for key, variable in entries.items()}

    def save_current_data() -> None:
        save_gui_state(
            current_values(),
            mode_var.get(),
            debug_enabled=debug_enabled_var.get(),
            debug_value_rounding_modes={step: variable.get() for step, variable in debug_value_rounding_vars.items()},
            debug_result_rounding_modes={step: variable.get() for step, variable in debug_result_rounding_vars.items()},
        )
        messagebox.showinfo("保存成功", f"当前数据和debug设置已保存，下次打开会自动加载。\n保存位置：{SAVE_FILE}")

    def open_debug_window() -> None:
        debug_window = tk.Toplevel(root)
        debug_window.title("Debug取整设置")
        debug_window.geometry("760x640")
        debug_window.transient(root)

        ttk.Checkbutton(
            debug_window,
            text="开启debug取整模式",
            variable=debug_enabled_var,
        ).pack(anchor="w", padx=12, pady=(12, 6))

        ttk.Label(
            debug_window,
            text="数值取整：对输入数值/原始数值先取整；计算结果取整：对每一步公式计算后的结果取整。点击按钮可循环切换取整方式。",
            wraplength=720,
        ).pack(anchor="w", padx=12, pady=(0, 6))

        mode_order = list(ROUNDING_MODES)

        def button_text(label: str, mode: str) -> str:
            return f"{label}: {ROUNDING_MODE_LABELS[mode]}"

        def make_cycle_button(parent: ttk.Frame, label: str, variable: tk.StringVar) -> ttk.Button:
            button = ttk.Button(parent)

            def refresh() -> None:
                button.configure(text=button_text(label, variable.get()))

            def cycle() -> None:
                current_index = mode_order.index(variable.get()) if variable.get() in mode_order else 0
                variable.set(mode_order[(current_index + 1) % len(mode_order)])
                refresh()

            button.configure(command=cycle)
            refresh()
            return button

        notebook = ttk.Notebook(debug_window)
        notebook.pack(fill="both", expand=True, padx=12, pady=6)

        value_frame = ttk.Frame(notebook, padding=12)
        result_frame = ttk.Frame(notebook, padding=12)
        notebook.add(value_frame, text="数值取整")
        notebook.add(result_frame, text="计算结果取整")

        def fill_rounding_frame(frame: ttk.Frame, steps: tuple[tuple[str, str], ...], variables: dict[str, tk.StringVar]) -> None:
            for row, (step, label) in enumerate(steps):
                ttk.Label(frame, text=f"{label}（{step}）").grid(row=row, column=0, sticky="w", padx=4, pady=3)
                make_cycle_button(frame, "取整方式", variables[step]).grid(row=row, column=1, sticky="w", padx=4, pady=3)
            frame.columnconfigure(0, weight=1)

        fill_rounding_frame(value_frame, DEBUG_VALUE_STEPS, debug_value_rounding_vars)
        fill_rounding_frame(result_frame, DEBUG_RESULT_STEPS, debug_result_rounding_vars)

        def set_all(variables: dict[str, tk.StringVar], mode: str) -> None:
            for variable in variables.values():
                variable.set(mode)
            debug_enabled_var.set(mode != "off")
            debug_window.destroy()
            open_debug_window()

        all_frame = ttk.LabelFrame(debug_window, text="一键控制", padding=8)
        all_frame.pack(fill="x", padx=12, pady=(6, 12))
        ttk.Label(all_frame, text="数值取整：").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Button(all_frame, text="全部四舍五入", command=lambda: set_all(debug_value_rounding_vars, "round")).grid(row=0, column=1, padx=3, pady=3)
        ttk.Button(all_frame, text="全部向上取整", command=lambda: set_all(debug_value_rounding_vars, "ceil")).grid(row=0, column=2, padx=3, pady=3)
        ttk.Button(all_frame, text="全部向下取整", command=lambda: set_all(debug_value_rounding_vars, "floor")).grid(row=0, column=3, padx=3, pady=3)
        ttk.Button(all_frame, text="全部关闭取整", command=lambda: set_all(debug_value_rounding_vars, "off")).grid(row=0, column=4, padx=3, pady=3)
        ttk.Label(all_frame, text="计算结果取整：").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        ttk.Button(all_frame, text="全部四舍五入", command=lambda: set_all(debug_result_rounding_vars, "round")).grid(row=1, column=1, padx=3, pady=3)
        ttk.Button(all_frame, text="全部向上取整", command=lambda: set_all(debug_result_rounding_vars, "ceil")).grid(row=1, column=2, padx=3, pady=3)
        ttk.Button(all_frame, text="全部向下取整", command=lambda: set_all(debug_result_rounding_vars, "floor")).grid(row=1, column=3, padx=3, pady=3)
        ttk.Button(all_frame, text="全部关闭取整", command=lambda: set_all(debug_result_rounding_vars, "off")).grid(row=1, column=4, padx=3, pady=3)

    def toggle_damage_mode() -> None:
        if mode_var.get() == "期望":
            mode_var.set("暴伤")
            summary_var.set("当前模式：暴击伤害。暴击率系数按 1 计算，点击“计算”查看结果")
        else:
            mode_var.set("期望")
            summary_var.set("当前模式：期望伤害。点击“计算”查看结果")
        result_text.delete("1.0", tk.END)

    ttk.Button(button_frame, text="计算", command=show_results).pack(side="left", padx=(0, 8))
    ttk.Button(button_frame, text="切换期望/暴伤", command=toggle_damage_mode).pack(side="left", padx=(0, 8))
    ttk.Button(button_frame, text="Debug取整", command=open_debug_window).pack(side="left", padx=(0, 8))
    ttk.Button(button_frame, text="保存当前数据", command=save_current_data).pack(side="left", padx=(0, 8))
    ttk.Button(button_frame, text="恢复示例默认值", command=reset_defaults).pack(side="left")

    root.mainloop()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据星超导反应公式计算原神角色期望伤害。百分比请用小数输入，如 80%% 输入 0.8。"
    )
    parser.add_argument("--list-inputs", action="store_true", help="列出所需输入的数据名称和中文说明后退出")
    parser.add_argument("--gui", action="store_true", help="打开可视化输入界面")
    parser.add_argument("--crit-damage-only", action="store_true", help="切换为暴伤模式：暴击率系数按 1 计算")
    parser.add_argument("--debug-rounding", action="store_true", help="开启debug取整模式")
    parser.add_argument("--value-rounding-mode", choices=ROUNDING_MODES, default="off", help="debug模式下所有数值默认取整方式")
    parser.add_argument("--result-rounding-mode", "--rounding-mode", dest="result_rounding_mode", choices=ROUNDING_MODES, default="off", help="debug模式下所有计算结果默认取整方式")
    parser.add_argument("--round-value", action="append", default=[], metavar="STEP=MODE", help="为单个数值设置取整方式，可重复使用")
    parser.add_argument("--round-result", "--round-step", dest="round_result", action="append", default=[], metavar="STEP=MODE", help="为单个计算结果设置取整方式，可重复使用")
    parser.add_argument("--atk", type=non_negative_float, help="角色 atk / 角色面板攻击力")
    parser.add_argument("--em", type=non_negative_float, help="元素精通")
    parser.add_argument("--crit-rate", type=non_negative_float, help="暴击率，例如 0.7")
    parser.add_argument("--crit-damage", type=non_negative_float, help="暴击伤害，例如 1.4")
    parser.add_argument("--talent-multiplier", type=non_negative_float, help="天赋倍率，例如 2.5")
    parser.add_argument("--stacks", type=int, default=0, help="星超导层数，0 到 12")
    parser.add_argument("--reaction-bonus", type=non_negative_float, default=0.0, help="反应提升")
    parser.add_argument("--base-reaction-damage-bonus", type=non_negative_float, default=0.0, help="星反应基础伤害提升")
    parser.add_argument("--flat-damage-increase", type=non_negative_float, default=0.0, help="伤害提高（固定加值）")
    parser.add_argument("--enemy-resistance", type=float, default=0.1, help="目标抗性，例如 0.1；可为负数")
    parser.add_argument("--elevation-bonus", type=non_negative_float, default=0.0, help="擢升提升")
    return parser


def parse_round_step_options(
    round_step_options: list[str],
    default_mode: str,
    steps: tuple[tuple[str, str], ...] = DEBUG_RESULT_STEPS,
) -> dict[str, str]:
    """Parse repeated STEP=MODE CLI options into rounding modes."""

    rounding_modes = default_rounding_modes(default_mode, steps)
    valid_steps = {step for step, _label in steps}
    for option in round_step_options:
        if "=" not in option:
            raise ValueError(f"取整参数格式错误：{option}，应为 STEP=MODE")
        step, mode = option.split("=", 1)
        if step not in valid_steps:
            raise ValueError(f"未知计算步骤：{step}")
        if mode not in ROUNDING_MODES:
            raise ValueError(f"未知取整模式：{mode}")
        rounding_modes[step] = mode
    return rounding_modes


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.list_inputs:
        print_input_fields()
        return
    if args.gui:
        run_gui()
        return

    required_inputs = ("atk", "em", "crit_rate", "crit_damage", "talent_multiplier")
    missing_inputs = [f"--{name.replace('_', '-')}" for name in required_inputs if getattr(args, name) is None]
    if missing_inputs:
        parser.error("缺少必填参数：" + ", ".join(missing_inputs))

    character = CharacterInfo(
        atk=args.atk,
        elemental_mastery=args.em,
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
    try:
        value_rounding_modes = parse_round_step_options(args.round_value, args.value_rounding_mode, DEBUG_VALUE_STEPS)
        result_rounding_modes = parse_round_step_options(args.round_result, args.result_rounding_mode, DEBUG_RESULT_STEPS)
    except ValueError as error:
        parser.error(str(error))
    debug_config = DebugConfig(
        enabled=args.debug_rounding,
        value_rounding_modes=value_rounding_modes,
        result_rounding_modes=result_rounding_modes,
    )
    result = calculate_damage(
        character,
        coefficients,
        crit_damage_only=args.crit_damage_only,
        debug_config=debug_config,
    )

    mode_label = "暴击伤害" if args.crit_damage_only else "期望伤害"
    print(f"原神星超导反应角色伤害计算结果（{mode_label}模式）")
    if args.debug_rounding:
        print("Debug取整模式：开启")
    for key, value in result.items():
        print(f"{key}: {value:.6f}")


if __name__ == "__main__":
    main()
