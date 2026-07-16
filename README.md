# Genshin Impact Damage Calculator

这是一个用于计算原神角色星超导反应期望伤害的 Python 命令行程序。

## 公式

程序按题图实现：

```text
星超导反应角色伤害 = 基础区 × 双爆区 × 抗性区 × 擢升区
基础区 = 倍率区 × 增伤区 × 加伤区 + 伤害提高
倍率区 = 反应系数 × 角色 atk × 天赋倍率
增伤区 = 1 + 精通提升 + 反应提升
精通提升 = 元素精通 × 6 / (元素精通 + 2000)
加伤区 = 1 + 星反应基础伤害提升
双爆区（期望）= 1 + 暴击率 × 暴击伤害
擢升区 = 1 + 擢升提升
```

其中，题图基础区里的“角色面板”按 `atk` 处理，“倍率”按天赋倍率处理。

抗性区为：

```text
目标抗性 > 75%：1 / (1 + 4 × 目标抗性)
0 ≤ 目标抗性 ≤ 75%：1 - 目标抗性
目标抗性 < 0：1 - 目标抗性 / 2
```

反应系数为：

```text
星超导层数 = 0：1
星超导层数 = 1-12：0.05 × 层数 + 1.4
```

## 使用方式

百分比请用小数输入，例如 80% 输入 `0.8`，140% 输入 `1.4`。

```bash
python damage_calculator.py \
  --atk 2000 \
  --em 300 \
  --crit-rate 0.7 \
  --crit-damage 1.4 \
  --talent-multiplier 2.5 \
  --stacks 6 \
  --reaction-bonus 0.15 \
  --base-reaction-damage-bonus 0.14 \
  --flat-damage-increase 0 \
  --enemy-resistance 0.1 \
  --elevation-bonus 0
```

程序会输出各分区系数以及最终 `expected_damage`。
