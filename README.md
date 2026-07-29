# 原神伤害计算器

这是一个用于扩展原神角色伤害计算模块的 Python 项目。当前已实现 **星超导伤害** 模块，计算后端位于 `damage_calculator.py`；主界面采用 PySide6/QML Signal UI，后续模块通过顶部的计算模式选择器接入。

## 推荐启动方式

```powershell
python qml_prototype/main.py
```

主界面包含星超导伤害计算、常驻 ATK 计算器、配置槽、自动保存、UGC 截图异步识别、主题切换和 Windows 无边框窗口支持。详细界面说明见 [`qml_prototype/README.md`](qml_prototype/README.md)。

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

当前主界面为 QML Signal UI：

```powershell
python qml_prototype/main.py
```

窗口固定为 `1180 × 820`，顶部中央可切换计算模块；当前模块为“星超导伤害”。左侧菜单提供跟随系统、手动深色模式和芙宁娜主题设置。Windows 11 下会请求系统原生圆角，右上角提供最小化与关闭按钮。

旧 Tkinter 界面仍可通过 `python damage_calculator.py --gui` 启动，仅作为兼容入口保留。

### 配置、主题与自动保存

QML 主界面包含 5 个配置槽。保存时会写入当前输入、伤害模式、百分比输入模式、条件 ATK 加成、自动保存状态，以及下列主题状态：

- `followSystem`
- `darkMode`
- `furinaTheme`

主题会随配置槽恢复；如果某个配置启用了“跟随系统”，读取后会按当前 Windows 系统主题决定实际浅色或深色。旧存档没有主题字段时保持兼容。

伤害配置默认保存到用户目录下的 `.genshin_damage_calculator.json` 与各槽位文件；ATK 计算器配置保存在 `.genshin_atk_artifacts.json`。

### Debug 取整模式

如果你在对比实际游戏伤害时发现有十几点偏差，可以打开 debug 取整模式来测试取整造成的影响。

Debug 取整现在分成两部分：

- **数值取整**：对参与公式的原始数值先取整，例如 `atk`、元素精通、暴击率、暴击伤害、天赋倍率、目标抗性等。
- **计算结果取整**：对每一步公式计算后的结果取整，例如反应系数、倍率区、增伤区、基础区、双爆区、最终伤害等。

在 GUI 中点击计算栏里的“Debug取整”按钮，会打开单独的 debug 设置窗口。该窗口支持：

- 自由开启或关闭 debug 取整模式。
- 在“数值取整”和“计算结果取整”两个页签里分别设置取整方式。
- 每个取整方式都改为按钮循环切换：点击按钮会在 `关闭取整 → 四舍五入 → 向上取整 → 向下取整 → 关闭取整` 之间循环。
- 一键把全部数值或全部计算结果设置为同一种取整方式。
- 点击“保存当前数据”时，也会保存当前 debug 开关、数值取整方式和计算结果取整方式，下次打开 GUI 自动加载。

命令行也可以控制 debug 取整：

```bash
python damage_calculator.py \
  --atk 2000 \
  --em 300 \
  --crit-rate 0.7 \
  --crit-damage 1.4 \
  --talent-multiplier 2.5 \
  --debug-rounding \
  --value-rounding-mode off \
  --result-rounding-mode floor
```

如果只想控制某一个数值或某一步计算结果，可以使用：

- `--round-value STEP=MODE`：控制单个数值取整。
- `--round-result STEP=MODE`：控制单个计算结果取整。

例如：

```bash
python damage_calculator.py \
  --atk 2000.6 \
  --em 300 \
  --crit-rate 0.7 \
  --crit-damage 1.4 \
  --talent-multiplier 2.5 \
  --debug-rounding \
  --value-rounding-mode off \
  --result-rounding-mode off \
  --round-value atk=floor \
  --round-result expected_damage=floor
```

可用取整模式：`off`（关闭取整）、`round`（四舍五入）、`ceil`（向上取整）、`floor`（向下取整）。旧参数 `--rounding-mode` 和 `--round-step` 仍可使用，分别等同于 `--result-rounding-mode` 和 `--round-result`。

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
