# STS2 存档修改器 ![浏览量](https://visitor-badge.laobi.icu/badge?page_id=Izayoi9/sts2_save_editor)

杀戮尖塔 2 (Slay the Spire 2) 存档修改器，提供图形化界面编辑游戏存档。

> ⚠️ 修改存档可能导致成就无法解锁或存档损坏，请在修改前确保游戏已退出，并妥善保管备份文件。使用本工具造成的任何后果由使用者自行承担。

## 功能一览

### 全局进度编辑 (progress.save)

- **角色编辑** — 修改各角色的进阶难度、胜负场次、连胜记录、最快通关时间
- **全局统计** — 修改总游戏时间、攀爬层数、多人模式进阶等

### 对局编辑 (current_run.save)

- **玩家状态** — HP、金币、能量、药水栏位、稀有卡概率、药水掉率
- **牌组编辑** — 搜索并添加/删除卡牌，支持中文名和 ID 搜索
- **遗物编辑** — 搜索并添加/删除遗物
- **地图编辑** — 修改未访问节点的类型（怪物/精英/休息点/宝箱/商店/事件）
- **遭遇池 & 事件池** — 编辑精英、普通、事件三个队列的内容
- **概率 & RNG** — 调控问号房概率、RNG 计数器

### 工具

- **ID 图鉴** — 查看全部 1400+ 条卡牌/遗物/怪物/事件的内部 ID 与中文名对照表，支持搜索
- **使用说明** — 内置完整的功能说明和注意事项

## 截图

*（欢迎提交截图 PR）*

## 安装与使用

### 方式一：直接下载可执行文件（推荐）

前往 [Releases](../../releases) 下载 `STS2_SaveEditor.exe`，双击运行即可。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/sts2_save_editor.git
cd sts2_save_editor

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

**环境要求：** Python 3.10+

## 存档位置

```
%APPDATA%/SlayTheSpire2/steam/{Steam ID}/profile{1,2,3}/saves/
├── progress.save          # 全局进度
├── progress.save.backup   # 游戏自动备份
├── current_run.save       # 当前对局（仅对局进行中存在）
└── current_run.save.backup
```

启动修改器后会自动扫描上述路径，也可以手动选择文件。

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

## License

[MIT](LICENSE)
