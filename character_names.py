"""角色显示名解析，含 Mod 角色的**动态**名称提取。

为什么不能硬编码
----------------
Mod 角色不会进入游戏自带的 ``characters`` 本地化表——游戏日志里可以反复
看到它自己的回退：

    [WARN] [BaseLib] GetRawText: Key 'LEX_NINJA2_CHARACTER_LEX_NINJA2'
           not found in table 'characters'

于是游戏界面直接显示内部 ID。不同玩家装的 Mod 完全不同，因此本模块不在
代码或译名表里写死任何 Mod 角色译名，而是**在读取存档时扫描该玩家本机
已安装的 Mod 资源包**，从 Mod 作者自带的简中本地化里取出角色名。

解析顺序（逐级回退，任何一级失败都不影响下一级）：

  1. ``id_names_zh.json``：仅原版角色，随工具发布、不含任何 Mod 条目
  2. 本机 Mod 资源包（本模块实时扫描，结果只写入本机缓存文件）
  3. 从角色 ID 反推的简短可读名（离线/Mod 已删除时的最后兜底）

第 2 步的结果**不会**写进 ``id_names_zh.json``：那会把"本机装了什么 Mod"
固化进随工具发布的文件里，等于换一种形式的硬编码。机器相关信息一律只进
``character_names_cache.json``（已在 .gitignore 中排除）。
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ── 路径 ──────────────────────────────────────────────────────────────

_TOOL_DIR = Path(__file__).parent
# 扫描结果缓存：与工具同目录，便于随工具一起拷贝；
# 这是一个机器相关的缓存文件，已在 .gitignore 中排除。
CACHE_PATH = _TOOL_DIR / "character_names_cache.json"

GAME_DIR_NAME = "Slay the Spire 2"
STS2_WORKSHOP_APPID = "2868840"          # Slay the Spire 2 的创意工坊 appid

# ── 角色 ID 形态 ──────────────────────────────────────────────────────

# 形如 CHARACTER.<模组前缀>_CHARACTER_<角色名>
MOD_CHARACTER_RE = re.compile(r"^([A-Z0-9_]+?)_CHARACTER_(.+)$")
# 形如 <ID>.title / <ID>.name / ... 后面紧跟一个字符串字面量。
# 直接用字节正则在 .pck 里搜索，避免解析 Godot 包索引（格式随版本变化）。
NAME_KEY_RE = re.compile(
    rb'"([A-Z0-9_]+)\.([A-Za-z]{3,24})"\s*:\s*"([^"\\\x00-\x1f]{1,60})"'
)

# 这些后缀是"角色名"的候选；按此顺序取第一个命中的。
# 其余后缀（description / aromaPrinciple / banter.* …）是长文本，一律排除。
NAME_KEY_PRIORITY = ("title", "name", "displayName", "characterName", "charName")

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# ── 缓存 ──────────────────────────────────────────────────────────────

# character_id -> {后缀: 值}
_scan_cache: dict[str, dict[str, str]] = {}
_cache_loaded = False
_scanned_this_run = False


def _load_cache() -> dict[str, dict[str, str]]:
    global _scan_cache, _cache_loaded
    if _cache_loaded:
        return _scan_cache
    _cache_loaded = True
    try:
        if CACHE_PATH.exists():
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _scan_cache = {
                    str(k): dict(v) for k, v in data.items() if isinstance(v, dict)
                }
    except Exception as e:  # 缓存损坏不应影响使用
        logger.warning("角色名缓存读取失败 %s: %s", CACHE_PATH, e)
        _scan_cache = {}
    return _scan_cache


def _save_cache() -> None:
    """尽量落盘；工具目录只读时静默跳过（内存缓存仍然有效）。"""
    try:
        CACHE_PATH.write_text(
            json.dumps(_load_cache(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception as e:
        logger.info("角色名缓存写入跳过（%s）：%s", CACHE_PATH, e)


def _best_name(entry: dict[str, str]) -> str | None:
    """按后缀优先级取一个名字。"""
    for suffix in NAME_KEY_PRIORITY:
        value = entry.get(suffix)
        if value:
            return value
    return None


def _merge_names(character_id: str, entry: dict[str, str]) -> str | None:
    """把新发现的候选后缀并进缓存；返回当前可用的最佳名字。"""
    cache = _load_cache()
    merged = cache.setdefault(character_id, {})
    changed = False
    for suffix, value in entry.items():
        # 优先保留已有的「更靠前」后缀，同后缀则新值覆盖（可能修了翻译）
        if merged.get(suffix) != value:
            merged[suffix] = value
            changed = True
    if changed:
        _save_cache()
    return _best_name(merged)


# ── 定位 Mod 资源包 ───────────────────────────────────────────────────


def _steam_root_from_registry() -> Path | None:
    """从注册表读 Steam 安装目录（读不到就返回 None）。"""
    try:
        import winreg  # 仅 Windows 可用
    except ImportError:
        return None
    for hive, key in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
    ):
        try:
            with winreg.OpenKey(hive, key) as handle:
                for value_name in ("SteamPath", "InstallPath"):
                    try:
                        raw, _ = winreg.QueryValueEx(handle, value_name)
                    except OSError:
                        continue
                    if raw:
                        return Path(str(raw))
        except OSError:
            continue
    return None


def _library_roots() -> list[Path]:
    """所有 Steam 库根目录（含默认位置兜底）。"""
    roots: list[Path] = []
    steam = _steam_root_from_registry()
    if steam:
        roots.append(steam)
    for guess in (
        Path("C:/Program Files (x86)/Steam"),
        Path("C:/Program Files/Steam"),
        Path("D:/Steam"),
        Path("E:/Steam"),
    ):
        if guess not in roots:
            roots.append(guess)

    # libraryfolders.vdf 里登记的其他库
    extra: list[Path] = []
    for base in list(roots):
        vdf = base / "steamapps" / "libraryfolders.vdf"
        try:
            if not vdf.is_file():
                continue
            text = vdf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r'"path"\s*"([^"]+)"', text):
            extra.append(Path(m.group(1).replace("\\\\", "\\")))
    for p in extra:
        if p not in roots:
            roots.append(p)
    return [p for p in roots if p.is_dir()]


def mod_resource_dirs() -> list[Path]:
    """可能存放 Mod 资源包的目录（不存在则跳过）。

    覆盖三种安装方式：
      * 游戏自带的 ``mods/`` 目录（本地/手动安装）
      * Steam 创意工坊内容目录
    """
    dirs: list[Path] = []
    for lib in _library_roots():
        game_mods = lib / "steamapps" / "common" / GAME_DIR_NAME / "mods"
        if game_mods.is_dir():
            dirs.append(game_mods)
        workshop = lib / "steamapps" / "workshop" / "content" / STS2_WORKSHOP_APPID
        if workshop.is_dir():
            dirs.append(workshop)
    return dirs


def _candidate_packs(dirs: list[Path]) -> list[Path]:
    """收集候选资源包。Mod 很小，但游戏本体包巨大，这里按名字排除掉。"""
    packs: list[Path] = []
    seen: set[Path] = set()
    for d in dirs:
        try:
            for p in d.rglob("*.pck"):
                if p in seen:
                    continue
                seen.add(p)
                # 游戏本体的包不用扫（原版角色走译名表）
                if p.name.lower().startswith("slaythespire"):
                    continue
                packs.append(p)
        except OSError:
            continue
    return packs


# ── 扫描资源包 ────────────────────────────────────────────────────────


def scan_pack_for_character_names(path: Path) -> dict[str, dict[str, str]]:
    """在单个 .pck 中找出「像角色名」的条目。

    返回 ``{角色ID: {后缀: 值}}``。只接受含中文的值，避免把同键的英文
    版本（如 "Lex Ninja"）也当成中文名。
    """
    found: dict[str, dict[str, str]] = {}
    chunk_size = 4 << 20
    overlap = 512
    tail = b""
    try:
        with path.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                data = tail + chunk
                for m in NAME_KEY_RE.finditer(data):
                    char_id = m.group(1).decode("ascii", "replace")
                    if "_CHARACTER_" not in char_id:
                        continue
                    suffix = m.group(2).decode("ascii", "replace")
                    if suffix not in NAME_KEY_PRIORITY:
                        continue
                    value = m.group(3).decode("utf-8", "replace")
                    if not _CJK_RE.search(value):
                        continue
                    # 去掉本地化里可能带的标记
                    value = re.sub(r"\[/?[^\]]{0,32}\]", "", value).strip()
                    if not value or len(value) > 40:
                        continue
                    found.setdefault(char_id, {})[suffix] = value
                tail = data[-overlap:] if len(data) > overlap else data
    except OSError as e:
        logger.warning("扫描 %s 失败: %s", path, e)
    return found


def scan_and_cache_mod_names(force: bool = False) -> int:
    """扫描本机 Mod 资源包并把角色名写入缓存；返回本次发现的名字数。

    同一进程内重复调用直接返回 0（已扫过），``force=True`` 可强制重扫。
    结果只进 ``character_names_cache.json``，不触碰 ``id_names_zh.json``。
    """
    global _scanned_this_run
    _load_cache()
    if _scanned_this_run and not force:
        return 0

    found_count = 0
    for pack in _candidate_packs(mod_resource_dirs()):
        try:
            for char_id, entry in scan_pack_for_character_names(pack).items():
                if _merge_names(char_id, entry):
                    found_count += 1
        except Exception as e:  # 单个包出错不应影响其他包
            logger.warning("处理 %s 时出错: %s", pack, e)

    _scanned_this_run = True
    if found_count:
        logger.info("从本机 Mod 资源包解析出 %d 个角色名", found_count)
    return found_count


# ── 对外入口 ──────────────────────────────────────────────────────────


def _readable_mod_name(raw: str) -> str:
    """把 Mod 角色 ID 的裸名转成简短可读文本（最后的兜底）。"""
    m = MOD_CHARACTER_RE.match(raw)
    if m:
        mod_prefix, char_part = m.group(1), m.group(2)
        # 模组前缀在角色名里重复时去掉一次：LEX_NINJA2 + LEX_NINJA2 -> LEX_NINJA2
        if char_part.startswith(mod_prefix + "_"):
            char_part = char_part[len(mod_prefix) + 1:]
    else:
        char_part = raw
    # 下划线分词转词首大写；仅 ASCII 才处理，避免破坏非英文名
    if char_part.isascii():
        words = [w for w in char_part.split("_") if w]
        if words and all(w.isalpha() for w in words):
            return " ".join(w.capitalize() for w in words)
    return char_part


def mod_character_names() -> dict[str, str]:
    """本机缓存里的 ``CHARACTER.<ID> -> 名称`` 映射（供 core 叠加到译名表）。"""
    out: dict[str, str] = {}
    for char_id, entry in _load_cache().items():
        name = _best_name(entry)
        if name:
            out[f"CHARACTER.{char_id}"] = name
    return out


def mod_character_name_count() -> int:
    """本机当前可用的 Mod 角色名数量（无论是否本次扫描得到）。"""
    return len(mod_character_names())


def resolve_character_name(character_id: str) -> str:
    """解析角色显示名，必要时触发一次本机 Mod 扫描。

    任何异常都回退到兜底名——角色名解析失败绝不能让整个界面起不来。
    """
    try:
        from core import load_name_map  # 延迟导入，避免循环依赖

        # 静态译名表 + 已缓存的本机 Mod 角色名
        zh = load_name_map().get(character_id)
        if zh:
            return zh

        # 缓存里还没有：实时扫描本机 Mod 资源包，再查一次
        if "_CHARACTER_" in character_id:
            scan_and_cache_mod_names()
            bare = character_id.split(".", 1)[1]
            name = _best_name(_load_cache().get(bare, {}))
            if name:
                return name

        raw = character_id.split(".", 1)[1] if "." in character_id else character_id
        return _readable_mod_name(raw)
    except Exception as e:  # 兜底：绝不抛异常
        logger.warning("解析角色名失败 %s: %s", character_id, e)
        raw = character_id.split(".", 1)[1] if "." in character_id else character_id
        return _readable_mod_name(raw)


def reset_cache() -> None:
    """清空内存状态（供测试或重新扫描使用）。"""
    global _scan_cache, _cache_loaded, _scanned_this_run
    _scan_cache = {}
    _cache_loaded = False
    _scanned_this_run = False
