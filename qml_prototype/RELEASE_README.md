# 原神伤害计算器

这是 QML 版本的可运行源码包。

## 启动

双击 `start.bat`，或在此目录执行：

```powershell
python main.py
```

## 依赖

建议使用 Python 3.10 或更高版本：

```powershell
python -m pip install -r requirements.txt
```

UGC 截图识别额外需要本地安装 Tesseract。安装后如未加入系统 PATH，可用环境变量 `GENSHIN_TESSERACT` 指向 `tesseract.exe`。

## 保存文件

配置不会写入压缩包目录，而是保存到当前 Windows 用户目录：

```text
.genshin_damage_calculator.json
.genshin_damage_calculator_slot2.json
...
.genshin_atk_artifacts.json
```
