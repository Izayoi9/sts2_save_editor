"""对局存档 (current_run.save) 编辑页。"""

from typing import Any

import customtkinter as ctk

from models import (
    MAP_POINT_TYPES,
    CardEntry,
    CurrentRunData,
    RelicEntry,
)
from core import get_display_name, get_zh_name, load_name_map
from ui.widgets import LabeledEntry, LabeledFloatEntry, ListEditor

# 地图节点类型中文映射
_MAP_TYPE_ZH: dict[str, str] = {
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


class DeckTab(ctk.CTkFrame):
    """子 Tab: 牌组编辑。"""

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

        card_ids = [c.id for c in player.deck]
        name_map = load_name_map()
        self._editor = ListEditor(
            self,
            title=f"牌组 ({len(card_ids)} 张)",
            items=card_ids,
            preset_items=discovered_cards if discovered_cards else None,
            name_map=name_map,
            height=400,
        )
        self._editor.pack(fill="both", expand=True, padx=8, pady=8)

    def apply(self, data: CurrentRunData) -> None:
        if not data.players:
            return
        player = data.players[0]
        # 保留已有卡牌的 floor 信息，新卡牌使用已访问节点数
        existing = {c.id: c.floor_added_to_deck for c in player.deck}
        floor = len(data.visited_map_coords)
        new_deck: list[CardEntry] = []
        for card_id in self._editor.get_items():
            new_deck.append(CardEntry(
                id=card_id,
                floor_added_to_deck=existing.get(card_id, floor),
            ))
        player.deck = new_deck


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


class MapTab(ctk.CTkScrollableFrame):
    """子 Tab: 地图节点编辑。"""

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._type_vars: list[tuple[int, ctk.StringVar]] = []  # (point_index, var)

        act = data.acts[0] if data.acts else None
        if act is None:
            ctk.CTkLabel(self, text="无地图数据").pack(pady=20)
            return

        # 已访问坐标集合
        visited = {(c.col, c.row) for c in data.visited_map_coords}

        # 用中文显示地图节点类型
        display_types = [f"{_MAP_TYPE_ZH.get(t, t)}" for t in MAP_POINT_TYPES]
        # 显示名 -> 内部值 的映射
        self._display_to_type = dict(zip(display_types, MAP_POINT_TYPES))
        self._type_to_display = dict(zip(MAP_POINT_TYPES, display_types))

        ctk.CTkLabel(
            self, text=f"地图节点 ({len(act.saved_map.points)} 个)",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 8))

        for i, point in enumerate(act.saved_map.points):
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)

            coord_text = f"({point.coord.col}, {point.coord.row})"
            is_visited = (point.coord.col, point.coord.row) in visited
            can_edit = point.can_modify and not is_visited

            # 坐标标签
            label_color = "gray50" if is_visited else "white"
            ctk.CTkLabel(
                row, text=coord_text, width=80, anchor="w", text_color=label_color,
            ).pack(side="left")

            # 类型选择（用中文显示）
            current_display = self._type_to_display.get(point.type, point.type)
            var = ctk.StringVar(value=current_display)
            menu = ctk.CTkOptionMenu(
                row, variable=var, values=display_types, width=140,
            )
            if not can_edit:
                menu.configure(state="disabled")
            menu.pack(side="left", padx=(8, 0))

            # 状态标识
            if is_visited:
                ctk.CTkLabel(row, text="[已访问]", text_color="gray50").pack(side="left", padx=8)
            elif not point.can_modify:
                ctk.CTkLabel(row, text="[锁定]", text_color="gray50").pack(side="left", padx=8)

            self._type_vars.append((i, var))

    def apply(self, data: CurrentRunData) -> None:
        if not data.acts:
            return
        points = data.acts[0].saved_map.points
        for idx, var in self._type_vars:
            if idx < len(points):
                display_val = var.get()
                points[idx].type = self._display_to_type.get(display_val, display_val)


class EncounterPoolTab(ctk.CTkScrollableFrame):
    """子 Tab: 遭遇池 & 事件池编辑。"""

    def __init__(
        self,
        master: Any,
        data: CurrentRunData,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)

        act = data.acts[0] if data.acts else None
        if act is None:
            ctk.CTkLabel(self, text="无数据").pack(pady=20)
            return

        rooms = act.rooms

        # 访问计数（只读）
        info = ctk.CTkFrame(self)
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
        boss_display = get_display_name(rooms.boss_id)
        ctk.CTkLabel(
            self, text=f"Boss: {boss_display}", font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=16, pady=(8, 4))

        name_map = load_name_map()

        # 精英遭遇池
        self._elite_editor = ListEditor(
            self, title="精英遭遇池", items=rooms.elite_encounter_ids,
            name_map=name_map, height=120,
        )
        self._elite_editor.pack(fill="x", padx=8, pady=4)

        # 普通遭遇池
        self._normal_editor = ListEditor(
            self, title="普通遭遇池", items=rooms.normal_encounter_ids,
            name_map=name_map, height=120,
        )
        self._normal_editor.pack(fill="x", padx=8, pady=4)

        # 事件池
        self._event_editor = ListEditor(
            self, title="事件池", items=rooms.event_ids,
            name_map=name_map, height=120,
        )
        self._event_editor.pack(fill="x", padx=8, pady=4)

    def apply(self, data: CurrentRunData) -> None:
        if not data.acts:
            return
        rooms = data.acts[0].rooms
        rooms.elite_encounter_ids = self._elite_editor.get_items()
        rooms.normal_encounter_ids = self._normal_editor.get_items()
        rooms.event_ids = self._event_editor.get_items()


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
