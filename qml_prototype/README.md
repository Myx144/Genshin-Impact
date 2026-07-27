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
