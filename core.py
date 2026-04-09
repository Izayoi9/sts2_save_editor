"""存档加载、备份、写入和路径扫描逻辑。"""

import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from models import CurrentRunData, ProgressData

logger = logging.getLogger(__name__)

# 已知兼容的 schema 版本
KNOWN_PROGRESS_VERSIONS = {21}
KNOWN_RUN_VERSIONS = {14}


@dataclass
class SaveProfile:
    """表示一个可用的存档 profile。"""

    path: Path
    steam_id: str
    profile_name: str  # "profile1", "profile2", "profile3"
    is_modded: bool
    has_current_run: bool = False

    @property
    def current_run_path(self) -> Path | None:
        """current_run.save 与 progress.save 在同一目录。"""
        run_path = self.path.parent / "current_run.save"
        return run_path if run_path.exists() else None

    @property
    def display_name(self) -> str:
        mod_tag = "[Mod] " if self.is_modded else ""
        return f"{mod_tag}{self.profile_name} (Steam: {self.steam_id})"


def get_save_root() -> Path:
    """获取 STS2 存档根目录。"""
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "SlayTheSpire2" / "steam"


def scan_profiles() -> list[SaveProfile]:
    """扫描所有可用的存档 profile。"""
    root = get_save_root()
    profiles: list[SaveProfile] = []

    if not root.exists():
        return profiles

    for steam_dir in root.iterdir():
        if not steam_dir.is_dir():
            continue
        steam_id = steam_dir.name

        # 扫描普通 profile
        for i in range(1, 4):
            profile_path = steam_dir / f"profile{i}" / "saves" / "progress.save"
            if profile_path.exists():
                run_exists = (profile_path.parent / "current_run.save").exists()
                profiles.append(SaveProfile(
                    path=profile_path,
                    steam_id=steam_id,
                    profile_name=f"profile{i}",
                    is_modded=False,
                    has_current_run=run_exists,
                ))

        # 扫描 modded profile
        for i in range(1, 4):
            profile_path = steam_dir / "modded" / f"profile{i}" / "saves" / "progress.save"
            if profile_path.exists():
                run_exists = (profile_path.parent / "current_run.save").exists()
                profiles.append(SaveProfile(
                    path=profile_path,
                    steam_id=steam_id,
                    profile_name=f"profile{i}",
                    is_modded=True,
                    has_current_run=run_exists,
                ))

    return profiles


# ── 通用存档读写 ──────────────────────────────────────────────────────


def _load_save(path: Path, model: type[BaseModel]) -> Any:
    """读取 JSON 存档并用指定模型解析。"""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    return model.model_validate(data)


def _save_file(data: BaseModel, path: Path) -> None:
    """写入存档，同时写入 .save 和 .save.backup，创建 .bak 用户备份。"""
    if path.exists():
        user_backup = path.with_suffix(".save.bak")
        shutil.copy2(path, user_backup)

    json_data = data.model_dump(mode="json")
    text = json.dumps(json_data, indent=2, ensure_ascii=False)

    path.write_text(text, encoding="utf-8")
    game_backup = path.with_suffix(".save.backup")
    game_backup.write_text(text, encoding="utf-8")


def load_progress(path: Path) -> ProgressData:
    """读取并解析 progress.save。"""
    return _load_save(path, ProgressData)


def save_progress(data: ProgressData, path: Path) -> None:
    """写入 progress.save。"""
    _save_file(data, path)


def load_current_run(path: Path) -> CurrentRunData:
    """读取并解析 current_run.save。"""
    return _load_save(path, CurrentRunData)


def save_current_run(data: CurrentRunData, path: Path) -> None:
    """写入 current_run.save。"""
    _save_file(data, path)


# ── Schema 版本检查 ───────────────────────────────────────────────────


def check_schema_version(data: ProgressData) -> str | None:
    """检查 schema 版本，返回警告信息或 None。"""
    if data.schema_version not in KNOWN_PROGRESS_VERSIONS:
        return (
            f"存档 schema 版本 {data.schema_version} 不在已知兼容列表 {KNOWN_PROGRESS_VERSIONS} 中，"
            f"修改后可能导致存档不兼容。"
        )
    return None


def check_run_schema_version(data: CurrentRunData) -> str | None:
    """检查 current_run schema 版本。"""
    if data.schema_version not in KNOWN_RUN_VERSIONS:
        return (
            f"对局存档 schema 版本 {data.schema_version} 不在已知兼容列表 {KNOWN_RUN_VERSIONS} 中，"
            f"修改后可能导致存档不兼容。"
        )
    return None


# ── discovered IDs ────────────────────────────────────────────────────


def get_discovered_ids(progress_path: Path) -> tuple[list[str], list[str]]:
    """从 progress.save 提取 discovered_cards 和 discovered_relics，用作 ID 选择列表。"""
    try:
        text = progress_path.read_text(encoding="utf-8")
        data = json.loads(text)
        cards = sorted(data.get("discovered_cards", []))
        relics = sorted(data.get("discovered_relics", []))
        return cards, relics
    except Exception as e:
        logger.warning("无法从 %s 读取 discovered IDs: %s", progress_path, e)
        return [], []


# ── 中文名称映射 ──────────────────────────────────────────────────────

_name_map: dict[str, str] = {}
_name_map_loaded: bool = False


def load_name_map() -> dict[str, str]:
    """加载 id_names_zh.json 名称映射表，懒加载 + 缓存。加载失败允许下次重试。"""
    global _name_map, _name_map_loaded
    if _name_map_loaded:
        return _name_map

    json_path = Path(__file__).parent / "id_names_zh.json"
    try:
        text = json_path.read_text(encoding="utf-8")
        _name_map = json.loads(text)
        _name_map_loaded = True
    except Exception as e:
        logger.warning("无法加载名称映射 %s: %s", json_path, e)
    return _name_map


def get_display_name(game_id: str) -> str:
    """将游戏 ID 转为 '中文名 (ID)' 格式，找不到则原样返回。"""
    zh_name = load_name_map().get(game_id)
    if zh_name:
        return f"{zh_name} ({game_id})"
    return game_id


def get_zh_name(game_id: str) -> str:
    """仅返回中文名，找不到则返回 ID。"""
    return load_name_map().get(game_id, game_id)
