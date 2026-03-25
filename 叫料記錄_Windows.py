#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
叫料記錄系統 - 圖形化介面版 (Windows 版本)
"""

import csv
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

# 設定檔 - Windows 版放在使用者文件資料夾
# 預設路徑
CSV_FILE = Path(os.path.expanduser("~")) / "Documents" / "叫料記錄.csv"

ENGINEERS = ["Hank", "盆栽", "小綠", "老洪", "冠勳", "科錞", "翔哥", "阿承"]
ITEM_TYPES = ["事故維修", "訂貨", "顧關", "其他"]
DEPOSIT_METHODS = ["現金", "刷卡", "轉帳", "無"]
CONTACT_STATUSES = [
    "待叫料", "已叫料", "到貨", "到貨已通知", "到貨未接", 
    "已預約進廠", "車在廠內", "需追蹤", "已完工", "缺料中"
]

FIELDS = [
    "日期", "工程師", "車牌號碼", "聯繫人", "電話", 
    "事項", "估價單號", "料件備註", 
    "是否收取訂金", "訂金金額", 
    "聯繫狀態", "最後聯繫日", "其餘備註"
]


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("叫料記錄系統")
        self.root.geometry("1400x700")
        
        # 資料
        self.data = []
        self.filtered_data = []
        
        # 樣式
        self.setup_styles()
        
        # 建立介面
        self.create_widgets()
        
        # 載入資料
        self.load_data()
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 按鈕樣式
        self.style.configure("TButton", font=(FONT_FAMILY, 10), padding=8)
        
        # 標籤樣式
        self.style.configure("TLabel", font=(FONT_FAMILY, 11))
        
        # 表格樣式
        self.style.configure("Treeview", font=(FONT_FAMILY, 10), rowheight=28)
        self.style.configure("Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))
    
    def create_widgets(self):
        # 頂部標題
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="叫料記錄系統", 
            font=(FONT_FAMILY, 20, "bold"),
            bg="#2c3e50", 
            fg="black"
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        # 功能按鈕區
        btn_frame = tk.Frame(header_frame, bg="#2c3e50")
        btn_frame.pack(side="right", padx=20, pady=10)
        
        buttons = [
            ("新增", self.add_record),
            ("修改", self.edit_record),
            ("刪除", self.delete_record),
            ("重新整理", self.load_data),
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(
                btn_frame, text=text, font=(FONT_FAMILY, 11),
                bg="#3498db", fg="white", relief="flat", padx=15, pady=8,
                cursor="hand2", command=cmd
            )
            btn.pack(side="left", padx=5)
        
        # 篩選區
        filter_frame = tk.Frame(self.root, bg="#f5f5f5")
        filter_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        tk.Label(filter_frame, text="篩選狀態：", font=(FONT_FAMILY, 11), bg="#f5f5f5").pack(side="left")
        
        self.filter_var = tk.StringVar(value="全部")
        status_options = ["全部"] + CONTACT_STATUSES
        
        for status in status_options:
            rb = tk.Radiobutton(
                filter_frame, text=status, variable=self.filter_var, value=status,
                font=(FONT_FAMILY, 10), bg="#f5f5f5",
                command=self.apply_filter
            )
            rb.pack(side="left", padx=5)
        
        # 統計資訊
        self.stats_label = tk.Label(
            self.root, text="", font=(FONT_FAMILY, 10),
            bg="#f5f5f5"
        )
        self.stats_label.pack(fill="x", padx=20, pady=(0, 5))
        
        # 表格區
        table_frame = tk.Frame(self.root, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 定義欄位
        columns = [
            ("序", 40), ("日期", 90), ("工程師", 60), ("車牌號碼", 90), 
            ("聯繫人", 80), ("電話", 100), ("事項", 70), 
            ("估價單號", 90), ("訂金", 80), ("聯繫狀態", 90), ("最後聯繫日", 90)
        ]
        
        self.tree = ttk.Treeview(table_frame, columns=[c[0] for c in columns], show="headings", selectmode="browse")
        
        for col, width in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=width, anchor="center", minwidth=50)
        
        # 滾動條
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # 雙擊編輯
        self.tree.bind("<Double-1>", lambda e: self.edit_record())
        
        # 底部狀態列
        self.status_bar = tk.Label(
            self.root, text="就緒", font=(FONT_FAMILY, 9),
            bg="#ecf0f1", anchor="w", padx=10
        )
        self.status_bar.pack(fill="x")
    
    def load_data(self):
        """載入 CSV 資料"""
        if CSV_FILE.exists():
            with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self.data = list(reader)
        else:
            self.data = []
        
        self.apply_filter()
        self.set_status(f"已載入 {len(self.data)} 筆記錄")
    
    def save_data(self):
        """儲存資料至 CSV"""
        CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.data)
    
    def apply_filter(self):
        """套用篩選"""
        filter_status = self.filter_var.get()
        
        if filter_status == "全部":
            self.filtered_data = self.data
        else:
            self.filtered_data = [r for r in self.data if r.get("聯繫狀態") == filter_status]
        
        self.update_table()
        self.update_stats()
    
    def update_table(self):
        """更新表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, row in enumerate(self.filtered_data, 1):
            values = (
                i,
                row.get("日期", ""),
                row.get("工程師", ""),
                row.get("車牌號碼", ""),
                row.get("聯繫人", ""),
                row.get("電話", ""),
                row.get("事項", ""),
                row.get("估價單號", ""),
                f"{row.get('是否收取訂金', '')} {row.get('訂金金額', '')}".strip(),
                row.get("聯繫狀態", ""),
                row.get("最後聯繫日", ""),
            )
            self.tree.insert("", "end", values=values, iid=str(i-1))
    
    def update_stats(self):
        """更新統計資訊"""
        total = len(self.data)
        
        status_counts = {}
        for r in self.data:
            s = r.get("聯繫狀態", "未知")
            status_counts[s] = status_counts.get(s, 0) + 1
        
        status_str = " | ".join([f"{k}: {v}" for k, v in status_counts.items()])
        
        if self.filter_var.get() == "全部":
            self.stats_label.config(text=f"總記錄數：{total} | {status_str}")
        else:
            filtered = len(self.filtered_data)
            self.stats_label.config(text=f"篩選「{self.filter_var.get()}」：{filtered} 筆 (總記錄：{total})")
    
    def set_status(self, text):
        self.status_bar.config(text=text)
    
    def add_record(self):
        self.open_form()
    
    def edit_record(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("請選擇", "請先選取要修改的記錄")
            return
        
        idx = int(selection[0])
        record = self.filtered_data[idx]
        self.open_form(record, idx)
    
    def delete_record(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("請選擇", "請先選取要刪除的記錄")
            return
        
        if not messagebox.askyesno("確認刪除", "確定要刪除選取的記錄嗎？"):
            return
        
        idx = int(selection[0])
        del self.filtered_data[idx]
        self.data = self.filtered_data if self.filter_var.get() == "全部" else self.data
        self.load_data()
        self.save_data()
        messagebox.showinfo("完成", "記錄已刪除")
    
    def open_form(self, record=None, idx=None):
        """開表單視窗"""
        form = tk.Toplevel(self.root)
        form.title("編輯記錄" if record else "新增記錄")
        form.geometry("500x700")
        form.transient(self.root)
        form.grab_set()
        
        today = datetime.now().strftime("%Y-%m-%d")
        defaults = record if record else {}
        
        entries = {}
        
        required_fields = [
            ("日期", "日期", today),
            ("工程師", "工程師", None),
            ("車牌號碼", "車牌號碼", None),
            ("聯繫人", "聯繫人", None),
            ("電話", "電話", None),
            ("事項", "事項", None),
            ("聯繫狀態", "聯繫狀態", "待叫料"),
            ("最後聯繫日", "最後聯繫日", today),
        ]
        
        optional_fields = [
            ("估價單號", "估價單號", ""),
            ("料件備註", "料件備註", ""),
            ("是否收取訂金", "是否收取訂金", "無"),
            ("訂金金額", "訂金金額", "0"),
            ("其餘備註", "其餘備註", ""),
        ]
        
        all_fields = required_fields + optional_fields
        
        # 滾動區域
        canvas = tk.Canvas(form, highlightthickness=0)
        scrollbar = ttk.Scrollbar(form, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_scroll_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", configure_scroll_width)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        form.update_idletasks()
        
        # 建立欄位
        for field, label, default in all_fields:
            frame = tk.Frame(scrollable_frame)
            frame.pack(fill="x", padx=20, pady=8)
            
            lbl = tk.Label(
                frame, text=label + (" *" if (field, label, default) in required_fields else ""),
                font=(FONT_FAMILY, 11), width=12, anchor="e"
            )
            lbl.pack(side="left")
            
            value = defaults.get(field, default)
            
            if field == "工程師":
                var = tk.StringVar(value=value)
                combo = ttk.Combobox(frame, textvariable=var, values=ENGINEERS, font=(FONT_FAMILY, 11), width=23)
                combo.pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field == "事項":
                var = tk.StringVar(value=value)
                combo = ttk.Combobox(frame, textvariable=var, values=ITEM_TYPES, font=(FONT_FAMILY, 11), width=23)
                combo.pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field == "是否收取訂金":
                var = tk.StringVar(value=value)
                combo = ttk.Combobox(frame, textvariable=var, values=DEPOSIT_METHODS, font=(FONT_FAMILY, 11), width=23)
                combo.pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field == "聯繫狀態":
                var = tk.StringVar(value=value)
                combo = ttk.Combobox(frame, textvariable=var, values=CONTACT_STATUSES, font=(FONT_FAMILY, 11), width=23)
                combo.pack(side="left", fill="x", expand=True)
                entries[field] = var
                text = tk.Text(frame, font=(FONT_FAMILY, 11), width=28, height=3, wrap="word")
                text.pack(side="left", fill="x", expand=True)
                text.insert("1.0", value)
                entries[field] = text
                
            else:
                var = tk.StringVar(value=value)
                entry = tk.Entry(frame, textvariable=var, font=(FONT_FAMILY, 11), width=28)
                entry.pack(side="left", fill="x", expand=True)
                entries[field] = var
        
        # 按鈕區
        btn_frame = tk.Frame(form)
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        def save():
            for field, label, default in required_fields:
                val = entries[field].get() if not isinstance(entries[field], tk.Text) else entries[field].get("1.0", "end").strip()
                if not val:
                    messagebox.showwarning("必填", f"「{label}」為必填欄位")
                    return
            
            new_record = {}
            for field, label, default in all_fields:
                if isinstance(entries[field], tk.Text):
                    new_record[field] = entries[field].get("1.0", "end").strip()
                else:
                    new_record[field] = entries[field].get()
            
            if idx is not None:
                original_idx = self.data.index(self.filtered_data[idx]) if self.filtered_data[idx] in self.data else idx
                self.data[original_idx] = new_record
            else:
                self.data.append(new_record)
            
            self.save_data()
            self.load_data()
            form.destroy()
            messagebox.showinfo("完成", "記錄已儲存")
        
        tk.Button(
            btn_frame, text="儲存", font=(FONT_FAMILY, 12),
            bg="#27ae60", fg="white", relief="flat", padx=20, pady=8,
            cursor="hand2", command=save
        ).pack(side="right", padx=5)
        
        tk.Button(
            btn_frame, text="取消", font=(FONT_FAMILY, 12),
            bg="#95a5a6", fg="white", relief="flat", padx=20, pady=8,
            cursor="hand2", command=form.destroy
        ).pack(side="right", padx=5)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
