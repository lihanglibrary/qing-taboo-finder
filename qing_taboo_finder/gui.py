"""Tkinter desktop interface for QingTabooFinder."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .constants import ATOMIC_CATEGORY_DEFINITIONS, CATEGORY_SELECTION_LABELS, CHECK_MODE_DEFINITIONS
from .service import DetectionResult, default_csv_path, run_detection, selectable_emperors


APP_TITLE = "QingTabooFinder 清代避讳定位器"
DEFAULT_OUTPUT_DIRECTORY = Path.home() / "QingTabooFinder Reports"


class QingTabooFinderApp(ttk.Frame):
    """A complete local workflow for choosing inputs and exporting reports."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=18)
        self.root = root
        self.csv_path = tk.StringVar(value=str(default_csv_path()))
        self.document_path = tk.StringVar()
        self.output_directory = tk.StringVar(value=str(DEFAULT_OUTPUT_DIRECTORY))
        self.emperor = tk.StringVar()
        self.status = tk.StringVar(value="请选择待查验文档。")
        self.category_variables = {
            category: tk.BooleanVar(value=index < 4)
            for index, category in enumerate(ATOMIC_CATEGORY_DEFINITIONS)
        }
        self.mode_keys = {
            tuple(definition["categories"]): mode_key
            for mode_key, definition in CHECK_MODE_DEFINITIONS.items()
        }
        self.start_button: ttk.Button
        self.open_output_button: ttk.Button
        self.progress: ttk.Progressbar
        self.summary: tk.Text

        self._configure_window()
        self._build_layout()
        self._load_emperors()

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.minsize(780, 660)
        self.root.geometry("900x730")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)

    def _build_layout(self) -> None:
        title = ttk.Label(self, text=APP_TITLE, style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")
        ttk.Label(
            self,
            text="在本地定位清代避讳线索，并导出可供复核的 CSV 与 Excel 报告。",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 16))

        input_frame = ttk.LabelFrame(self, text="文件与朝代", padding=12)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        self._add_path_row(input_frame, 0, "规则 CSV", self.csv_path, self._choose_csv)
        self._add_path_row(input_frame, 1, "待查验文档", self.document_path, self._choose_document)
        self._add_path_row(input_frame, 2, "报告输出目录", self.output_directory, self._choose_output_directory)

        ttk.Label(input_frame, text="目标皇帝").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.emperor_box = ttk.Combobox(
            input_frame,
            textvariable=self.emperor,
            state="readonly",
            width=24,
        )
        self.emperor_box.grid(row=3, column=1, sticky="w", pady=(10, 0))
        ttk.Button(input_frame, text="重新读取规则", command=self._load_emperors).grid(
            row=3,
            column=2,
            sticky="e",
            padx=(8, 0),
            pady=(10, 0),
        )

        category_frame = ttk.LabelFrame(self, text="避讳项目", padding=12)
        category_frame.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        for index, category in enumerate(ATOMIC_CATEGORY_DEFINITIONS):
            row, column = divmod(index, 2)
            ttk.Checkbutton(
                category_frame,
                text=CATEGORY_SELECTION_LABELS[category],
                variable=self.category_variables[category],
            ).grid(row=row, column=column, sticky="w", padx=(0, 26), pady=3)

        controls = ttk.Frame(self)
        controls.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        controls.columnconfigure(1, weight=1)
        self.start_button = ttk.Button(controls, text="开始查验", command=self._start_detection)
        self.start_button.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(controls, mode="indeterminate", length=160)
        self.progress.grid(row=0, column=1, sticky="w", padx=12)
        self.open_output_button = ttk.Button(
            controls,
            text="打开输出目录",
            command=self._open_output_directory,
            state="disabled",
        )
        self.open_output_button.grid(row=0, column=2, sticky="e")
        ttk.Label(controls, textvariable=self.status).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        results_frame = ttk.LabelFrame(self, text="查验结果", padding=8)
        results_frame.grid(row=5, column=0, sticky="nsew", pady=(14, 0))
        self.rowconfigure(5, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        self.summary = tk.Text(results_frame, height=15, wrap="word", state="disabled", font=("Menlo", 12))
        self.summary.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.summary.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary.configure(yscrollcommand=scrollbar.set)

    def _add_path_row(
        self,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: object,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=(12, 8), pady=4)
        ttk.Button(parent, text="选择...", command=command).grid(row=row, column=2, sticky="e", pady=4)

    def _choose_csv(self) -> None:
        selected_path = filedialog.askopenfilename(
            title="选择规则 CSV 文件",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if selected_path:
            self.csv_path.set(selected_path)
            self._load_emperors()

    def _choose_document(self) -> None:
        selected_path = filedialog.askopenfilename(
            title="选择待查验文档",
            filetypes=[
                ("支持的文档", "*.txt *.docx *.epub"),
                ("文本文件", "*.txt"),
                ("Word 文档", "*.docx"),
                ("EPUB 电子书", "*.epub"),
                ("所有文件", "*.*"),
            ],
        )
        if selected_path:
            self.document_path.set(selected_path)

    def _choose_output_directory(self) -> None:
        selected_path = filedialog.askdirectory(title="选择报告输出目录")
        if selected_path:
            self.output_directory.set(selected_path)

    def _load_emperors(self) -> None:
        try:
            emperors = selectable_emperors(self.csv_path.get())
        except Exception as exc:  # noqa: BLE001
            self.emperor_box["values"] = ()
            self.status.set(f"无法读取规则文件：{exc}")
            return

        self.emperor_box["values"] = emperors
        preferred_emperor = "道光" if "道光" in emperors else emperors[0] if emperors else ""
        self.emperor.set(preferred_emperor)
        self.status.set("规则文件已读取。请选择文档和避讳项目后开始查验。")

    def _selected_mode_key(self) -> str:
        categories = tuple(
            category
            for category, variable in self.category_variables.items()
            if variable.get()
        )
        if not categories:
            raise ValueError("请至少选择一项避讳项目。")
        return self.mode_keys[categories]

    def _start_detection(self) -> None:
        if not self.document_path.get().strip():
            messagebox.showerror(APP_TITLE, "请选择待查验文档。")
            return
        if not self.emperor.get():
            messagebox.showerror(APP_TITLE, "请选择目标皇帝。")
            return

        try:
            mode_key = self._selected_mode_key()
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return

        self.start_button.configure(state="disabled")
        self.open_output_button.configure(state="disabled")
        self.progress.start(12)
        self.status.set("正在查验文档，请稍候...")
        self._set_summary("正在读取文档并生成报告，请稍候...")
        worker = threading.Thread(
            target=self._run_detection_in_background,
            args=(mode_key,),
            daemon=True,
        )
        worker.start()

    def _run_detection_in_background(self, mode_key: str) -> None:
        try:
            result = run_detection(
                self.csv_path.get(),
                self.document_path.get(),
                self.emperor.get(),
                mode_key,
                self.output_directory.get(),
            )
        except Exception as exc:  # noqa: BLE001
            self.root.after(0, self._show_detection_error, str(exc))
            return
        self.root.after(0, self._show_detection_result, result)

    def _show_detection_result(self, result: DetectionResult) -> None:
        current_hits = sum(1 for hit in result.hits if not hit.is_cumulative_prior)
        prior_hits = len(result.hits) - current_hits
        message = result.message or ""
        summary = "\n".join(
            [
                "查验完成",
                f"文档：{result.document_path.name}",
                f"目标皇帝：{result.emperor}",
                f"分段数：{result.segment_count}",
                f"启用避讳项数：{result.entry_count}",
                f"总命中数：{len(result.hits)}",
                f"本朝新增避讳命中：{current_hits}",
                f"前朝累计避讳命中：{prior_hits}",
                "",
                f"CSV 报告：{result.csv_report}",
                f"Excel 报告：{result.excel_report}",
                *(["", f"提示：{message}"] if message else []),
            ]
        )
        self._set_summary(summary)
        self.progress.stop()
        self.start_button.configure(state="normal")
        self.open_output_button.configure(state="normal")
        self.status.set("查验完成，报告已导出。")

    def _show_detection_error(self, error_message: str) -> None:
        self.progress.stop()
        self.start_button.configure(state="normal")
        self._set_summary(f"查验未完成：\n{error_message}")
        self.status.set("查验未完成，请检查文件与设置。")
        messagebox.showerror(APP_TITLE, error_message)

    def _set_summary(self, text: str) -> None:
        self.summary.configure(state="normal")
        self.summary.delete("1.0", tk.END)
        self.summary.insert("1.0", text)
        self.summary.configure(state="disabled")

    def _open_output_directory(self) -> None:
        directory = Path(self.output_directory.get())
        directory.mkdir(parents=True, exist_ok=True)
        if sys.platform == "darwin":
            subprocess.run(["open", str(directory)], check=False)
        elif os.name == "nt":
            os.startfile(directory)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(directory)], check=False)


def main() -> int:
    root = tk.Tk()
    style = ttk.Style(root)
    style.configure("Title.TLabel", font=("Helvetica Neue", 22, "bold"))
    style.configure("Subtitle.TLabel", foreground="#4b5563")
    QingTabooFinderApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())