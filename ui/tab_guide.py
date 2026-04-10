"""使用说明页面。"""

from typing import Any

import customtkinter as ctk


_GUIDE_TEXT = """\
==================== STS2 存档修改器 使用说明 ====================

# 基本操作

1. 启动后自动扫描存档目录，选择要编辑的 profile
2. 也可以点击「加载存档」手动选择 progress.save 文件
3. 修改完成后点击「保存修改」写入存档
4. 每次保存会自动创建 .bak 备份文件，可用于恢复

# 存档路径

  %APPDATA%/SlayTheSpire2/steam/{Steam ID}/profile{1,2,3}/saves/
  - progress.save        全局进度（角色统计、解锁等）
  - current_run.save     当前对局（仅在对局进行中存在）

  两个文件各有一个 .backup 副本，游戏要求两者内容一致，
  修改器会自动同步写入。

==================== 功能说明 ====================

# 角色编辑

  修改各角色的进阶难度、胜负场次、连胜记录、最快通关时间等。
  - 进阶难度范围：0-10（目前版本上限）
  - 最快获胜时间设为 -1 表示尚未通关

# 全局统计

  修改总游戏时间、攀爬层数、多人模式进阶等全局数据。

# 对局编辑（仅当前有进行中的对局时可用）

  ## 玩家状态
    - HP / 最大 HP / 金币 / 最大能量 / 药水栏位
    - 稀有卡概率偏移：负值越大，下次出稀有卡的概率越高
      （每次跳过卡牌奖励会 +0.03 左右）
    - 药水掉落概率：每场战斗不掉药水时自动递增

  ## 牌组编辑
    - 可添加/删除卡牌
    - 添加时从已发现卡牌中搜索，支持中文名和 ID
    - 同一张卡可以添加多次（游戏允许重复）
    - 卡牌升级：点击「升级」按钮可将卡牌升级（等同于火堆锻造），
      升级后的卡牌名称显示为绿色并带有"+"后缀（如"王国资产+"）
    - 卡牌附魔：点击「附魔」按钮可为卡牌添加附魔效果，
      附魔后卡牌旁会显示紫色附魔名称标签
    - 注意：部分附魔的功能需要依赖对应的遗物才能生效，
      例如「克隆」附魔需要持有遗物「佩尔的增生组织」才能在火堆处触发克隆，请悉知

  ## 遗物编辑
    - 与牌组编辑类似
    - 注意：某些遗物有触发条件，单纯添加 ID 不一定能生效

  ## 地图编辑
    - 地图以可视化树形网格展示，节点按层级和列位置排列
    - 不同节点类型用不同颜色区分，连线显示节点间的路径关系
    - 已访问路径以蓝色高亮显示，当前所在层有蓝色指示条标记
    - 点击未访问且未锁定的节点可弹出菜单修改其类型
    - 节点类型：怪物 / 精英 / 休息点 / 宝箱 / 未知 / 商店 / 事件
    - 已访问的节点（灰色）和锁定节点无法修改
    - Boss 节点不建议修改
    - 鼠标悬停在节点上可查看坐标和类型信息

  ## 遭遇池 & 事件池
    - 精英/普通/事件三个池子分别管理
    - 池子是预洗好的队列，不是去重集合
    - 重复项是正常的！多个相同遭遇代表权重分配
    - 删除过多会导致队列过短，指针越界后行为未知（可能循环或崩溃）
    - 建议：只做替换（删一个加一个），不要大幅缩短池子

  ## 概率 & RNG
    - 问号房概率：控制未知房间随机到各类型的概率
      - 精英房概率 -1 表示不会从问号房随机到精英
    - RNG 计数器：控制随机数序列的偏移位置
      - 修改 rewards 计数器可以改变下一次的卡牌/金币奖励
      - 修改 shuffle 会影响战斗中的洗牌顺序
      - 种子（seed）为只读，修改种子不会改变已生成的地图和遭遇池

# ID 图鉴

  查看所有卡牌、遗物、怪物、遭遇、事件的内部 ID 和中文名。
  支持搜索，可用于查找要添加的卡牌/遗物 ID。

==================== 注意事项 ====================

  - 修改前请确保游戏已完全退出，否则游戏可能覆盖你的修改
  - 每次保存会创建 .bak 备份，如果改坏了可以手动恢复
  - 恢复方法：将 .bak 文件重命名为 .save 和 .save.backup
  - 不建议修改 schema_version、seed 等底层字段
  - 对局存档 (current_run.save) 仅在对局进行中存在，
    通关或放弃后会被游戏删除
  - 修改存档可能导致后续成就无法解锁或存档损坏，请自行承担风险
  - 使用此软件后导致的任何损失均由使用者自行承担。
"""


class GuideTab(ctk.CTkFrame):
    """使用说明页面。"""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        # 标题
        ctk.CTkLabel(
            self, text="使用说明",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))

        # 可滚动文本区域
        text_frame = ctk.CTkScrollableFrame(self)
        text_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # 逐段渲染，# 开头的行作为标题样式
        font_normal = ctk.CTkFont(size=13, family="Consolas")
        font_heading = ctk.CTkFont(size=14, weight="bold")
        font_section = ctk.CTkFont(size=16, weight="bold")

        for line in _GUIDE_TEXT.strip().split("\n"):
            stripped = line.strip()

            if stripped.startswith("===="):
                # 分隔线 — 用空行代替
                ctk.CTkFrame(text_frame, height=2, fg_color="gray30").pack(
                    fill="x", padx=8, pady=8,
                )
            elif stripped.startswith("# "):
                ctk.CTkLabel(
                    text_frame, text=stripped[2:],
                    font=font_section, anchor="w",
                ).pack(anchor="w", padx=8, pady=(10, 2))
            elif stripped.startswith("## "):
                ctk.CTkLabel(
                    text_frame, text="  " + stripped[3:],
                    font=font_heading, anchor="w",
                ).pack(anchor="w", padx=8, pady=(6, 2))
            else:
                ctk.CTkLabel(
                    text_frame, text=line,
                    font=font_normal, anchor="w", text_color="gray80",
                    wraplength=700, justify="left",
                ).pack(anchor="w", padx=8, pady=0)
