"""主窗口框架 + 侧边栏导航 + 存档选择。"""

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from core import (
    SaveProfile,
    check_schema_version,
    check_run_schema_version,
    get_discovered_ids,
    load_current_run,
    load_progress,
    save_current_run,
    save_progress,
    scan_profiles,
)
from models import CurrentRunData, ProgressData
from ui.tab_character import CharacterTab
from ui.tab_dictionary import DictionaryTab
from ui.tab_guide import GuideTab
from ui.tab_run import RunTab
from ui.tab_stats import StatsTab


from __version__ import __version__


class ProfileSelector(ctk.CTkToplevel):
    """存档选择对话框。"""

    def __init__(self, master: Any, profiles: list[SaveProfile]) -> None:
        super().__init__(master)
        self.title("选择存档")
        self.geometry("500x400")
        self.resizable(False, False)
        self.grab_set()

        self.selected_path: Path | None = None

        label = ctk.CTkLabel(self, text="检测到以下存档：", font=ctk.CTkFont(size=14))
        label.pack(padx=16, pady=(16, 8))

        # 存档列表
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        for profile in profiles:
            btn = ctk.CTkButton(
                scroll,
                text=profile.display_name,
                anchor="w",
                command=lambda p=profile: self._select(p),
            )
            btn.pack(fill="x", pady=2)

        # 手动选择按钮
        manual_btn = ctk.CTkButton(
            self, text="手动选择文件...", fg_color="gray30", command=self._manual_select,
        )
        manual_btn.pack(padx=16, pady=(0, 16))

    def _select(self, profile: SaveProfile) -> None:
        self.selected_path = profile.path
        self.destroy()

    def _manual_select(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 progress.save 文件",
            filetypes=[("Save files", "*.save"), ("All files", "*.*")],
        )
        if path:
            self.selected_path = Path(path)
            self.destroy()


