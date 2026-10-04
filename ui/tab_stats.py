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

        self.total_unlocks = LabeledEntry(self, "总解锁数", data.total_unlocks)
        self.total_unlocks.pack(anchor="w", padx=16, pady=3)

        self.wongo_points = LabeledEntry(self, "旺购积分", data.wongo_points)
        self.wongo_points.pack(anchor="w", padx=16, pady=3)

        self.current_score = LabeledEntry(self, "当前分数", data.current_score)
        self.current_score.pack(anchor="w", padx=16, pady=3)

        # 战绩概览（只读：游戏按卡牌/遭遇/怪物逐条累计，逐条编辑意义不大）
        ctk.CTkLabel(
            self, text="战绩概览", font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text=(
                f"卡牌统计: {len(data.card_stats)} 条    "
                f"遭遇统计: {len(data.encounter_stats)} 条    "
                f"怪物统计: {len(data.enemy_stats)} 条    "
                f"古代统计: {len(data.ancient_stats)} 条"
            ),
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(anchor="w", padx=16, pady=2)

        ctk.CTkLabel(
            self,
            text=(
                f"已解锁 Epoch: {len(data.epochs)} 个    "
                f"已发现卡牌: {len(data.discovered_cards)}    "
                f"已发现遗物: {len(data.discovered_relics)}    "
                f"已发现药水: {len(data.discovered_potions)}"
            ),
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(anchor="w", padx=16, pady=2)

        # ── Epoch 解锁编辑 ──
        ctk.CTkLabel(
            self, text="Epoch 解锁", font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text="勾选表示该 Epoch 已在游戏中揭示（state=revealed）。取消勾选会从列表中移除。",
            font=ctk.CTkFont(size=11), text_color="gray", wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 4))

        self._epoch_checks: dict[str, ctk.BooleanVar] = {}
        epoch_box = ctk.CTkScrollableFrame(self, height=180)
        epoch_box.pack(fill="x", padx=16, pady=(0, 8))

        for epoch in data.epochs:
            var = ctk.BooleanVar(value=True)
            self._epoch_checks[epoch.id] = var
            ctk.CTkCheckBox(
                epoch_box, text=epoch.id, variable=var,
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", pady=1)

    def apply(self, data: ProgressData) -> None:
        """将 UI 中的值写回 ProgressData。"""
        data.max_multiplayer_ascension = self.max_mp_ascension.get_value()
        data.preferred_multiplayer_ascension = self.pref_mp_ascension.get_value()
        data.floors_climbed = self.floors_climbed.get_value()
        data.total_playtime = self.total_playtime.get_value()
        data.architect_damage = self.architect_damage.get_value()
        data.test_subject_kills = self.test_subject_kills.get_value()
        data.total_unlocks = self.total_unlocks.get_value()
        data.wongo_points = self.wongo_points.get_value()
        data.current_score = self.current_score.get_value()

        # Epoch：勾选保留，取消勾选则移除
        from models import Epoch

        original = {e.id: e for e in data.epochs}
        new_epochs = []
        for epoch in data.epochs:
            var = self._epoch_checks.get(epoch.id)
            if var is None or var.get():
                new_epochs.append(epoch)
        # 全部取消时保留原样，避免误操作清空解锁记录
        if new_epochs or not original:
            data.epochs = new_epochs
            data.__pydantic_fields_set__.add("epochs")
