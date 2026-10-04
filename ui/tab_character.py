"""角色数据编辑页。"""

from typing import Any

import customtkinter as ctk

from core import get_character_name
from models import CharacterStats
from ui.widgets import LabeledEntry, LabeledSlider, TimeEntry


class CharacterCard(ctk.CTkFrame):
    """单个角色的编辑卡片。"""

    def __init__(self, master: Any, stats: CharacterStats, **kwargs: Any) -> None:
        super().__init__(master, corner_radius=10, **kwargs)
        self._stats = stats

        char_name = get_character_name(stats.id)
        title = ctk.CTkLabel(
            self, text=char_name, font=ctk.CTkFont(size=16, weight="bold"),
        )
        title.pack(anchor="w", padx=16, pady=(12, 4))

        subtitle = ctk.CTkLabel(
            self, text=stats.id, font=ctk.CTkFont(size=11), text_color="gray",
        )
        subtitle.pack(anchor="w", padx=16, pady=(0, 8))

        # 编辑控件容器
        fields = ctk.CTkFrame(self, fg_color="transparent")
        fields.pack(fill="x", padx=16, pady=(0, 12))

        # 左列
        left = ctk.CTkFrame(fields, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        self.max_ascension = LabeledSlider(left, "进阶难度", stats.max_ascension, 0, 10)
        self.max_ascension.pack(anchor="w", pady=3)

        self.preferred_ascension = LabeledSlider(left, "当前进阶", stats.preferred_ascension, 0, 10)
        self.preferred_ascension.pack(anchor="w", pady=3)

        self.total_wins = LabeledEntry(left, "胜场数", stats.total_wins)
        self.total_wins.pack(anchor="w", pady=3)

        self.total_losses = LabeledEntry(left, "败场数", stats.total_losses)
        self.total_losses.pack(anchor="w", pady=3)

        # 右列
        right = ctk.CTkFrame(fields, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self.best_win_streak = LabeledEntry(right, "最高连胜", stats.best_win_streak)
        self.best_win_streak.pack(anchor="w", pady=3)

        self.current_streak = LabeledEntry(right, "当前连胜", stats.current_streak)
        self.current_streak.pack(anchor="w", pady=3)

        self.fastest_win_time = TimeEntry(right, "最快获胜", stats.fastest_win_time)
        self.fastest_win_time.pack(anchor="w", pady=3)
        # 记录原值：游戏用 -1 表示"尚未通关"，而 TimeEntry 只能表示 0+
        self._fastest_original = stats.fastest_win_time

        self.playtime = TimeEntry(right, "游玩时间", stats.playtime)
        self.playtime.pack(anchor="w", pady=3)

    def apply(self) -> CharacterStats:
        """将 UI 中的值写回 CharacterStats 对象。

        两点保护：
          - 只写回"原本就存在"的字段，未出现的字段不凭空补上默认值
          - 「最快获胜」用 -1 表示尚未通关，而 TimeEntry 只能表示 0 及以上。
            若原值为负且用户没有实际改动（仍显示 0 秒），保持原值不动，
            避免把"尚未通关"写成"0 秒通关"。
        """
        was_set = self._stats.__pydantic_fields_set__
        pairs = (
            ("max_ascension", self.max_ascension),
            ("preferred_ascension", self.preferred_ascension),
            ("total_wins", self.total_wins),
            ("total_losses", self.total_losses),
            ("best_win_streak", self.best_win_streak),
            ("current_streak", self.current_streak),
            ("fastest_win_time", self.fastest_win_time),
            ("playtime", self.playtime),
        )
        for name, widget in pairs:
            if name not in was_set:
                continue
            value = widget.get_value()
            # "最快获胜" 为负数是"尚未通关"的哨兵值。TimeEntry 无法回显 -1，
            # 若用户没有实际改动（仍为 0 秒），保持原值不动。
            if name == "fastest_win_time" and self._fastest_original < 0 and value == 0:
                continue
            setattr(self._stats, name, value)
        return self._stats


class CharacterTab(ctk.CTkTabview):
    """角色编辑标签页，每个角色一个 Tab，避免滚动渲染问题。

    注：CTkTabview 内部用 grid 布局，不能再往里 pack 自己的控件
    （会报 "already has slaves managed by grid"）。因此本页只负责
    角色 Tab 本身，Mod 角色名的扫描时机由 app 层负责。
    """

    def __init__(self, master: Any, character_stats: list[CharacterStats], **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._cards: list[CharacterCard] = []

        for stats in character_stats:
            tab = self.add(get_character_name(stats.id))
            card = CharacterCard(tab, stats)
            card.pack(fill="both", expand=True, padx=4, pady=4)
            self._cards.append(card)

    def apply_all(self) -> list[CharacterStats]:
        """将所有卡片中的值写回并返回。"""
        return [card.apply() for card in self._cards]
