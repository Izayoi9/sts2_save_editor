# STS2 存档修改器 ![浏览量](https://visitor-badge.laobi.icu/badge?page_id=Izayoi9/sts2_save_editor)

杀戮尖塔 2 (Slay the Spire 2) 存档修改器，提供图形化界面编辑游戏存档。

> ⚠️ 修改存档可能导致成就无法解锁或存档损坏，请在修改前确保游戏已退出，并妥善保管备份文件。使用本工具造成的任何后果由使用者自行承担。

## 功能一览

### 全局进度编辑 (progress.save)

- **角色编辑** — 修改各角色的进阶难度、胜负场次、连胜记录、最快通关时间
- **全局统计** — 修改总游戏时间、攀爬层数、多人模式进阶、总解锁数、旺购积分等
- **Epoch 解锁** — 勾选/取消各 Epoch 的解锁记录

### 对局编辑 (current_run.save)

- **玩家状态** — HP、金币、能量、药水栏位、稀有卡概率、药水掉率、持有药水
- **牌组编辑** — 搜索并添加/删除卡牌，支持中文名和 ID 搜索
- **遗物编辑** — 搜索并添加/删除遗物
- **地图编辑** — 修改未访问节点的类型（古代/怪物/精英/休息点/宝箱/商店/事件）
- **遭遇池 & 事件池** — 编辑精英、普通、事件三个队列的内容，支持按 Act 切换
- **概率 & RNG** — 调控问号房概率、RNG 计数器

### 工具

- **ID 图鉴** — 查看全部 1650 条卡牌/遗物/药水/遭遇/怪物/事件/附魔的内部 ID 与中文名对照表，支持搜索（仅含游戏本体内容，不含 Mod 条目）
- **使用说明** — 内置完整的功能说明和注意事项

## 截图

*（欢迎提交截图 PR）*

## 安装与使用

### 方式一：下载打包版（推荐）

前往 [Releases](../../releases) 下载 `STS2_SaveEditor_vX.Y.Z.zip`，**解压后双击文件夹里的 `STS2_SaveEditor.exe`** 即可运行。

> 注意：从 v1.4.5 起改为「文件夹 + zip」形式，不再是单个 exe。
>
> 原因：此前的单文件（onefile）版本每次启动都要先把内容解包到
> `%TEMP%\_MEIxxxxx`，这一步在部分机器上会被安全软件或系统策略拦下，
> 直接弹出「Could not create temporary directory!」而无法启动。
> 现改为单目录形式，依赖放在 exe 同级的 `_internal` 目录里，
> **启动时不创建任何临时目录**，从根上避免该问题，启动也更快。
>
> 解压后请保持文件夹结构完整（`STS2_SaveEditor.exe` 与 `_internal`
> 必须在同一层），不要只把 exe 单独拷出来。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/Izayoi9/sts2_save_editor.git
cd sts2_save_editor

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

**环境要求：** Python 3.10+

### 自行打包

```bash
pip install pyinstaller
python -m PyInstaller STS2_SaveEditor.spec --noconfirm --clean
# 产物在 dist/STS2_SaveEditor/ ，整个目录即为发布内容
```

### 如果出现「Windows 已保护你的电脑」

这是 **Microsoft Defender SmartScreen** 的提示，不是查毒结果，也不是程序损坏。出现的原因是：

- exe **没有数字签名**（代码签名证书需付费购买），Windows 无法确认发布者身份
- 文件刚下载自带「来自 Internet」标记，且下载量少、尚无信誉积累

**处理方法**（任选其一）：

1. 点弹窗里的「**更多信息**」，出现「**仍要运行**」按钮后点击即可
2. 先解除文件锁定：右键 zip → 属性 → 勾选「解除锁定」→ 确定，再解压
3. PowerShell 解除锁定：
   ```powershell
   Get-ChildItem -Recurse | Unblock-File
   ```

本项目是开源工具，代码全部公开可查，你也可以从源码运行（方式二）或自行打包，完全不依赖发布的可执行文件。

> 说明：v1.4.5 起已为 exe 补充版本资源（产品名、版本号、版权），使属性页不再显示为空白；这能降低误报面，但**无法完全免除** SmartScreen 提示——彻底消除只能靠购买代码签名证书。

