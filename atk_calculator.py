"""ATK Calculator module for Genshin Impact damage calculator.

Provides open_atk_calculator - a Toplevel window for computing the
persistent portion of character ATK.

Formula:
    常驻ATK = 白值 x (1 + 武器副词条ATK% + 圣遗物ATK%) + 圣遗物固定ATK

Conditional bonuses (weapon passive, artifact set, external buffs)
live in the main GUI so the user can toggle them without reopening.
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk

SAVE_ARTIFACT_FILE = Path.home() / ".genshin_atk_artifacts.json"

# Track the currently open ATK calculator window to prevent duplicates
_open_atk_window: tk.Toplevel | None = None

ARTIFACT_SLOTS = [
    {"key": "flower",  "name": "生之花", "desc": "主词条固定HP，仅副词条提供攻击属性",
     "main_flat": False, "main_pct": False, "sub_flat": True,  "sub_pct": True},
    {"key": "plume",   "name": "死之羽", "desc": "主词条固定攻击力311，副词条不会出现固定攻击力",
     "main_flat": True,  "main_pct": False, "sub_flat": False, "sub_pct": True},
    {"key": "sands",   "name": "时之沙", "desc": "可选攻击力%主词条；若选攻击力%则副词条不再出现攻击力%",
     "main_flat": False, "main_pct": True,  "sub_flat": True,  "sub_pct": True},
    {"key": "goblet",  "name": "空之杯", "desc": "可选攻击力%主词条；若选攻击力%则副词条不再出现攻击力%",
     "main_flat": False, "main_pct": True,  "sub_flat": True,  "sub_pct": True},
    {"key": "circlet", "name": "理之冠", "desc": "可选攻击力%主词条；若选攻击力%则副词条不再出现攻击力%",
     "main_flat": False, "main_pct": True,  "sub_flat": True,  "sub_pct": True},
]

STAR = ["main_flat", "main_pct", "sub_flat", "sub_pct"]
PCT_STAR = {"main_pct", "sub_pct"}  # fields that are percentage-based
STAT_LABELS = {
    "main_flat": "主词条固定ATK", "main_pct": "主词条ATK%",
    "sub_flat":  "副词条固定ATK", "sub_pct":  "副词条ATK%",
}

MAXED_MAIN_ONLY = {
    "flower":  {},
    "plume":   {"main_flat": 311},
    "sands":   {"main_pct": 0.466},
    "goblet":  {"main_pct": 0.466},
    "circlet": {"main_pct": 0.466},
}


def _safe_float(var: tk.StringVar, name: str, parent: tk.Toplevel) -> float:
    text = var.get().strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        messagebox.showerror("输入错误", f"「{name}」不是有效的数字: {text}", parent=parent)
        raise


def _pct_from_entry(entry_var: tk.StringVar, pct_mode_var: tk.BooleanVar) -> float:
    """Read a percentage field, converting from display to decimal if needed."""
    text = entry_var.get().strip()
    value = float(text) if text else 0.0
    if pct_mode_var.get():
        value = value / 100.0
    return value


def open_atk_calculator(root: tk.Tk, atk_entry_var: tk.StringVar,
                        base_atk_var: tk.DoubleVar | None = None) -> None:
    global _open_atk_window

    # Prevent duplicate windows: bring existing to front
    if _open_atk_window is not None and _open_atk_window.winfo_exists():
        _open_atk_window.lift()
        _open_atk_window.focus_force()
        return

    atk_win = tk.Toplevel(root)
    atk_win.title("ATK计算器 - 常驻攻击力")
    atk_win.geometry("940x800")
    atk_win.transient(root)
    _open_atk_window = atk_win

    def _on_close():
        global _open_atk_window
        _open_atk_window = None
        atk_win.destroy()

    atk_win.protocol("WM_DELETE_WINDOW", _on_close)

    container = ttk.Frame(atk_win, padding=8)
    container.pack(fill="both")

    # ---- Percentage mode ----
    pct_mode_var = tk.BooleanVar(value=False)
    pct_mode_label_var = tk.StringVar(value="当前：小数输入（0.466 = 46.6%）")

    def _toggle_pct_mode():
        """Toggle between decimal and percentage display for all pct fields."""
        new_mode = not pct_mode_var.get()
        factor = 100.0 if new_mode else 0.01
        # Convert weapon secondary
        try:
            cur = float(weapon_secondary_var.get() or "0")
            weapon_secondary_var.set(f"{cur * factor:.5g}")
        except ValueError:
            weapon_secondary_var.set("0")
        # Convert artifact pct fields
        for slot in ARTIFACT_SLOTS:
            sk = slot["key"]
            sd = slot_data.get(sk, {})
            for st in PCT_STAR:
                info = sd.get(st)
                if info is None:
                    continue
                try:
                    cur = float(info["entry_var"].get() or "0")
                    info["entry_var"].set(f"{cur * factor:.5g}")
                except ValueError:
                    info["entry_var"].set("0")
        pct_mode_var.set(new_mode)
        if new_mode:
            pct_mode_label_var.set("当前：百分比输入（46.6 = 46.6%）")
            subtitle_var.set("百分比请用百分数输入（46.6% = 46.6）。勾选复选框启用，取消则不计入。")
        else:
            pct_mode_label_var.set("当前：小数输入（0.466 = 46.6%）")
            subtitle_var.set("百分比请用小数输入（46.6% = 0.466）。勾选复选框启用，取消则不计入。")

    # ---- Title ----
    ttk.Label(container, text="常驻攻击力 (ATK) 计算器",
              font=("Arial", 14, "bold")).pack(pady=(4, 2))
    subtitle_var = tk.StringVar(value="百分比请用小数输入（46.6% = 0.466）。勾选复选框启用，取消则不计入。")
    ttk.Label(container, textvariable=subtitle_var,
              font=("Arial", 9)).pack(pady=(0, 6))

    # ---- 白值 ----
    base_frame = ttk.LabelFrame(container, text="白值 (基础攻击力)", padding=6)
    base_frame.pack(fill="x", padx=4, pady=(0, 4))
    ttk.Label(base_frame, text="白值").grid(row=0, column=0, sticky="w", padx=4, pady=2)
    base_atk_entry_var = tk.StringVar(value="")
    ttk.Entry(base_frame, textvariable=base_atk_entry_var, width=14).grid(row=0, column=1, padx=4, pady=2)
    ttk.Label(base_frame, text="游戏界面白色数字 = 角色基础 + 武器基础").grid(
        row=0, column=2, sticky="w", padx=4, pady=2)

    # ---- 武器副词条 ----
    wpn_frame = ttk.LabelFrame(container, text="武器", padding=6)
    wpn_frame.pack(fill="x", padx=4, pady=(0, 4))
    ttk.Label(wpn_frame, text="武器副词条 ATK%").grid(row=0, column=0, sticky="w", padx=4, pady=2)
    weapon_secondary_var = tk.StringVar(value="0")
    ttk.Entry(wpn_frame, textvariable=weapon_secondary_var, width=14).grid(row=0, column=1, padx=4, pady=2)
    ttk.Label(wpn_frame, text="武器第二词条的攻击力百分比").grid(
        row=0, column=2, sticky="w", padx=4, pady=2)

    # ---- 圣遗物 ----
    art_frame = ttk.LabelFrame(container, text="圣遗物（五个部位）", padding=6)
    art_frame.pack(fill="x", padx=4, pady=(0, 4))

    ttk.Label(art_frame, text="勾选复选框启用对应攻击属性。已按游戏规则屏蔽冲突组合。",
              wraplength=880, font=("Arial", 9)).grid(
        row=0, column=0, columnspan=7, sticky="w", padx=4, pady=(0, 4))

    ttk.Label(art_frame, text="部位", font=("Arial", 9, "bold")).grid(row=1, column=0, padx=4, pady=2)
    ttk.Label(art_frame, text="主词条固定ATK", font=("Arial", 9, "bold")).grid(row=1, column=1, padx=4, pady=2)
    ttk.Label(art_frame, text="主词条ATK%", font=("Arial", 9, "bold")).grid(row=1, column=2, padx=4, pady=2)
    ttk.Label(art_frame, text="副词条固定ATK", font=("Arial", 9, "bold")).grid(row=1, column=3, padx=4, pady=2)
    ttk.Label(art_frame, text="副词条ATK%", font=("Arial", 9, "bold")).grid(row=1, column=4, padx=4, pady=2)
    ttk.Label(art_frame, text="说明", font=("Arial", 9, "bold")).grid(row=1, column=5, padx=4, pady=2)

    for c in range(1, 5):
        art_frame.columnconfigure(c, minsize=140)

    slot_data: dict[str, dict[str, dict]] = {}

    for i, slot in enumerate(ARTIFACT_SLOTS):
        r = i + 2
        sk = slot["key"]
        slot_data[sk] = {}

        ttk.Label(art_frame, text=slot["name"], font=("Arial", 10)).grid(
            row=r, column=0, sticky="w", padx=4, pady=3)

        main_pct_cv = sub_pct_cv = None

        for ci, st in enumerate(STAR):
            col = ci + 1
            if not slot[st]:
                ttk.Label(art_frame, text="-", foreground="gray").grid(
                    row=r, column=col, padx=4, pady=3)
                continue

            is_always_on = (sk == "plume" and st == "main_flat")
            cv = tk.BooleanVar(value=is_always_on)
            ev = tk.StringVar(value="0")
            slot_data[sk][st] = {"check_var": cv, "entry_var": ev}
            if st == "main_pct":
                main_pct_cv = cv
            if st == "sub_pct":
                sub_pct_cv = cv

            cell = ttk.Frame(art_frame)
            cell.grid(row=r, column=col, sticky="ew", padx=4, pady=2)
            cb = ttk.Checkbutton(cell, variable=cv,
                                 state="disabled" if is_always_on else "normal")
            cb.pack(side="left")
            entry = ttk.Entry(cell, textvariable=ev, width=8)
            entry.pack(side="right", padx=(4, 0))
            if is_always_on:
                ev.set("311")

            def _make_toggle(_cv=cv, _e=entry):
                def _toggle(*_a):
                    _e.configure(state="normal" if _cv.get() else "disabled")
                return _toggle
            cv.trace_add("write", _make_toggle())
            if not cv.get():
                entry.configure(state="disabled")

        if sk in ("sands", "goblet", "circlet"):
            def _make_conflict(mcv, scv):
                def _on_m(*_a):
                    if mcv.get():
                        scv.set(False)
                def _on_s(*_a):
                    if scv.get():
                        mcv.set(False)
                return _on_m, _on_s
            om, os_ = _make_conflict(main_pct_cv, sub_pct_cv)
            main_pct_cv.trace_add("write", om)
            sub_pct_cv.trace_add("write", os_)

        ttk.Label(art_frame, text=slot["desc"], wraplength=180, font=("Arial", 9)).grid(
            row=r, column=5, sticky="w", padx=4, pady=3)

    # ---- One-click maxed main stats ----
    def fill_maxed_main():
        for slot in ARTIFACT_SLOTS:
            sk = slot["key"]
            preset = MAXED_MAIN_ONLY.get(sk, {})
            sd = slot_data.get(sk, {})
            for st, val in preset.items():
                if st in sd:
                    sd[st]["check_var"].set(True)
                    if st in PCT_STAR and pct_mode_var.get():
                        sd[st]["entry_var"].set(f"{val * 100:.5g}")
                    else:
                        sd[st]["entry_var"].set(str(val))

    maxed_btn_frame = ttk.Frame(art_frame)
    maxed_btn_frame.grid(row=7, column=0, columnspan=6, pady=(4, 0))
    ttk.Button(maxed_btn_frame, text="一键已满级攻击主词条 (5* +20)",
               command=fill_maxed_main).pack(side="left", padx=(0, 8))
    ttk.Button(maxed_btn_frame, text="清空圣遗物",
               command=lambda: _clear_artifacts()).pack(side="left")

    # ---- Save / Load state helpers ----
    def _gather_state() -> dict:
        state = {"base_atk": base_atk_entry_var.get(),
                 "weapon_secondary": weapon_secondary_var.get(),
                 "pct_mode": pct_mode_var.get()}
        for slot in ARTIFACT_SLOTS:
            sk = slot["key"]
            sd = slot_data.get(sk, {})
            entry = {}
            for st, info in sd.items():
                entry[st] = {"checked": info["check_var"].get(),
                             "value": info["entry_var"].get()}
            state[sk] = entry
        return state

    def _restore_state(state: dict) -> None:
        base_atk_entry_var.set(state.get("base_atk", ""))
        weapon_secondary_var.set(state.get("weapon_secondary", "0"))
        for slot in ARTIFACT_SLOTS:
            sk = slot["key"]
            saved = state.get(sk, {})
            sd = slot_data.get(sk, {})
            for st, info in sd.items():
                v = saved.get(st, {})
                info["check_var"].set(v.get("checked", False))
                info["entry_var"].set(str(v.get("value", "0")))
        # Restore percentage mode (saved as decimal, so load first, then toggle display)
        saved_pct_mode = state.get("pct_mode", False)
        if saved_pct_mode and not pct_mode_var.get():
            _toggle_pct_mode()

    def _clear_artifacts():
        for slot in ARTIFACT_SLOTS:
            sk = slot["key"]
            sd = slot_data.get(sk, {})
            for st, info in sd.items():
                if sk == "plume" and st == "main_flat":
                    info["check_var"].set(True)
                    info["entry_var"].set("311")
                else:
                    info["check_var"].set(False)
                    info["entry_var"].set("0")

    def _silent_save():
        try:
            state = _gather_state()
            SAVE_ARTIFACT_FILE.write_text(
                json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def save_artifacts():
        _silent_save()
        messagebox.showinfo("已保存", f"圣遗物配置已保存到\n{SAVE_ARTIFACT_FILE}", parent=atk_win)

    def load_artifacts():
        if not SAVE_ARTIFACT_FILE.exists():
            messagebox.showwarning("无存档", "没有已保存的圣遗物配置文件。", parent=atk_win)
            return
        try:
            state = json.loads(SAVE_ARTIFACT_FILE.read_text(encoding="utf-8"))
            _restore_state(state)
            messagebox.showinfo("已加载", "圣遗物配置已加载。", parent=atk_win)
        except Exception as e:
            messagebox.showerror("加载失败", f"无法读取存档: {e}", parent=atk_win)

    def _silent_load():
        """Load saved config without showing any dialogs. No error if file missing."""
        if not SAVE_ARTIFACT_FILE.exists():
            return
        try:
            state = json.loads(SAVE_ARTIFACT_FILE.read_text(encoding="utf-8"))
            _restore_state(state)
        except Exception:
            pass

    # ---- Button row ----
    io_frame = ttk.Frame(container)
    io_frame.pack(fill="x", padx=4, pady=(0, 4))
    ttk.Button(io_frame, text="保存圣遗物配置", command=save_artifacts).pack(side="left", padx=(0, 6))
    ttk.Button(io_frame, text="加载圣遗物配置", command=load_artifacts).pack(side="left", padx=(0, 6))
    ttk.Button(io_frame, text="计算 ATK", command=lambda: calculate_atk()).pack(side="left", padx=(0, 6))
    ttk.Button(io_frame, text="应用 ATK 到主计算器", command=lambda: apply_to_main()).pack(side="left")

    # ---- Pct mode toggle ----
    pct_frame = ttk.Frame(container)
    pct_frame.pack(fill="x", padx=4, pady=(4, 0))
    ttk.Label(pct_frame, textvariable=pct_mode_label_var,
              font=("Arial", 9, "bold"), foreground="#0b6bcb").pack(side="left", padx=(0, 8))
    ttk.Button(pct_frame, text="切换小数/百分比输入",
               command=_toggle_pct_mode).pack(side="left")

    # ---- Result ----
    result_section = ttk.LabelFrame(container, text="计算结果", padding=6)
    result_section.pack(fill="x", padx=4, pady=(4, 4))

    result_var = tk.StringVar(value="请填写数据后点击「计算 ATK」")
    ttk.Label(result_section, textvariable=result_var, font=("Arial", 13, "bold"),
              foreground="#0b6bcb").pack(anchor="w", padx=4, pady=4)

    detail_text = tk.Text(result_section, height=8, wrap="word",
                          font=("Arial", 10), state="disabled")
    detail_text.pack(fill="x", padx=4, pady=(0, 2))

    atk_win._final_atk_result = None
    atk_win._final_base_atk = None

    # ---- calculate / apply ----
    def calculate_atk():
        try:
            base = _safe_float(base_atk_entry_var, "白值", atk_win)
            wpn_sec = _pct_from_entry(weapon_secondary_var, pct_mode_var)
            # basic validation pass
            _ = float(weapon_secondary_var.get() or "0")  # will raise if non-numeric
        except ValueError:
            # _pct_from_entry already validates; _safe_float shows error for base
            if pct_mode_var.get():
                try:
                    float(weapon_secondary_var.get() or "0")
                except ValueError:
                    messagebox.showerror("输入错误",
                                         f"「武器副词条ATK%」不是有效的数字: {weapon_secondary_var.get()}",
                                         parent=atk_win)
            return

        total_art_flat = 0.0
        total_art_pct = 0.0
        lines = []
        for slot in ARTIFACT_SLOTS:
            sk = slot["key"]
            sd = slot_data.get(sk, {})
            sf = sp = 0.0
            for st in STAR:
                info = sd.get(st)
                if info is None or not info["check_var"].get():
                    continue
                try:
                    if st in PCT_STAR:
                        val = _pct_from_entry(info["entry_var"], pct_mode_var)
                        # Validate numeric
                        _ = float(info["entry_var"].get() or "0")
                    else:
                        val = _safe_float(info["entry_var"],
                                          f"{slot['name']}-{STAT_LABELS[st]}", atk_win)
                except ValueError:
                    return
                if st in ("main_flat", "sub_flat"):
                    sf += val
                else:
                    sp += val
            total_art_flat += sf
            total_art_pct += sp
            if sf > 0 or sp > 0:
                lines.append(f"  {slot['name']}: 固定+{sf:.2f}  ATK%+{sp*100:.2f}%")

        total_pct = wpn_sec + total_art_pct
        final_atk = base * (1 + total_pct) + total_art_flat

        result_var.set(f"常驻 ATK = {final_atk:.5f}")
        detail_lines = [
            f"白值 = {base:.5f}",
            f"总ATK% = {total_pct*100:.5f}%",
            f"  * 武器副词条: {wpn_sec*100:.5f}%",
            f"  * 圣遗物总计: {total_art_pct*100:.5f}%",
            *lines,
            f"圣遗物固定ATK = {total_art_flat:.5f}",
            f"",
            f"常驻ATK = {base:.5f} x (1 + {total_pct:.5f}) + {total_art_flat:.5f} = {final_atk:.5f}",
        ]
        detail_text.configure(state="normal")
        detail_text.delete("1.0", "end")
        detail_text.insert("1.0", "\n".join(detail_lines))
        detail_text.configure(state="disabled")

        atk_win._final_atk_result = final_atk
        atk_win._final_base_atk = base
        _silent_save()

    def apply_to_main():
        final_atk = atk_win._final_atk_result
        base_atk_val = atk_win._final_base_atk
        if final_atk is None:
            messagebox.showwarning("未计算", "请先点击「计算 ATK」后再应用。", parent=atk_win)
            return
        if base_atk_var is not None:
            base_atk_var.set(base_atk_val)
        atk_entry_var.set(f"{final_atk:.5f}")
        _on_close()

    # ---- Auto-load saved config on open ----
    _silent_load()
