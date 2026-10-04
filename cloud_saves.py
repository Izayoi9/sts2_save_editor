"""Steam 云存档检测：避免"改完一启动游戏就被云端覆盖回去"。

为什么需要这个
--------------
游戏启动时会执行 "Syncing cloud save files to the local save directory"，
其冲突处理并不总是"取更新的那份"。实测日志（本机 2026-10-04）：

    05:24:57  云端 current_run.save
    05:26:46  本地 current_run.save（游戏上次保存）
    05:27:36  修改器写入修改 ← 此时本地比云端新
    05:28:34  游戏启动：Copying ... from cloud to local
              （云端 05:26:46 / 本地 05:28:34）→ 本地被云端覆盖

玩家的直观感受是"修改器保存了但进游戏没生效"，实际是 Steam 云存档把本地
文件换回了旧版本。

本模块只做两件事：
  1. 定位本机当前账号的云端存档目录（按存档路径里的 SteamID 反推账号 ID）
  2. 在保存后对比"本地文件"与"云端副本"，若不一致就提示玩家如何处理

不修改任何 Steam 数据，也不尝试替玩家上传——那属于 Steam 客户端的职责，
从外部代劳有可能把云存档写坏。
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

STS2_APPID = "2868840"

# SteamID64 -> 账号 ID：账号 ID 是 SteamID64 的低 32 位
_STEAMID64_BASE = 76561197960265728


def account_id_from_steamid64(steam_id: str) -> str | None:
    """把存档路径里的 SteamID64 换算成 Steam 账号 ID（云目录用的就是它）。"""
    digits = re.sub(r"\D", "", steam_id or "")
    if len(digits) != 17:
        return None
    try:
        return str(int(digits) - _STEAMID64_BASE)
    except ValueError:
        return None


def _steam_roots() -> list[Path]:
    """可能的 Steam 安装根目录。"""
    roots: list[Path] = []
    try:
        import winreg

        for hive, key in (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        ):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    raw, _ = winreg.QueryValueEx(handle, "SteamPath")
                    if raw:
                        roots.append(Path(str(raw)))
            except OSError:
                continue
    except ImportError:
        pass
    for guess in ("C:/Program Files (x86)/Steam", "C:/Program Files/Steam",
                  "D:/Steam", "E:/Steam"):
        p = Path(guess)
        if p not in roots:
            roots.append(p)
    return [p for p in roots if p.is_dir()]


def find_cloud_save(local_save: Path) -> Path | None:
    """按本地存档路径反查它在 Steam 云目录里的对应副本。

    ``.../steam/<SteamID>/modded/profile1/saves/current_run.save``
    对应
    ``<Steam>/userdata/<账号ID>/2868840/remote/modded/profile1/saves/current_run.save``
    """
    parts = local_save.parts
    try:
        i = next(i for i, p in enumerate(parts) if p.lower() == "steam")
    except StopIteration:
        return None
    steam_id = parts[i + 1] if i + 1 < len(parts) else ""
    account_id = account_id_from_steamid64(steam_id)
    if not account_id:
        return None
    # SteamID 之后的相对路径（modded/profile1/saves/xxx.save）
    rel = Path(*parts[i + 2:])
    for root in _steam_roots():
        candidate = root / "userdata" / account_id / STS2_APPID / "remote" / rel
        if candidate.exists():
            return candidate
    return None


def cloud_state(local_save: Path) -> dict:
    """返回本地存档与其云端副本的对比结果（仅读取，不修改任何东西）。

    键：
      cloud_path       云端副本路径（找不到为 None）
      cloud_exists     云端副本是否存在
      differs          内容是否不同
      cloud_is_older   云端副本是否比本地旧（即会被云端覆盖回旧状态）
    """
    info = {"cloud_path": None, "cloud_exists": False,
            "differs": False, "cloud_is_older": False}
    try:
        cloud = find_cloud_save(local_save)
    except Exception as e:
        logger.info("云存档路径解析失败: %s", e)
        return info
    if cloud is None:
        return info

    info["cloud_path"] = cloud
    info["cloud_exists"] = True
    try:
        local_bytes = local_save.read_bytes()
        cloud_bytes = cloud.read_bytes()
        info["differs"] = local_bytes != cloud_bytes
        info["cloud_is_older"] = cloud.stat().st_mtime < local_save.stat().st_mtime
    except OSError as e:
        logger.info("读取云存档失败: %s", e)
    return info


def cloud_overwrite_warning(local_save: Path) -> str | None:
    """若存在"本地已改、云端仍是旧版"的情况，返回给玩家看的提示；否则 None。"""
    st = cloud_state(local_save)
    if not (st["cloud_exists"] and st["differs"]):
        return None
    rel = local_save.name
    return (
        f"⚠ 检测到 Steam 云存档同步冲突（{rel}）\n\n"
        f"本地文件已是你修改后的版本，但 Steam 云端的副本仍是旧版本：\n"
        f"  {st['cloud_path']}\n\n"
        f"游戏启动时会执行「云端 → 本地」的同步，可能把这次的修改覆盖回去，\n"
        f"表现为「修改器保存了，进游戏却没生效」。\n\n"
        f"建议按下面任一方式处理：\n"
        f"  1. 启动游戏前，在 Steam 中右键游戏 → 属性 → 通用，\n"
        f"     临时关闭「Steam 云」再进游戏（最稳妥）\n"
        f"  2. 先正常启动游戏一次，让它把本地改动同步到云端，再重开游戏验证；\n"
        f"     若发现没生效，说明被云端覆盖了，改回方式 1\n"
        f"  3. 确认要在本机独占使用该存档时，可删除云端副本：\n"
        f"     {st['cloud_path'].parent}\n"
        f"     （删除后 Steam 会在下次启动时以本地为准重新上传）\n\n"
        f"提示：修改存档前请务必完全退出游戏；本工具不会改动任何 Steam 数据。"
    )
