#!/usr/bin/env python3
'''Genshin Impact damage calculator - modern CustomTkinter GUI.'''

import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from damage_calculator import (
    INPUT_FIELDS, MAIN_PCT_FIELDS, DEBUG_VALUE_STEPS, DEBUG_RESULT_STEPS,
    ROUNDING_MODES, ROUNDING_MODE_LABELS,
    CharacterInfo, DamageCoefficients, DebugConfig,
    calculate_from_values, default_gui_values,
    load_saved_gui_state, save_gui_state,
    _slot_file, _get_meta_slot, _save_meta_slot, NUM_SLOTS,
    SAVE_FILE,
)

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

TRUNC_MODES = ['round', 'ceil', 'floor']


def make_section(parent, title, **kwargs):
    '''Create a labelled section frame.'''
    frame = ctk.CTkFrame(parent, corner_radius=10, **kwargs)
    if title:
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=13, weight='bold')).pack(
            anchor='w', padx=14, pady=(12, 4))
    return frame


class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title('原神星超导角色伤害计算器')
        self.root.geometry('780x980')
        self.root.minsize(700, 800)

        # ---- state ----
        self.base_atk_var = tk.DoubleVar(value=0.0)
        self.base_atk_input_var = tk.StringVar(value='')
        self.precision_var = tk.IntVar(value=-1)
        self.em_precision_var = tk.IntVar(value=-1)
        self.em_trunc_mode_var = tk.StringVar(value='round')
        self.trunc_mode_var = tk.StringVar(value='round')
        self.atk_decimal_var = tk.IntVar(value=-1)
        self.atk_trunc_var = tk.StringVar(value='round')
        self.effective_atk_value = tk.DoubleVar(value=0.0)
        self.main_pct_mode_var = tk.BooleanVar(value=False)
        self.log_enabled_var = tk.BooleanVar(value=False)
        self.slot_name_var = tk.StringVar(value='')
        self.mode_var = tk.StringVar(value='期望')
        self.auto_save_var = tk.BooleanVar(value=True)
        self.debug_enabled_var = tk.BooleanVar(value=False)

        self.entries: dict[str, tk.StringVar] = {}
        self.cond_vars: dict[str, tuple] = {}

        # ---- build UI ----
        self._build_title()
        self._build_slots()
        self._build_input_section()
        self._build_cond_section()
        self._build_mode_bar()
        self._build_buttons()
        self._build_menu()

        # apply saved state and mode (deferred)
        if hasattr(self, '_saved_state_pending'):
            self._apply_saved_state(self._saved_state_pending)
        self.root.after(50, self._apply_saved_pct_mode)
        self.root.after(150, self._update_effective_atk)

    def _apply_saved_pct_mode(self):
        if self._loaded_pct_mode:
            self._toggle_main_pct_mode()

    # ============ BUILD ============

    def _build_menu(self):
        # Settings button in the button bar
        self.settings_btn = ctk.CTkButton(self._button_frame, text='⚙ 设置', width=70, height=32,
                                          command=self._toggle_settings_dropdown,
                                          fg_color='transparent', border_width=1)
        self.settings_btn.pack(side='right', padx=(6, 14))

        # In-window dropdown frame (initially hidden)
        self.settings_dd = ctk.CTkFrame(self.root, corner_radius=8, fg_color='#2b2b2b',
                                        border_width=1, border_color='#1f5383',
                                        width=160, height=80)
        self.settings_dd.pack_propagate(False)
        ctk.CTkButton(self.settings_dd, text='Debug 取整',
                      command=lambda: [self._hide_dropdown(), self._open_debug()],
                      fg_color='transparent', text_color='#dce4ee', anchor='w',
                      hover_color='#1f5383', height=30).pack(fill='x', padx=2, pady=(2, 0))
        ctk.CTkCheckBox(self.settings_dd, text='自动保存', variable=self.auto_save_var,
                        text_color='#dce4ee',
                        font=ctk.CTkFont(size=12)).pack(fill='x', padx=8, pady=(2, 6))
        self._dropdown_visible = False

    def _update_dropdown_position(self):
        b = self.settings_btn
        x = self.root.winfo_width() - 170
        y = b.winfo_rooty() - self.root.winfo_rooty() - 80
        self.settings_dd.place(x=x, y=y)

    def _toggle_settings_dropdown(self):
        if self._dropdown_visible:
            self._hide_dropdown()
        else:
            self._update_dropdown_position()
            self.settings_dd.lift()
            self._dropdown_visible = True
            # Bind to close on outside click
            self.root.bind('<Button-1>', self._on_root_click, add='+')

    def _hide_dropdown(self):
        self.settings_dd.place_forget()
        self._dropdown_visible = False
        self.root.unbind('<Button-1>')

    def _on_root_click(self, event):
        if self._dropdown_visible:
            x, y = event.x_root, event.y_root
            dx, dy = self.settings_dd.winfo_rootx(), self.settings_dd.winfo_rooty()
            dw, dh = self.settings_dd.winfo_width(), self.settings_dd.winfo_height()
            if not (dx <= x <= dx + dw and dy <= y <= dy + dh):
                self._hide_dropdown()

    def _build_title(self):
        ctk.CTkLabel(self.root, text='原神星超导角色伤害计算器',
                     font=ctk.CTkFont(size=22, weight='bold')).pack(pady=(18, 2))
        ctk.CTkLabel(self.root, text='百分比可用小数 (0.7) 或百分数 (70) 输入',
                     font=ctk.CTkFont(size=11), text_color='gray').pack(pady=(0, 6))

    def _build_slots(self):
        frame = ctk.CTkFrame(self.root, corner_radius=8)
        frame.pack(fill='x', padx=20, pady=(4, 0))

        self.current_slot_var = tk.IntVar(value=_get_meta_slot())
        slot = self.current_slot_var.get()
        saved = load_saved_gui_state(_slot_file(slot))
        self._saved_state_pending = saved
        self._loaded_pct_mode = saved.get('main_pct_mode', False)
        self.slot_name_var.set(saved.get('values', {}).get('__slot_name__', f'配置 {slot}'))
        as_val = saved.get('values', {}).get('__auto_save__', 'True') == 'True'
        self.auto_save_var.set(as_val)

        ctk.CTkLabel(frame, text='配置槽:', font=ctk.CTkFont(size=12)).pack(
            side='left', padx=(14, 8))

        self.slot_buttons = []
        for i in range(1, NUM_SLOTS + 1):
            btn = ctk.CTkButton(frame, text=str(i), width=32, height=28,
                                command=lambda n=i: self._switch_slot(n),
                                fg_color='#1f5383' if i == slot else 'transparent',
                                border_width=1 if i != slot else 0)
            btn.pack(side='left', padx=(0, 3))
            self.slot_buttons.append(btn)
        ctk.CTkLabel(frame, text='名称:', font=ctk.CTkFont(size=11)).pack(
            side='left', padx=(12, 4))
        self.slot_name_entry = ctk.CTkEntry(frame, textvariable=self.slot_name_var, width=120)
        self.slot_name_entry.pack(side='left', padx=(0, 8))
        ctk.CTkLabel(frame, text='点击槽位切换配置',
                     font=ctk.CTkFont(size=10), text_color='gray').pack(
            side='left', padx=(8, 0))

    def _build_input_section(self):
        sec = make_section(self.root, '输入数据')
        sec.pack(fill='x', padx=20, pady=(10, 0))

        self.effective_atk_label_var = tk.StringVar(value='有效 ATK: —')

        grid = ctk.CTkFrame(sec, fg_color='transparent')
        grid.pack(fill='x', padx=10, pady=(0, 10))

        for row, (key, chinese_name, requirement, default) in enumerate(INPUT_FIELDS):
            ctk.CTkLabel(grid, text=chinese_name, width=140, anchor='w',
                         font=ctk.CTkFont(size=12)).grid(row=row, column=0, sticky='w', padx=4, pady=3)
            var = tk.StringVar(value=default)
            self.entries[key] = var
            ctk.CTkEntry(grid, textvariable=var, width=120).grid(
                row=row, column=1, padx=4, pady=3, sticky='w')
            ctk.CTkLabel(grid, text=requirement, font=ctk.CTkFont(size=10),
                         text_color='gray').grid(row=row, column=2, sticky='w', padx=4, pady=3)

        # effective ATK display (row 0, col 3)
        ctk.CTkLabel(grid, textvariable=self.effective_atk_label_var,
                     font=ctk.CTkFont(size=13, weight='bold'),
                     text_color='#ff6b6b').grid(row=0, column=3, sticky='w', padx=12, pady=3)

    def _build_cond_section(self):
        # horizontal container: cond on left, results on right
        hframe = ctk.CTkFrame(self.root, fg_color='transparent')
        hframe.pack(fill='both', expand=True, padx=20, pady=(10, 0))
        hframe.columnconfigure(0, weight=0, minsize=380)
        hframe.columnconfigure(1, weight=1)

        sec = make_section(hframe, '条件加成 & 白值')
        sec.grid(row=0, column=0, sticky='nsew', padx=(0, 6))

        res_frame = make_section(hframe, '计算结果')
        res_frame.grid(row=0, column=1, sticky='nsew')
        self.result_text = ctk.CTkTextbox(res_frame, wrap='word',
                                          font=ctk.CTkFont(size=12))
        self.result_text.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        inner = ctk.CTkFrame(sec, fg_color='transparent')
        inner.pack(fill='x', padx=10, pady=(6, 10))

        # Row 0: weapon passive + set bonus
        self.wp_check = tk.BooleanVar(value=False)
        self.wp_var = tk.StringVar(value='0')
        self.set_check = tk.BooleanVar(value=False)
        self.set_var = tk.StringVar(value='0')

        ctk.CTkCheckBox(inner, text='武器特效 ATK%', variable=self.wp_check,
                        font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky='w', padx=4, pady=2)
        ctk.CTkEntry(inner, textvariable=self.wp_var, width=70).grid(row=0, column=1, padx=4, pady=2)
        ctk.CTkCheckBox(inner, text='圣遗物套装 ATK%', variable=self.set_check,
                        font=ctk.CTkFont(size=12)).grid(row=0, column=2, sticky='w', padx=(16, 4), pady=2)
        ctk.CTkEntry(inner, textvariable=self.set_var, width=70).grid(row=0, column=3, padx=4, pady=2)

        # Row 1: other pct + other flat + 白值
        self.op_check = tk.BooleanVar(value=False)
        self.op_var = tk.StringVar(value='0')
        self.of_check = tk.BooleanVar(value=False)
        self.of_var = tk.StringVar(value='0')

        ctk.CTkCheckBox(inner, text='其他 ATK%', variable=self.op_check,
                        font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky='w', padx=4, pady=2)
        ctk.CTkEntry(inner, textvariable=self.op_var, width=70).grid(row=1, column=1, padx=4, pady=2)
        ctk.CTkCheckBox(inner, text='其他固定 ATK', variable=self.of_check,
                        font=ctk.CTkFont(size=12)).grid(row=1, column=2, sticky='w', padx=(16, 4), pady=2)
        ctk.CTkEntry(inner, textvariable=self.of_var, width=70).grid(row=1, column=3, padx=4, pady=2)

        # Row 2: 白值
        ctk.CTkLabel(inner, text='白值 (角色基础 + 武器基础):',
                     font=ctk.CTkFont(size=12)).grid(row=2, column=0, columnspan=2,
                                                      sticky='w', padx=4, pady=(8, 2))
        ctk.CTkEntry(inner, textvariable=self.base_atk_input_var, width=100).grid(
            row=2, column=2, columnspan=2, sticky='w', padx=4, pady=(8, 2))
        ctk.CTkLabel(inner, text='游戏界面白色数字',
                     font=ctk.CTkFont(size=10), text_color='gray').grid(
            row=3, column=0, columnspan=4, sticky='w', padx=4, pady=(0, 4))

    def _build_mode_bar(self):
        frame = ctk.CTkFrame(self.root, corner_radius=8)
        frame.pack(fill='x', padx=20, pady=(6, 0))

        self.pct_mode_label_var = tk.StringVar(value='当前: 小数输入')
        ctk.CTkLabel(frame, textvariable=self.pct_mode_label_var,
                     font=ctk.CTkFont(size=12, weight='bold'),
                     text_color='#5dade2').pack(side='left', padx=(14, 8))
        ctk.CTkButton(frame, text='切换 小数/百分比 输入',
                      command=self._toggle_main_pct_mode,
                      width=150, height=28).pack(side='left', padx=(0, 8))

        self.mode_label_var = tk.StringVar(value='期望伤害')
        ctk.CTkLabel(frame, textvariable=self.mode_label_var,
                     font=ctk.CTkFont(size=12)).pack(side='left', padx=(16, 8))
        ctk.CTkButton(frame, text='切换 期望/暴伤',
                      command=self._toggle_damage_mode,
                      width=130, height=28).pack(side='left')

    def _build_buttons(self):
        frame = ctk.CTkFrame(self.root, corner_radius=8)
        frame.pack(fill='x', padx=20, pady=(6, 0))
        self._button_frame = frame

        ctk.CTkButton(frame, text='计算', command=self._show_results,
                      width=90, height=32).pack(side='left', padx=(14, 6))
        ctk.CTkButton(frame, text='ATK 计算器', command=self._open_atk_calc,
                      width=100, height=32).pack(side='left', padx=6)
        ctk.CTkButton(frame, text='保存', command=self._save_current,
                      width=70, height=32).pack(side='left', padx=6)
        ctk.CTkButton(frame, text='恢复默认', command=self._reset_defaults,
                      width=80, height=32).pack(side='left', padx=6)

        ctk.CTkCheckBox(frame, text='显示计算日志', variable=self.log_enabled_var,
                        font=ctk.CTkFont(size=11),
                        command=lambda: None).pack(
            side='left', padx=(20, 6))

        # summary label
        self.summary_var = tk.StringVar(value='点击「计算」查看结果')
        ctk.CTkLabel(self.root, textvariable=self.summary_var,
                     font=ctk.CTkFont(size=14, weight='bold'),
                     text_color='#5dade2').pack(pady=(6, 2))

    # ============ CORE LOGIC ============

    def _current_values(self) -> dict[str, str]:
        return {key: v.get() for key, v in self.entries.items()}

    def _update_effective_atk(self, *_args):
        try:
            base_atk_val = float(self.entries['atk'].get() or 0)
            ba = self.base_atk_var.get() or (
                float(self.base_atk_input_var.get()) if self.base_atk_input_var.get().strip() else 0.0)
            cp = 0.0
            _pct = (lambda x: x / 100.0) if self.main_pct_mode_var.get() else (lambda x: x)
            if self.wp_check.get():
                cp += _pct(float(self.wp_var.get() or 0))
            if self.set_check.get():
                cp += _pct(float(self.set_var.get() or 0))
            if self.op_check.get():
                cp += _pct(float(self.op_var.get() or 0))
            cf = 0.0
            if self.of_check.get():
                cf += float(self.of_var.get() or 0)
            effective = base_atk_val + ba * cp + cf
            self.effective_atk_value.set(effective)
            if self.atk_decimal_var.get() >= 0:
                p = self.atk_decimal_var.get(); f = 10 ** p; m = self.atk_trunc_var.get()
                if m == 'round': effective = round(effective, p)
                elif m == 'ceil': effective = math.ceil(effective * f) / f
                elif m == 'floor': effective = math.floor(effective * f) / f
            self.effective_atk_label_var.set(f'有效 ATK: {effective:.5f}')
        except (ValueError, tk.TclError):
            self.effective_atk_label_var.set('有效 ATK: —')

    def _show_results(self):
        self._update_effective_atk()
        try:
            values = self._current_values()
            for key in MAIN_PCT_FIELDS:
                if self.main_pct_mode_var.get():
                    values[key] = str(float(values.get(key, '0') or 0) / 100.0)

            base_atk = self.base_atk_var.get() or (
                float(self.base_atk_input_var.get()) if self.base_atk_input_var.get().strip() else 0.0)
            cond_pct = 0.0; cond_flat = 0.0; cond_detail = []
            _pct2 = (lambda x: x / 100.0) if self.main_pct_mode_var.get() else (lambda x: x)
            if self.wp_check.get():
                v = _pct2(float(self.wp_var.get() or 0)); cond_pct += v
                cond_detail.append(f'  武器特效: +{v*100:.5f}%')
            if self.set_check.get():
                v = _pct2(float(self.set_var.get() or 0)); cond_pct += v
                cond_detail.append(f'  圣遗物套装: +{v*100:.5f}%')
            if self.op_check.get():
                v = _pct2(float(self.op_var.get() or 0)); cond_pct += v
                cond_detail.append(f'  其他ATK%: +{v*100:.5f}%')
            if self.of_check.get():
                v = float(self.of_var.get() or 0); cond_flat += v
                cond_detail.append(f'  其他固定ATK: +{v:.5f}')

            base_entries_atk = float(values['atk'])
            effective_atk = self.effective_atk_value.get()
            values['atk'] = str(effective_atk)
            if self.atk_decimal_var.get() >= 0:
                p = self.atk_decimal_var.get(); f = 10 ** p; m = self.atk_trunc_var.get()
                av = float(values['atk'])
                if m == 'round': av = round(av, p)
                elif m == 'ceil': av = math.ceil(av * f) / f
                elif m == 'floor': av = math.floor(av * f) / f
                values['atk'] = str(av)

            crit_damage_only = self.mode_var.get() == '暴伤'
            debug_config = DebugConfig(
                enabled=self.debug_enabled_var.get(),
                value_rounding_modes={s: v.get() for s, v in self.debug_value_rounding_vars.items()},
                result_rounding_modes={s: v.get() for s, v in self.debug_result_rounding_vars.items()},
                decimal_places=self.precision_var.get(),
                trunc_mode=self.trunc_mode_var.get(),
                em_decimal_places=self.em_precision_var.get(),
                em_trunc_mode=self.em_trunc_mode_var.get(),
            )
            result = calculate_from_values(values, crit_damage_only=crit_damage_only,
                                           debug_config=debug_config)
        except ValueError as e:
            messagebox.showerror('输入错误', str(e))
            return

        ed = result['expected_damage']
        mode_label = '暴击伤害' if crit_damage_only else '期望伤害'
        debug_label = 'Debug取整: 开启' if self.debug_enabled_var.get() else 'Debug取整: 关闭'
        self.summary_var.set(
            f'{mode_label} | {debug_label} | 最终伤害: {ed:.5f}')

        lines = [f'最终伤害: {ed:.5f}']
        if cond_detail:
            lines.append(''); lines.append('条件加成:')
            lines.extend(cond_detail)
            if base_atk > 0:
                lines.append(f'  白值: {base_atk:.5f}')
            lines.append(f'  有效 ATK: {effective_atk:.5f} '
                         f'(常驻 {base_entries_atk:.5f} + 条件 {effective_atk - base_entries_atk:.5f})')
        lines.append('')
        lines.extend(f'{key}: {value:.5f}' for key, value in result.items())

        if self.log_enabled_var.get():
            lines.append('')
            lines.append('=== 计算日志（逐步骤公式） ===')
            lines.append('')
            raw_stacks = int(values['stacks'])
            lines.append(f'有效 ATK = 常驻({base_entries_atk:.5f}) + 白值({base_atk:.5f}) x 条件ATK%({cond_pct:.5f}) + 条件固定({cond_flat:.5f}) = {effective_atk:.5f}')
            lines.append('')
            rc_label = f'0.05 x {raw_stacks} + 1.4' if raw_stacks > 0 else '1'
            lines.append(f'反应系数 = {rc_label} = {result["reaction_coefficient"]:.5f}')
            lines.append(f'倍率区 = 反应系数({result["reaction_coefficient"]:.5f}) x ATK({result["atk"]:.5f}) x 天赋倍率({result["talent_multiplier"]:.5f}) = {result["multiplier_area"]:.5f}')
            lines.append(f'精通提升 = EM({result["elemental_mastery"]:.5f}) x 6 / (EM({result["elemental_mastery"]:.5f}) + 2000) = {result["elemental_mastery_bonus"]:.5f}')
            lines.append(f'增伤区 = 1 + 精通提升({result["elemental_mastery_bonus"]:.5f}) + 反应提升({result["reaction_bonus"]:.5f}) = {result["damage_bonus_area"]:.5f}')
            lines.append(f'加伤区 = 1 + 星反应基础伤害提升({result["base_reaction_damage_bonus"]:.5f}) = {result["additive_area"]:.5f}')
            lines.append(f'基础区 = 倍率区({result["multiplier_area"]:.5f}) x 增伤区({result["damage_bonus_area"]:.5f}) x 加伤区({result["additive_area"]:.5f}) + 伤害提高({result["flat_damage_increase"]:.5f}) = {result["base_area"]:.5f}')
            crit_label = '1' if crit_damage_only else f'1 + 暴击率({result["crit_rate"]:.5f}) x 暴击伤害({result["crit_damage"]:.5f})'
            lines.append(f'双爆区 = {crit_label} = {result["crit_area"]:.5f}')
            lines.append(f'抗性区 = f(目标抗性={result["enemy_resistance"]:.5f}) = {result["resistance_area"]:.5f}')
            lines.append(f'擢升区 = 1 + 擢升提升({result["elevation_bonus"]:.5f}) = {result["elevation_area"]:.5f}')
            lines.append('')
            lines.append(f'最终伤害 = 基础区({result["base_area"]:.5f}) x 双爆区({result["crit_area"]:.5f}) x 抗性区({result["resistance_area"]:.5f}) x 擢升区({result["elevation_area"]:.5f}) = {ed:.5f}')

        if self.auto_save_var.get():
            vals = self._current_values()
            vals['base_atk_input'] = self.base_atk_input_var.get()
            save_gui_state(
                vals, self.mode_var.get(), slot=self.current_slot_var.get(),
                debug_enabled=self.debug_enabled_var.get(),
                debug_value_rounding_modes={s: v.get() for s, v in self.debug_value_rounding_vars.items()},
                debug_result_rounding_modes={s: v.get() for s, v in self.debug_result_rounding_vars.items()},
                cond_bonuses={'weapon_passive': (self.wp_var.get(), self.wp_check.get()),
                              'set_bonus': (self.set_var.get(), self.set_check.get()),
                              'other_pct': (self.op_var.get(), self.op_check.get()),
                              'other_flat': (self.of_var.get(), self.of_check.get())},
                main_pct_mode=self.main_pct_mode_var.get(),
            )
        self.result_text.delete('1.0', 'end')
        self.result_text.insert('1.0', '\n'.join(lines))

    # ============ SLOTS ============

    def _apply_saved_state(self, saved: dict):
        for key, var in self.entries.items():
            var.set(str(saved.get('values', {}).get(key, '0')))
        self.mode_var.set(str(saved.get('mode', '期望')))
        self.debug_enabled_var.set(bool(saved.get('debug_enabled', False)))
        dv = saved.get('debug_value_rounding_modes', {s: 'off' for s, _ in DEBUG_VALUE_STEPS})
        dr = saved.get('debug_result_rounding_modes', {s: 'off' for s, _ in DEBUG_RESULT_STEPS})
        self.debug_value_rounding_vars = {step: tk.StringVar(value=dv.get(step, 'off'))
                                          for step, _ in DEBUG_VALUE_STEPS}
        self.debug_result_rounding_vars = {step: tk.StringVar(value=dr.get(step, 'off'))
                                           for step, _ in DEBUG_RESULT_STEPS}
        cb = saved.get('cond_bonuses', {})
        for k, (check_var, entry_var) in [('weapon_passive', (self.wp_check, self.wp_var)),
                                           ('set_bonus', (self.set_check, self.set_var)),
                                           ('other_pct', (self.op_check, self.op_var)),
                                           ('other_flat', (self.of_check, self.of_var))]:
            v = cb.get(k, ('0', False))
            entry_var.set(str(v[0]) if isinstance(v, (list, tuple)) and len(v) > 0 else '0')
            check_var.set(bool(v[1]) if isinstance(v, (list, tuple)) and len(v) > 1 else False)
        self.base_atk_input_var.set(str(saved.get('values', {}).get('base_atk_input', '')))

    def _switch_slot(self, new_slot: int):
        old_slot = self.current_slot_var.get()
        if old_slot == new_slot:
            return
        # save current
        vals2 = self._current_values()
        vals2['base_atk_input'] = self.base_atk_input_var.get()
        save_gui_state(
            vals2, self.mode_var.get(), slot=old_slot,
            debug_enabled=self.debug_enabled_var.get(),
            debug_value_rounding_modes={s: v.get() for s, v in self.debug_value_rounding_vars.items()},
            debug_result_rounding_modes={s: v.get() for s, v in self.debug_result_rounding_vars.items()},
            cond_bonuses={'weapon_passive': (self.wp_var.get(), self.wp_check.get()),
                          'set_bonus': (self.set_var.get(), self.set_check.get()),
                          'other_pct': (self.op_var.get(), self.op_check.get()),
                          'other_flat': (self.of_var.get(), self.of_check.get())},
            main_pct_mode=self.main_pct_mode_var.get(),
        )
        self.current_slot_var.set(new_slot)
        _save_meta_slot(new_slot)
        saved = load_saved_gui_state(_slot_file(new_slot))
        self.slot_name_var.set(saved.get("values", {}).get("__slot_name__", f"配置 {new_slot}"))
        as_val = saved.get("values", {}).get("__auto_save__", "True") == "True"
        self.auto_save_var.set(as_val)
        self._apply_saved_state(saved)
        if saved.get('main_pct_mode', False) != self.main_pct_mode_var.get():
            self._toggle_main_pct_mode()
        self.root.after(50, self._update_effective_atk)
        for i, btn in enumerate(self.slot_buttons):
            btn.configure(fg_color='#1f5383' if (i + 1) == new_slot else 'transparent',
                          border_width=0 if (i + 1) == new_slot else 1)
        self.summary_var.set(f'切换到配置槽 {new_slot}。点击「计算」查看结果。')
        self.result_text.delete('1.0', 'end')

    # ============ ACTIONS ============

    def _update_slot_buttons(self, *_):
        name = self.slot_name_var.get()
        for i, btn in enumerate(self.slot_buttons):
            if (i + 1) == self.current_slot_var.get():
                display = name[:4] if name else str(i + 1)
                btn.configure(text=display)

    def _toggle_main_pct_mode(self):
        factor = 100.0 if not self.main_pct_mode_var.get() else 0.01
        for key in MAIN_PCT_FIELDS:
            if key in self.entries:
                try:
                    cur = float(self.entries[key].get() or '0')
                    self.entries[key].set(f'{cur * factor:.5g}')
                except ValueError:
                    pass
        self.main_pct_mode_var.set(not self.main_pct_mode_var.get())
        self.pct_mode_label_var.set(
            '当前: 百分比输入' if self.main_pct_mode_var.get() else '当前: 小数输入')
        self._update_effective_atk()

    def _toggle_damage_mode(self):
        if self.mode_var.get() == '期望':
            self.mode_var.set('暴伤')
            self.mode_label_var.set('暴击伤害')
            self.summary_var.set('暴击伤害模式，点击「计算」查看结果。')
        else:
            self.mode_var.set('期望')
            self.mode_label_var.set('期望伤害')
            self.summary_var.set('期望伤害模式，点击「计算」查看结果。')
        self.result_text.delete('1.0', 'end')

    def _open_atk_calc(self):
        from atk_calculator_ctk import open_atk_calculator
        open_atk_calculator(self.root, self.entries['atk'], self.base_atk_var)

    def _open_debug(self):
        dw = ctk.CTkToplevel(self.root)
        dw.title('Debug 取整设置')
        dw.geometry('800x780')
        dw.transient(self.root)

        ctk.CTkCheckBox(dw, text='开启 debug 取整模式',
                        variable=self.debug_enabled_var,
                        font=ctk.CTkFont(size=13)).pack(anchor='w', padx=16, pady=(14, 6))
        ctk.CTkLabel(dw, text='数值取整：对输入数值先取整\n计算结果取整：对每一步公式计算后的结果取整',
                     font=ctk.CTkFont(size=11), text_color='gray').pack(anchor='w', padx=16, pady=(0, 6))

        # precision controls
        pframe = ctk.CTkFrame(dw)
        pframe.pack(fill='x', padx=16, pady=(0, 4))
        ctk.CTkLabel(pframe, text='全局保留小数位 (-1=不截断):',
                     font=ctk.CTkFont(size=12)).pack(side='left', padx=(0, 6))
        ctk.CTkEntry(pframe, textvariable=self.precision_var, width=60).pack(side='left')
        trunc_btn = ctk.CTkButton(pframe, text='', width=120, height=28,
                                  command=self._make_trunc_cycle(self.trunc_mode_var, trunc_btn))
        trunc_btn.pack(side='left', padx=(12, 0))
        self._update_trunc_btn(trunc_btn, self.trunc_mode_var.get())

        # EM precision
        emframe = ctk.CTkFrame(dw)
        emframe.pack(fill='x', padx=16, pady=(4, 4))
        ctk.CTkLabel(emframe, text='元素精通保留小数位 (-1=不截断):',
                     font=ctk.CTkFont(size=12)).pack(side='left', padx=(0, 6))
        ctk.CTkEntry(emframe, textvariable=self.em_precision_var, width=60).pack(side='left')
        embtn = ctk.CTkButton(emframe, text='', width=120, height=28,
                              command=self._make_trunc_cycle(self.em_trunc_mode_var, embtn))
        embtn.pack(side='left', padx=(12, 0))
        self._update_trunc_btn(embtn, self.em_trunc_mode_var.get())

        # ATK precision
        atkframe = ctk.CTkFrame(dw)
        atkframe.pack(fill='x', padx=16, pady=(4, 6))
        ctk.CTkLabel(atkframe, text='角色ATK保留小数位 (-1=不截断):',
                     font=ctk.CTkFont(size=12)).pack(side='left', padx=(0, 6))
        ctk.CTkEntry(atkframe, textvariable=self.atk_decimal_var, width=60).pack(side='left')
        atkbtn = ctk.CTkButton(atkframe, text='', width=120, height=28,
                               command=self._make_trunc_cycle(self.atk_trunc_var, atkbtn))
        atkbtn.pack(side='left', padx=(12, 0))
        self._update_trunc_btn(atkbtn, self.atk_trunc_var.get())

        # Notebook tabs for rounding
        tabview = ctk.CTkTabview(dw)
        tabview.pack(fill='both', expand=True, padx=16, pady=(0, 6))
        tab_v = tabview.add('数值取整')
        tab_r = tabview.add('计算结果取整')

        self._fill_rounding_tab(tab_v, DEBUG_VALUE_STEPS, self.debug_value_rounding_vars)
        self._fill_rounding_tab(tab_r, DEBUG_RESULT_STEPS, self.debug_result_rounding_vars)

        # one-key controls
        af = ctk.CTkFrame(dw)
        af.pack(fill='x', padx=16, pady=(0, 12))
        ctk.CTkLabel(af, text='一键控制:',
                     font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', padx=6, pady=(6, 2))
        for label, varmap in [('数值取整', self.debug_value_rounding_vars),
                               ('计算结果取整', self.debug_result_rounding_vars)]:
            row = ctk.CTkFrame(af, fg_color='transparent')
            row.pack(fill='x', padx=6, pady=2)
            ctk.CTkLabel(row, text=f'{label}:', font=ctk.CTkFont(size=11)).pack(side='left', padx=(0, 6))
            for mode in ['round', 'ceil', 'floor', 'off']:
                ctk.CTkButton(row, text=ROUNDING_MODE_LABELS[mode], width=70, height=24,
                              command=lambda m=mode, vm=varmap: self._set_all_rounding(vm, m)).pack(
                    side='left', padx=2)

    @staticmethod
    def _make_trunc_cycle(var, btn):
        def cycle():
            modes = TRUNC_MODES
            ci = modes.index(var.get()) if var.get() in modes else 0
            var.set(modes[(ci + 1) % len(modes)])
            App._update_trunc_btn(btn, var.get())
        return cycle

    @staticmethod
    def _update_trunc_btn(btn, mode):
        labels = {'round': '四舍五入', 'ceil': '向上取整', 'floor': '向下取整'}
        btn.configure(text=f'截断: {labels.get(mode, mode)}')

    def _fill_rounding_tab(self, tab, steps, varmap):
        for i, (step, label) in enumerate(steps):
            row = ctk.CTkFrame(tab, fg_color='transparent')
            row.pack(fill='x', padx=6, pady=2)
            ctk.CTkLabel(row, text=f'{label} ({step})',
                         font=ctk.CTkFont(size=11)).pack(side='left', padx=4)
            btn = ctk.CTkButton(row, text='', width=100, height=26,
                                command=self._make_cycle_cmd(varmap[step], btn))
            btn.pack(side='left', padx=(8, 0))
            self._update_rounding_btn(btn, varmap[step].get())

    @staticmethod
    def _make_cycle_cmd(var, btn):
        def cycle():
            modes = list(ROUNDING_MODES)
            ci = modes.index(var.get()) if var.get() in modes else 0
            var.set(modes[(ci + 1) % len(modes)])
            App._update_rounding_btn(btn, var.get())
        return cycle

    @staticmethod
    def _update_rounding_btn(btn, mode):
        btn.configure(text=f'取整: {ROUNDING_MODE_LABELS.get(mode, mode)}')

    @staticmethod
    def _set_all_rounding(varmap, mode):
        for v in varmap.values():
            v.set(mode)

    def _save_current(self):
        vals = self._current_values()
        vals['base_atk_input'] = self.base_atk_input_var.get()
        vals['__slot_name__'] = self.slot_name_var.get()
        vals['__auto_save__'] = 'True' if self.auto_save_var.get() else 'False'
        save_gui_state(
            vals, self.mode_var.get(), slot=self.current_slot_var.get(),
            debug_enabled=self.debug_enabled_var.get(),
            debug_value_rounding_modes={s: v.get() for s, v in self.debug_value_rounding_vars.items()},
            debug_result_rounding_modes={s: v.get() for s, v in self.debug_result_rounding_vars.items()},
            cond_bonuses={'weapon_passive': (self.wp_var.get(), self.wp_check.get()),
                          'set_bonus': (self.set_var.get(), self.set_check.get()),
                          'other_pct': (self.op_var.get(), self.op_check.get()),
                          'other_flat': (self.of_var.get(), self.of_check.get())},
            main_pct_mode=self.main_pct_mode_var.get(),
        )
        messagebox.showinfo('保存成功',
                            f'配置槽 {self.current_slot_var.get()} 已保存。\n'
                            f'文件: {_slot_file(self.current_slot_var.get())}')

    def _reset_defaults(self):
        for key, _cn, _req, default in INPUT_FIELDS:
            self.entries[key].set(default)
        self.mode_var.set('期望')
        self.mode_label_var.set('期望伤害')
        self.debug_enabled_var.set(False)
        self.log_enabled_var.set(False)
        self.result_text.configure(height=200)
        for vm in [self.debug_value_rounding_vars, self.debug_result_rounding_vars]:
            for v in vm.values():
                v.set('off')
        self.wp_check.set(False); self.wp_var.set('0')
        self.set_check.set(False); self.set_var.set('0')
        self.op_check.set(False); self.op_var.set('0')
        self.of_check.set(False); self.of_var.set('0')
        self.base_atk_var.set(0.0); self.base_atk_input_var.set('')
        self.precision_var.set(-1); self.trunc_mode_var.set('round')
        self.em_precision_var.set(-1); self.em_trunc_mode_var.set('round')
        self.atk_decimal_var.set(-1); self.atk_trunc_var.set('round')
        self.main_pct_mode_var.set(False)
        self.pct_mode_label_var.set('当前: 小数输入')
        self.summary_var.set('点击「计算」查看结果。')
        self.result_text.delete('1.0', 'end')

    def run(self):
        # trace effective ATK updates
        self.entries['atk'].trace_add('write', self._update_effective_atk)
        for var in [self.wp_check, self.set_check, self.op_check, self.of_check,
                    self.wp_var, self.set_var, self.op_var, self.of_var,
                    self.base_atk_input_var]:
            var.trace_add('write', self._update_effective_atk)
        self.root.mainloop()


if __name__ == '__main__':
    App().run()
