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
双爆区（暴伤）= 1 + 1 × 暴击伤害
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

## 所需输入数据名称

百分比统一用小数输入，例如 80% 输入 `0.8`，140% 输入 `1.4`。

| 程序参数名称 | 中文名称 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `--atk` | 角色 atk / 角色面板攻击力 | 必填 | 题图基础区中的“角色面板”，直接填角色攻击力数值。 |
| `--em` | 元素精通 | 必填 | 用于计算精通提升：元素精通 × 6 / (元素精通 + 2000)。 |
| `--crit-rate` | 暴击率 | 必填 | 用小数输入，例如 70% 填 `0.7`。 |
| `--crit-damage` | 暴击伤害 | 必填 | 用小数输入，例如 140% 填 `1.4`。 |
| `--talent-multiplier` | 天赋倍率 | 必填 | 题图基础区中的“倍率”，例如 250% 填 `2.5`。 |
| `--stacks` | 星超导层数 | 可选，默认 `0` | 取值范围为 0 到 12，用于计算反应系数。 |
| `--reaction-bonus` | 反应提升 | 可选，默认 `0` | 增伤区中的反应提升，用小数输入。 |
| `--base-reaction-damage-bonus` | 星反应基础伤害提升 | 可选，默认 `0` | 加伤区中的基础伤害提升，用小数输入。 |
| `--flat-damage-increase` | 伤害提高 | 可选，默认 `0` | 基础区末尾直接相加的固定伤害值。 |
| `--enemy-resistance` | 目标抗性 | 可选，默认 `0.1` | 抗性区输入，可为负数；10% 填 `0.1`。 |
| `--elevation-bonus` | 擢升提升 | 可选，默认 `0` | 擢升区提升，用小数输入。 |

也可以用下面的命令在终端直接查看输入名称：

```bash
python damage_calculator.py --list-inputs
```

## 可视化界面

如果不想在命令行里逐个输入参数，可以打开 Tkinter 可视化界面：

```bash
python damage_calculator.py --gui
```

界面会显示所有输入框、中文字段名、是否必填、输入说明，并在输入区下方提供“计算”、“切换期望/暴伤”、“保存当前数据”和“恢复示例默认值”按钮。默认模式为期望伤害；点击“切换期望/暴伤”后进入暴伤模式，此时暴击率系数按 `1` 计算，即双爆区变为 `1 + 1 × 暴击伤害`。点击“计算”后，窗口会用醒目文字显示最终伤害，并在下方结果区显示各分区系数和最终 `expected_damage`。

### 保存输入数据

在可视化界面中点击“保存当前数据”后，程序会保存当前所有输入框内容和当前模式；下次运行 `python damage_calculator.py --gui` 时会自动加载这些数据。默认保存位置为用户目录下的 `.genshin_damage_calculator.json`。

### Debug 取整模式

如果你在对比实际游戏伤害时发现有十几点偏差，可以打开 debug 取整模式来测试每一步取整造成的影响。

在 GUI 中点击计算栏里的“Debug取整”按钮，会打开单独的 debug 设置窗口。该窗口支持：

- 自由开启或关闭 debug 取整模式。
- 为每一个计算步骤单独选择取整方式：四舍五入、向上取整、向下取整、关闭取整。
- 一键把全部计算步骤设置为同一种取整方式。
- 点击“保存当前数据”时，也会保存当前 debug 开关和每一步取整方式，下次打开 GUI 自动加载。

命令行也可以控制 debug 取整：

```bash
python damage_calculator.py \
  --atk 2000 \
  --em 300 \
  --crit-rate 0.7 \
  --crit-damage 1.4 \
  --talent-multiplier 2.5 \
  --debug-rounding \
  --rounding-mode floor
```

如果只想控制某一步，可以使用 `--round-step STEP=MODE`，例如：

```bash
python damage_calculator.py \
  --atk 2000 \
  --em 300 \
  --crit-rate 0.7 \
  --crit-damage 1.4 \
  --talent-multiplier 2.5 \
  --debug-rounding \
  --rounding-mode off \
  --round-step base_area=ceil \
  --round-step expected_damage=floor
```

可用取整模式：`off`（关闭取整）、`round`（四舍五入）、`ceil`（向上取整）、`floor`（向下取整）。可用步骤名会在计算结果中以英文 key 形式显示，例如 `multiplier_area`、`base_area`、`crit_area`、`expected_damage`。

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

如果要在命令行中使用暴伤模式（暴击率系数按 `1` 计算），增加 `--crit-damage-only`：

```bash
python damage_calculator.py \
  --atk 2000 \
  --em 300 \
  --crit-rate 0.7 \
  --crit-damage 1.4 \
  --talent-multiplier 2.5 \
  --crit-damage-only
```

程序会输出各分区系数以及最终 `expected_damage`。
