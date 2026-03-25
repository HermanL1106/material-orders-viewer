#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
叫料記錄系統 - Firebase 雲端同步版 (REST API)
不需要額外安裝 firebase-admin！
"""

import json
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import calendar


import calendar


class DatePicker:
    """簡單的月曆選擇器"""
    def __init__(self, parent, current_date=None):
        self.result = None
        self.win = tk.Toplevel(parent)
        self.win.withdraw()
        self.win.transient(parent)
        self.win.grab_set()
        
        if current_date:
            try:
                self.selected_date = datetime.strptime(current_date, "%Y-%m-%d")
            except:
                self.selected_date = datetime.now()
        else:
            self.selected_date = datetime.now()
        
        self.cal = calendar.Calendar(firstweekday=6)
        self.build_calendar()
        
        # 等待視窗顯示
        self.win.update()
        width = 300
        height = 280
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.deiconify()
        
        self.win.wait_window()
    
    def build_calendar(self):
        self.win.title("選擇日期")
        
        # 年月選擇
        nav_frame = tk.Frame(self.win)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        self.year_var = tk.StringVar(value=str(self.selected_date.year))
        self.month_var = tk.StringVar(value=str(self.selected_date.month))
        
        tk.Button(nav_frame, text="◀", command=self.prev_month, width=3).pack(side="left")
        
        tk.Entry(nav_frame, textvariable=self.year_var, width=5, justify="center").pack(side="left", padx=5)
        tk.Label(nav_frame, text="年").pack(side="left")
        
        month_combo = ttk.Combobox(nav_frame, textvariable=self.month_var, values=[str(i) for i in range(1, 13)], width=3, state="readonly")
        month_combo.pack(side="left", padx=5)
        month_combo.bind("<<ComboboxSelected>>", lambda e: self.update_calendar())
        
        tk.Button(nav_frame, text="▶", command=self.next_month, width=3).pack(side="left")
        
        # 星期標題
        days_frame = tk.Frame(self.win)
        days_frame.pack(fill="x", padx=10)
        
        for day in ["日", "一", "二", "三", "四", "五", "六"]:
            tk.Label(days_frame, text=day, width=4, font=(FONT_FAMILY, FONT_SIZES["label"], "bold"), bg="#ddd").pack(side="left", padx=1, pady=1)
        
        # 日曆格
        self.days_frame = tk.Frame(self.win)
        self.days_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.update_calendar()
        
        # 按鈕
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="今天", command=self.select_today, bg="#3498db", fg="white", relief="flat", padx=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="取消", command=self.win.destroy, bg="#95a5a6", fg="white", relief="flat", padx=15).pack(side="right", padx=5)
    
    def update_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()
        
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
        except:
            return
        
        if month < 1: month = 1
        if month > 12: month = 12
        
        self.month_var.set(str(month))
        
        # 取得該月日曆
        month_days = self.cal.monthdayscalendar(year, month)
        
        for week in month_days:
            week_frame = tk.Frame(self.days_frame)
            week_frame.pack(fill="x")
            
            for day in week:
                if day == 0:
                    tk.Label(week_frame, width=4, height=2).pack(side="left", padx=1, pady=1)
                else:
                    is_today = (day == datetime.now().day and month == datetime.now().month and year == datetime.now().year)
                    bg_color = "#3498db" if is_today else "#f5f5f5"
                    fg_color = "white" if is_today else "black"
                    
                    btn = tk.Button(
                        week_frame, text=str(day), width=4, height=2,
                        bg=bg_color, fg=fg_color, relief="flat",
                        command=lambda d=day: self.select_date(year, month, d)
                    )
                    btn.pack(side="left", padx=1, pady=1)
    
    def prev_month(self):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
        except:
            return
        
        if month == 1:
            self.year_var.set(str(year - 1))
            self.month_var.set("12")
        else:
            self.month_var.set(str(month - 1))
        self.update_calendar()
    
    def next_month(self):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
        except:
            return
        
        if month == 12:
            self.year_var.set(str(year + 1))
            self.month_var.set("1")
        else:
            self.month_var.set(str(month + 1))
        self.update_calendar()
    
    def select_date(self, year, month, day):
        self.result = f"{year}-{month:02d}-{day:02d}"
        self.win.destroy()
    
    def select_today(self):
        today = datetime.now()
        self.result = today.strftime("%Y-%m-%d")
        self.win.destroy()


# Firebase 設定
FIREBASE_PROJECT = "electric-bike-workorders"
COLLECTION_NAME = "materialOrders"
# Firestore REST API
FIRESTORE_API = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT}/databases/(default)/documents"

# 字體 (1920x1080 解析度)
FONT_FAMILY = "Microsoft JhengHei"

# 字體大小設定 (適合 1920x1080)
FONT_SIZES = {
    "title": 22,          # 標題
    "header": 14,        # 欄位標題
    "label": 12,         # 標籤
    "button": 12,        # 按鈕
    "entry": 12,         # 輸入框
    "table_header": 12,  # 表格標題
    "table": 11,         # 表格內容
    "small": 10,         # 小字（狀態列等）
}

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


class FirebaseManager:
    """Firebase REST API 管理"""
    
    def __init__(self):
        self.api = f"{FIRESTORE_API}/{COLLECTION_NAME}"
        self.connected = False
        self.test_connection()
    
    def test_connection(self):
        """測試連線"""
        try:
            url = f"{self.api}?pageSize=1"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                self.connected = True
        except Exception as e:
            print(f"連線測試失敗: {e}")
            self.connected = False
    
    def make_request(self, method, url, data=None):
        """發送請求"""
        try:
            req = urllib.request.Request(url, method=method)
            req.add_header('Content-Type', 'application/json')
            
            if data:
                json_data = json.dumps(data).encode('utf-8')
                req.add_header('Content-Length', str(len(json_data)))
                response = urllib.request.urlopen(req, data=json_data, timeout=30)
            else:
                response = urllib.request.urlopen(req, timeout=30)
            
            if response.status in [200, 201]:
                content = response.read().decode('utf-8')
                return json.loads(content) if content else {}
            return {"error": f"HTTP {response.status}"}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP 錯誤 {e.code}: {error_body}")
            return {"error": f"HTTP {e.code}: {error_body}"}
        except Exception as e:
            print(f"請求失敗: {e}")
            return {"error": str(e)}
    
    def get_all_records(self):
        """取得所有記錄"""
        try:
            # 使用 REST API 取得所有文件
            url = f"{self.api}?pageSize=1000"
            result = self.make_request("GET", url)
            
            if not result or "documents" not in result:
                return []
            
            records = []
            for doc in result["documents"]:
                # 解析文件資料
                data = {}
                if "fields" in doc:
                    for key, value in doc["fields"].items():
                        if "stringValue" in value:
                            data[key] = value["stringValue"]
                        elif "integerValue" in value:
                            data[key] = value["integerValue"]
                        elif "doubleValue" in value:
                            data[key] = value["doubleValue"]
                        elif "booleanValue" in value:
                            data[key] = value["booleanValue"]
                
                data['id'] = doc['name'].split('/')[-1]
                records.append(data)
            
            return records
        except Exception as e:
            print(f"取得資料失敗: {e}")
            return []
    
    def add_record(self, data):
        """新增記錄"""
        try:
            # 轉換資料格式為 Firestore format
            firestore_data = {"fields": {}}
            for key, value in data.items():
                if value is None:
                    value = ""
                firestore_data["fields"][key] = {"stringValue": str(value)}
            
            url = self.api
            result = self.make_request("POST", url, firestore_data)
            
            if result and "error" not in result:
                return True, "成功"
            else:
                error_msg = result.get("error", "未知錯誤") if result else "無法連線"
                return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def update_record(self, doc_id, data):
        """更新記錄"""
        try:
            # 先取得現有資料
            existing_url = f"{self.api}/{doc_id}"
            existing = self.make_request("GET", existing_url)
            
            if existing and "fields" in existing:
                # 合併現有資料和新資料
                merged_fields = {}
                
                # 保留現有欄位
                for key, value in existing["fields"].items():
                    if "stringValue" in value:
                        merged_fields[key] = {"stringValue": value["stringValue"]}
                    elif "integerValue" in value:
                        merged_fields[key] = {"integerValue": value["integerValue"]}
                    elif "doubleValue" in value:
                        merged_fields[key] = {"doubleValue": value["doubleValue"]}
                    elif "booleanValue" in value:
                        merged_fields[key] = {"booleanValue": value["booleanValue"]}
                
                # 更新要修改的欄位
                for key, value in data.items():
                    if value is None:
                        value = ""
                    merged_fields[key] = {"stringValue": str(value)}
                
                # 發送更新
                url = f"{self.api}/{doc_id}"
                result = self.make_request("PATCH", url, {"fields": merged_fields})
                
                if result and "error" not in result:
                    return True, "成功"
                else:
                    error_msg = result.get("error", "未知錯誤") if result else "無法連線"
                    return False, error_msg
            else:
                # 如果找不到現有資料，直接更新
                firestore_data = {"fields": {}}
                for key, value in data.items():
                    if value is None:
                        value = ""
                    firestore_data["fields"][key] = {"stringValue": str(value)}
                
                url = f"{self.api}/{doc_id}"
                result = self.make_request("PATCH", url, firestore_data)
                
                if result and "error" not in result:
                    return True, "成功"
                else:
                    error_msg = result.get("error", "未知錯誤") if result else "無法連線"
                    return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def delete_record(self, doc_id):
        """刪除記錄"""
        try:
            url = f"{self.api}/{doc_id}"
            result = self.make_request("DELETE", url)
            return True
        except Exception as e:
            print(f"刪除失敗: {e}")
            return False


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("叫料記錄系統 (Firebase 雲端版)")
        self.root.geometry("1600x800")
        
        # Firebase 管理
        self.firebase = FirebaseManager()
        
        if not self.firebase.connected:
            messagebox.showwarning(
                "連線警告", 
                "無法連線到 Firebase！\n\n"
                "請檢查網路連線\n\n"
                "程式將以離線模式運行"
            )
        
        self.data = []
        self.filtered_data = []
        
        self.setup_styles()
        self.create_widgets()
        self.load_data()
    
    def open_date_picker(self, parent, field_name, var):
        """開啟月曆選擇器"""
        current_value = var.get() if var.get() else datetime.now().strftime("%Y-%m-%d")
        picker = DatePicker(parent, current_value)
        if picker.result:
            var.set(picker.result)
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", font=(FONT_FAMILY, FONT_SIZES["button"]), padding=8)
        self.style.configure("TLabel", font=(FONT_FAMILY, FONT_SIZES["label"]))
        self.style.configure("Treeview", font=(FONT_FAMILY, FONT_SIZES["table"]), rowheight=30)
        self.style.configure("Treeview.Heading", font=(FONT_FAMILY, FONT_SIZES["table_header"], "bold"))
    
    def create_widgets(self):
        # 頂部標題
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # 連線狀態
        self.conn_status = tk.Label(
            header_frame, text="⚫", font=("Arial", 12),
            bg="#2c3e50", fg="red"
        )
        self.conn_status.pack(side="right", padx=10)
        
        tk.Label(
            header_frame, text="叫料記錄系統 (雲端同步)", 
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            bg="#2c3e50", fg="black"
        ).pack(side="left", padx=20, pady=10)
        
        # 功能按鈕
        btn_frame = tk.Frame(header_frame, bg="#2c3e50")
        btn_frame.pack(side="right", padx=20, pady=10)
        
        for text, cmd in [
            ("新增", self.add_record),
            ("修改", self.edit_record),
            ("刪除", self.delete_record),
            ("批量改狀態", self.batch_edit_status),
            ("重新整理", self.load_data),
        ]:
            tk.Button(
                btn_frame, text=text, font=(FONT_FAMILY, FONT_SIZES["button"]),
                bg="#3498db", fg="white", relief="flat", padx=15, pady=8,
                cursor="hand2", command=cmd
            ).pack(side="left", padx=5)
        
        # 搜尋區
        search_frame = tk.Frame(self.root, bg="#f5f5f5")
        search_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        tk.Label(search_frame, text="搜尋：", font=(FONT_FAMILY, FONT_SIZES["label"]), bg="#f5f5f5").pack(side="left")
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        tk.Entry(search_frame, textvariable=self.search_var, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=30).pack(side="left", padx=5)
        
        tk.Button(search_frame, text="清除", font=(FONT_FAMILY, FONT_SIZES["small"]), 
                  command=self.clear_search, bg="#95a5a6", fg="white", relief="flat", padx=10, pady=4).pack(side="left")
        
        # 篩選區
        filter_frame = tk.Frame(self.root, bg="#f5f5f5")
        filter_frame.pack(fill="x", padx=20, pady=(5, 5))
        
        tk.Label(filter_frame, text="篩選狀態：", font=(FONT_FAMILY, FONT_SIZES["label"]), bg="#f5f5f5").pack(side="left")
        
        self.filter_var = tk.StringVar(value="全部")
        self.show_completed = tk.BooleanVar(value=False)  # 預設隱藏已完工
        
        # 顯示已完成記錄的選項
        tk.Checkbutton(
            filter_frame, text="顯示已完工", variable=self.show_completed,
            font=(FONT_FAMILY, FONT_SIZES["small"]), bg="#f5f5f5",
            command=self.toggle_show_completed
        ).pack(side="left", padx=10)
        for status in ["全部"] + CONTACT_STATUSES:
            tk.Radiobutton(
                filter_frame, text=status, variable=self.filter_var, value=status,
                font=(FONT_FAMILY, FONT_SIZES["small"]), bg="#f5f5f5",
                command=self.apply_filter
            ).pack(side="left", padx=5)
        
        # 統計
        self.stats_label = tk.Label(self.root, text="", font=(FONT_FAMILY, FONT_SIZES["small"]), bg="#f5f5f5")
        self.stats_label.pack(fill="x", padx=20, pady=(0, 5))
        
        # 表格
        table_frame = tk.Frame(self.root, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = [
            ("序", 45), ("日期", 100), ("工程師", 70), ("車牌號碼", 100), 
            ("聯繫人", 90), ("電話", 110), ("事項", 80), 
            ("估價單號", 100), ("訂金", 90), ("聯繫狀態", 100), 
            ("最後聯繫日", 100), ("料件備註", 180), ("其餘備註", 180)
        ]
        
        self.tree = ttk.Treeview(table_frame, columns=[c[0] for c in columns], show="headings", selectmode="extended")
        
        for col, width in columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=width, anchor="center", minwidth=50)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        self.tree.bind("<Double-1>", lambda e: self.edit_record())
        
        # 右鍵選單
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="複製估價單號", command=self.copy_quote_no)
        self.context_menu.add_separator()
        for status in CONTACT_STATUSES:
            self.context_menu.add_command(label=f"改為「{status}」", command=lambda s=status: self.quick_change_status(s))
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # 底部狀態列
        self.status_bar = tk.Label(self.root, text="就緒", font=(FONT_FAMILY, FONT_SIZES["small"]), bg="#ecf0f1", anchor="w", padx=10)
        self.status_bar.pack(fill="x")
        
        # 更新連線狀態
        self.update_connection_status()
    
    def update_connection_status(self):
        if self.firebase.connected:
            self.conn_status.config(text="🟢 已連線", fg="green")
        else:
            self.conn_status.config(text="🔴 未連線", fg="red")
    
    def load_data(self):
        self.data = self.firebase.get_all_records()
        self.data.sort(key=lambda x: x.get("日期", ""), reverse=True)
        self.apply_filter()
        self.set_status(f"已載入 {len(self.data)} 筆記錄")
        self.update_connection_status()
    
    def toggle_show_completed(self):
        """切換顯示已完成記錄"""
        self.apply_filter()
    
    def apply_filter(self):
        # 預設隱藏已完工的記錄
        show_completed = self.show_completed.get()
        
        if self.filter_var.get() == "全部":
            if show_completed:
                self.filtered_data = self.data
            else:
                self.filtered_data = [r for r in self.data if r.get("聯繫狀態") != "已完工"]
        else:
            self.filtered_data = [r for r in self.data if r.get("聯繫狀態") == self.filter_var.get()]
        
        self.update_table()
        self.update_stats()
    
    def update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, row in enumerate(self.filtered_data):
            self.tree.insert("", "end", values=(
                i + 1,
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
                row.get("料件備註", ""),
                row.get("其餘備註", ""),
            ), iid=str(i))
    
    def update_stats(self):
        total = len(self.data)
        status_counts = {}
        for r in self.data:
            s = r.get("聯繫狀態", "未知")
            status_counts[s] = status_counts.get(s, 0) + 1
        
        status_str = " | ".join([f"{k}: {v}" for k, v in status_counts.items()])
        
        if self.filter_var.get() == "全部":
            self.stats_label.config(text=f"總記錄數：{total} | {status_str}")
        else:
            self.stats_label.config(text=f"篩選「{self.filter_var.get()}」：{len(self.filtered_data)} 筆")
    
    def set_status(self, text):
        self.status_bar.config(text=text)
    
    def on_search(self, *args):
        keyword = self.search_var.get().strip().lower()
        
        if not keyword:
            self.apply_filter()
            return
        
        self.filtered_data = []
        for r in self.data:
            search_fields = [
                r.get("日期", ""),
                r.get("工程師", ""),
                r.get("車牌號碼", ""),
                r.get("聯繫人", ""),
                r.get("電話", ""),
                r.get("事項", ""),
                r.get("估價單號", ""),
                r.get("聯繫狀態", ""),
                r.get("料件備註", ""),
                r.get("其餘備註", ""),
            ]
            
            if any(keyword in str(f).lower() for f in search_fields):
                self.filtered_data.append(r)
        
        self.update_table()
        self.update_stats()
    
    def clear_search(self):
        self.search_var.set("")
        self.apply_filter()
    
    def add_record(self):
        self.open_form()
    
    def edit_record(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("請選擇", "請先選取要修改的記錄")
            return
        
        idx = int(selection[0])
        self.open_form(self.filtered_data[idx], idx)
    
    def delete_record(self):
        if not self.tree.selection():
            messagebox.showwarning("請選擇", "請先選取要刪除的記錄")
            return
        
        if not messagebox.askyesno("確認刪除", "確定要刪除選取的記錄嗎？"):
            return
        
        idx = int(self.tree.selection()[0])
        record = self.filtered_data[idx]
        
        if self.firebase.delete_record(record.get("id", "")):
            self.load_data()
            messagebox.showinfo("完成", "記錄已刪除")
        else:
            messagebox.showerror("錯誤", "刪除失敗")
    
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def copy_quote_no(self):
        """複製估價單號"""
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = int(selection[0])
        record = self.filtered_data[idx]
        quote_no = record.get("估價單號", "")
        
        if quote_no:
            self.root.clipboard_clear()
            self.root.clipboard_append(quote_no)
            self.set_status(f"已複製估價單號：{quote_no}")
        else:
            messagebox.showinfo("提示", "無估價單號")
    
    def quick_change_status(self, new_status):
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = int(selection[0])
        record = self.filtered_data[idx]
        
        update_data = {
            "聯繫狀態": new_status,
            "最後聯繫日": datetime.now().strftime("%Y-%m-%d")
        }
        
        success, msg = self.firebase.update_record(record.get("id", ""), update_data)
        if success:
            self.load_data()
            self.set_status(f"已修改狀態為：{new_status}")
        else:
            messagebox.showerror("錯誤", f"更新失敗：{msg}")
    
    def batch_edit_status(self):
        batch_win = tk.Toplevel(self.root)
        batch_win.title("批量修改狀態")
        batch_win.geometry("450x280")
        batch_win.transient(self.root)
        
        tk.Label(batch_win, text="選擇要修改的狀態：", font=(FONT_FAMILY, FONT_SIZES["label"])).pack(pady=20)
        
        new_status_var = tk.StringVar()
        status_combo = ttk.Combobox(batch_win, textvariable=new_status_var, values=CONTACT_STATUSES, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=20)
        status_combo.pack(pady=10)
        
        tk.Label(batch_win, text="將選取的所有記錄狀態改為：", font=(FONT_FAMILY, FONT_SIZES["small"]), fg="gray").pack()
        
        def do_batch_edit():
            new_status = new_status_var.get()
            if not new_status:
                messagebox.showwarning("請選擇", "請選擇新狀態")
                return
            
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("請選擇", "請先選取要修改的記錄")
                return
            
            count = 0
            fail_count = 0
            for item in selection:
                idx = int(item)
                record = self.filtered_data[idx]
                update_data = {
                    "聯繫狀態": new_status,
                    "最後聯繫日": datetime.now().strftime("%Y-%m-%d")
                }
                success, msg = self.firebase.update_record(record.get("id", ""), update_data)
                if success:
                    count += 1
                else:
                    fail_count += 1
            
            self.load_data()
            batch_win.destroy()
            if fail_count == 0:
                self.set_status(f"已批量修改 {count} 筆記錄")
                messagebox.showinfo("完成", f"已修改 {count} 筆記錄")
            else:
                messagebox.showwarning("部分失敗", f"成功：{count} 筆，失敗：{fail_count} 筆")
        
        tk.Button(batch_win, text="確認修改", font=(FONT_FAMILY, FONT_SIZES["button"]), 
                  bg="#27ae60", fg="white", command=do_batch_edit).pack(pady=20)
    
    def open_form(self, record=None, idx=None):
        form = tk.Toplevel(self.root)
        form.title("編輯記錄" if record else "新增記錄")
        form.geometry("600x750")
        form.transient(self.root)
        form.grab_set()
        
        today = datetime.now().strftime("%Y-%m-%d")
        defaults = record or {}
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
        
        canvas = tk.Canvas(form, highlightthickness=0)
        scrollbar = ttk.Scrollbar(form, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        form.update_idletasks()
        
        for field, label, default in all_fields:
            frame = tk.Frame(scrollable_frame)
            frame.pack(fill="x", padx=20, pady=8)
            
            tk.Label(frame, text=label + (" *" if (field, label, default) in required_fields else ""),
                font=(FONT_FAMILY, FONT_SIZES["label"]), width=12, anchor="e").pack(side="left")
            
            value = defaults.get(field, default)
            
            if field == "工程師":
                var = tk.StringVar(value=value)
                ttk.Combobox(frame, textvariable=var, values=ENGINEERS, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=25).pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field == "事項":
                var = tk.StringVar(value=value)
                ttk.Combobox(frame, textvariable=var, values=ITEM_TYPES, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=25).pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field == "是否收取訂金":
                var = tk.StringVar(value=value)
                ttk.Combobox(frame, textvariable=var, values=DEPOSIT_METHODS, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=25).pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field == "聯繫狀態":
                var = tk.StringVar(value=value)
                ttk.Combobox(frame, textvariable=var, values=CONTACT_STATUSES, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=25).pack(side="left", fill="x", expand=True)
                entries[field] = var
                
            elif field in ["料件備註", "其餘備註"]:
                text = tk.Text(frame, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=28, height=3, wrap="word")
                text.pack(side="left", fill="x", expand=True)
                text.insert("1.0", value)
                entries[field] = text
                
            elif field in ["日期", "最後聯繫日"]:
                # 日期欄位 - 使用月曆選擇
                var = tk.StringVar(value=value)
                entry = tk.Entry(frame, textvariable=var, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=20)
                entry.pack(side="left", fill="x", expand=True)
                entry.bind("<Button-1>", lambda e, f=field, v=var: self.open_date_picker(form, f, v))
                entries[field] = var
                
                # 月曆按鈕
                tk.Button(frame, text="📅", font=("Arial", FONT_SIZES["button"]), width=3, relief="flat",
                          command=lambda f=field, v=var: self.open_date_picker(form, f, v)).pack(side="left", padx=2)
                
            else:
                var = tk.StringVar(value=value)
                tk.Entry(frame, textvariable=var, font=(FONT_FAMILY, FONT_SIZES["entry"]), width=28).pack(side="left", fill="x", expand=True)
                entries[field] = var
        
        btn_frame = tk.Frame(form)
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        def format_phone(phone):
            """將電話號碼格式化為 0900-000-000"""
            import re
            # 移除所有非數字
            digits = re.sub(r'\D', '', phone)
            # 如果是 10 碼，格式化
            if len(digits) == 10:
                return f"{digits[:4]}-{digits[4:7]}-{digits[7:]}"
            elif len(digits) == 9:
                return f"{digits[:4]}-{digits[4:7]}-{digits[7:]}"
            return phone
        
        def save():
            # 先驗證
            for field, label, default in required_fields:
                val = entries[field].get() if not isinstance(entries[field], tk.Text) else entries[field].get("1.0", "end").strip()
                if not val:
                    messagebox.showwarning("必填", f"「{label}」為必填欄位")
                    return
            
            new_record = {}
            for field, label, default in all_fields:
                if isinstance(entries[field], tk.Text):
                    value = entries[field].get("1.0", "end").strip()
                else:
                    value = entries[field].get()
                
                # 電話號碼格式化
                if field == "電話" and value:
                    value = format_phone(value)
                
                new_record[field] = value
            
            # 儲存
            try:
                if record:
                    doc_id = record.get("id", "")
                    success, msg = self.firebase.update_record(doc_id, new_record)
                else:
                    success, msg = self.firebase.add_record(new_record)
                
                if success:
                    self.load_data()
                    form.destroy()
                    messagebox.showinfo("完成", "記錄已儲存")
                else:
                    messagebox.showerror("儲存失敗", f"無法儲存資料：\n{msg}\n\n請檢查：\n1. 網路連線\n2. Firebase 權限設定")
            except Exception as e:
                messagebox.showerror("錯誤", f"發生錯誤：{str(e)}")
        
        tk.Button(btn_frame, text="儲存", font=(FONT_FAMILY, FONT_SIZES["button"]),
            bg="#27ae60", fg="white", relief="flat", padx=20, pady=8,
            cursor="hand2", command=save).pack(side="right", padx=5)
        
        tk.Button(btn_frame, text="取消", font=(FONT_FAMILY, FONT_SIZES["button"]),
            bg="#95a5a6", fg="white", relief="flat", padx=20, pady=8,
            cursor="hand2", command=form.destroy).pack(side="right", padx=5)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
