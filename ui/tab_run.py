"""对局存档 (current_run.save) 编辑页。"""

from typing import Any

import customtkinter as ctk

from models import (
    MAP_POINT_TYPES,
    CardEntry,
    CurrentRunData,
    Enchantment,
    RelicEntry,
)
from core import get_display_name, get_zh_name, load_name_map
from ui.widgets import LabeledEntry, LabeledFloatEntry, ListEditor

# 所有可用附魔 ID（ENCHANTMENT.XXX 格式）
ENCHANTMENT_IDS: list[str] = [
    "ENCHANTMENT.ADROIT",
    "ENCHANTMENT.CLONE",
    "ENCHANTMENT.CORRUPTED",
    "ENCHANTMENT.FAVORED",
    "ENCHANTMENT.GLAM",
    "ENCHANTMENT.GOOPY",
    "ENCHANTMENT.IMBUED",
    "ENCHANTMENT.INSTINCT",
    "ENCHANTMENT.MOMENTUM",
    "ENCHANTMENT.NIMBLE",
    "ENCHANTMENT.PERFECT_FIT",
    "ENCHANTMENT.ROYALLY_APPROVED",
    "ENCHANTMENT.SHARP",
    "ENCHANTMENT.SLITHER",
    "ENCHANTMENT.SLUMBERING_ESSENCE",
    "ENCHANTMENT.SOULS_POWER",
    "ENCHANTMENT.SOWN",
    "ENCHANTMENT.SPIRAL",
    "ENCHANTMENT.STEADY",
    "ENCHANTMENT.SWIFT",
    "ENCHANTMENT.TEZCATARAS_EMBER",
    "ENCHANTMENT.VIGOROUS",
]

# 地图节点类型中文映射
# "ancient" 为游戏后续版本加入的古代事件节点（即 saved_map.start）。
# v1.3.0 未定义该类型，起点节点只能落到未知类型的兜底配色上。
_MAP_TYPE_ZH: dict[str, str] = {
    "ancient": "古代",
    "monster": "怪物",
    "elite": "精英",
    "rest_site": "休息点",
    "treasure": "宝箱",
    "unknown": "未知",
    "shop": "商店",
    "event": "事件",
    "boss": "Boss",
}


