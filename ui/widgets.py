"""可复用的 CustomTkinter 控件。"""

from typing import Any

import customtkinter as ctk


class LabeledEntry(ctk.CTkFrame):
    """带标签的数字输入框。"""

    def __init__(
        self,
        master: Any,
        label: str,
        value: int = 0,
        width: int = 120,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(self, text=label, anchor="w", width=160)
        self._label.pack(side="left", padx=(0, 8))

        self._var = ctk.StringVar(value=str(value))
        self._entry = ctk.CTkEntry(self, textvariable=self._var, width=width)
        self._entry.pack(side="left")

    def get_value(self) -> int:
        try:
            return int(self._var.get())
        except ValueError:
            return 0

    def set_value(self, value: int) -> None:
        self._var.set(str(value))


class TimeEntry(ctk.CTkFrame):
    """带标签的时分秒输入框，内部存储秒数。"""

    def __init__(
        self,
        master: Any,
        label: str,
        total_seconds: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(self, text=label, anchor="w", width=100)
        self._label.pack(side="left", padx=(0, 8))

        h, m, s = self._split(total_seconds)

        self._h_var = ctk.StringVar(value=str(h))
        self._m_var = ctk.StringVar(value=str(m))
        self._s_var = ctk.StringVar(value=str(s))

        # 失焦时自动校验并钳位
        self._h_var.trace_add("write", lambda *_: self._clamp(self._h_var, 0, 9999))
        self._m_var.trace_add("write", lambda *_: self._clamp(self._m_var, 0, 59))
        self._s_var.trace_add("write", lambda *_: self._clamp(self._s_var, 0, 59))

        self._h_entry = ctk.CTkEntry(self, textvariable=self._h_var, width=50)
        self._h_entry.pack(side="left")
        ctk.CTkLabel(self, text="时").pack(side="left", padx=(2, 6))

        self._m_entry = ctk.CTkEntry(self, textvariable=self._m_var, width=50)
        self._m_entry.pack(side="left")
        ctk.CTkLabel(self, text="分").pack(side="left", padx=(2, 6))

        self._s_entry = ctk.CTkEntry(self, textvariable=self._s_var, width=50)
        self._s_entry.pack(side="left")
        ctk.CTkLabel(self, text="秒").pack(side="left", padx=(2, 0))

    @staticmethod
    def _clamp(var: ctk.StringVar, min_val: int, max_val: int) -> None:
        """将输入值钳位到 [min_val, max_val]，非数字则忽略。"""
        raw = var.get()
        # 允许空字符串（用户正在清空输入框）
        if not raw:
            return
        # 过滤非数字字符
        digits = "".join(c for c in raw if c.isdigit())
        if not digits:
            var.set("")
            return
        val = int(digits)
        clamped = max(min_val, min(val, max_val))
        if str(clamped) != raw:
            var.set(str(clamped))

    @staticmethod
    def _split(total: int) -> tuple[int, int, int]:
        if total < 0:
            return (0, 0, 0)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return (h, m, s)

    def get_value(self) -> int:
        """返回总秒数。"""
        try:
            h = int(self._h_var.get())
            m = int(self._m_var.get())
            s = int(self._s_var.get())
            return h * 3600 + m * 60 + s
        except ValueError:
            return 0

    def set_value(self, total_seconds: int) -> None:
        h, m, s = self._split(total_seconds)
        self._h_var.set(str(h))
        self._m_var.set(str(m))
        self._s_var.set(str(s))


class LabeledSlider(ctk.CTkFrame):
    """带标签和数值显示的滑块。"""

    def __init__(
        self,
        master: Any,
        label: str,
        value: int = 0,
        from_: int = 0,
        to: int = 20,
        width: int = 200,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(self, text=label, anchor="w", width=160)
        self._label.pack(side="left", padx=(0, 8))

        self._value_label = ctk.CTkLabel(self, text=str(value), width=36)

        self._slider = ctk.CTkSlider(
            self,
            from_=from_,
            to=to,
            number_of_steps=to - from_,
            width=width,
            command=self._on_change,
        )
        self._slider.set(value)
        self._slider.pack(side="left", padx=(0, 8))

        self._value_label.pack(side="left")

    def _on_change(self, val: float) -> None:
        self._value_label.configure(text=str(int(val)))

    def get_value(self) -> int:
        return int(self._slider.get())

    def set_value(self, value: int) -> None:
        self._slider.set(value)
        self._value_label.configure(text=str(value))


class LabeledFloatEntry(ctk.CTkFrame):
    """带标签的浮点数输入框。"""

    def __init__(
        self,
        master: Any,
        label: str,
        value: float = 0.0,
        width: int = 120,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(self, text=label, anchor="w", width=160)
        self._label.pack(side="left", padx=(0, 8))

        self._var = ctk.StringVar(value=str(value))
        self._entry = ctk.CTkEntry(self, textvariable=self._var, width=width)
        self._entry.pack(side="left")

    def get_value(self) -> float:
        try:
            return float(self._var.get())
        except ValueError:
            return 0.0

    def set_value(self, value: float) -> None:
        self._var.set(str(value))


class ListEditor(ctk.CTkFrame):
    """通用列表增删控件。

    支持两种添加模式：
    - preset_items 非空时显示搜索框 + 可滚动候选列表
    - 否则显示手动输入框

    name_map: ID -> 显示名 的映射，列表和候选项都会显示中文名，
              但内部存储和 get_items() 返回的仍然是原始 ID。
    """

    def __init__(
        self,
        master: Any,
        title: str,
        items: list[str],
        preset_items: list[str] | None = None,
        name_map: dict[str, str] | None = None,
        height: int = 200,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        self._items = list(items)
        self._preset_items = preset_items or []
        self._name_map = name_map or {}

        # 预计算 preset 的显示文本和反向映射
        self._display_to_id: dict[str, str] = {}
        self._preset_display: list[str] = []
        for item_id in self._preset_items:
            display = self._format_display(item_id)
            self._display_to_id[display] = item_id
            self._preset_display.append(display)

        # 标题
        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(8, 4))

        # 列表区域（已有项目）
        self._list_frame = ctk.CTkScrollableFrame(self, height=height)
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        # 底部添加栏
        add_bar = ctk.CTkFrame(self, fg_color="transparent")
        add_bar.pack(fill="x", padx=8, pady=(0, 4))

        if self._preset_items:
            # 搜索输入框
            self._search_var = ctk.StringVar()
            self._search_after_id: str | None = None
            self._search_var.trace_add("write", lambda *_: self._on_search_debounced())
            self._search_entry = ctk.CTkEntry(
                add_bar, textvariable=self._search_var,
                placeholder_text="搜索卡牌/遗物...", width=360,
            )
            self._search_entry.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                add_bar, text="添加选中", width=80, command=self._add_selected,
            ).pack(side="left")

            # 候选列表（搜索结果）
            self._candidate_frame = ctk.CTkScrollableFrame(self, height=120)
            self._candidate_frame.pack(fill="x", padx=8, pady=(0, 8))

            self._selected_id: str | None = None
            self._filter_candidates()
        else:
            self._search_after_id = None
            self._add_var = ctk.StringVar()
            self._add_entry = ctk.CTkEntry(add_bar, textvariable=self._add_var, width=360)
            self._add_entry.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                add_bar, text="添加", width=60, command=self._add_item_manual,
            ).pack(side="left")

        self._rebuild_list()

    def _format_display(self, item_id: str) -> str:
        """将 ID 格式化为显示文本。"""
        zh = self._name_map.get(item_id)
        if zh:
            return f"{zh} ({item_id})"
        return item_id

    def _on_search_debounced(self) -> None:
        """搜索防抖：200ms 内无新输入才触发过滤。"""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(200, self._filter_candidates)

    def _filter_candidates(self) -> None:
        """根据搜索词过滤候选列表。"""
        self._search_after_id = None
        for widget in self._candidate_frame.winfo_children():
            widget.destroy()

        query = self._search_var.get().strip().lower()
        # 无搜索词时不显示候选项，避免一次性渲染几百个
        if not query:
            ctk.CTkLabel(
                self._candidate_frame, text="输入关键词搜索...",
                text_color="gray", font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=4, pady=2)
            return

        matched = [
            d for d in self._preset_display if query in d.lower()
        ]

        if not matched:
            ctk.CTkLabel(
                self._candidate_frame, text="无匹配项",
                text_color="gray", font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=4, pady=2)
            return

        # 限制显示数量避免卡顿
        for display in matched[:50]:
            btn = ctk.CTkButton(
                self._candidate_frame, text=display, anchor="w",
                fg_color="transparent", hover_color="gray25",
                text_color="white", font=ctk.CTkFont(size=12),
                height=28, command=lambda d=display: self._select_candidate(d),
            )
            btn.pack(fill="x", pady=0)

        if len(matched) > 50:
            ctk.CTkLabel(
                self._candidate_frame,
                text=f"...还有 {len(matched) - 50} 项，请缩小搜索范围",
                text_color="gray", font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=4, pady=2)

    def _select_candidate(self, display: str) -> None:
        """点击候选项直接添加。"""
        item_id = self._display_to_id.get(display, display)
        self._items.append(item_id)
        self._rebuild_list()

    def _add_selected(self) -> None:
        """将搜索框内容作为添加（兜底：直接输入 ID 也能加）。"""
        raw = self._search_var.get().strip()
        if not raw:
            return
        item_id = self._display_to_id.get(raw, raw)
        self._items.append(item_id)
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        """重新渲染已有项目列表。"""
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        for i, item in enumerate(self._items):
            row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            display_text = self._format_display(item)
            ctk.CTkLabel(row, text=display_text, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="×", width=30, fg_color="firebrick",
                command=lambda idx=i: self._remove_item(idx),
            ).pack(side="right")

    def _add_item_manual(self) -> None:
        """手动输入模式的添加。"""
        raw = self._add_var.get().strip()
        if not raw:
            return
        self._items.append(raw)
        self._rebuild_list()

    def _remove_item(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._items.pop(index)
            self._rebuild_list()

    def get_items(self) -> list[str]:
        return list(self._items)

    def destroy(self) -> None:
        """销毁前取消未完成的防抖 timer。"""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
        super().destroy()
