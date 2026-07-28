# UGC 面板识别

识别流程：四个白色方块定位 → 归一化到 1240×740 → 裁剪四组数值列 → 数字 OCR → 按 UGC 倍率解码。

当前数字 OCR 后端使用本地 Tesseract，不依赖 `pytesseract`。可通过环境变量 `GENSHIN_TESSERACT` 指定 `tesseract.exe`。
