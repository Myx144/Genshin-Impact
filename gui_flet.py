import json, math
from pathlib import Path
import flet as ft
from damage_calculator import (
    INPUT_FIELDS, MAIN_PCT_FIELDS, DEBUG_VALUE_STEPS, DEBUG_RESULT_STEPS,
    ROUNDING_MODES, ROUNDING_MODE_LABELS,
    CharacterInfo, DamageCoefficients, DebugConfig,
    calculate_from_values, default_gui_values,
    load_saved_gui_state, save_gui_state,
    _slot_file, _get_meta_slot, _save_meta_slot, NUM_SLOTS,
)

TRUNC_MODES = ["round", "ceil", "floor"]
TRUNC_LABELS = {"round": "四舍五入", "ceil": "向上取整", "floor": "向下取整"}

class GenshinCalc:
    def __init__(self, page: ft.Page):
        self.page = page
        page.on_resize = lambda e: print(f"{page.window.width}x{page.window.height}")
        page.title = "原神星超导角色伤害计算器"
        page.theme_mode = ft.ThemeMode.DARK
        page.window.width = 720
        page.window.height = 1280
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 20
        page.window.min_width = 720
        page.window.min_height = 1280
        page.window.resizable = False

        self.base_atk_val = 0.0; self.main_pct_mode = False
        self.log_enabled = False; self.auto_save_val = False
        self.damage_mode = "期望"; self.debug_enabled = False
        self.current_slot = _get_meta_slot()
        self.precision_val = -1; self.em_precision_val = -1; self.atk_decimal_val = -1
        self.trunc_mode = "round"; self.em_trunc_mode = "round"; self.atk_trunc_mode = "round"
        self.dv_rounding = {step: "off" for step, _ in DEBUG_VALUE_STEPS}
        self.dr_rounding = {step: "off" for step, _ in DEBUG_RESULT_STEPS}
        self._build()

    def _pct_div(self, x): return x / 100.0 if self.main_pct_mode else x
    def _read(self, tf, default=0.0):
        try: return float(tf.value or default)
        except: return default

    def _sec(self, title, children):
        return ft.Container(
            content=ft.Column([ft.Text(title, weight=ft.FontWeight.BOLD, size=14)] + children, spacing=6),
            border_radius=10, bgcolor="#1e1e1e", padding=14, expand=True)

    def _build(self):
        page = self.page

        # ---- INPUT FIELDS ----
        self.entries = {}
        input_widgets = []
        row_buf = []
        for key, cn_name, req, default in INPUT_FIELDS:
            tf = ft.TextField(value=default, label=cn_name, width=140, dense=True, hint_text=req)
            self.entries[key] = tf
            row_buf.append(tf)
            if len(row_buf) == 2:
                input_widgets.append(ft.Row(row_buf, spacing=8))
                row_buf = []
        if row_buf:
            input_widgets.append(ft.Row(row_buf, spacing=8))

        self.eff_atk_text = ft.Text("有效 ATK: -", weight=ft.FontWeight.BOLD, color="#ff6b6b", size=14)

        # ---- CONDITIONAL BONUSES ----
        self.wp_check = ft.Checkbox(label="武器特效 ATK%", value=False)
        self.wp_var = ft.TextField(value="0", width=80, dense=True)
        self.set_check = ft.Checkbox(label="圣遗物套装 ATK%", value=False)
        self.set_var = ft.TextField(value="0", width=80, dense=True)
        self.op_check = ft.Checkbox(label="其他 ATK%", value=False)
        self.op_var = ft.TextField(value="0", width=80, dense=True)
        self.of_check = ft.Checkbox(label="其他固定 ATK", value=False)
        self.of_var = ft.TextField(value="0", width=80, dense=True)
        self.base_atk_tf = ft.TextField(value="", label="白值 (基础攻击力)", width=160, dense=True, hint_text="角色+武器白值")

        cond_col = ft.Column([
            ft.Row([self.wp_check, self.wp_var, self.set_check, self.set_var], spacing=8, wrap=False),
            ft.Row([self.op_check, self.op_var, self.of_check, self.of_var], spacing=8, wrap=False),
            ft.Row([self.base_atk_tf, ft.Text("游戏界面白色数字", size=10, color="#888888")], spacing=8),
        ], spacing=8)

        # ---- RESULTS ----
        self.result_text = ft.TextField(multiline=True, read_only=True, min_lines=15, max_lines=25,
                                         expand=True, text_style=ft.TextStyle(size=13, font_family="monospace"))
        self.summary_text = ft.Text("点击「计算」查看结果", weight=ft.FontWeight.BOLD, color="#5dade2", size=14)

        # ---- MODE BAR ----
        self.pct_mode_text = ft.Text("小数输入", weight=ft.FontWeight.BOLD, color="#5dade2", size=12)
        self.dm_text = ft.Text("期望伤害", size=12)
        mode_row = ft.Row([
            ft.Text("模式:", size=12), self.pct_mode_text,
            ft.Button(content=ft.Text("切换小数/百分比", size=12), on_click=self._toggle_pct_mode, height=28),
            self.dm_text,
            ft.Button(content=ft.Text("切换期望/暴伤", size=12), on_click=self._toggle_damage_mode, height=28),
        ], spacing=8)

        # ---- SLOTS ----
        self.slot_buttons = []
        slot_btns = []
        for i in range(1, NUM_SLOTS + 1):
            color = "#1f5383" if i == self.current_slot else "#333333"
            btn = ft.Container(
                content=ft.Text(str(i), size=12, color="#ffffff"),
                width=32, height=28, border_radius=6, bgcolor=color,
                on_click=lambda e, n=i: self._switch_slot(n))
            self.slot_buttons.append(btn)
            slot_btns.append(btn)

        self.auto_save_val = True
        self.auto_save_check = ft.Button(
            content=ft.Text("自动保存: 开", size=12),
            on_click=self._toggle_auto_save, height=28)
        # ---- TOP BAR (slots + settings) ----
        top_bar = ft.Row([
            ft.Text("配置槽:", size=12),
            ft.Row(slot_btns, spacing=4),
            ft.Container(width=20),
            ft.Button(content=ft.Text("Debug取整", size=12), on_click=self._open_debug, height=28),
            self.auto_save_check,
        ], spacing=6)

        # ---- BUTTON BAR ----
        self.log_check = ft.Checkbox(label="显示日志", value=False,
                                      on_change=lambda e: setattr(self, "log_enabled", e.control.value))
        btn_bar = ft.Row([
            ft.Button(content=ft.Text("计算", size=13, weight=ft.FontWeight.BOLD), on_click=self._do_calculate, height=34),
            ft.Button(content=ft.Text("保存"), on_click=self._do_save, height=30),
            ft.Button(content=ft.Text("恢复默认"), on_click=self._reset_defaults, height=30),
            self.log_check,
        ], spacing=8)

        # ---- BUILD LAYOUT ----
        page.add(
            ft.Text("原神星超导角色伤害计算器", size=24, weight=ft.FontWeight.BOLD),
            top_bar,
            mode_row,
            ft.Divider(),
            ft.Row([
                self._sec("输入数据", [*input_widgets, self.eff_atk_text]),
            ], expand=False,wrap=False),
            ft.Row([
                self._sec("条件加成 & 计算结果", [cond_col, ft.Divider(), self.result_text]),
            ]),
            self.summary_text,
            btn_bar,
        )

        self._load_slot(self.current_slot)
        page.update()

    # ============ CALLBACKS ============
    def _update_effective_atk(self):
        ba = self.base_atk_val or self._read(self.base_atk_tf)
        cp = 0.0; cf = 0.0
        if self.wp_check.value: cp += self._pct_div(self._read(self.wp_var))
        if self.set_check.value: cp += self._pct_div(self._read(self.set_var))
        if self.op_check.value: cp += self._pct_div(self._read(self.op_var))
        if self.of_check.value: cf += self._read(self.of_var)
        effective = self._read(self.entries["atk"]) + ba * cp + cf
        if self.atk_decimal_val >= 0:
            f = 10 ** self.atk_decimal_val; m = self.atk_trunc_mode
            if m == "round": effective = round(effective, self.atk_decimal_val)
            elif m == "ceil": effective = math.ceil(effective * f) / f
            elif m == "floor": effective = math.floor(effective * f) / f
        self.eff_atk_text.value = f"有效 ATK: {effective:.5f}"; self.eff_atk_text.update()

    def _do_calculate(self, _):
        self._update_effective_atk()
        values = {key: tf.value for key, tf in self.entries.items()}
        for key in MAIN_PCT_FIELDS:
            if self.main_pct_mode: values[key] = str(self._read(self.entries[key]) / 100.0)
        ba = self.base_atk_val or self._read(self.base_atk_tf)
        cp = 0.0; cf = 0.0; cd_lines = []
        if self.wp_check.value: v = self._pct_div(self._read(self.wp_var)); cp += v; cd_lines.append(f"  武器特效: +{v*100:.5f}%")
        if self.set_check.value: v = self._pct_div(self._read(self.set_var)); cp += v; cd_lines.append(f"  圣遗物套装: +{v*100:.5f}%")
        if self.op_check.value: v = self._pct_div(self._read(self.op_var)); cp += v; cd_lines.append(f"  其他ATK%: +{v*100:.5f}%")
        if self.of_check.value: v = self._read(self.of_var); cf += v; cd_lines.append(f"  其他固定ATK: +{v:.5f}")
        base_entries_atk = self._read(self.entries["atk"])
        effective = base_entries_atk + ba * cp + cf
        values["atk"] = str(effective)
        if self.atk_decimal_val >= 0:
            f = 10 ** self.atk_decimal_val; m = self.atk_trunc_mode
            av = effective
            if m == "round": av = round(av, self.atk_decimal_val)
            elif m == "ceil": av = math.ceil(av * f) / f
            elif m == "floor": av = math.floor(av * f) / f
            values["atk"] = str(av)
        crit_damage_only = self.damage_mode == "暴伤"
        debug_config = DebugConfig(enabled=self.debug_enabled, value_rounding_modes=self.dv_rounding,
                                   result_rounding_modes=self.dr_rounding,
                                   decimal_places=self.precision_val, trunc_mode=self.trunc_mode,
                                   em_decimal_places=self.em_precision_val, em_trunc_mode=self.em_trunc_mode)
        try:
            result = calculate_from_values(values, crit_damage_only=crit_damage_only, debug_config=debug_config)
        except ValueError as e:
            self.result_text.value = f"输入错误: {e}"; self.result_text.update(); return
        ed = result["expected_damage"]
        mode_label = "暴击伤害" if crit_damage_only else "期望伤害"
        self.summary_text.value = f"{mode_label} | 最终伤害: {ed:.5f}"; self.summary_text.update()
        lines = [f"最终伤害: {ed:.5f}"]
        if cd_lines:
            lines.extend(["", "条件加成:"] + cd_lines)
            if ba > 0: lines.append(f"  白值: {ba:.5f}")
            lines.append(f"  有效 ATK: {effective:.5f} (常驻 {base_entries_atk:.5f} + 条件 {effective - base_entries_atk:.5f})")
        lines.append("")
        for k, v in result.items(): lines.append(f"{k}: {v:.5f}")
        if self.log_enabled:
            lines.extend(["", "=== 计算日志 ===", ""])
            st = int(values["stacks"])
            rc = f"0.05 x {st} + 1.4" if st > 0 else "1"
            lines.append(f"有效 ATK = {base_entries_atk:.5f} + {ba:.5f} x {cp:.5f} + {cf:.5f} = {effective:.5f}")
            lines.append(f"反应系数 = {rc} = {result['reaction_coefficient']:.5f}")
            lines.append(f"倍率区 = {result['reaction_coefficient']:.5f} x {result['atk']:.5f} x {result['talent_multiplier']:.5f} = {result['multiplier_area']:.5f}")
            lines.append(f"精通提升 = EM({result['elemental_mastery']:.5f}) x 6 / (EM+2000) = {result['elemental_mastery_bonus']:.5f}")
            lines.append(f"增伤区 = 1 + {result['elemental_mastery_bonus']:.5f} + {result['reaction_bonus']:.5f} = {result['damage_bonus_area']:.5f}")
            lines.append(f"加伤区 = 1 + {result['base_reaction_damage_bonus']:.5f} = {result['additive_area']:.5f}")
            lines.append(f"基础区 = {result['multiplier_area']:.5f} x {result['damage_bonus_area']:.5f} x {result['additive_area']:.5f} + {result['flat_damage_increase']:.5f} = {result['base_area']:.5f}")
            cl = "1" if crit_damage_only else f"1 + {result['crit_rate']:.5f} x {result['crit_damage']:.5f}"
            lines.append(f"双爆区 = {cl} = {result['crit_area']:.5f}")
            lines.append(f"抗性区 = {result['resistance_area']:.5f}")
            lines.append(f"擢升区 = {result['elevation_area']:.5f}")
            lines.append(f"最终 = {result['base_area']:.5f} x {result['crit_area']:.5f} x {result['resistance_area']:.5f} x {result['elevation_area']:.5f} = {ed:.5f}")
        self.result_text.value = "\n".join(lines); self.result_text.update()
        if self.auto_save_val: self._save_to_slot(self.current_slot)

    # ============ SLOTS ============
    def _save_to_slot(self, slot):
        vals = {key: tf.value for key, tf in self.entries.items()}
        vals["base_atk_input"] = self.base_atk_tf.value
        vals["auto_save"] = str(self.auto_save_val)
        save_gui_state(vals, self.damage_mode, slot=slot, debug_enabled=self.debug_enabled,
                       debug_value_rounding_modes=self.dv_rounding, debug_result_rounding_modes=self.dr_rounding,
                       cond_bonuses={"weapon_passive": (self.wp_var.value, self.wp_check.value),
                                     "set_bonus": (self.set_var.value, self.set_check.value),
                                     "other_pct": (self.op_var.value, self.op_check.value),
                                     "other_flat": (self.of_var.value, self.of_check.value)},
                       main_pct_mode=self.main_pct_mode)
    def _do_save(self, _):
        self._save_to_slot(self.current_slot)
        self.summary_text.value = f"配置槽 {self.current_slot} 已保存"
        self.summary_text.update()
    def _load_slot(self, slot):
        saved = load_saved_gui_state(_slot_file(slot))
        for key, tf in self.entries.items():
            tf.value = str(saved.get("values", {}).get(key, "0"))
        self.damage_mode = str(saved.get("mode", "期望"))
        self.dm_text.value = "暴击伤害" if self.damage_mode == "暴伤" else "期望伤害"
        self.debug_enabled = bool(saved.get("debug_enabled", False))
        dv = saved.get("debug_value_rounding_modes", {s: "off" for s, _ in DEBUG_VALUE_STEPS})
        dr = saved.get("debug_result_rounding_modes", {s: "off" for s, _ in DEBUG_RESULT_STEPS})
        for step in self.dv_rounding: self.dv_rounding[step] = dv.get(step, "off")
        for step in self.dr_rounding: self.dr_rounding[step] = dr.get(step, "off")
        cb = saved.get("cond_bonuses", {})
        for name, (check, var) in [("weapon_passive", (self.wp_check, self.wp_var)),
                                     ("set_bonus", (self.set_check, self.set_var)),
                                     ("other_pct", (self.op_check, self.op_var)),
                                     ("other_flat", (self.of_check, self.of_var))]:
            v = cb.get(name, ("0", False))
            var.value = str(v[0]) if isinstance(v, (list, tuple)) and len(v) > 0 else "0"
            check.value = bool(v[1]) if isinstance(v, (list, tuple)) and len(v) > 1 else False
        self.base_atk_tf.value = str(saved.get("values", {}).get("base_atk_input", ""))
        self.auto_save_val = saved.get("values", {}).get("auto_save", "True") == "True"
        self.auto_save_check.content.value = f"自动保存: {'开' if self.auto_save_val else '关'}"
        self.auto_save_check.update()

    def _switch_slot(self, new_slot):
        if self.current_slot == new_slot: return
        self._save_to_slot(self.current_slot)
        self.current_slot = new_slot; _save_meta_slot(new_slot)
        self._load_slot(new_slot)
        for i, btn in enumerate(self.slot_buttons):
            btn.bgcolor = "#1f5383" if (i + 1) == new_slot else "#333333"
        self.page.update()

    def _toggle_pct_mode(self, _):
        factor = 100.0 if not self.main_pct_mode else 0.01
        for key in MAIN_PCT_FIELDS:
            try: self.entries[key].value = f"{self._read(self.entries[key]) * factor:.5g}"
            except: pass
        self.main_pct_mode = not self.main_pct_mode
        self.pct_mode_text.value = "百分比输入" if self.main_pct_mode else "小数输入"; self.page.update()

    def _toggle_auto_save(self, _):
        self.auto_save_val = not self.auto_save_val
        self.auto_save_check.content.value = f"自动保存: {'开' if self.auto_save_val else '关'}"
        self.auto_save_check.update()

    def _toggle_damage_mode(self, _):
        self.damage_mode = "暴伤" if self.damage_mode == "期望" else "期望"
        self.dm_text.value = "暴击伤害" if self.damage_mode == "暴伤" else "期望伤害"; self.page.update()

    def _reset_defaults(self, _):
        for key, _, _, default in INPUT_FIELDS: self.entries[key].value = default
        self.damage_mode = "期望"; self.dm_text.value = "期望伤害"
        self.debug_enabled = False; self.main_pct_mode = False; self.pct_mode_text.value = "小数输入"
        self.wp_check.value = False; self.wp_var.value = "0"
        self.set_check.value = False; self.set_var.value = "0"
        self.op_check.value = False; self.op_var.value = "0"
        self.of_check.value = False; self.of_var.value = "0"
        self.base_atk_tf.value = ""
        self.precision_val = -1; self.em_precision_val = -1; self.atk_decimal_val = -1
        self.trunc_mode = "round"; self.em_trunc_mode = "round"; self.atk_trunc_mode = "round"
        self.result_text.value = ""; self.summary_text.value = "点击「计算」查看结果"; self.page.update()

    def _open_debug(self, _):
        prec_tf = ft.TextField(value=str(self.precision_val), label="全局保留小数位 (-1=不截断)", width=160, dense=True)
        em_prec_tf = ft.TextField(value=str(self.em_precision_val), label="元素精通保留小数位 (-1=不截断)", width=160, dense=True)
        atk_prec_tf = ft.TextField(value=str(self.atk_decimal_val), label="角色ATK保留小数位 (-1=不截断)", width=160, dense=True)
        def _trunc_dd(current, setter):
            return ft.Dropdown(value=current,
                               options=[ft.dropdown.Option(key=m, text=TRUNC_LABELS[m]) for m in TRUNC_MODES],
                               width=120, dense=True,
                               on_change=lambda e, s=setter: s(e.control.value))
        def _apply(_):
            try: self.precision_val = int(prec_tf.value or "-1")
            except: pass
            try: self.em_precision_val = int(em_prec_tf.value or "-1")
            except: pass
            try: self.atk_decimal_val = int(atk_prec_tf.value or "-1")
            except: pass
            self.page.close(self.page.dialog)
        dlg = ft.AlertDialog(
            title=ft.Text("Debug 取整设置"),
            content=ft.Column([
                ft.Checkbox(label="开启 debug 取整模式", value=self.debug_enabled,
                            on_change=lambda e: setattr(self, "debug_enabled", e.control.value)),
                ft.Text("全局精度:", weight=ft.FontWeight.BOLD),
                ft.Row([prec_tf, _trunc_dd(self.trunc_mode, lambda v: setattr(self, "trunc_mode", v))], spacing=8),
                ft.Text("元素精通精度:", weight=ft.FontWeight.BOLD),
                ft.Row([em_prec_tf, _trunc_dd(self.em_trunc_mode, lambda v: setattr(self, "em_trunc_mode", v))], spacing=8),
                ft.Text("角色ATK精度:", weight=ft.FontWeight.BOLD),
                ft.Row([atk_prec_tf, _trunc_dd(self.atk_trunc_mode, lambda v: setattr(self, "atk_trunc_mode", v))], spacing=8),
                ft.Button(content=ft.Text("确定"), on_click=_apply, height=30),
            ], spacing=8, scroll=ft.ScrollMode.AUTO, height=500),
        )
        self.page.open(dlg)

def main(page: ft.Page):
    GenshinCalc(page)

if __name__ == "__main__":
    ft.app(main)
