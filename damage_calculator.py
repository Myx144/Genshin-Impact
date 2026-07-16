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
    ("--atk", "角色 atk / 角色面板攻击力", "必填", "基础区中的角色面板，直接填角色攻击力数值"),
    ("--em", "元素精通", "必填", "用于计算精通提升：元素精通 × 6 / (元素精通 + 2000)"),
    ("--crit-rate", "暴击率", "必填", "用小数输入，例如 70% 填 0.7"),
    ("--crit-damage", "暴击伤害", "必填", "用小数输入，例如 140% 填 1.4"),
    ("--talent-multiplier", "天赋倍率", "必填", "基础区中的倍率，例如 250% 填 2.5"),
    ("--stacks", "星超导层数", "可选，默认 0", "0 到 12，用于计算反应系数"),
    ("--reaction-bonus", "反应提升", "可选，默认 0", "增伤区中的反应提升，用小数输入"),
    ("--base-reaction-damage-bonus", "星反应基础伤害提升", "可选，默认 0", "加伤区中的基础伤害提升，用小数输入"),
    ("--flat-damage-increase", "伤害提高", "可选，默认 0", "基础区末尾直接相加的固定伤害值"),
    ("--enemy-resistance", "目标抗性", "可选，默认 0.1", "抗性区输入，可为负数；10% 填 0.1"),
    ("--elevation-bonus", "擢升提升", "可选，默认 0", "擢升区提升，用小数输入"),
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


def calculate_damage(character: CharacterInfo, coefficients: DamageCoefficients) -> dict[str, float]:
    """Calculate expected damage and expose each formula area for review."""

    coefficient = reaction_coefficient(coefficients.catalyze_stacks)
    multiplier_area = coefficient * character.atk * coefficients.talent_multiplier
    em_bonus = elemental_mastery_bonus(character.elemental_mastery)
    damage_bonus_area = 1 + em_bonus + coefficients.reaction_bonus
    additive_area = 1 + coefficients.base_reaction_damage_bonus
    base_area = (
        multiplier_area * damage_bonus_area * additive_area
        + coefficients.flat_damage_increase
    )
    crit_area = 1 + character.crit_rate * character.crit_damage
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
    for name, chinese_name, requirement, note in INPUT_FIELDS:
        print(f"{name}: {chinese_name}｜{requirement}｜{note}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据星超导反应公式计算原神角色期望伤害。百分比请用小数输入，如 80%% 输入 0.8。"
    )
    parser.add_argument("--list-inputs", action="store_true", help="列出所需输入的数据名称和中文说明后退出")
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
    result = calculate_damage(character, coefficients)

    print("原神星超导反应角色伤害计算结果")
    for key, value in result.items():
        print(f"{key}: {value:.6f}")


if __name__ == "__main__":
    main()
