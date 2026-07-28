# PySide6 + QML 原型

这是一个使用 Qt Quick 的独立 UI 原型。它复用 `damage_calculator.py` 的计算公式，并读取、切换和保存与 CTK 主程序相同的 5 个配置槽。

运行：

```powershell
python qml_prototype/main.py
```

当前原型包含：

- 11 项核心伤害输入
- 期望伤害 / 暴击伤害模式切换
- 伤害计算与分区系数显示
- Qt Quick 的颜色、尺寸和透明度过渡动画
- 读取、切换和保存 CTK 使用的 5 个配置槽
- 槽位名称编辑与当前槽位记忆
- QML 版常驻 ATK 计算器页面，可读取和保存原 ATK 配置
- 伤害页 / ATK 页上下移动淡入淡出
- 槽位按位置左右移动淡入淡出
- 期望 / 暴击模式文字上下淡入淡出
- 保存时保留尚未迁移的 Debug / 条件加成数据

尚未迁移：条件 ATK 加成与 Debug 取整。

## UGC 截图识别

伤害页的“截图识别”按钮支持固定 UGC 面板 V1：四个白色方块用于校准安全区，识别 1～4 号位角色的 ATK、Basic ATK、Crit Rate 与 Crit DMG。

数字 OCR 使用本地 Tesseract。默认自动查找 `C:\Program Files\Tesseract-OCR\tesseract.exe`，也可用环境变量 `GENSHIN_TESSERACT` 指定路径。识别结果必须经过蓝色背景验证、四方块几何验证以及 PSM 8/13 双重 OCR 一致性验证。
