# 原神伤害计算器 · QML Signal UI

这是项目当前的主界面，使用 **PySide6 + QML** 实现；数值计算仍由项目根目录的 `damage_calculator.py` 提供。

## 启动

```powershell
python qml_prototype/main.py
```

## 当前计算模块

当前已实现模块为：

- **星超导伤害** / `SUPERCONDUCT DAMAGE`

窗口顶部中央的倒梯形按钮是计算模块选择器。后续新增伤害模块时，可在 `Main.qml` 的 `damageModules` 中登记模块信息，并为对应模块接入页面和计算逻辑。

## 功能

- 星超导伤害计算、期望伤害 / 暴击伤害模式切换
- 常驻 ATK 计算器、有效 ATK 预览与一键回填
- 5 个配置槽、配置命名、自动保存与手动保存提示
- UGC 截图异步识别：加载遮罩、识别结果选择、应用与撤销识别值
- 顶部下拉式模块菜单、左侧设置菜单、最小化和关闭按钮
- 固定 `1180 × 820` 的无边框 Windows 窗口；Windows 11 下会请求系统原生圆角

## 主题

左侧菜单提供三项主题设置：

- **跟随系统**：根据 Windows 的浅色 / 深色设置自动切换，并监听系统主题变化。
- **深色模式**：关闭“跟随系统”后可手动切换。
- **芙宁娜主题**：独立开关；在浅色和深色模式中分别使用对应的芙宁娜配色。

主题状态会随当前配置槽保存：`followSystem`、`darkMode` 和 `furinaTheme`。

## 保存

伤害配置槽保存在用户目录下：

```text
.genshin_damage_calculator.json
.genshin_damage_calculator_slot2.json
...
.genshin_damage_calculator_slot5.json
```

每个槽会保存输入值、伤害模式、百分比输入模式、条件 ATK 加成、自动保存状态以及主题设置。旧存档没有主题字段时仍可正常读取。

ATK 计算器配置单独保存在：

```text
.genshin_atk_artifacts.json
```

## 图标

`Columbina.gif` 的首帧已转换为透明多尺寸图标：

```text
qml_prototype/Columbina.ico
```

启动时会同时设置 Qt 应用图标和 Windows 原生窗口图标，以便任务栏显示角色图标。

## 主要文件

```text
qml_prototype/Main.qml       主界面、模块菜单、主题与配置槽
qml_prototype/AtkPage.qml    常驻 ATK 计算器
qml_prototype/AppButton.qml  通用按钮
qml_prototype/AppCheckBox.qml 通用复选框
qml_prototype/main.py        QML Bridge、保存、OCR 任务、Windows 原生窗口处理
damage_calculator.py         伤害计算后端
```
