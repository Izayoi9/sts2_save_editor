"""ID 图鉴 — 以表格形式查看所有卡牌/遗物/怪物/事件的内部 ID 和中文名。"""

from typing import Any

import customtkinter as ctk

from core import load_name_map


# 按前缀分类
_CATEGORIES: list[tuple[str, str]] = [
    ("CARD.", "卡牌"),
    ("RELIC.", "遗物"),
    ("ENCOUNTER.", "遭遇"),
    ("MONSTER.", "怪物"),
    ("EVENT.", "事件"),
    ("ACT.", "章节"),
    ("CHARACTER.", "角色"),
]

# 每页最大渲染行数，防止 CTk 控件过多卡死
_MAX_RENDER = 100


class DictionaryTab(ctk.CTkFrame):
    """ID 图鉴页面：搜索 + 分类 Tab + 表格。"""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self._name_map = load_name_map()

        # 按类别分组（一次性预计算，之后只做过滤）
        self._grouped: dict[str, list[tuple[str, str]]] = {}
        for prefix, label in _CATEGORIES:
            entries = sorted(
                [(gid, zh) for gid, zh in self._name_map.items() if gid.startswith(prefix)],
                key=lambda x: x[0],
            )
            self._grouped[label] = entries

        # 预创建字体对象，避免每行重复创建
        self._font_id = ctk.CTkFont(size=12, family="Consolas")
        self._font_zh = ctk.CTkFont(size=12)
        self._font_header = ctk.CTkFont(size=12, weight="bold")

        # ── 顶部搜索栏 ──
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(search_bar, text="搜索:", width=50).pack(side="left")
        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            search_bar, textvariable=self._search_var,
            placeholder_text="输入 ID 或中文名...", width=300,
        )
        self._search_entry.pack(side="left", padx=(4, 8))

        self._count_label = ctk.CTkLabel(
            search_bar, text="", font=ctk.CTkFont(size=12), text_color="gray",
        )
        self._count_label.pack(side="left")

        # 搜索防抖
        self._search_after_id: str | None = None
        self._search_var.trace_add("write", lambda *_: self._on_search_debounced())

        # ── 分类 Tabview ──
        self._tabview = ctk.CTkTabview(self, command=self._on_tab_switch)
        self._tabview.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._tab_frames: dict[str, ctk.CTkScrollableFrame] = {}
        for _, label in _CATEGORIES:
            tab = self._tabview.add(label)
            scroll = ctk.CTkScrollableFrame(tab)
            scroll.pack(fill="both", expand=True)
            self._tab_frames[label] = scroll

        # 缓存当前 query 避免重复渲染
        self._last_query = ""

        # 只渲染首个 tab
        self._render_tab(_CATEGORIES[0][1])

    def _on_search_debounced(self) -> None:
        """搜索防抖：300ms 内无新输入才触发渲染。"""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._on_search)

    def _on_search(self) -> None:
        """执行搜索：只渲染当前激活的 tab。"""
        self._search_after_id = None
        current_label = self._tabview.get()
        self._render_tab(current_label)

    def _on_tab_switch(self) -> None:
        """切换分类 tab 时渲染对应内容。"""
        current_label = self._tabview.get()
        self._render_tab(current_label)

    def _render_tab(self, label: str) -> None:
        """只渲染指定分类的表格。"""
        frame = self._tab_frames.get(label)
        if frame is None:
            return

        query = self._search_var.get().strip().lower()

        # 清空旧内容
        for w in frame.winfo_children():
            w.destroy()

        entries = self._grouped.get(label, [])
        if query:
            entries = [
                (gid, zh) for gid, zh in entries
                if query in gid.lower() or query in zh.lower()
            ]

        total = len(entries)

        # 表头
        header = ctk.CTkFrame(frame, fg_color="gray20", corner_radius=4)
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(
            header, text="内部 ID", width=360, anchor="w", font=self._font_header,
        ).pack(side="left", padx=8, pady=4)
        ctk.CTkLabel(
            header, text="中文名称", width=200, anchor="w", font=self._font_header,
        ).pack(side="left", padx=8, pady=4)

        # 数据行（限制渲染数量）
        render_count = min(total, _MAX_RENDER)
        for i in range(render_count):
            game_id, zh_name = entries[i]
            bg = "gray15" if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(frame, fg_color=bg, corner_radius=0)
            row.pack(fill="x")
            ctk.CTkLabel(
                row, text=game_id, width=360, anchor="w", font=self._font_id,
            ).pack(side="left", padx=8, pady=2)
            ctk.CTkLabel(
                row, text=zh_name, width=200, anchor="w", font=self._font_zh,
            ).pack(side="left", padx=8, pady=2)

        if total > _MAX_RENDER:
            ctk.CTkLabel(
                frame, text=f"...还有 {total - _MAX_RENDER} 项，请使用搜索缩小范围",
                text_color="gray", font=self._font_zh,
            ).pack(anchor="w", padx=8, pady=4)

        self._count_label.configure(text=f"当前分类: {total} 条")
