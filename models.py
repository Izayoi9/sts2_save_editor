"""Pydantic 数据模型，映射 STS2 存档 JSON 结构。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CharacterStats(BaseModel):
    """单个角色的累计统计。

    `badges` 并非原版字段：装了成就/徽章类 Mod 的档会在每个角色上多出
    这一项。这里显式声明（类型为 list，内容原样透传），既保证读写不丢，
    也让写出的键序与游戏/Mod 一致。
    """

    model_config = ConfigDict(extra="allow")

    badges: list = Field(default_factory=list)
    best_win_streak: int = 0
    current_streak: int = 0
    fastest_win_time: int = -1
    id: str
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


class FightStats(BaseModel):
    """某角色在某场遭遇/某个敌人上的战绩（schema 21 新增）。"""

    model_config = ConfigDict(extra="allow")

    character: str = ""
    losses: int = 0
    wins: int = 0


class AncientStats(BaseModel):
    """古代事件战绩：按古代 ID 汇总各角色胜负（schema 21 新增）。"""

    model_config = ConfigDict(extra="allow")

    ancient_id: str = ""
    character_stats: list[FightStats] = []


class EncounterStats(BaseModel):
    """遭遇战绩（schema 21 新增）。"""

    model_config = ConfigDict(extra="allow")

    encounter_id: str = ""
    fight_stats: list[FightStats] = []


class EnemyStats(BaseModel):
    """怪物战绩（schema 21 新增）。"""

    model_config = ConfigDict(extra="allow")

    enemy_id: str = ""
    fight_stats: list[FightStats] = []


class CardStats(BaseModel):
    """单张卡牌的累计战绩（progress.save 中的 card_stats 数组）。"""

    model_config = ConfigDict(extra="allow")

    id: str = ""
    times_lost: int = 0
    times_picked: int = 0
    times_skipped: int = 0
    times_won: int = 0


class ProgressData(BaseModel):
    """顶层存档模型。extra='allow' 确保未显式定义的字段（如 card_stats 等大数组）在读写时不丢失。

    字段声明顺序刻意与游戏写出的键序（字母序）一致，这样写回存档时
    键序与游戏自身产生的文件相同，便于用备份做逐行比对。
    """

    model_config = ConfigDict(extra="allow")

    # 古代 / 卡牌 / 角色 / 遭遇 / 怪物战绩
    ancient_stats: list[AncientStats] = []
    architect_damage: int = 0
    card_stats: list[CardStats] = []
    character_stats: list[CharacterStats] = []
    current_score: int = 0
    discovered_acts: list[str] = []
    discovered_cards: list[str] = []
    discovered_events: list[str] = []
    discovered_potions: list[str] = []
    discovered_relics: list[str] = []
    enable_ftues: bool = True
    encounter_stats: list[EncounterStats] = []
    enemy_stats: list[EnemyStats] = []
    epochs: list[Epoch] = []
    floors_climbed: int = 0
    ftue_completed: list[str] = []
    max_multiplayer_ascension: int = 0
    pending_character_unlock: str = "NONE.NONE"
    preferred_multiplayer_ascension: int = 0
    schema_version: int = 0
    test_subject_kills: int = 0
    total_playtime: int = 0
    total_unlocks: int = 0
    unique_id: str = ""
    unlocked_achievements: list[str] = []
    wongo_points: int = 0


# 说明：角色显示名统一由 core.get_character_name() 解析（优先译名表，
# Mod 角色回退为从 ID 推导的简短名）。此前这里另有一份硬编码的
# CHARACTER_NAMES，因其只覆盖 6 个原版角色、Mod 角色会直接显示超长内部 ID，
# 且与 id_names_zh.json 重复维护，已移除。


# ── current_run.save 数据模型 ──────────────────────────────────────────


class Enchantment(BaseModel):
    """卡牌附魔数据。"""
    model_config = ConfigDict(extra="allow")

    id: str = ""
    amount: int = 1


class CardEntry(BaseModel):
    """牌组中的一张卡牌。"""
    model_config = ConfigDict(extra="allow")

    current_upgrade_level: int = 0
    enchantment: Enchantment | None = None
    floor_added_to_deck: int = 1
    id: str


class RelicEntry(BaseModel):
    """玩家持有的一个遗物。"""
    model_config = ConfigDict(extra="allow")

    floor_added_to_deck: int = 1
    id: str


class PotionEntry(BaseModel):
    """玩家持有的一个药水（进度存档与历史对局记录中出现）。"""
    model_config = ConfigDict(extra="allow")

    id: str
    slot_index: int = 0


class MapCoord(BaseModel):
    col: int
    row: int


class MapPoint(BaseModel):
    """地图上的一个节点。

    注意：存档中 `can_modify` 是**可选**字段，游戏只在值为 true 时写入
    （60 个普通节点中 50 个带该键，6 个宝箱节点不带）。因此默认值必须为
    False 并配合 model_dump(exclude_unset=True)，否则会把"不可修改"的
    节点写成可修改，反而破坏存档语义。
    """
    model_config = ConfigDict(extra="allow")

    can_modify: bool = False
    children: list[MapCoord] = []
    coord: MapCoord
    type: str = "unknown"


class SavedMap(BaseModel):
    """一个 Act 的完整地图。

    `boss` 节点没有 children；`start` 是起点古代事件节点；
    `start_coords` 是起点可选的下一层坐标。三者都可能缺失。
    """
    model_config = ConfigDict(extra="allow")

    boss: MapPoint | None = None
    height: int = 16
    points: list[MapPoint] = []
    start: MapPoint | None = None
    start_coords: list[MapCoord] = []
    width: int = 7


class PlayerOdds(BaseModel):
    """玩家级别的概率值。"""
    model_config = ConfigDict(extra="allow")

    card_rarity_odds_value: float = 0.0
    potion_reward_odds_value: float = 0.4


class GlobalOdds(BaseModel):
    """全局问号房概率分配。

    注意类型用 ``float | int``：游戏会把默认值写成整数 ``-1``（表示
    "不会随机到精英"），若声明为 float，Pydantic 会规范化成 ``-1.0``，
    虽然数值等价，但会让写出的存档与游戏自身格式产生无谓差异。
    """
    model_config = ConfigDict(extra="allow")

    unknown_map_point_elite_odds_value: float | int = -1.0
    unknown_map_point_monster_odds_value: float | int = 0.1
    unknown_map_point_shop_odds_value: float | int = 0.03
    unknown_map_point_treasure_odds_value: float | int = 0.02


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
    boss_encounters_visited: int = 0
    boss_id: str = ""
    elite_encounter_ids: list[str] = []
    elite_encounters_visited: int = 0
    event_ids: list[str] = []
    events_visited: int = 0
    normal_encounter_ids: list[str] = []
    normal_encounters_visited: int = 0
    second_boss_id: str | None = None


class Act(BaseModel):
    """一个 Act 的完整数据。

    重要：只有**当前** Act 才有 `saved_map`。存档中已完成/未进入的 Act
    只有 `id` 与 `rooms`（例如 3 个 act 里仅 acts[0] 带地图）。因此这里
    必须是 ``SavedMap | None``，否则 UI 会渲染出一张并不存在的空地图，
    且容易在保存时把默认地图写进存档。
    """
    model_config = ConfigDict(extra="allow")

    id: str = ""
    rooms: ActRooms = Field(default_factory=ActRooms)
    saved_map: SavedMap | None = None


class RunPlayer(BaseModel):
    """current_run 中的玩家数据。

    schema 16 新增：extra_fields、relic_grab_bag、unlock_state、potions。
    """
    model_config = ConfigDict(extra="allow")

    base_orb_slot_count: int = 0
    character_id: str = ""
    current_hp: int = 0
    deck: list[CardEntry] = []
    extra_fields: dict = Field(default_factory=dict)
    gold: int = 0
    max_energy: int = 3
    max_hp: int = 0
    max_potion_slot_count: int = 2
    net_id: int = 1
    odds: PlayerOdds = Field(default_factory=PlayerOdds)
    potions: list[PotionEntry] = []
    relic_grab_bag: dict = Field(default_factory=dict)
    relics: list[RelicEntry] = []
    rng: PlayerRng = Field(default_factory=PlayerRng)
    unlock_state: dict = Field(default_factory=dict)


class CurrentRunData(BaseModel):
    """current_run.save 顶层模型（schema 16）。

    schema 14 → 16 新增顶层字段：
        ascension, current_act_index, extra_fields, game_mode, map_drawings,
        map_point_history, modifiers, num_reloads, pre_finished_room,
        shared_relic_grab_bag
    其中 map_point_history / modifiers / shared_relic_grab_bag 体量大且结构
    复杂，这里以 dict / list 原样透传，不做界面编辑。
    """
    model_config = ConfigDict(extra="allow")

    acts: list[Act] = []
    ascension: int = 0
    current_act_index: int = 0
    extra_fields: dict = Field(default_factory=dict)
    game_mode: str = "standard"
    map_drawings: str = ""
    map_point_history: list = Field(default_factory=list)
    modifiers: list = Field(default_factory=list)
    num_reloads: int = 0
    odds: GlobalOdds = Field(default_factory=GlobalOdds)
    platform_type: str = "steam"
    players: list[RunPlayer] = []
    pre_finished_room: dict = Field(default_factory=dict)
    rng: GlobalRng = Field(default_factory=GlobalRng)
    run_time: int = 0
    save_time: int = 0
    schema_version: int = 0
    shared_relic_grab_bag: dict = Field(default_factory=dict)
    start_time: int = 0
    visited_map_coords: list[MapCoord] = []
    win_time: int = 0


# 地图节点类型选项
# 说明：游戏地图中还会出现 "ancient"（古代事件节点，即 saved_map.start）。
# 该类型在 v1.3.0 中未定义，导致起点节点以未知类型的灰色显示。
MAP_POINT_TYPES: list[str] = [
    "ancient",
    "monster",
    "elite",
    "rest_site",
    "treasure",
    "unknown",
    "shop",
    "event",
    "boss",
]
