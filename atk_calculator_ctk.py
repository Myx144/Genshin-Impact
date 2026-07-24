"""CustomTkinter ATK calculator for Genshin Impact damage calculator."""

import json, tkinter as tk
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

SAVE_ATK = Path.home() / ".genshin_atk_artifacts.json"

ART_SLOTS = [
    {"key":"flower","name":"生之花","desc":"主词条固定HP","mf":False,"mp":False,"sf":True,"sp":True},
    {"key":"plume","name":"死之羽","desc":"主词条固定攻击力311","mf":True,"mp":False,"sf":False,"sp":True},
    {"key":"sands","name":"时之沙","desc":"可选攻击力%主词条","mf":False,"mp":True,"sf":True,"sp":True},
    {"key":"goblet","name":"空之杯","desc":"可选攻击力%主词条","mf":False,"mp":True,"sf":True,"sp":True},
    {"key":"circlet","name":"理之冠","desc":"可选攻击力%主词条","mf":False,"mp":True,"sf":True,"sp":True},
]
STATS = ["main_flat", "main_pct", "sub_flat", "sub_pct"]
MAXED = {"plume":{"main_flat":311},"sands":{"main_pct":0.466},"goblet":{"main_pct":0.466},"circlet":{"main_pct":0.466}}


def open_atk_calculator(parent, atk_entry_var: tk.StringVar, base_atk_var: tk.DoubleVar):
    atk_win = ctk.CTkToplevel(parent)
    atk_win.title("ATK计算器 - 常驻攻击力")
    atk_win.geometry("820x700")
    atk_win.transient(parent)

    container = ctk.CTkFrame(atk_win)
    container.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(container, text="常驻攻击力 (ATK) 计算器", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(4,8))

    # ---- 白值 ----
    base_frame = ctk.CTkFrame(container)
    base_frame.pack(fill="x", pady=(0,6))
    ctk.CTkLabel(base_frame, text="白值", width=80).pack(side="left", padx=6)
    base_entry_var = tk.StringVar(value="")
    ctk.CTkEntry(base_frame, textvariable=base_entry_var, width=120).pack(side="left", padx=4)
    ctk.CTkLabel(base_frame, text="角色基础+武器基础", font=ctk.CTkFont(size=10), text_color="gray").pack(side="left", padx=4)

    # ---- 武器副词条 ----
    wpn_frame = ctk.CTkFrame(container)
    wpn_frame.pack(fill="x", pady=(0,6))
    ctk.CTkLabel(wpn_frame, text="武器副词条ATK%", width=80).pack(side="left", padx=6)
    wpn_var = tk.StringVar(value="0")
    ctk.CTkEntry(wpn_frame, textvariable=wpn_var, width=120).pack(side="left", padx=4)

    # ---- 圣遗物表头 ----
    art_header = ctk.CTkFrame(container)
    art_header.pack(fill="x", pady=(8,2))
    for h, w in zip(["部位","主词条固定ATK","主词条ATK%","副词条固定ATK","副词条ATK%"], [80,140,140,140,140]):
        ctk.CTkLabel(art_header, text=h, width=w, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=2)

    # ---- 圣遗物槽位 ----
    slot_data = {}

    def _rebuild():
        if hasattr(atk_win, "_art_inner"):
            atk_win._art_inner.destroy()
        atk_win._art_inner = ctk.CTkScrollableFrame(container, height=300)
        atk_win._art_inner.pack(fill="x", pady=(0,6))
        for slot in ART_SLOTS:
            row = ctk.CTkFrame(atk_win._art_inner)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=slot["name"], width=80).pack(side="left", padx=4)
            for st in STATS:
                if not slot[st[:2]]:
                    ctk.CTkLabel(row, text="-", width=140, text_color="gray").pack(side="left", padx=2)
                    continue
                is_on = (slot["key"] == "plume" and st == "main_flat")
                cv = tk.BooleanVar(value=is_on)
                ev = tk.StringVar(value="311" if is_on else "0")
                slot_data.setdefault(slot["key"], {})[st] = {"check": cv, "entry": ev}
                cell = ctk.CTkFrame(row)
                cell.pack(side="left", padx=2)
                cb = ctk.CTkCheckBox(cell, text="", variable=cv, width=20)
                if is_on: cb.configure(state="disabled")
                cb.pack(side="left")
                ctk.CTkEntry(cell, textvariable=ev, width=100).pack(side="left", padx=2)
    _rebuild()

    # ---- 保存/加载 ----
    def _silent_save():
        st = {"base_atk": base_entry_var.get(), "weapon_secondary": wpn_var.get()}
        for k, sd in slot_data.items():
            st[k] = {sk: {"checked": info["check"].get(), "value": info["entry"].get()} for sk, info in sd.items()}
        try: SAVE_ATK.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
        except: pass

    def _silent_load():
        if not SAVE_ATK.exists(): return
        try:
            st = json.loads(SAVE_ATK.read_text(encoding="utf-8"))
            base_entry_var.set(st.get("base_atk", ""))
            wpn_var.set(st.get("weapon_secondary", "0"))
            for k, sd in slot_data.items():
                saved = st.get(k, {})
                for sk, info in sd.items():
                    v = saved.get(sk, {})
                    info["check"].set(v.get("checked", False))
                    info["entry"].set(str(v.get("value", "0")))
        except: pass

    # ---- 一键满级 ----
    def fill_maxed():
        for slot in ART_SLOTS:
            preset = MAXED.get(slot["key"], {})
            sd = slot_data.get(slot["key"], {})
            for st, val in preset.items():
                if st in sd:
                    sd[st]["check"].set(True)
                    sd[st]["entry"].set(str(val))

    # ---- 计算 ----
    def do_calc():
        try:
            base = float(base_entry_var.get() or 0)
            wpn = float(wpn_var.get() or 0)
        except ValueError:
            result_var.set("输入错误"); return
        total_flat, total_pct, lines = 0.0, 0.0, []
        for slot in ART_SLOTS:
            sd = slot_data.get(slot["key"], {})
            sf, sp = 0.0, 0.0
            for st in STATS:
                info = sd.get(st)
                if info is None or not info["check"].get(): continue
                try: val = float(info["entry"].get() or 0)
                except ValueError: result_var.set("输入错误"); return
                if "flat" in st: sf += val
                else: sp += val
            total_flat += sf; total_pct += sp
            if sf or sp: lines.append(f"  {slot['name']}: 固定+{sf:.2f}  ATK%+{sp*100:.2f}%")
        total_pct_all = wpn + total_pct
        final = base * (1 + total_pct_all) + total_flat
        result_var.set(f"常驻 ATK = {final:.5f}")
        detail_text.configure(state="normal")
        detail_text.delete("1.0", "end")
        detail_text.insert("1.0", "\n".join([
            f"白值 = {base:.5f}", f"总ATK% = {total_pct_all*100:.5f}%",
            f"  武器副词条: {wpn*100:.5f}%", f"  圣遗物总计: {total_pct*100:.5f}%",
            *lines, f"圣遗物固定ATK = {total_flat:.5f}", "",
            f"常驻ATK = {base:.5f} x (1 + {total_pct_all:.5f}) + {total_flat:.5f} = {final:.5f}",
        ]))
        detail_text.configure(state="disabled")
        atk_win._final = final
        atk_win._base = base
        _silent_save()

    def apply_to_main():
        if not hasattr(atk_win, "_final") or atk_win._final is None:
            messagebox.showwarning("未计算", "请先点击「计算 ATK」后再应用", parent=atk_win)
            return
        atk_entry_var.set(f"{atk_win._final:.5f}")
        base_atk_var.set(atk_win._base)
        atk_win.destroy()

    # ---- 按钮栏 ----
    btn_frame = ctk.CTkFrame(container)
    btn_frame.pack(fill="x", pady=(6,4))
    ctk.CTkButton(btn_frame, text="计算 ATK", command=do_calc).pack(side="left", padx=4)
    ctk.CTkButton(btn_frame, text="应用到主界面", command=apply_to_main).pack(side="left", padx=4)
    ctk.CTkButton(btn_frame, text="满级主词条", command=fill_maxed).pack(side="left", padx=4)
    ctk.CTkButton(btn_frame, text="保存配置", command=_silent_save).pack(side="left", padx=4)

    # ---- 结果区 ----
    result_var = tk.StringVar(value="请填写数据后点击「计算 ATK」")
    ctk.CTkLabel(container, textvariable=result_var, font=ctk.CTkFont(size=14, weight="bold"),
                 text_color="#5dade2").pack(anchor="w", pady=(8,4))

    detail_text = tk.Text(container, height=8, wrap="word", font=("Arial",11),
                           bg="#2b2b2b", fg="#dce4ee", insertbackground="white",
                           relief="flat", borderwidth=0, highlightthickness=0)
    detail_text.pack(fill="both", expand=True)
    detail_text.configure(state="disabled")

    atk_win._final = None; atk_win._base = None
    atk_win.protocol("WM_DELETE_WINDOW", lambda: (_silent_save(), atk_win.destroy()))
    _silent_load()
    atk_win.after(100, atk_win.lift)
