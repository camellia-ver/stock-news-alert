"""
config_manager.py
─────────────────
config.py 의 STOCK_TICKERS / ALERT_THRESHOLD 를 GUI 로 관리하는 도구.
  • KRX / US 탭 분리
  • US 최대 25 종목 제한
  • 더블클릭 → 편집 모드
  • Delete 키 → 삭제
  • Escape 키 → 편집 취소
"""

import ast
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import threading
import urllib.request
import json

US_MAX = 25
FONT   = "맑은 고딕"   # Windows; 다른 OS 에서는 시스템 기본 폰트로 대체됨


# ─────────────────────────────────────────────────────────────────────────────
class ConfigManager(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Stock Config Manager")
        self.geometry("720x590")
        self.minsize(620, 500)
        self.configure(bg="#ECEFF1")

        # 기본 config.py 위치: 이 스크립트와 같은 디렉터리
        self.config_path: str = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.py"
        )
        self.stock_tickers: dict = {"KRX": {}, "US": {}}
        self.alert_threshold: int = 10
        self._editing: dict = {}  # {market: old_ticker}  편집 중인 항목

        self.krx_all: list = []  # (ticker, name) 전체 캐시
        self._krx_loaded: bool = False # 로딩 완료 여부

        self._apply_style()
        self._build_ui()

        threading.Thread(target=self._load_krx_tickers, daemon= True).start()
        self._load()

    def _load_krx_tickers(self) -> None:
        """pykrx로 KRX 전체 종목을 백그라운드에서 로드"""
        try:
            from pykrx import stock
            from datetime import datetime
    
            today = datetime.today().strftime('%Y%m%d')
            tickers = stock.get_market_ticker_list(today, market='ALL')
            self.krx_all = [
                (t, stock.get_market_ticker_name(t)) for t in tickers
            ]
            self._krx_loaded = True

            # UI 스레드에서 상태 표시 갱신
            self.after(0, lambda: self._set_status(
                f'✔ KRX 종목 {len(self.krx_all)}개 로드 완료'
            ))
        except Exception as e:
            self.after(0, lambda:self._set_status(f"⚠ KRX 로드 실패: {e}")))

    # ── 스타일 ───────────────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview",
                     font=(FONT, 10), rowheight=26,
                     background="#FAFAFA", fieldbackground="#FAFAFA")
        s.configure("Treeview.Heading",
                     font=(FONT, 10, "bold"), background="#CFD8DC")
        s.configure("TNotebook.Tab", font=(FONT, 10), padding=[14, 6])
        s.configure("TScrollbar", troughcolor="#ECEFF1")
        s.map("Treeview",
              background=[("selected", "#1565C0")],
              foreground=[("selected", "white")])

    # ── UI 뼈대 ──────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # ── 상단 바 (파일 경로 + 임계값) ─────────────────────────────────
        top = tk.Frame(self, bg="#90A4AE", padx=12, pady=7)
        top.pack(fill="x")

        tk.Label(top, text="설정 파일:", bg="#90A4AE",
                 font=(FONT, 10)).pack(side="left")
        self.path_var = tk.StringVar(value=self.config_path)
        tk.Entry(top, textvariable=self.path_var, width=34,
                 font=(FONT, 10)).pack(side="left", padx=(4, 0))
        self._btn(top, "찾기", self._browse, "#546E7A").pack(side="left", padx=4)
        self._btn(top, "로드", self._load,   "#546E7A").pack(side="left")

        # 임계값 (오른쪽 정렬)
        tk.Label(top, text="변동률 임계값:", bg="#90A4AE",
                 font=(FONT, 10)).pack(side="right", padx=(10, 0))
        self.threshold_var = tk.StringVar(value="10")
        vcmd = (self.register(lambda s: s.isdigit() or s == ""), "%P")
        tk.Entry(top, textvariable=self.threshold_var, width=5,
                 font=(FONT, 10), justify="center",
                 validate="key", validatecommand=vcmd).pack(side="right", padx=2)
        tk.Label(top, text="%", bg="#90A4AE",
                 font=(FONT, 10)).pack(side="right")

        # ── 탭 ──────────────────────────────────────────────────────────
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=6)

        self.tabs: dict = {}
        for market in ("KRX", "US"):
            frame = tk.Frame(nb, bg="#ECEFF1")
            nb.add(frame, text=f"  {market} 종목  ")
            self.tabs[market] = self._build_market_tab(frame, market)

        # ── 하단 바 (상태 표시 + 저장 버튼) ─────────────────────────────
        bot = tk.Frame(self, bg="#ECEFF1", padx=12, pady=8)
        bot.pack(fill="x")

        self.status_var = tk.StringVar(value="파일을 로드하거나 종목을 추가하세요.")
        tk.Label(bot, textvariable=self.status_var, bg="#ECEFF1",
                 font=(FONT, 9), fg="#607D8B", anchor="w").pack(side="left")
        self._btn(bot, "💾  설정 저장", self._save, "#1565C0", size=11).pack(side="right")

    # ── 마켓 탭 ──────────────────────────────────────────────────────────────
    def _build_market_tab(self, parent: tk.Frame, market: str) -> dict:
        """각 마켓 탭의 위젯을 구성하고 참조 dict를 반환"""

        # 정보 행
        info_row = tk.Frame(parent, bg="#ECEFF1")
        info_row.pack(fill="x", padx=10, pady=(8, 2))

        count_lbl = None
        if market == "US":
            count_lbl = tk.Label(info_row, text=f"0 / {US_MAX}개",
                                  bg="#ECEFF1", font=(FONT, 10), fg="#555555")
            count_lbl.pack(side="right")
            tk.Label(info_row, text="US 종목 목록", bg="#ECEFF1",
                     font=(FONT, 10, "bold"), fg="#37474F").pack(side="left")
        else:
            tk.Label(info_row, text="KRX 종목 목록", bg="#ECEFF1",
                     font=(FONT, 10, "bold"), fg="#37474F").pack(side="left")

        # Treeview
        tv_wrap = tk.Frame(parent, bg="#ECEFF1")
        tv_wrap.pack(fill="both", expand=True, padx=10)

        tree = ttk.Treeview(tv_wrap, columns=("ticker", "name"),
                            show="headings", selectmode="browse")
        tree.heading("ticker", text="티커 코드")
        tree.heading("name",   text="종목명")
        tree.column("ticker", width=170, anchor="center", stretch=False)
        tree.column("name",   width=360, anchor="w")

        vsb = ttk.Scrollbar(tv_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # 이벤트
        tree.bind("<Double-1>",        lambda e, m=market: self._on_double_click(m, e))
        tree.bind("<<TreeviewSelect>>",lambda e, m=market: self._on_select(m))
        tree.bind("<Delete>",          lambda e, m=market: self._delete(m))

        # ── 입력 폼 ──────────────────────────────────────────────────
        form = tk.Frame(parent, bg="#ECEFF1", pady=6)
        form.pack(fill="x", padx=10)

        tk.Label(form, text="티커:", bg="#ECEFF1",
                 font=(FONT, 10)).grid(row=0, column=0, sticky="e", padx=(0, 4))
        ticker_var = tk.StringVar()
        ticker_e = tk.Entry(form, textvariable=ticker_var, width=14, font=(FONT, 10))
        ticker_e.grid(row=0, column=1, padx=(0, 14), pady=3)

        tk.Label(form, text="종목명:", bg="#ECEFF1",
                 font=(FONT, 10)).grid(row=0, column=2, sticky="e", padx=(0, 4))
        name_var = tk.StringVar()
        name_e = tk.Entry(form, textvariable=name_var, width=26, font=(FONT, 10))
        name_e.grid(row=0, column=3, pady=3)

        for entry in (ticker_e, name_e):
            entry.bind("<Return>", lambda ev, m=market: self._add(m))
            entry.bind("<Escape>", lambda ev, m=market: self._cancel_edit(m))

        # ── 버튼 행 ──────────────────────────────────────────────────
        btn_row = tk.Frame(parent, bg="#ECEFF1", pady=2, padx=10)
        btn_row.pack(fill="x", anchor="w")

        add_btn = self._btn(btn_row, "+ 추가",
                            lambda m=market: self._add(m), "#2E7D32")
        add_btn.pack(side="left", padx=(0, 6))

        # 수정 확정: 주황 배경 → 어두운 글자(#1A1A1A)로 대비비 4.8:1 확보
        edit_btn = self._btn(btn_row, "✎ 수정 확정",
                             lambda m=market: self._commit_edit(m),
                             "#1A1A1A")
        edit_btn.config(state="disabled", disabledforeground="#7B3A00")
        edit_btn.pack(side="left", padx=(0, 6))

        # 삭제: 진한 빨강 배경 → 아이보리 화이트(#FFF3E0)로 눈부심 감소
        del_btn = self._btn(btn_row, "− 삭제",
                            lambda m=market: self._delete(m),
                            "#FFF3E0")
        del_btn.config(state="disabled", disabledforeground="#EF9A9A")
        del_btn.pack(side="left", padx=(0, 6))

        # 취소: 회색 배경 → 연한 회색(#F5F5F5)으로 순백 대비 눈 부담 경감
        cancel_btn = self._btn(btn_row, "취소",
                               lambda m=market: self._cancel_edit(m),
                               "#F5F5F5")
        cancel_btn.config(state="disabled", disabledforeground="#BDBDBD")
        cancel_btn.pack(side="left")

        return {
            "tree":         tree,
            "ticker_var":   ticker_var,
            "name_var":     name_var,
            "ticker_entry": ticker_e,
            "name_entry":   name_e,
            "count_lbl":    count_lbl,
            "add_btn":      add_btn,
            "edit_btn":     edit_btn,
            "del_btn":      del_btn,
            "cancel_btn":   cancel_btn,
        }

    # ── 버튼 팩토리 ──────────────────────────────────────────────────────────
    def _btn(self, parent, text: str, cmd, color: str,
             size: int = 10, fg: str = "white") -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         font=(FONT, size), bg=color, fg=fg,
                         padx=10, pady=4, relief="flat", cursor="hand2",
                         activebackground=color, activeforeground=fg)

    # ── 화면 갱신 ─────────────────────────────────────────────────────────────
    def _refresh(self, market: str = None) -> None:
        targets = [market] if market else list(self.tabs.keys())
        for m in targets:
            w    = self.tabs[m]
            tree: ttk.Treeview = w["tree"]
            tree.delete(*tree.get_children())
            for ticker, name in self.stock_tickers.get(m, {}).items():
                tree.insert("", "end", iid=ticker, values=(ticker, name))
            if w["count_lbl"]:
                n  = len(self.stock_tickers.get(m, {}))
                fg = "#B71C1C" if n >= US_MAX else "#555555"
                w["count_lbl"].config(text=f"{n} / {US_MAX}개", fg=fg)

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)

    # ── 이벤트 핸들러 ─────────────────────────────────────────────────────────
    def _on_select(self, market: str) -> None:
        """항목 선택 시 삭제 버튼 활성화 (편집 중이 아닐 때)"""
        if market not in self._editing:
            w       = self.tabs[market]
            has_sel = bool(w["tree"].selection())
            w["del_btn"].config(state="normal" if has_sel else "disabled")

    def _on_double_click(self, market: str, event: tk.Event) -> None:
        """더블클릭 → 편집 모드 진입"""
        w    = self.tabs[market]
        tree = w["tree"]

        # 헤더 클릭이면 무시
        if tree.identify_region(event.x, event.y) == "heading":
            return

        sel = tree.selection()
        if not sel:
            return
        ticker = sel[0]
        name   = self.stock_tickers[market].get(ticker, "")

        self._editing[market] = ticker
        w["ticker_var"].set(ticker)
        w["name_var"].set(name)

        w["add_btn"].config(state="disabled")
        w["edit_btn"].config(state="normal")
        w["del_btn"].config(state="disabled")
        w["cancel_btn"].config(state="normal")

        w["ticker_entry"].focus_set()
        w["ticker_entry"].select_range(0, "end")
        self._set_status(f"✎ '{ticker}' 편집 중 — 수정 후 [수정 확정] 또는 Escape 로 취소")

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self, market: str) -> None:
        w      = self.tabs[market]
        ticker = w["ticker_var"].get().strip().upper()
        name   = w["name_var"].get().strip()

        if not ticker or not name:
            messagebox.showwarning("입력 오류", "티커와 종목명을 모두 입력하세요.", parent=self)
            return

        tickers = self.stock_tickers.setdefault(market, {})

        if market == "US" and len(tickers) >= US_MAX:
            messagebox.showwarning(
                "제한 초과",
                f"US 종목은 최대 {US_MAX}개까지 추가할 수 있습니다.\n"
                f"현재 {len(tickers)}개 등록됨.",
                parent=self,
            )
            return

        if ticker in tickers:
            messagebox.showwarning("중복 오류",
                                   f"'{ticker}'는 이미 등록된 티커입니다.", parent=self)
            return

        tickers[ticker] = name
        self._refresh(market)
        w["ticker_var"].set("")
        w["name_var"].set("")
        w["ticker_entry"].focus_set()
        self._set_status(f"✔ '{ticker}' 추가 완료")

    def _commit_edit(self, market: str) -> None:
        """편집 내용 확정"""
        if market not in self._editing:
            return
        w          = self.tabs[market]
        old_ticker = self._editing[market]
        new_ticker = w["ticker_var"].get().strip().upper()
        new_name   = w["name_var"].get().strip()

        if not new_ticker or not new_name:
            messagebox.showwarning("입력 오류", "티커와 종목명을 모두 입력하세요.", parent=self)
            return

        tickers = self.stock_tickers[market]
        if new_ticker != old_ticker and new_ticker in tickers:
            messagebox.showwarning("중복 오류",
                                   f"'{new_ticker}'는 이미 등록된 티커입니다.", parent=self)
            return

        del tickers[old_ticker]
        tickers[new_ticker] = new_name
        self._cancel_edit(market)
        self._refresh(market)
        self._set_status(f"✔ '{old_ticker}' → '{new_ticker}' 수정 완료")

    def _cancel_edit(self, market: str) -> None:
        """편집 모드 취소"""
        self._editing.pop(market, None)
        w = self.tabs[market]
        w["ticker_var"].set("")
        w["name_var"].set("")
        w["add_btn"].config(state="normal")
        w["edit_btn"].config(state="disabled")
        w["del_btn"].config(state="disabled")
        w["cancel_btn"].config(state="disabled")
        self._set_status("편집이 취소되었습니다.")

    def _delete(self, market: str) -> None:
        """선택 항목 삭제"""
        w   = self.tabs[market]
        sel = w["tree"].selection()
        if not sel:
            return
        ticker = sel[0]
        if messagebox.askyesno("삭제 확인",
                               f"'{ticker}' 종목을 삭제하시겠습니까?", parent=self):
            del self.stock_tickers[market][ticker]
            self._refresh(market)
            w["del_btn"].config(state="disabled")
            self._set_status(f"✔ '{ticker}' 삭제 완료")

    # ── 파일 I/O ──────────────────────────────────────────────────────────────
    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="config.py 선택",
            filetypes=[("Python 파일", "*.py"), ("모든 파일", "*.*")],
            parent=self,
        )
        if path:
            self.path_var.set(path)

    def _load(self) -> None:
        path = self.path_var.get().strip()
        if not os.path.exists(path):
            messagebox.showwarning("파일 없음",
                                   f"파일을 찾을 수 없습니다:\n{path}", parent=self)
            self._set_status(f"⚠ 파일 없음: {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()

            parsed_tree = ast.parse(src)
            for node in ast.walk(parsed_tree):
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            if t.id == "STOCK_TICKERS":
                                self.stock_tickers = ast.literal_eval(node.value)
                            elif t.id == "ALERT_THRESHOLD":
                                self.alert_threshold = ast.literal_eval(node.value)

            # 탭에 없는 마켓 키 보장
            self.stock_tickers.setdefault("KRX", {})
            self.stock_tickers.setdefault("US",  {})
            self.threshold_var.set(str(self.alert_threshold))
            self.config_path = path
            self._refresh()
            self._set_status(f"✔ 로드 완료: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("로드 오류", f"파일 로드 실패:\n{exc}", parent=self)
            self._set_status("✘ 로드 실패")

    def _save(self) -> None:
        path = self.path_var.get().strip()

        raw = self.threshold_var.get().strip()
        if not raw or not raw.isdigit():
            messagebox.showwarning("입력 오류", "임계값은 양의 정수로 입력하세요.", parent=self)
            return
        threshold = int(raw)

        lines = [
            "# config.py\n",
            "STOCK_TICKERS = {\n",
        ]
        for market, tickers in self.stock_tickers.items():
            lines.append(f"    '{market}': {{\n")
            for ticker, name in tickers.items():
                lines.append(f'        "{ticker}": "{name}",\n')
            lines.append("    },\n")
        lines.append("} # 모니터링 종목\n")
        lines.append(f"\nALERT_THRESHOLD = {threshold}  # 변동률 임계값 (%)\n")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            messagebox.showinfo("저장 완료", "설정이 저장되었습니다.", parent=self)
            self._set_status(f"✔ 저장 완료: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("저장 오류", f"파일 저장 실패:\n{exc}", parent=self)
            self._set_status("✘ 저장 실패")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ConfigManager()
    app.mainloop()