class PlayerStatusTab(ctk.CTkScrollableFrame):
    """子 Tab: 玩家基础状态。"""

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        player = data.players[0] if data.players else None
        act = data.acts[0] if data.acts else None

        # 只读信息
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=16, pady=(12, 4))

        char_name = get_zh_name(player.character_id) if player else "未知"
        act_name = get_zh_name(act.id) if act else "未知"
        ctk.CTkLabel(
            info_frame, text=f"角色: {char_name}    Act: {act_name}    种子: {data.rng.seed}",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(anchor="w", padx=12, pady=8)

        if player is None:
            ctk.CTkLabel(self, text="无玩家数据").pack(pady=20)
            return

        # 编辑区域
        section = ctk.CTkLabel(self, text="基础属性", font=ctk.CTkFont(size=15, weight="bold"))
        section.pack(anchor="w", padx=16, pady=(12, 4))

        self.current_hp = LabeledEntry(self, "当前 HP", player.current_hp)
        self.current_hp.pack(anchor="w", padx=16, pady=3)

        self.max_hp = LabeledEntry(self, "最大 HP", player.max_hp)
        self.max_hp.pack(anchor="w", padx=16, pady=3)

        self.gold = LabeledEntry(self, "金币", player.gold)
        self.gold.pack(anchor="w", padx=16, pady=3)

        self.max_energy = LabeledEntry(self, "最大能量", player.max_energy)
        self.max_energy.pack(anchor="w", padx=16, pady=3)

        self.max_potion_slots = LabeledEntry(self, "药水栏位", player.max_potion_slot_count)
        self.max_potion_slots.pack(anchor="w", padx=16, pady=3)

        # 玩家概率
        section2 = ctk.CTkLabel(self, text="玩家概率", font=ctk.CTkFont(size=15, weight="bold"))
        section2.pack(anchor="w", padx=16, pady=(16, 4))

        self.card_rarity = LabeledFloatEntry(
            self, "稀有卡概率偏移", player.odds.card_rarity_odds_value,
        )
        self.card_rarity.pack(anchor="w", padx=16, pady=3)

        self.potion_reward = LabeledFloatEntry(
            self, "药水掉落概率", player.odds.potion_reward_odds_value,
        )
        self.potion_reward.pack(anchor="w", padx=16, pady=3)

        # 药水（schema 16 的 players[].potions）
        section3 = ctk.CTkLabel(self, text="药水", font=ctk.CTkFont(size=15, weight="bold"))
        section3.pack(anchor="w", padx=16, pady=(16, 4))

        self._potions = [
            (p.id, getattr(p, "slot_index", 0)) for p in player.potions
        ]
        self._potions_changed = False
        self._potion_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._potion_frame.pack(fill="x", padx=16, pady=(0, 4))

        potion_bar = ctk.CTkFrame(self, fg_color="transparent")
        potion_bar.pack(fill="x", padx=16, pady=(0, 8))

        self._potion_var = ctk.StringVar()
        ctk.CTkEntry(
            potion_bar, textvariable=self._potion_var,
            placeholder_text="输入药水 ID，如 POTION.FIRE_POTION", width=340,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            potion_bar, text="添加药水", width=80, command=self._add_potion,
        ).pack(side="left")
        ctk.CTkLabel(
            potion_bar, text="槽位按顺序自动分配",
            font=ctk.CTkFont(size=11), text_color="gray",
        ).pack(side="left", padx=(8, 0))

        self._rebuild_potions()

    def _rebuild_potions(self) -> None:
        for w in self._potion_frame.winfo_children():
            w.destroy()
        if not self._potions:
            ctk.CTkLabel(
                self._potion_frame, text="（无药水）",
                font=ctk.CTkFont(size=12), text_color="gray",
            ).pack(anchor="w")
            return
        for i, (pid, slot) in enumerate(self._potions):
            row = ctk.CTkFrame(self._potion_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row, text=f"槽位 {slot}: {get_display_name(pid)}",
                anchor="w", font=ctk.CTkFont(size=12),
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="×", width=30, height=26, fg_color="#8B3A3A",
                hover_color="#6B2A2A",
                command=lambda idx=i: self._remove_potion(idx),
            ).pack(side="right")

    def _add_potion(self) -> None:
        raw = self._potion_var.get().strip()
        if not raw:
            return
        self._potions.append((raw, len(self._potions)))
        self._potions_changed = True
        self._potion_var.set("")
        self._rebuild_potions()

    def _remove_potion(self, index: int) -> None:
        if 0 <= index < len(self._potions):
            self._potions.pop(index)
            self._potions = [(pid, i) for i, (pid, _) in enumerate(self._potions)]
            self._potions_changed = True
            self._rebuild_potions()

    def apply(self, data: CurrentRunData) -> None:
        if not data.players:
            return
        player = data.players[0]
        player.current_hp = self.current_hp.get_value()
        player.max_hp = self.max_hp.get_value()
        player.gold = self.gold.get_value()
        player.max_energy = self.max_energy.get_value()
        player.max_potion_slot_count = self.max_potion_slots.get_value()
        player.odds.card_rarity_odds_value = self.card_rarity.get_value()
        player.odds.potion_reward_odds_value = self.potion_reward.get_value()

        from models import PotionEntry

        # 仅当玩家原本就有 potions 字段，或本次确实改动过药水时才写回。
        # 否则会把一个"游戏没有的空数组"注入存档。
        if "potions" in player.__pydantic_fields_set__ or self._potions_changed:
            player.potions = [
                PotionEntry(id=pid, slot_index=slot) for pid, slot in self._potions
            ]
            player.__pydantic_fields_set__.add("potions")


class EnchantmentSelector(ctk.CTkToplevel):
    """附魔选择弹窗。"""

    def __init__(self, master: Any, name_map: dict[str, str]) -> None:
        super().__init__(master)
        self.title("选择附魔")
        self.geometry("380x480")
        self.resizable(False, False)
        self.grab_set()

        self._name_map = name_map
        self.selected_id: str | None = None

        ctk.CTkLabel(
            self, text="选择附魔", font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=12, pady=(12, 4))

        # 搜索
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkEntry(
            self, textvariable=self._search_var,
            placeholder_text="搜索附魔...", width=340,
        ).pack(padx=12, pady=(4, 8))

        # 列表
        self._list_frame = ctk.CTkScrollableFrame(self, height=320)
        self._list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        # 移除附魔按钮
        ctk.CTkButton(
            self, text="移除附魔", fg_color="#8B3A3A", hover_color="#6B2A2A",
            command=self._remove, width=340,
        ).pack(padx=12, pady=(4, 12))

        self._filter()

    def _filter(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        query = self._search_var.get().strip().lower()
        for eid in ENCHANTMENT_IDS:
            zh = self._name_map.get(eid, eid)
            display = f"{zh} ({eid})"
            if query and query not in display.lower():
                continue
            btn = ctk.CTkButton(
                self._list_frame, text=display, anchor="w",
                fg_color="transparent", hover_color="gray25",
                text_color="#DCE4EE", font=ctk.CTkFont(size=12),
                height=32, command=lambda e=eid: self._select(e),
            )
            btn.pack(fill="x", pady=1)

    def _select(self, eid: str) -> None:
        self.selected_id = eid
        self.destroy()

    def _remove(self) -> None:
        self.selected_id = "__REMOVE__"
        self.destroy()


class DeckTab(ctk.CTkFrame):
    """子 Tab: 牌组编辑（支持升级和附魔）。"""

    _UPGRADE_COLOR = "#4E9972"   # 柔和绿（与主题 rest_site 同系）
    _ENCHANT_COLOR = "#8668A4"   # 亮紫（与主题 elite 同系）
    _ENCHANT_BG = "#3A2E4A"      # 附魔标签背景

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        discovered_cards: list[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        player = data.players[0] if data.players else None
        if player is None:
            ctk.CTkLabel(self, text="无玩家数据").pack(pady=20)
            return

        self._name_map = load_name_map()
        self._cards: list[CardEntry] = list(player.deck)
        self._discovered = discovered_cards or []
        self._floor = len(data.visited_map_coords)
        self._search_after_id: str | None = None

        # 预计算候选项显示
        self._preset_display: list[str] = []
        self._display_to_id: dict[str, str] = {}
        for cid in self._discovered:
            d = self._format_card_name(cid)
            self._preset_display.append(d)
            self._display_to_id[d] = cid

        # 标题
        self._title_label = ctk.CTkLabel(
            self, text=f"牌组 ({len(self._cards)} 张)",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._title_label.pack(anchor="w", padx=12, pady=(10, 4))

        # 卡牌列表
        self._list_frame = ctk.CTkScrollableFrame(self, height=340)
        self._list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        # 添加栏
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=12, pady=(4, 4))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_debounced())
        ctk.CTkEntry(
            add_frame, textvariable=self._search_var,
            placeholder_text="搜索卡牌添加到牌组...", width=360,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            add_frame, text="添加", width=60,
            command=self._add_from_search,
        ).pack(side="left")

        # 候选列表
        self._candidate_frame = ctk.CTkScrollableFrame(self, height=100)
        self._candidate_frame.pack(fill="x", padx=12, pady=(0, 8))

        self._rebuild_list()
        self._show_search_hint()

    def _format_card_name(self, card_id: str) -> str:
        zh = self._name_map.get(card_id)
        return f"{zh} ({card_id})" if zh else card_id

    def _format_enchant_name(self, enchant_id: str) -> str:
        zh = self._name_map.get(enchant_id)
        return zh if zh else enchant_id

    def _rebuild_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()

        self._title_label.configure(text=f"牌组 ({len(self._cards)} 张)")

        for i, card in enumerate(self._cards):
            row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # 卡牌名：升级卡追加"+"后缀，名称显示为绿色
            is_upgraded = card.current_upgrade_level > 0
            zh = self._name_map.get(card.id)
            if zh:
                display_name = f"{zh}+" if is_upgraded else zh
                name_text = f"{display_name} ({card.id})"
            else:
                name_text = f"{card.id}+" if is_upgraded else card.id

            name_color = self._UPGRADE_COLOR if is_upgraded else "#DCE4EE"
            ctk.CTkLabel(
                row, text=name_text, anchor="w", width=220,
                font=ctk.CTkFont(size=12),
                text_color=name_color,
            ).pack(side="left")

            # 附魔标签：带背景色的圆角标签
            has_enchant = card.enchantment and card.enchantment.id
            if has_enchant:
                ench_name = self._format_enchant_name(card.enchantment.id)
                ench_badge = ctk.CTkLabel(
                    row, text=f" {ench_name} ",
                    text_color=self._ENCHANT_COLOR,
                    fg_color=self._ENCHANT_BG,
                    corner_radius=4,
                    font=ctk.CTkFont(size=10),
                    height=22,
                )
                ench_badge.pack(side="left", padx=(6, 0))

            # 操作按钮（从右到左排列）
            ctk.CTkButton(
                row, text="×", width=30, height=26,
                fg_color="#8B3A3A", hover_color="#6B2A2A",
                command=lambda idx=i: self._remove_card(idx),
            ).pack(side="right", padx=(2, 0))

            ctk.CTkButton(
                row, text="附魔", width=50, height=26,
                fg_color="#4A3A60" if has_enchant else "gray30",
                hover_color="#5A4A70",
                command=lambda idx=i: self._edit_enchantment(idx),
            ).pack(side="right", padx=(2, 0))

            upgrade_text = "取消升级" if is_upgraded else "升级"
            upgrade_fg = "#3A7D5C" if is_upgraded else "gray30"
            ctk.CTkButton(
                row, text=upgrade_text, width=65, height=26,
                fg_color=upgrade_fg, hover_color="#2E6348",
                command=lambda idx=i: self._toggle_upgrade(idx),
            ).pack(side="right", padx=(2, 0))

    def _toggle_upgrade(self, index: int) -> None:
        card = self._cards[index]
        card.current_upgrade_level = 0 if card.current_upgrade_level > 0 else 1
        self._rebuild_list()

    def _edit_enchantment(self, index: int) -> None:
        dialog = EnchantmentSelector(self, self._name_map)
        self.wait_window(dialog)
        if dialog.selected_id is None:
            return
        card = self._cards[index]
        if dialog.selected_id == "__REMOVE__":
            card.enchantment = None
        else:
            card.enchantment = Enchantment(id=dialog.selected_id, amount=1)
        self._rebuild_list()

    def _remove_card(self, index: int) -> None:
        if 0 <= index < len(self._cards):
            self._cards.pop(index)
            self._rebuild_list()

    def _on_search_debounced(self) -> None:
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(200, self._filter_candidates)

    def _show_search_hint(self) -> None:
        for w in self._candidate_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._candidate_frame, text="输入关键词搜索卡牌...",
            text_color="gray", font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=4, pady=2)

    def _filter_candidates(self) -> None:
        self._search_after_id = None
        for w in self._candidate_frame.winfo_children():
            w.destroy()

        query = self._search_var.get().strip().lower()
        if not query:
            self._show_search_hint()
            return

        matched = [d for d in self._preset_display if query in d.lower()]
        if not matched:
            ctk.CTkLabel(
                self._candidate_frame, text="无匹配项",
                text_color="gray", font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=4, pady=2)
            return

        for display in matched[:50]:
            btn = ctk.CTkButton(
                self._candidate_frame, text=display, anchor="w",
                fg_color="transparent", hover_color="gray25",
                text_color="#DCE4EE", font=ctk.CTkFont(size=12),
                height=28, command=lambda d=display: self._add_candidate(d),
            )
            btn.pack(fill="x", pady=0)

        if len(matched) > 50:
            ctk.CTkLabel(
                self._candidate_frame,
                text=f"...还有 {len(matched) - 50} 项，请缩小搜索范围",
                text_color="gray", font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=4, pady=2)

    def _add_candidate(self, display: str) -> None:
        card_id = self._display_to_id.get(display, display)
        self._cards.append(CardEntry(
            id=card_id, floor_added_to_deck=self._floor,
        ))
        self._rebuild_list()

    def _add_from_search(self) -> None:
        raw = self._search_var.get().strip()
        if not raw:
            return
        card_id = self._display_to_id.get(raw, raw)
        self._cards.append(CardEntry(
            id=card_id, floor_added_to_deck=self._floor,
        ))
        self._rebuild_list()

    def apply(self, data: CurrentRunData) -> None:
        if not data.players:
            return
        data.players[0].deck = list(self._cards)
        # 整表替换必须显式标记，否则 exclude_unset 不会写出 deck
        data.players[0].__pydantic_fields_set__.add("deck")

    def destroy(self) -> None:
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
        super().destroy()


class RelicTab(ctk.CTkFrame):
    """子 Tab: 遗物编辑。"""

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        discovered_relics: list[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        player = data.players[0] if data.players else None
        if player is None:
            ctk.CTkLabel(self, text="无玩家数据").pack(pady=20)
            return

        relic_ids = [r.id for r in player.relics]
        name_map = load_name_map()
        self._editor = ListEditor(
            self,
            title=f"遗物 ({len(relic_ids)} 个)",
            items=relic_ids,
            preset_items=discovered_relics if discovered_relics else None,
            name_map=name_map,
            height=400,
        )
        self._editor.pack(fill="both", expand=True, padx=8, pady=8)

    def apply(self, data: CurrentRunData) -> None:
        if not data.players:
            return
        player = data.players[0]
        existing = {r.id: r.floor_added_to_deck for r in player.relics}
        floor = len(data.visited_map_coords)
        new_relics: list[RelicEntry] = []
        for relic_id in self._editor.get_items():
            new_relics.append(RelicEntry(
                id=relic_id,
                floor_added_to_deck=existing.get(relic_id, floor),
            ))
        player.relics = new_relics
        player.__pydantic_fields_set__.add("relics")


class MapTab(ctk.CTkFrame):
    """子 Tab: Canvas 可视化地图编辑。

    配色方案与 CustomTkinter dark+blue 主题保持一致：
    - 画布背景：gray17 (#2B2B2B)，与 CTkFrame 背景相同
    - 节点颜色：低饱和柔和色调，在深色背景上清晰但不刺眼
    - 连线：中灰色，已访问路径使用主题蓝 (#1F6AA5)
    - 文字：统一使用主题文字色 (#DCE4EE)
    """

    # ── 主题色常量（来自 CustomTkinter dark+blue 主题）──
    _BG_COLOR = "#2B2B2B"        # gray17 - CTkFrame 背景
    _BG_DARKER = "#242424"       # gray14 - 窗口背景
    _TEXT_COLOR = "#DCE4EE"      # 主题文字色
    _TEXT_DIM = "#8A9099"        # 次要文字
    _TEXT_DISABLED = "#5A5E62"   # 禁用文字
    _ACCENT_BLUE = "#1F6AA5"    # 主题蓝
    _ACCENT_HOVER = "#144870"   # 主题深蓝
    _BORDER_COLOR = "#565B5E"   # 边框色

    # 节点类型 → (填充色, 描边色) — 低饱和柔和色调
    _TYPE_STYLES: dict[str, tuple[str, str]] = {
        "ancient": ("#6A5A8A", "#8A78AC"),   # 古代：偏紫
        "monster": ("#8B3A3A", "#A85454"),   # 暗红
        "elite": ("#6B4C8A", "#8668A4"),     # 暗紫
        "rest_site": ("#3A7D5C", "#4E9972"), # 暗绿
        "treasure": ("#9C7A2E", "#B8944A"),  # 暗金
        "unknown": ("#505A62", "#6A747C"),   # 灰蓝
        "shop": ("#2E6B8A", "#4285A4"),      # 蓝灰
        "event": ("#2E7A7A", "#429494"),     # 青灰
        "boss": ("#A63C3C", "#C45656"),      # 偏红
    }
    # 已访问节点样式
    _VISITED_FILL = "#383C40"
    _VISITED_OUTLINE = "#4A4E52"
    # 当前层高亮
    _CURRENT_ROW_COLOR = "#1A2D40"  # 深蓝底色，与主题蓝呼应
    _CURRENT_ROW_BORDER = "#1F6AA5"

    # 图例中的节点颜色（稍微提亮用于小色块）
    _LEGEND_COLORS: dict[str, str] = {
        "ancient": "#8A78AC",
        "monster": "#A85454",
        "elite": "#8668A4",
        "rest_site": "#4E9972",
        "treasure": "#B8944A",
        "unknown": "#6A747C",
        "shop": "#4285A4",
        "event": "#429494",
        "boss": "#C45656",
    }

    _CELL_W = 100
    _CELL_H = 70
    _NODE_RX = 32  # 节点半宽
    _NODE_RY = 18  # 节点半高
    _NODE_ROUND = 8  # 圆角半径
    _PAD_LEFT = 50
    _PAD_TOP = 40

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        import tkinter as tk

        self._data = data
        self._tk = tk
        # 每个 Act 各自的修改补丁：act_index -> {point_index: new_type}
        self._modifications: dict[int, dict[int, str]] = {}
        self._act_index = 0

        # 只有当前 Act 带 saved_map，其余 Act 只有 rooms（saved_map 为 None）
        self._act_options: list[tuple[int, str]] = [
            (i, get_zh_name(act.id)) for i, act in enumerate(data.acts)
            if act.saved_map is not None
        ]
        if not self._act_options:
            ctk.CTkLabel(self, text="无地图数据").pack(pady=20)
            return

        act = data.acts[self._act_options[0][0]]
        smap = act.saved_map
        assert smap is not None
        points = smap.points
        self._visited = {(c.col, c.row) for c in data.visited_map_coords}

        max_row = max((p.coord.row for p in points), default=0)

        self._coord_to_idx: dict[tuple[int, int], int] = {}
        for i, p in enumerate(points):
            self._coord_to_idx[(p.coord.col, p.coord.row)] = i

        canvas_w = smap.width * self._CELL_W + self._PAD_LEFT + 20
        canvas_h = (max_row + 1) * self._CELL_H + self._PAD_TOP + 60

        has_boss = smap.boss is not None
        if has_boss:
            canvas_h += self._CELL_H

        # ── 标题 ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            header, text=f"地图节点 ({len(points)} 个)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="点击可编辑节点修改类型",
            font=ctk.CTkFont(size=12), text_color=self._TEXT_DIM,
        ).pack(side="left", padx=(12, 0))

        # 当前 Act 标识（只有当前 Act 带地图；用于区分进度）
        ctk.CTkLabel(
            header, text=f"当前：{get_zh_name(act.id)}",
            font=ctk.CTkFont(size=12), text_color=self._TEXT_DIM,
        ).pack(side="right")

        # ── 图例 ──
        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", padx=12, pady=(6, 6))
        for type_key, zh in _MAP_TYPE_ZH.items():
            color = self._LEGEND_COLORS.get(type_key, "#6A747C")
            # 用 Canvas 画小色块，比纯文字 ● 更精致
            chip = ctk.CTkFrame(legend, fg_color="transparent")
            chip.pack(side="left", padx=(0, 14))
            dot = tk.Canvas(chip, width=10, height=10, bg=self._BG_DARKER,
                            highlightthickness=0)
            dot.pack(side="left", padx=(0, 4))
            dot.create_oval(1, 1, 9, 9, fill=color, outline="")
            ctk.CTkLabel(
                chip, text=zh, font=ctk.CTkFont(size=11),
                text_color=self._TEXT_DIM,
            ).pack(side="left")

        # ── Canvas ──
        canvas_frame = ctk.CTkFrame(self, corner_radius=6)
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self._canvas_frame = canvas_frame

        self._canvas = tk.Canvas(
            canvas_frame, bg=self._BG_COLOR, highlightthickness=0,
            scrollregion=(0, 0, canvas_w, canvas_h),
        )
        scrollbar_y = tk.Scrollbar(
            canvas_frame, orient="vertical", command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<Enter>", lambda e: self._canvas.focus_set())

        self._node_items: dict[int, tuple[int, Any, bool]] = {}
        self._node_text_items: dict[int, int] = {}
        self._tooltip_ids: list[int] = []

        # ── 计算当前层 ──
        current_row = -1
        if data.visited_map_coords:
            current_row = max(c.row for c in data.visited_map_coords) + 1

        boss_offset = self._CELL_H if has_boss else 0

        # ── 当前层高亮条 ──
        if 0 <= current_row <= max_row:
            hy = self._row_to_y(current_row, max_row, boss_offset) - self._CELL_H // 2
            self._canvas.create_rectangle(
                0, hy, canvas_w, hy + self._CELL_H,
                fill=self._CURRENT_ROW_COLOR, outline="",
            )
            # 左侧蓝色指示条
            self._canvas.create_rectangle(
                0, hy, 4, hy + self._CELL_H,
                fill=self._CURRENT_ROW_BORDER, outline="",
            )

        # ── 层号标签 ──
        for r in range(max_row + 1):
            y = self._row_to_y(r, max_row, boss_offset)
            self._canvas.create_text(
                24, y, text=str(r), fill=self._TEXT_DISABLED,
                font=("Microsoft YaHei", 9),
            )

        # ── 连线 ──
        for point in points:
            px, py = self._coord_to_xy(point.coord.col, point.coord.row, max_row, smap.width, boss_offset)
            parent_visited = (point.coord.col, point.coord.row) in self._visited
            for child in point.children:
                cx, cy = self._coord_to_xy(child.col, child.row, max_row, smap.width, boss_offset)
                child_visited = (child.col, child.row) in self._visited
                if parent_visited and child_visited:
                    line_color = self._ACCENT_BLUE
                    line_width = 2.5
                else:
                    line_color = "#454A50"
                    line_width = 1.5
                self._canvas.create_line(
                    px, py, cx, cy,
                    fill=line_color, width=line_width,
                )

        # ── 起点（古代事件节点）──
        if smap.start is not None:
            self._draw_node(smap.start, -1, max_row, smap.width, boss_offset,
                            is_start=True)

        # ── 节点 ──
        for i, point in enumerate(points):
            self._draw_node(point, i, max_row, smap.width, boss_offset)

        # ── Boss 节点 ──
        if has_boss and smap.boss is not None:
            self._draw_node(smap.boss, -2, max_row, smap.width, boss_offset,
                            is_boss=True, canvas_w=canvas_w)

    def _draw_node(
        self,
        point: Any,
        index: int,
        max_row: int,
        width: int,
        boss_offset: int,
        is_start: bool = False,
        is_boss: bool = False,
        canvas_w: int = 0,
    ) -> None:
        """绘制单个节点。index < 0 表示起点/Boss，不参与按索引改写。"""
        if is_boss:
            px = canvas_w // 2
            py = self._PAD_TOP // 2 + 10
            rx, ry = 42, 22
        else:
            px, py = self._coord_to_xy(
                point.coord.col, point.coord.row, max_row, width, boss_offset)
            rx, ry = self._NODE_RX, self._NODE_RY

        is_visited = (point.coord.col, point.coord.row) in self._visited
        # 起点与 Boss 不参与按索引修改
        can_edit = (bool(getattr(point, "can_modify", False))
                    and not is_visited and index >= 0 and not is_boss)

        if is_visited:
            fill, outline = self._VISITED_FILL, self._VISITED_OUTLINE
        else:
            fill, outline = self._TYPE_STYLES.get(point.type, ("#505A62", "#6A747C"))

        node_id = self._create_rounded_rect(
            px - rx, py - ry, px + rx, py + ry, self._NODE_ROUND,
            fill=fill, outline=outline, width=2 if is_boss else 1.5,
        )

        type_zh = _MAP_TYPE_ZH.get(point.type, point.type)
        text_color = self._TEXT_DISABLED if is_visited else self._TEXT_COLOR
        text_id = self._canvas.create_text(
            px, py, text=type_zh, fill=text_color,
            font=("Microsoft YaHei", 11 if is_boss else 9, "bold"),
        )

        # 底部状态标签
        if is_visited:
            self._canvas.create_text(
                px, py + ry + 11, text="已访问", fill=self._TEXT_DISABLED,
                font=("Microsoft YaHei", 7),
            )
        elif is_start:
            self._canvas.create_text(
                px, py + ry + 11, text="起点", fill=self._TEXT_DISABLED,
                font=("Microsoft YaHei", 7),
            )
        elif index >= 0 and not getattr(point, "can_modify", False):
            self._canvas.create_text(
                px, py + ry + 11, text="锁定", fill=self._TEXT_DISABLED,
                font=("Microsoft YaHei", 7),
            )

        self._node_items[node_id] = (index, point, can_edit)
        self._node_items[text_id] = (index, point, can_edit)
        self._node_text_items[node_id] = text_id

        self._canvas.tag_bind(node_id, "<Button-1>", self._on_node_click)
        self._canvas.tag_bind(text_id, "<Button-1>", self._on_node_click)
        self._canvas.tag_bind(node_id, "<Enter>", self._on_node_enter)
        self._canvas.tag_bind(text_id, "<Enter>", self._on_node_enter)
        self._canvas.tag_bind(node_id, "<Leave>", self._on_node_leave)
        self._canvas.tag_bind(text_id, "<Leave>", self._on_node_leave)

    def _create_rounded_rect(
        self, x1: int, y1: int, x2: int, y2: int, r: int, **kwargs: Any,
    ) -> int:
        """在 Canvas 上绘制圆角矩形，返回 item_id。"""
        points = [
            x1 + r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kwargs)

    def _row_to_y(self, row: int, max_row: int, boss_offset: int) -> int:
        return self._PAD_TOP + boss_offset + (max_row - row) * self._CELL_H + self._CELL_H // 2

    def _coord_to_xy(
        self, col: int, row: int, max_row: int, width: int, boss_offset: int,
    ) -> tuple[int, int]:
        x = self._PAD_LEFT + col * self._CELL_W + self._CELL_W // 2
        y = self._row_to_y(row, max_row, boss_offset)
        return x, y

    def _on_mousewheel(self, event: Any) -> None:
        self._canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_node_click(self, event: Any) -> None:
        """点击节点弹出类型选择菜单。"""
        import tkinter as tk
        cx = self._canvas.canvasx(event.x)
        cy = self._canvas.canvasy(event.y)
        item_id = self._canvas.find_closest(cx, cy)[0]
        info = self._node_items.get(item_id)
        if info is None:
            return
        point_idx, point, can_edit = info
        if not can_edit:
            return

        menu = tk.Menu(
            self._canvas, tearoff=0,
            bg="#343638", fg=self._TEXT_COLOR,
            activebackground=self._ACCENT_BLUE,
            activeforeground=self._TEXT_COLOR,
            relief="flat", bd=1,
        )
        for type_key, zh in _MAP_TYPE_ZH.items():
            menu.add_command(
                label=f"  {zh}",
                command=lambda t=type_key, idx=point_idx, iid=item_id: self._set_node_type(idx, t, iid),
            )
        menu.tk_popup(event.x_root, event.y_root)

    def _set_node_type(self, point_idx: int, new_type: str, item_id: int) -> None:
        """更新节点类型（视觉 + 数据）。只允许对普通节点（index >= 0）操作。"""
        if point_idx < 0:
            return
        self._modifications.setdefault(self._act_index, {})[point_idx] = new_type

        style = self._TYPE_STYLES.get(new_type, ("#505A62", "#6A747C"))
        # 找到 polygon item（可能点击的是 text）
        poly_id = item_id
        if item_id not in self._node_text_items:
            for oid, tid in self._node_text_items.items():
                if tid == item_id:
                    poly_id = oid
                    break
        self._canvas.itemconfigure(poly_id, fill=style[0], outline=style[1])

        text_id = self._node_text_items.get(poly_id, item_id)
        self._canvas.itemconfigure(text_id, text=_MAP_TYPE_ZH.get(new_type, new_type))

    def _on_node_enter(self, event: Any) -> None:
        """鼠标悬停显示 tooltip。"""
        cx = self._canvas.canvasx(event.x)
        cy = self._canvas.canvasy(event.y)
        item_id = self._canvas.find_closest(cx, cy)[0]
        info = self._node_items.get(item_id)
        if info is None:
            return
        point_idx, point, can_edit = info
        current_type = self._modifications.get(self._act_index, {}).get(point_idx, point.type)
        type_zh = _MAP_TYPE_ZH.get(current_type, current_type)
        status = "可编辑" if can_edit else "不可编辑"

        tip_text = f" ({point.coord.col}, {point.coord.row})  {type_zh}  [{status}] "

        # tooltip 位置（节点上方）
        tip_x = cx
        tip_y = cy - self._NODE_RY - 18

        # 测量文字宽度（近似）
        tw = len(tip_text) * 7.5 + 8
        th = 20

        bg_id = self._canvas.create_rectangle(
            tip_x - tw / 2, tip_y - th / 2,
            tip_x + tw / 2, tip_y + th / 2,
            fill="#343638", outline=self._BORDER_COLOR, width=1,
        )
        txt_id = self._canvas.create_text(
            tip_x, tip_y, text=tip_text, fill=self._TEXT_COLOR,
            font=("Microsoft YaHei", 9),
        )
        self._tooltip_ids = [bg_id, txt_id]

    def _on_node_leave(self, event: Any) -> None:
        """移除 tooltip。"""
        for tid in self._tooltip_ids:
            self._canvas.delete(tid)
        self._tooltip_ids.clear()

    def apply(self, data: CurrentRunData) -> None:
        """把各 Act 的类型修改写回（仅对当前存在地图的 Act）。"""
        for act_index, patch in self._modifications.items():
            if act_index >= len(data.acts):
                continue
            smap = data.acts[act_index].saved_map
            if smap is None:
                continue
            points = smap.points
            for idx, new_type in patch.items():
                if 0 <= idx < len(points):
                    points[idx].type = new_type
                    # 手动改过类型的节点必须显式标记集合，确保写出
                    points[idx].__pydantic_fields_set__.add("type")


class EncounterPoolTab(ctk.CTkScrollableFrame):
    """子 Tab: 遭遇池 & 事件池编辑。

    存档中每个 Act 有独立的遭遇/事件池（当前对局的 3 个 Act 会同时存在），
    因此这里提供 Act 切换，编辑结果按 Act 分别保留。
    """

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        self._data = data
        if not data.acts:
            ctk.CTkLabel(self, text="无数据").pack(pady=20)
            return

        self._act_index = 0
        # act_index -> {"elite": [...], "normal": [...], "event": [...]}
        self._edits: dict[int, dict[str, list[str]]] = {}

        # ── Act 切换 ──
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            bar, text="遭遇池 & 事件池", font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")
        self._act_selector = ctk.CTkOptionMenu(
            bar, values=[get_zh_name(a.id) for a in data.acts],
            width=160, command=self._on_act_change,
        )
        self._act_selector.pack(side="right")

        # 动态内容容器
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True)

        self._build_act(0)

    def _on_act_change(self, choice: str) -> None:
        try:
            idx = self._act_selector.cget("values").index(choice)
        except (ValueError, AttributeError):
            return
        self._build_act(idx)

    def _build_act(self, act_index: int) -> None:
        # 先保存当前 Act 的编辑
        self._stash_current()
        self._act_index = act_index

        for w in self._body.winfo_children():
            w.destroy()

        rooms = self._data.acts[act_index].rooms
        saved = self._edits.get(act_index)

        # 访问计数（只读）
        info = ctk.CTkFrame(self._body)
        info.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            info,
            text=(
                f"精英已访问: {rooms.elite_encounters_visited}    "
                f"普通已访问: {rooms.normal_encounters_visited}    "
                f"事件已访问: {rooms.events_visited}"
            ),
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(anchor="w", padx=8, pady=4)

        # Boss
        ctk.CTkLabel(
            self._body, text=f"Boss: {get_display_name(rooms.boss_id)}",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=16, pady=(8, 4))

        name_map = load_name_map()

        self._elite_editor = ListEditor(
            self._body, title="精英遭遇池",
            items=saved["elite"] if saved else rooms.elite_encounter_ids,
            name_map=name_map, height=120,
        )
        self._elite_editor.pack(fill="x", padx=8, pady=4)

        self._normal_editor = ListEditor(
            self._body, title="普通遭遇池",
            items=saved["normal"] if saved else rooms.normal_encounter_ids,
            name_map=name_map, height=120,
        )
        self._normal_editor.pack(fill="x", padx=8, pady=4)

        self._event_editor = ListEditor(
            self._body, title="事件池",
            items=saved["event"] if saved else rooms.event_ids,
            name_map=name_map, height=120,
        )
        self._event_editor.pack(fill="x", padx=8, pady=4)

    def _stash_current(self) -> None:
        """把当前编辑控件的值暂存到 _edits。"""
        if not hasattr(self, "_elite_editor"):
            return
        self._edits[self._act_index] = {
            "elite": self._elite_editor.get_items(),
            "normal": self._normal_editor.get_items(),
            "event": self._event_editor.get_items(),
        }

    def apply(self, data: CurrentRunData) -> None:
        self._stash_current()
        for act_index, patch in self._edits.items():
            if act_index >= len(data.acts):
                continue
            rooms = data.acts[act_index].rooms
            rooms.elite_encounter_ids = patch["elite"]
            rooms.normal_encounter_ids = patch["normal"]
            rooms.event_ids = patch["event"]
            rooms.__pydantic_fields_set__.update(
                {"elite_encounter_ids", "normal_encounter_ids", "event_ids"})


class OddsRngTab(ctk.CTkScrollableFrame):
    """子 Tab: 概率 & RNG 编辑。"""

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        # ── 全局问号房概率 ──
        ctk.CTkLabel(
            self, text="问号房概率", font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        odds = data.odds
        self.elite_odds = LabeledFloatEntry(self, "精英房概率", odds.unknown_map_point_elite_odds_value)
        self.elite_odds.pack(anchor="w", padx=16, pady=3)

        self.monster_odds = LabeledFloatEntry(self, "怪物房概率", odds.unknown_map_point_monster_odds_value)
        self.monster_odds.pack(anchor="w", padx=16, pady=3)

        self.shop_odds = LabeledFloatEntry(self, "商店概率", odds.unknown_map_point_shop_odds_value)
        self.shop_odds.pack(anchor="w", padx=16, pady=3)

        self.treasure_odds = LabeledFloatEntry(self, "宝箱概率", odds.unknown_map_point_treasure_odds_value)
        self.treasure_odds.pack(anchor="w", padx=16, pady=3)

        # ── 全局 RNG ──
        ctk.CTkLabel(
            self, text="全局 RNG", font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            self, text=f"种子: {data.rng.seed}", font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(anchor="w", padx=16, pady=2)

        counters = data.rng.counters
        self.rng_up_front = LabeledEntry(self, "up_front", counters.up_front)
        self.rng_up_front.pack(anchor="w", padx=16, pady=2)

        self.rng_shuffle = LabeledEntry(self, "shuffle", counters.shuffle)
        self.rng_shuffle.pack(anchor="w", padx=16, pady=2)

        self.rng_unknown_map = LabeledEntry(self, "unknown_map_point", counters.unknown_map_point)
        self.rng_unknown_map.pack(anchor="w", padx=16, pady=2)

        self.rng_niche = LabeledEntry(self, "niche", counters.niche)
        self.rng_niche.pack(anchor="w", padx=16, pady=2)

        self.rng_treasure = LabeledEntry(self, "treasure_room_relics", counters.treasure_room_relics)
        self.rng_treasure.pack(anchor="w", padx=16, pady=2)

        # ── 玩家 RNG ──
        player = data.players[0] if data.players else None
        if player:
            ctk.CTkLabel(
                self, text="玩家 RNG", font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))

            ctk.CTkLabel(
                self, text=f"种子: {player.rng.seed}", font=ctk.CTkFont(size=12), text_color="gray",
            ).pack(anchor="w", padx=16, pady=2)

            pc = player.rng.counters
            self.prng_rewards = LabeledEntry(self, "rewards", pc.rewards)
            self.prng_rewards.pack(anchor="w", padx=16, pady=2)

            self.prng_shops = LabeledEntry(self, "shops", pc.shops)
            self.prng_shops.pack(anchor="w", padx=16, pady=2)

            self.prng_transforms = LabeledEntry(self, "transformations", pc.transformations)
            self.prng_transforms.pack(anchor="w", padx=16, pady=2)

    def apply(self, data: CurrentRunData) -> None:
        # 全局 odds
        data.odds.unknown_map_point_elite_odds_value = self.elite_odds.get_value()
        data.odds.unknown_map_point_monster_odds_value = self.monster_odds.get_value()
        data.odds.unknown_map_point_shop_odds_value = self.shop_odds.get_value()
        data.odds.unknown_map_point_treasure_odds_value = self.treasure_odds.get_value()

        # 全局 RNG counters
        c = data.rng.counters
        c.up_front = self.rng_up_front.get_value()
        c.shuffle = self.rng_shuffle.get_value()
        c.unknown_map_point = self.rng_unknown_map.get_value()
        c.niche = self.rng_niche.get_value()
        c.treasure_room_relics = self.rng_treasure.get_value()

        # 玩家 RNG counters
        if data.players:
            pc = data.players[0].rng.counters
            pc.rewards = self.prng_rewards.get_value()
            pc.shops = self.prng_shops.get_value()
            pc.transformations = self.prng_transforms.get_value()


class RunTab(ctk.CTkTabview):
    """对局编辑主 Tab，包含 6 个子页面。"""

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        discovered_cards: list[str],
        discovered_relics: list[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._data = data

        # 创建子 Tab
        tab_status = self.add("玩家状态")
        self._status_tab = PlayerStatusTab(tab_status, data)
        self._status_tab.pack(fill="both", expand=True)

        tab_deck = self.add("牌组")
        self._deck_tab = DeckTab(tab_deck, data, discovered_cards)
        self._deck_tab.pack(fill="both", expand=True)

        tab_relic = self.add("遗物")
        self._relic_tab = RelicTab(tab_relic, data, discovered_relics)
        self._relic_tab.pack(fill="both", expand=True)

        tab_map = self.add("地图")
        self._map_tab = MapTab(tab_map, data)
        self._map_tab.pack(fill="both", expand=True)

        tab_pool = self.add("遭遇池")
        self._pool_tab = EncounterPoolTab(tab_pool, data)
        self._pool_tab.pack(fill="both", expand=True)

        tab_rng = self.add("概率/RNG")
        self._rng_tab = OddsRngTab(tab_rng, data)
        self._rng_tab.pack(fill="both", expand=True)

    def apply(self) -> CurrentRunData:
        """将所有子 Tab 的值写回 data 并返回。"""
        self._status_tab.apply(self._data)
        self._deck_tab.apply(self._data)
        self._relic_tab.apply(self._data)
        self._map_tab.apply(self._data)
        self._pool_tab.apply(self._data)
        self._rng_tab.apply(self._data)
        return self._data
