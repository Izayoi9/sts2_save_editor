"""Pydantic 数据模型，映射 STS2 存档 JSON 结构。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CharacterStats(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    best_win_streak: int = 0
    current_streak: int = 0
    fastest_win_time: int = -1
    max_ascension: int = 0
    playtime: int = 0
    preferred_ascension: int = 0
    total_losses: int = 0
    total_wins: int = 0


class Epoch(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    obtain_date: int = 0
    state: str = "revealed"


class ProgressData(BaseModel):
    """顶层存档模型。extra='allow' 确保未显式定义的字段（如 card_stats 等大数组）在读写时不丢失。"""

    model_config = ConfigDict(extra="allow")

    # 角色统计
    character_stats: list[CharacterStats] = []

    # 全局数值
    architect_damage: int = 0
    current_score: int = 0
    floors_climbed: int = 0
    max_multiplayer_ascension: int = 0
    preferred_multiplayer_ascension: int = 0
    total_playtime: int = 0
    test_subject_kills: int = 0
    wongo_points: int = 0

    # Epoch 解锁
    epochs: list[Epoch] = []

    # 元数据
    schema_version: int = 0
    unique_id: str = ""
    enable_ftues: bool = True
    pending_character_unlock: str = "NONE.NONE"

    # 已发现内容（保持原样即可，不做编辑）
    discovered_acts: list[str] = []
    discovered_cards: list[str] = []
    discovered_events: list[str] = []
    discovered_potions: list[str] = []
    discovered_relics: list[str] = []
    ftue_completed: list[str] = []
    unlocked_achievements: list[str] = []


# 角色 ID 到中文名的映射
CHARACTER_NAMES: dict[str, str] = {
    "CHARACTER.IRONCLAD": "铁甲战士",
    "CHARACTER.SILENT": "静默猎手",
    "CHARACTER.DEFECT": "故障机器人",
    "CHARACTER.REGENT": "储君",
    "CHARACTER.NECROBINDER": "亡灵契约师",
    "CHARACTER.RANDOM_CHARACTER": "随机角色",
}


# ── current_run.save 数据模型 ──────────────────────────────────────────


class Enchantment(BaseModel):
    """卡牌附魔数据。"""
    model_config = ConfigDict(extra="allow")

    id: str = ""
    amount: int = 1


class CardEntry(BaseModel):
    """牌组中的一张卡牌。"""
    model_config = ConfigDict(extra="allow")

    id: str
    floor_added_to_deck: int = 1
    current_upgrade_level: int = 0
    enchantment: Enchantment | None = None


class RelicEntry(BaseModel):
    """玩家持有的一个遗物。"""
    model_config = ConfigDict(extra="allow")

    id: str
    floor_added_to_deck: int = 1


class MapCoord(BaseModel):
    col: int
    row: int


class MapPoint(BaseModel):
    """地图上的一个节点。"""
    model_config = ConfigDict(extra="allow")

    coord: MapCoord
    children: list[MapCoord] = []
    type: str = "unknown"
    can_modify: bool = True


class SavedMap(BaseModel):
    """一个 Act 的完整地图。"""
    model_config = ConfigDict(extra="allow")

    boss: MapPoint | None = None
    height: int = 16
    width: int = 7
    points: list[MapPoint] = []


class PlayerOdds(BaseModel):
    """玩家级别的概率值。"""
    model_config = ConfigDict(extra="allow")

    card_rarity_odds_value: float = 0.0
    potion_reward_odds_value: float = 0.4


class GlobalOdds(BaseModel):
    """全局问号房概率分配。"""
    model_config = ConfigDict(extra="allow")

    unknown_map_point_elite_odds_value: float = -1.0
    unknown_map_point_monster_odds_value: float = 0.1
    unknown_map_point_shop_odds_value: float = 0.03
    unknown_map_point_treasure_odds_value: float = 0.02


class RngCounters(BaseModel):
    """全局 RNG 计数器。"""
    model_config = ConfigDict(extra="allow")

    up_front: int = 0
    shuffle: int = 0
    unknown_map_point: int = 0
    combat_card_generation: int = 0
    combat_potion_generation: int = 0
    combat_card_selection: int = 0
    combat_energy_costs: int = 0
    combat_targets: int = 0
    monster_ai: int = 0
    niche: int = 0
    combat_orbs: int = 0
    treasure_room_relics: int = 0


class GlobalRng(BaseModel):
    """全局 RNG（种子为字符串）。"""
    model_config = ConfigDict(extra="allow")

    counters: RngCounters = Field(default_factory=RngCounters)
    seed: str = ""


class PlayerRngCounters(BaseModel):
    """玩家级别 RNG 计数器。"""
    model_config = ConfigDict(extra="allow")

    rewards: int = 0
    shops: int = 0
    transformations: int = 0


class PlayerRng(BaseModel):
    """玩家级别 RNG（种子为数字）。"""
    model_config = ConfigDict(extra="allow")

    counters: PlayerRngCounters = Field(default_factory=PlayerRngCounters)
    seed: int = 0


class ActRooms(BaseModel):
    """一个 Act 中的房间/遭遇配置。"""
    model_config = ConfigDict(extra="allow")

    ancient_id: str = ""
    boss_id: str = ""
    boss_encounters_visited: int = 0
    elite_encounter_ids: list[str] = []
    elite_encounters_visited: int = 0
    event_ids: list[str] = []
    events_visited: int = 0
    normal_encounter_ids: list[str] = []
    normal_encounters_visited: int = 0
    second_boss_id: str | None = None


class Act(BaseModel):
    """一个 Act 的完整数据。"""
    model_config = ConfigDict(extra="allow")

    id: str = ""
    rooms: ActRooms = Field(default_factory=ActRooms)
    saved_map: SavedMap = Field(default_factory=SavedMap)


class RunPlayer(BaseModel):
    """current_run 中的玩家数据。"""
    model_config = ConfigDict(extra="allow")

    character_id: str = ""
    current_hp: int = 0
    max_hp: int = 0
    gold: int = 0
    max_energy: int = 3
    max_potion_slot_count: int = 2
    base_orb_slot_count: int = 0
    net_id: int = 1
    deck: list[CardEntry] = []
    relics: list[RelicEntry] = []
    odds: PlayerOdds = Field(default_factory=PlayerOdds)
    rng: PlayerRng = Field(default_factory=PlayerRng)


class CurrentRunData(BaseModel):
    """current_run.save 顶层模型。"""
    model_config = ConfigDict(extra="allow")

    acts: list[Act] = []
    players: list[RunPlayer] = []
    odds: GlobalOdds = Field(default_factory=GlobalOdds)
    rng: GlobalRng = Field(default_factory=GlobalRng)
    visited_map_coords: list[MapCoord] = []
    run_time: int = 0
    save_time: int = 0
    start_time: int = 0
    win_time: int = 0
    schema_version: int = 0
    platform_type: str = "steam"


# 地图节点类型选项
MAP_POINT_TYPES: list[str] = [
    "monster",
    "elite",
    "rest_site",
    "treasure",
    "unknown",
    "shop",
    "event",
    "boss",
]