## 存档位置

```
%APPDATA%/SlayTheSpire2/steam/{Steam ID}/
├── profile{1,2,3}/saves/           # 普通档
│   ├── progress.save               # 全局进度
│   ├── progress.save.backup        # 游戏自动备份
│   ├── current_run.save            # 当前对局（仅对局进行中存在）
│   ├── current_run.save.backup
│   └── history/*.run               # 已完成对局的历史记录（本工具不编辑）
├── modded/profile{1,2,3}/saves/    # Mod 档，结构同上
└── backup/                         # 游戏自身的额外备份副本
```

启动修改器后会自动扫描上述路径，也可以手动选择文件。

> 说明：`history/*.run` 是独立的历史对局格式（用 `players[].character` 而非
> `character_id`，另有 `win` / `was_abandoned` / `killed_by_encounter` 等字段），
> `schema_version` 与进行中的对局也不相同。本工具只读写 `progress.save` 与
> `current_run.save`，不会改动历史记录。

## 备份与恢复

- 每次保存修改时，修改器会自动创建 `.bak` 备份文件
- 如需恢复：将 `.bak` 文件重命名为 `.save`，同时复制一份为 `.save.backup`

## 技术栈

- [Python 3.10+](https://www.python.org/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — 现代化 GUI 框架
- [Pydantic](https://docs.pydantic.dev/) — 数据模型与校验
- [PyInstaller](https://pyinstaller.org/) — 打包为可执行文件

## 项目结构

```
sts2_save_editor/
├── main.py                  # 入口文件
├── core.py                  # 存档读写、备份、名称映射
├── models.py                # Pydantic 数据模型
├── id_names_zh.json         # 1400+ 条 ID ↔ 中文名映射表
├── requirements.txt         # Python 依赖
└── ui/
    ├── app.py               # 主窗口与导航
    ├── widgets.py            # 可复用控件
    ├── tab_character.py      # 角色编辑页
    ├── tab_stats.py          # 全局统计页
    ├── tab_run.py            # 对局编辑页（6 个子页）
    ├── tab_dictionary.py     # ID 图鉴页
    └── tab_guide.py          # 使用说明页
```

## 反馈与贡献

欢迎使用后提交 [Issues](../../issues) 进行反馈，包括但不限于：

- 🐛 Bug 报告
- 💡 功能建议
- 📝 翻译数据补充 / 纠错
- 🔧 Pull Request

## 更新日志

### v1.4.5

- **修复启动报错 `Could not create temporary directory!`**：打包方式由单文件（onefile）改为**单目录（onedir）**。

  单文件版把全部依赖压进一个 exe，每次启动都要先解包到 `%TEMP%\_MEIxxxxx`；这一步在部分机器上会被安全软件或系统策略拦下，程序直接无法启动。改为单目录后，依赖放在 exe 同级的 `_internal` 目录，**启动时不创建任何临时目录**，从根上避免该问题，启动也更快、被杀软误报的概率更低。

  **发布形式随之变化**：Release 资产从单个 `STS2_SaveEditor.exe` 变为 `STS2_SaveEditor_vX.Y.Z.zip`，解压后双击文件夹内的 exe 运行。注意 `STS2_SaveEditor.exe` 与 `_internal` 必须保持在同一层，不能只把 exe 单独拷出来。

- **补充 exe 版本资源**：此前 exe 的属性页里公司名/产品名/版本号全为空，Windows 只能显示「未知发布者」，会加重 Microsoft Defender SmartScreen 的拦截倾向。现在打包时会自动读取 `__version__.py` 生成版本资源（产品名、版本号、版权等），与程序版本号始终一致。`STS2_SaveEditor.spec` 已相应改写为 EXE + COLLECT 结构。

### v1.4.0

**适配游戏更新后的存档结构。**

- **对局存档 schema 14 → 16**：`current_run.save` 的 `schema_version` 已升到 16，旧版会误报"版本不兼容"。现在识别 14/15/16，并补全了新增字段：`ascension`、`game_mode`、`current_act_index`、`modifiers`、`map_point_history`、`pre_finished_room`、`shared_relic_grab_bag`、`map_drawings`、`num_reloads`、`extra_fields`
- **进度存档新增统计**：补全 `ancient_stats`（古代战绩）、`encounter_stats`（遭遇战绩）、`enemy_stats`（怪物战绩）、`total_unlocks`、`card_stats`；全局统计页新增总解锁数、旺购积分、当前分数与战绩概览
- **Epoch 解锁编辑**：新增 Epoch 勾选列表，可查看与调整解锁记录
- **药水编辑**：玩家状态页新增药水增删，槽位按顺序自动分配
- **多 Act 支持**：遭遇池/事件池与地图不再只读取第一个 Act。游戏会同时保存 3 个 Act，但只有当前 Act 带 `saved_map`；现在按 Act 切换编辑，且不会给没有地图的 Act 注入空白地图
- **新增"古代"节点类型**：地图起点为 `type: "ancient"`（`saved_map.start`），v1.3.0 未定义该类型，会显示成未知的灰色节点；现在有独立配色与原生的"起点"标记
- **修复存档污染缺陷**（重要）：
  - 地图节点的 `can_modify` 在存档中是**可选**字段，游戏只在为 `true` 时写入。旧版默认值为 `True` 且全量写回，会把游戏标记为"不可修改"的宝箱节点改成可修改，并给所有节点补上该键
  - 旧版会给 `players[].deck[]` 的每张牌注入存档中并不存在的 `current_upgrade_level` 与 `enchantment` 字段
  - 旧版会给没有地图的 Act 注入一份默认 `saved_map`
  - 旧版会把"最快获胜时间 = -1（尚未通关）"写成 0 秒
  - 现在写出使用 `model_dump(exclude_unset=True)`：只写回原本存在或本次确实编辑过的字段
- **写入策略改进**：改为「先写临时文件再替换」的原子写入，并先写 `.save.backup` 再写主文件，缩小两者不一致的时间窗口
- **字段顺序对齐游戏**：模型字段声明顺序与游戏写出的字母序一致，写回的存档可用备份直接逐行比对
- **译名扩充**：`id_names_zh.json` 从 1427 条扩充到 1650 条，补上缺失的 64 条药水、古代事件（特兹卡塔拉/佩尔/瓦库/欧洛巴斯/达弗/坦克斯/诺奴佩普）、3 条千足虫节点等；译名从游戏本体 `SlayTheSpire2.pck` 内的简中本地化提取，非人工翻译
- **修正**：`CHARACTER.RANDOM_CHARACTER` 的游戏内显示名为「随机」，此前误作「随机角色」

### v1.4.1

- **修复 Mod 角色在角色编辑页显示为超长内部 ID**：此前角色名取自一份只覆盖 6 个原版角色的硬编码表，Mod 角色取不到就回退显示完整 ID（如 `CHARACTER.LUST_TRAVEL2_CHARACTER_FOX_HIME`），把标签栏撑到极宽。

  现在改为**运行时动态解析**，不硬编码任何 Mod 角色译名——不同玩家装的 Mod 完全不同，写死必然失效：

  1. `id_names_zh.json`：仅原版角色（随工具发布，**不含任何 Mod 条目**）
  2. **自动扫描该玩家本机的 Mod 资源包**：从游戏 `mods/` 目录与 Steam 创意工坊的 `.pck` 中，读取 Mod 作者自带的简中本地化（`<角色ID>.title` / `.name` 等），拿到真正的角色名
  3. 仍无结果时，按 Mod 角色 ID 的固定形态 `<模组前缀>_CHARACTER_<角色名>` 反推简短可读名，保证界面永远不会出现长 ID

  实现要点：
  - 新增 `character_names.py` 专门负责此事；`core.get_character_name()` 仍是统一入口
  - 自动定位 Steam：注册表 `SteamPath` → 常见路径兜底 → 解析 `libraryfolders.vdf`，因此换盘、多库、创意工坊都能找到
  - 扫描结果只写入本机缓存 `character_names_cache.json`（已 gitignore），**不回写** `id_names_zh.json`——否则等于把"本机装了什么 Mod"固化进随工具发布的文件
  - 全盘扫描实测约 0.3 秒，命中缓存后瞬时；任何一步失败都逐级回退，不影响使用
  - 说明：Mod 角色没有进入游戏的 `characters` 本地化表（游戏日志可见 `Key '...' not found in table 'characters'`），**游戏本体界面也是显示内部 ID 的**。所以准确中文名只能来自 Mod 作者自己的资源包
- **新增 `tests/test_character_name.py`**：不依赖任何真实 Mod，用临时构造的假 `.pck` 验证扫描器认名字、拒长文本、只收中文；并断言译名表里**不存在**硬编码的 Mod 角色条目

### v1.4.3

- **修复"保存了但进游戏没生效"**——根因是 **Steam 云存档覆盖**，不是工具没写入。

  实测日志（本机，UTC）：
  ```
  05:26:46  游戏保存 current_run.save
  05:27:36  修改器写入修改          ← 本地比云端新
  05:28:34  游戏启动："Copying ... from cloud to local"
            （云端 05:26:46 / 本地 05:28:34）→ 本地被云端旧版本覆盖
  ```
  游戏启动时会执行"云端 → 本地"同步，其冲突处理并不总是取更新的那份；结果是修改器确实写入了，但一进游戏就被换回旧存档，玩家只看到"改了没用"。

  本版加入三层防护：
  - **保存前检测 Steam 云冲突**：按存档路径里的 SteamID 反推账号 ID，定位 `<Steam>/userdata/<账号ID>/2868840/remote/...` 下的云端副本；若本地已改而云端仍是旧内容，保存时明确提示并给出三种处理办法（临时关闭 Steam 云 / 先启动一次游戏让它上传 / 删除云端副本）
  - **保存前检测游戏是否仍在运行**：游戏进程会从内存回写存档，检测到就弹窗确认
  - **保存后回读校验**：重新读取刚写出的文件与内存模型比对，若不一致（被其它程序立刻覆盖）或主文件与 `.save.backup` 不同步，直接在提示里报告

  新增 `cloud_saves.py`，**只读取 Steam 云目录，不修改任何 Steam 数据**（有测试断言这一点）。新增 `tests/test_cloud_saves.py`。

### v1.4.2

- **ID 图鉴页新增范围说明**：页面顶部加入提示——本图鉴仅包含游戏本体条目，**不包含 Mod 添加的卡牌 / 遗物 / 药水等内容**，避免玩家搜不到 Mod 内容时误以为工具出错
- **补上遗漏的图鉴分类**：译名表里实际有 65 条 `POTION.*` 与 25 条 `ENCHANTMENT.*`，但页面上没有对应分类，导致药水与附魔在图鉴中查不到。现新增「药水」「附魔」两个分类
- **新增 `tests/test_dictionary_coverage.py`**：断言译名表里每个前缀都有对应分类（防止以后再加内容时又漏分类）、译名表不含 Mod 条目、页面提示文案存在
- UI 冒烟测试新增"角色标签不超宽"断言

### v1.4.0

**适配游戏更新后的存档结构（摘要，详见下方各条）。**

### v1.3.0

- **地图可视化**：地图节点从坐标列表重构为 Canvas 树形网格视图，节点按层级和列位置排列，连线显示路径关系，不同节点类型以颜色区分，已访问路径蓝色高亮，点击节点弹出菜单修改类型
- **卡牌升级**：牌组编辑支持查看和修改卡牌升级状态，升级后的卡牌以绿色显示并带有"+"后缀（如"王国资产+"），对应游戏中火堆锻造功能
- **卡牌附魔**：牌组编辑支持查看和修改卡牌附魔，可从 22 种附魔中选择添加，附魔以紫色标签显示；部分附魔需要依赖对应遗物才能生效
- **附魔翻译**：新增 24 条附魔 ID 中文名映射
- **使用说明**：更新地图编辑、卡牌升级、卡牌附魔的功能说明
- **修复**：解决循环导入导致启动失败的问题

### v1.0.0

- 初始版本发布
- 支持全局进度编辑（角色统计、全局数据）
- 支持对局编辑（玩家状态、牌组、遗物、地图、遭遇池、概率/RNG）
- 内置 1400+ 条 ID 中文翻译图鉴
- 自动备份与原子性写入

## License

[MIT](LICENSE)
