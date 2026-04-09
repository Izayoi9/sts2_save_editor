"""全局统计数据编辑页。"""

from typing import Any

import customtkinter as ctk

from models import ProgressData
from ui.widgets import LabeledEntry, LabeledSlider, TimeEntry


class StatsTab(ctk.CTkScrollableFrame):
    """全局统计编辑标签页。"""

    def __init__(self, master: Any, data: ProgressData, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._data = data

        # 多人模式
        section_mp = ctk.CTkLabel(
            self, text="多人模式", font=ctk.CTkFont(size=16, weight="bold"),
        )
        section_mp.pack(anchor="w", padx=16, pady=(12, 4))

        self.max_mp_ascension = LabeledSlider(
            self, "最高多人进阶", data.max_multiplayer_ascension, 0, 10,
        )
        self.max_mp_ascension.pack(anchor="w", padx=16, pady=3)

        self.pref_mp_ascension = LabeledSlider(
            self, "当前多人进阶", data.preferred_multiplayer_ascension, 0, 10,
        )
        self.pref_mp_ascension.pack(anchor="w", padx=16, pady=3)

        # 全局统计
        section_global = ctk.CTkLabel(
            self, text="全局统计", font=ctk.CTkFont(size=16, weight="bold"),
        )
        section_global.pack(anchor="w", padx=16, pady=(20, 4))

        self.floors_climbed = LabeledEntry(self, "总攀爬层数", data.floors_climbed)
        self.floors_climbed.pack(anchor="w", padx=16, pady=3)

        self.total_playtime = TimeEntry(self, "总游戏时间", data.total_playtime)
        self.total_playtime.pack(anchor="w", padx=16, pady=3)

        self.architect_damage = LabeledEntry(self, "对建筑师造成的伤害", data.architect_damage)
        self.architect_damage.pack(anchor="w", padx=16, pady=3)

        self.test_subject_kills = LabeledEntry(self, "实验体击杀数", data.test_subject_kills)
        self.test_subject_kills.pack(anchor="w", padx=16, pady=3)

    def apply(self, data: ProgressData) -> None:
        """将 UI 中的值写回 ProgressData。"""
        data.max_multiplayer_ascension = self.max_mp_ascension.get_value()
        data.preferred_multiplayer_ascension = self.pref_mp_ascension.get_value()
        data.floors_climbed = self.floors_climbed.get_value()
        data.total_playtime = self.total_playtime.get_value()
        data.architect_damage = self.architect_damage.get_value()
        data.test_subject_kills = self.test_subject_kills.get_value()