class App(ctk.CTk):
    """主应用窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.title(f"STS2 存档修改器 v{__version__}")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._data: ProgressData | None = None
        self._save_path: Path | None = None
        self._run_data: CurrentRunData | None = None
        self._run_path: Path | None = None
        self._char_tab: CharacterTab | None = None
        self._stats_tab: StatsTab | None = None
        self._run_tab: RunTab | None = None
        self._dict_tab: DictionaryTab | None = None
        self._guide_tab: GuideTab | None = None

        self._build_layout()

        # 启动后弹出存档选择
        self.after(200, self._show_profile_selector)

    def _build_layout(self) -> None:
        # 顶部信息栏
        self._top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self._top_bar.pack(fill="x")
        self._top_bar.pack_propagate(False)

        self._path_label = ctk.CTkLabel(
            self._top_bar, text="未加载存档", anchor="w", font=ctk.CTkFont(size=12),
        )
        self._path_label.pack(side="left", padx=16)

        self._uid_label = ctk.CTkLabel(
            self._top_bar, text="", anchor="e", font=ctk.CTkFont(size=12), text_color="gray",
        )
        self._uid_label.pack(side="right", padx=16)

        # 主体区域
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # 侧边栏
        sidebar = ctk.CTkFrame(body, width=150, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        sidebar_label = ctk.CTkLabel(
            sidebar, text="STS2 Editor", font=ctk.CTkFont(size=18, weight="bold"),
        )
        sidebar_label.pack(padx=16, pady=(20, 24))

        self._btn_char = ctk.CTkButton(
            sidebar, text="角色编辑", command=lambda: self._show_tab("character"),
        )
        self._btn_char.pack(fill="x", padx=12, pady=4)

        self._btn_stats = ctk.CTkButton(
            sidebar, text="全局统计", command=lambda: self._show_tab("stats"),
        )
        self._btn_stats.pack(fill="x", padx=12, pady=4)

        self._btn_run = ctk.CTkButton(
            sidebar, text="对局编辑", command=lambda: self._show_tab("run"),
            state="disabled",
        )
        self._btn_run.pack(fill="x", padx=12, pady=4)

        self._btn_dict = ctk.CTkButton(
            sidebar, text="ID 图鉴", command=lambda: self._show_tab("dictionary"),
        )
        self._btn_dict.pack(fill="x", padx=12, pady=4)

        self._btn_guide = ctk.CTkButton(
            sidebar, text="使用说明", command=lambda: self._show_tab("guide"),
        )
        self._btn_guide.pack(fill="x", padx=12, pady=4)

        # 侧边栏底部按钮
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        load_btn = ctk.CTkButton(
            sidebar, text="加载存档", fg_color="gray30", command=self._show_profile_selector,
        )
        load_btn.pack(fill="x", padx=12, pady=4)

        save_btn = ctk.CTkButton(
            sidebar, text="保存修改", fg_color="#2fa572", hover_color="#1f7a54",
            command=self._save,
        )
        save_btn.pack(fill="x", padx=12, pady=(4, 16))

        # 内容区域
        self._content = ctk.CTkFrame(body)
        self._content.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # 占位提示
        self._placeholder = ctk.CTkLabel(
            self._content, text="请先选择一个存档文件", font=ctk.CTkFont(size=16),
            text_color="gray",
        )
        self._placeholder.pack(expand=True)

    def _show_profile_selector(self) -> None:
        profiles = scan_profiles()
        if profiles:
            dialog = ProfileSelector(self, profiles)
            self.wait_window(dialog)
            if dialog.selected_path:
                self._load_save(dialog.selected_path)
        else:
            path = filedialog.askopenfilename(
                title="选择 progress.save 文件",
                filetypes=[("Save files", "*.save"), ("All files", "*.*")],
            )
            if path:
                self._load_save(Path(path))

    def _load_save(self, path: Path) -> None:
        try:
            self._data = load_progress(path)
            self._save_path = path
        except Exception as e:
            messagebox.showerror("加载失败", f"无法解析存档文件:\n{e}")
            return

        # schema 版本检查
        warning = check_schema_version(self._data)
        if warning:
            messagebox.showwarning("版本警告", warning)

        # 尝试加载同目录下的 current_run.save
        self._run_data = None
        self._run_path = None
        run_path = path.parent / "current_run.save"
        if run_path.exists():
            try:
                self._run_data = load_current_run(run_path)
                self._run_path = run_path
                run_warning = check_run_schema_version(self._run_data)
                if run_warning:
                    messagebox.showwarning("对局版本警告", run_warning)
            except Exception as e:
                messagebox.showwarning("对局加载失败", f"current_run.save 解析失败:\n{e}")

        # 更新顶部栏
        self._path_label.configure(text=str(path))
        self._uid_label.configure(text=f"UID: {self._data.unique_id}")

        # 更新对局按钮状态
        self._btn_run.configure(state="normal" if self._run_data else "disabled")

        # 构建标签页
        self._build_tabs()
        self._show_tab("character")

    def _build_tabs(self) -> None:
        if self._data is None:
            return

        # 清除旧内容（包括懒加载的 dict/guide tab）
        for widget in self._content.winfo_children():
            widget.destroy()
        self._dict_tab = None
        self._guide_tab = None

        self._char_tab = CharacterTab(
            self._content, self._data.character_stats,
        )
        self._stats_tab = StatsTab(self._content, self._data)

        # 对局编辑 Tab
        self._run_tab = None
        if self._run_data and self._save_path:
            discovered_cards, discovered_relics = get_discovered_ids(self._save_path)
            self._run_tab = RunTab(
                self._content,
                self._run_data,
                discovered_cards=discovered_cards,
                discovered_relics=discovered_relics,
            )
            self._run_tab.pack_forget()

        # ID 图鉴 Tab（懒加载，点击时才创建）
        self._dict_tab = None

        # 默认隐藏
        self._char_tab.pack_forget()
        self._stats_tab.pack_forget()

    def _show_tab(self, tab_name: str) -> None:
        # ID 图鉴和使用说明不依赖存档加载，可以独立显示
        if tab_name in ("dictionary", "guide"):
            # 隐藏其他已存在的 tab
            for tab in (self._char_tab, self._stats_tab, self._run_tab,
                        self._dict_tab, self._guide_tab):
                if tab is not None:
                    tab.pack_forget()
            # 隐藏占位符
            if hasattr(self, "_placeholder") and self._placeholder.winfo_exists():
                self._placeholder.pack_forget()

            if tab_name == "dictionary":
                if self._dict_tab is None:
                    self._dict_tab = DictionaryTab(self._content)
                self._dict_tab.pack(fill="both", expand=True)
            elif tab_name == "guide":
                if self._guide_tab is None:
                    self._guide_tab = GuideTab(self._content)
                self._guide_tab.pack(fill="both", expand=True)
            return

        if self._char_tab is None or self._stats_tab is None:
            return

        self._char_tab.pack_forget()
        self._stats_tab.pack_forget()
        if self._run_tab:
            self._run_tab.pack_forget()
        if self._dict_tab:
            self._dict_tab.pack_forget()
        if self._guide_tab:
            self._guide_tab.pack_forget()

        if tab_name == "character":
            self._char_tab.pack(fill="both", expand=True)
        elif tab_name == "stats":
            self._stats_tab.pack(fill="both", expand=True)
        elif tab_name == "run" and self._run_tab:
            self._run_tab.pack(fill="both", expand=True)

    def _save(self) -> None:
        if self._data is None or self._save_path is None:
            messagebox.showwarning("提示", "未加载存档")
            return

        # 从 UI 收集数据（异常保护，避免部分收集导致数据不一致）
        try:
            if self._char_tab:
                self._data.character_stats = self._char_tab.apply_all()
            if self._stats_tab:
                self._stats_tab.apply(self._data)
            if self._run_tab and self._run_data:
                self._run_data = self._run_tab.apply()
        except Exception as e:
            messagebox.showerror("收集数据失败", f"从编辑器收集数据时出错:\n{e}")
            return

        saved_files: list[str] = []

        try:
            save_progress(self._data, self._save_path)
            saved_files.append(f"progress: {self._save_path.with_suffix('.save.bak')}")
        except Exception as e:
            messagebox.showerror("保存失败", f"progress 写入失败:\n{e}")
            return

        # 保存 current_run（如果已加载）
        if self._run_data and self._run_path:
            try:
                save_current_run(self._run_data, self._run_path)
                saved_files.append(f"current_run: {self._run_path.with_suffix('.save.bak')}")
            except Exception as e:
                messagebox.showerror("保存失败", f"current_run 写入失败:\n{e}")
                return

        messagebox.showinfo("成功", "存档已保存\n备份:\n" + "\n".join(saved_files))
