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
from dataclasses import dataclass


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
) -> dict[str, float]:
    """Calculate damage and expose each formula area for review.

    When crit_damage_only is True, the crit-rate coefficient is treated as 1,
    so the crit area becomes 1 + crit damage.
    """

    coefficient = reaction_coefficient(coefficients.catalyze_stacks)
    multiplier_area = coefficient * character.atk * coefficients.talent_multiplier
    em_bonus = elemental_mastery_bonus(character.elemental_mastery)
    damage_bonus_area = 1 + em_bonus + coefficients.reaction_bonus
    additive_area = 1 + coefficients.base_reaction_damage_bonus
    base_area = (
        multiplier_area * damage_bonus_area * additive_area
        + coefficients.flat_damage_increase
    )
    crit_rate_coefficient = 1.0 if crit_damage_only else character.crit_rate
    crit_area = 1 + crit_rate_coefficient * character.crit_damage
    resistance_area = resistance_multiplier(coefficients.enemy_resistance)
    elevation_area = 1 + coefficients.elevation_bonus
    expected_damage = base_area * crit_area * resistance_area * elevation_area

    return {
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


def calculate_from_values(values: dict[str, str], crit_damage_only: bool = False) -> dict[str, float]:
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
    return calculate_damage(character, coefficients, crit_damage_only=crit_damage_only)


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

    entries: dict[str, tk.StringVar] = {}
    for row, (key, cli_name, chinese_name, requirement, note, default) in enumerate(INPUT_FIELDS):
        ttk.Label(input_frame, text=f"{chinese_name}（{cli_name}）").grid(row=row, column=0, sticky="w", padx=4, pady=4)
        variable = tk.StringVar(value=default)
        entries[key] = variable
        ttk.Entry(input_frame, textvariable=variable, width=18).grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(input_frame, text=requirement).grid(row=row, column=2, sticky="w", padx=4, pady=4)
        ttk.Label(input_frame, text=note, wraplength=390).grid(row=row, column=3, sticky="w", padx=4, pady=4)

    input_frame.columnconfigure(1, weight=1)

    summary_var = tk.StringVar(value="当前模式：期望伤害。点击“计算”后显示最终伤害")
    mode_var = tk.StringVar(value="期望")

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
            values = {key: variable.get() for key, variable in entries.items()}
            crit_damage_only = mode_var.get() == "暴伤"
            result = calculate_from_values(values, crit_damage_only=crit_damage_only)
        except ValueError as error:
            messagebox.showerror("输入错误", str(error))
            return

        expected_damage = result["expected_damage"]
        mode_label = "暴击伤害" if mode_var.get() == "暴伤" else "期望伤害"
        summary_var.set(f"当前模式：{mode_label}｜最终伤害：{expected_damage:.6f}")
        lines = ["原神星超导反应角色伤害计算结果", f"当前模式：{mode_label}", "", f"最终伤害 expected_damage: {expected_damage:.6f}", ""]
        lines.extend(f"{key}: {value:.6f}" for key, value in result.items())
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "\n".join(lines))

    def reset_defaults() -> None:
        for key, _cli_name, _chinese_name, _requirement, _note, default in INPUT_FIELDS:
            entries[key].set(default)
        mode_var.set("期望")
        summary_var.set("当前模式：期望伤害。点击“计算”后显示最终伤害")
        result_text.delete("1.0", tk.END)

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
    ttk.Button(button_frame, text="恢复示例默认值", command=reset_defaults).pack(side="left")

    root.mainloop()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据星超导反应公式计算原神角色期望伤害。百分比请用小数输入，如 80%% 输入 0.8。"
    )
    parser.add_argument("--list-inputs", action="store_true", help="列出所需输入的数据名称和中文说明后退出")
    parser.add_argument("--gui", action="store_true", help="打开可视化输入界面")
    parser.add_argument("--crit-damage-only", action="store_true", help="切换为暴伤模式：暴击率系数按 1 计算")
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
    result = calculate_damage(character, coefficients, crit_damage_only=args.crit_damage_only)

    mode_label = "暴击伤害" if args.crit_damage_only else "期望伤害"
    print(f"原神星超导反应角色伤害计算结果（{mode_label}模式）")
    for key, value in result.items():
        print(f"{key}: {value:.6f}")


if __name__ == "__main__":
    main()
