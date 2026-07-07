import ast
import json
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from utils.logger import get_logger
from settings import DATA_GO_KR_SERVICE_KEY

logger = get_logger(__name__)

FONT   = "맑은 고딕"   # Windows; 다른 OS 에서는 시스템 기본 폰트로 대체됨

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILES = {
    "KRX": os.path.join(CACHE_DIR, "./stock_list/listing_cache_KRX.json"),
    "US":  os.path.join(CACHE_DIR, "./stock_list/listing_cache_US.json"),
}


# ─────────────────────────────────────────────────────────────────────────────
class ConfigManager(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Stock Config Manager")
        self.geometry("720x610")
        self.minsize(620, 520)
        self.configure(bg="#ECEFF1")

        # 기본 config.py 위치: 이 스크립트와 같은 디렉터리
        self.config_path: str = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.py"
        )
        self.stock_tickers: dict = {"KRX": {}, "US": {}}
        self.alert_threshold: int = 10
        self._editing: dict = {}  # {market: old_ticker}  편집 중인 항목

        # market -> {ticker: name} 전체 상장 종목 목록 (자동완성용)
        self.master_data: dict = {"KRX": {}, "US": {}}

        # name_var를 프로그램적으로 set()할 때 trace 콜백(_on_name_changed)이
        # 다시 드롭다운을 열거나 포커스를 뺏지 않도록 막는 플래그
        self._suppress_name_trace = False

        self._service_key = DATA_GO_KR_SERVICE_KEY

        self._apply_style()
        self._build_ui()
        self._load()
        self._load_master_data_async()

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
        s.configure("TCombobox", font=(FONT, 10))
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

        if market == "US":
            tk.Label(info_row, text="US 종목 목록", bg="#ECEFF1",
                     font=(FONT, 10, "bold"), fg="#37474F").pack(side="left")
        else:
            tk.Label(info_row, text="KRX 종목 목록", bg="#ECEFF1",
                     font=(FONT, 10, "bold"), fg="#37474F").pack(side="left")

        refresh_btn = self._btn(info_row, "⟳ 종목목록 새로고침",
                                lambda m=market: self._refresh_master_data(m),
                                "#546E7A", size=9)
        refresh_btn.pack(side="right", padx=(0, 10) if market == "US" else 0)

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
        ticker_cb = ttk.Combobox(form, textvariable=ticker_var, width=14,
                                  font=(FONT, 10))
        ticker_cb.grid(row=0, column=1, padx=(0, 14), pady=3)

        tk.Label(form, text="종목명:", bg="#ECEFF1",
                 font=(FONT, 10)).grid(row=0, column=2, sticky="e", padx=(0, 4))
        name_var = tk.StringVar()
        # 종목명도 티커와 동일하게 타이핑 → 실시간 필터링 → 선택 시 티커 자동 채움
        name_cb = ttk.Combobox(form, textvariable=name_var, width=26, font=(FONT, 10))
        name_cb.grid(row=0, column=3, pady=3)

        # 자동완성: 타이핑할 때마다 후보 필터링 (티커 → 종목명)
        ticker_cb.bind("<KeyRelease>", lambda e, m=market: self._on_ticker_keyrelease(e, m))
        # 드롭다운에서 항목 선택 시 종목명 자동 채움
        ticker_cb.bind("<<ComboboxSelected>>", lambda e, m=market: self._on_ticker_selected(e, m))
        ticker_cb.bind("<Return>", lambda ev, m=market: self._add(m))
        ticker_cb.bind("<Escape>", lambda ev, m=market: self._cancel_edit(m))

        # 자동완성: 값이 바뀔 때마다 후보 필터링 (종목명 → 티커, 포함 문자 매칭)
        # KeyRelease 대신 trace_add(write)를 쓰는 이유: 한글은 자소가 조합되는 IME 특성상
        # KeyRelease 시점에 위젯 버퍼가 아직 갱신되지 않아 한 글자 뒤처진 값으로 검색되는
        # 문제가 있다. trace_add는 StringVar 값이 실제로 바뀐 시점에 정확히 반응한다.
        name_var.trace_add("write", lambda *args, m=market: self._on_name_changed(m))
        # 드롭다운에서 항목 선택 시 티커 자동 채움
        name_cb.bind("<<ComboboxSelected>>", lambda e, m=market: self._on_name_selected(e, m))
        name_cb.bind("<Return>", lambda ev, m=market: self._add(m))
        name_cb.bind("<Escape>", lambda ev, m=market: self._cancel_edit(m))

        # ── 버튼 행 ──────────────────────────────────────────────────
        btn_row = tk.Frame(parent, bg="#ECEFF1", pady=2, padx=10)
        btn_row.pack(fill="x", anchor="w")

        add_btn = self._btn(btn_row, "+ 추가",
                            lambda m=market: self._add(m), "#2E7D32")
        add_btn.pack(side="left", padx=(0, 6))

        # 수정 확정: 주황 배경 → 어두운 글자(#1A1A1A)로 대비비 4.8:1 확보
        edit_btn = self._btn(btn_row, "✎ 수정 확정",
                             lambda m=market: self._commit_edit(m),
                             "#E65100", fg="#1A1A1A")
        edit_btn.config(state="disabled", disabledforeground="#7B3A00")
        edit_btn.pack(side="left", padx=(0, 6))

        # 삭제: 진한 빨강 배경 → 아이보리 화이트(#FFF3E0)로 눈부심 감소
        del_btn = self._btn(btn_row, "− 삭제",
                            lambda m=market: self._delete(m),
                            "#B71C1C", fg="#FFF3E0")
        del_btn.config(state="disabled", disabledforeground="#EF9A9A")
        del_btn.pack(side="left", padx=(0, 6))

        # 취소: 회색 배경 → 연한 회색(#F5F5F5)으로 순백 대비 눈 부담 경감
        cancel_btn = self._btn(btn_row, "취소",
                               lambda m=market: self._cancel_edit(m),
                               "#757575", fg="#F5F5F5")
        cancel_btn.config(state="disabled", disabledforeground="#BDBDBD")
        cancel_btn.pack(side="left")

        return {
            "tree":         tree,
            "ticker_var":   ticker_var,
            "name_var":     name_var,
            "ticker_entry": ticker_cb,
            "name_entry":   name_cb,
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

    # ── name_var 프로그램적 설정 헬퍼 ────────────────────────────────────────
    def _set_name_var(self, market: str, value: str) -> None:
        """
        name_var를 코드에서 직접 설정할 때 사용한다.
        trace_add로 걸어둔 _on_name_changed가 함께 트리거되면
        드롭다운이 제멋대로 다시 열리거나 포커스를 뺏어가므로,
        이 경우에는 trace 콜백을 잠시 무시하도록 플래그를 세운다.
        """
        self._suppress_name_trace = True
        try:
            self.tabs[market]["name_var"].set(value)
        finally:
            self._suppress_name_trace = False

    # ── 전체 종목 목록 로딩 (자동완성용) ────────────────────────────────────────
    def _load_master_data_async(self) -> None:
        """앱 시작 시 백그라운드 스레드로 전체 상장 종목 목록을 로드"""
        self._set_status("⏳ 종목 목록 로딩 중... (최초 실행 시 다소 시간이 걸릴 수 있습니다)")
        threading.Thread(target=self._load_master_data_worker, daemon=True).start()

    def _load_master_data_worker(self, markets=("KRX", "US")) -> None:
        import traceback
        errors = []
        for market in markets:
            try:
                data = self._load_or_fetch_listing(market)
                self.master_data[market] = data
                logger.info(f'{market}: {len(data)}건 로드됨')
            except Exception as exc:
                tb = traceback.format_exc()
                logger.error(f'{market} 로드 실패:\n{tb}')
                errors.append(f"{market}: {exc}")

        def _done():
            if errors:
                self._set_status("⚠ 종목 목록 로딩 일부 실패 - " + " / ".join(errors)
                                  + " (자세한 내용은 터미널 콘솔 확인)")
            else:
                n_krx = len(self.master_data.get("KRX", {}))
                n_us  = len(self.master_data.get("US", {}))
                self._set_status(f"✔ 종목 목록 로딩 완료 (KRX {n_krx}개, US {n_us}개)")
        self.after(0, _done)

    def _refresh_master_data(self, market: str) -> None:
        """지정한 마켓의 종목 목록 캐시를 삭제하고 다시 받아옴"""
        cache_path = CACHE_FILES[market]
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except OSError:
                pass
        self._set_status(f"⏳ {market} 종목 목록 새로고침 중...")
        threading.Thread(target=self._load_master_data_worker,
                         kwargs={"markets": (market,)}, daemon=True).start()

    def _load_or_fetch_listing(self, market: str) -> dict:
        cache_path = CACHE_FILES[market]
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if cached:
                    return cached  # 캐시가 있으면 이 값을 그대로 반환한다 (수정됨)
                logger.info(f'{market} 캐시가 비어있어 재수집합니다: {cache_path}')
            except Exception as exc:
                logger.error(f'{market} 캐시 로드 실패, 재수집합니다: {exc}')

        data = self._fetch_listing(market)
        if not data:
            raise RuntimeError(f"{market} 종목 목록이 비어 있습니다 (FinanceDataReader 응답 확인 필요)")

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            logger.info(f'{market} 캐시 저장 완료: {cache_path}')
        except OSError as exc:
            # 캐싱 실패해도 이번 실행에서는 메모리상 데이터로 계속 동작하지만,
            # 콘솔에는 반드시 남겨서 원인을 알 수 있게 한다.
            logger.debug(f'{market} 캐시 저장 실패 ({cache_path}): {exc}')
        return data

    # ── KRX 종목코드 정규화 ─────────────────────────────────────────────────
    @staticmethod
    def _normalize_krx_code(raw_code: str) -> str:
        """
        금융위원회 공공데이터 API(및 DART 계열)는 종목코드 앞에
        'A' 접두어를 붙여서 반환하는 경우가 많다 (예: A005930 → 005930).
        실제 6자리 KRX 코드로 정규화한다.
        """
        code = (raw_code or "").strip().upper()
        if code.startswith("A") and len(code) > 1 and code[1:].isdigit():
            code = code[1:]
        return code

    # ── KRX 상장 종목 목록 조회 (공공데이터포털) ──────────────────────────────
    def _fetch_krx_listing_for_date(self, date_str: str, headers: dict,
                                     max_retries: int = 3) -> dict:
        """
        지정한 기준일자(date_str, YYYYMMDD)의 상장 종목 목록을 페이지네이션하며
        수집한다. 페이지 중간에 오류가 나도 그때까지 모은 데이터는 보존하고,
        각 페이지 요청은 최대 max_retries 회까지 재시도한다.
        """
        import requests

        API_URL = "https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo"

        fetched: dict = {}
        page_no = 1
        num_of_rows = 500  # 한 번에 너무 많이 요청하면 타임아웃 위험이 있어 적당히 제한
        total_count = None

        while True:
            params = {
                "serviceKey": self._service_key,
                "resultType": "json",
                "basDt": date_str,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            }

            data = None
            for attempt in range(1, max_retries + 1):
                try:
                    resp = requests.get(API_URL, params=params, headers=headers, timeout=20)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except Exception as exc:
                    logger.error(f'[KRX] {date_str} page={page_no} 시도 {attempt}/{max_retries} 실패: {exc}')
                    if attempt == max_retries:
                        # 이 페이지는 끝내 실패 → 지금까지 모은 것만이라도 반환
                        return fetched
                    time.sleep(1.5 * attempt)

            header = (data or {}).get("response", {}).get("header", {})
            result_code = header.get("resultCode")
            if result_code not in (None, "00", 0, "0"):
                logger.error(f'[KRX] API 에러 응답: {header}')
                return fetched

            body = (data or {}).get("response", {}).get("body", {})
            items = body.get("items", {})
            item_list = items.get("item", []) if isinstance(items, dict) else []
            if isinstance(item_list, dict):  # 결과가 1건이면 dict로 오는 경우 대비
                item_list = [item_list]

            if total_count is None:
                total_count = int(body.get("totalCount", 0) or 0)
                logger.info(f'[KRX] {date_str} 전체 종목 수(totalCount): {total_count}')

            if not item_list:
                break

            for item in item_list:
                raw_code = item.get("srtnCd")  # 단축코드(종목코드), 'A' 접두어가 붙는 경우가 있음
                name = item.get("itmsNm")      # 종목명
                if raw_code and name:
                    code = self._normalize_krx_code(raw_code)
                    if code:
                        fetched[code] = name

            logger.info(f'[KRX] {date_str} page={page_no} 누적 수집: {len(fetched)}/{total_count}')

            if page_no * num_of_rows >= total_count:
                break
            page_no += 1

        return fetched

    def _fetch_listing(self, market: str) -> dict:
        """전체 상장 종목(티커→종목명)을 가져온다. KRX는 공공데이터포털, US는 FinanceDataReader 사용."""
        result: dict = {}

        if market == "KRX":
            if not self._service_key:
                raise RuntimeError(
                    "공공데이터포털 서비스키(DATA_GO_KR_SERVICE_KEY)가 설정되어 있지 않습니다."
                )

            try:
                import requests  # noqa: F401  (사용 여부 사전 체크용)
            except ImportError as exc:
                raise RuntimeError(
                    "requests 가 설치되어 있지 않습니다. 'pip install requests' 로 설치하세요."
                ) from exc

            import datetime

            HEADERS = {
                # 공공데이터포털 게이트웨이가 기본 python-requests User-Agent를
                # 차단하는 경우가 있어 브라우저처럼 보이는 UA를 명시적으로 지정한다.
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/124.0.0.0 Safari/537.36"),
            }

            today = datetime.date.today()

            for i in range(10):  # 휴장일 대비, 최근 영업일을 찾을 때까지 최대 10일 역산
                date_str = (today - datetime.timedelta(days=i)).strftime("%Y%m%d")
                fetched = self._fetch_krx_listing_for_date(date_str, HEADERS)
                if fetched:
                    result = fetched
                    break

            if not result:
                raise RuntimeError("공공데이터포털(KRX상장종목정보)에서 상장 종목 목록을 가져오지 못했습니다.")

            logger.info(f'KRX(공공데이터포털) 조회 완료: {len(result)}건')
        else:  # US: 주요 거래소 통합
            try:
                import FinanceDataReader as fdr
            except ImportError as exc:
                raise RuntimeError(
                    "FinanceDataReader 가 설치되어 있지 않습니다. "
                    "'pip install finance-datareader' 로 설치하세요."
                ) from exc

            def _collect(df, code_candidates, name_candidates):
                code_col = next((c for c in code_candidates if c in df.columns), df.columns[0])
                name_col = next((c for c in name_candidates if c in df.columns), df.columns[1])
                for _, row in df.iterrows():
                    code = str(row[code_col]).strip()
                    name = str(row[name_col]).strip()
                    if code and code not in result:
                        result[code] = name

            for exch in ("NASDAQ", "NYSE", "AMEX"):
                try:
                    df = fdr.StockListing(exch)
                except Exception:
                    continue
                _collect(df, ("Symbol", "Code"), ("Name",))

            logger.info(f'US(FinanceDataReader) 조회 완료: {len(result)}건')

        return result

    # ── 자동완성 이벤트 ───────────────────────────────────────────────────────
    def _on_ticker_keyrelease(self, event: tk.Event, market: str) -> None:
        # 방향키/엔터/이스케이프/탭은 필터링 대상에서 제외
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Left", "Right"):
            return

        w     = self.tabs[market]
        combo: ttk.Combobox = w["ticker_entry"]
        typed = combo.get().strip().upper()
        master = self.master_data.get(market, {}) or {}

        if not master:
            return  # 아직 목록 로딩 전

        if typed:
            matches = [t for t in master if t.upper().startswith(typed)]
            if not matches:
                matches = [t for t in master if typed in t.upper()]
        else:
            matches = list(master.keys())

        combo["values"] = matches[:50]

        # 주의: 자세한 이유는 _on_name_changed 쪽 주석 참고.
        # 타이핑 중 매번 Post를 호출하면 popdown이 키보드 grab을 계속 쥐게 되어
        # 다음 글자 입력이 씹히는 문제가 생기므로, 여기서는 values만 갱신한다.

        # 정확히 일치하는 티커면 종목명 자동 채움, 아니면 비움 (프로그램적 설정 → trace 억제)
        self._set_name_var(market, master.get(typed, ""))

    def _on_ticker_selected(self, event: tk.Event, market: str) -> None:
        w      = self.tabs[market]
        ticker = w["ticker_var"].get().strip().upper()
        name   = (self.master_data.get(market, {}) or {}).get(ticker, "")
        self._set_name_var(market, name)

    def _on_name_changed(self, market: str) -> None:
        """name_var 값이 바뀔 때마다 호출된다 (사용자 타이핑 + 프로그램적 변경 모두 포함).

        단, 프로그램적으로 값을 세팅할 때는 _set_name_var()를 통해
        _suppress_name_trace 플래그를 세우므로, 그 경우 여기서는 아무 것도 하지 않고
        사용자가 실제로 타이핑한 경우에만 필터링/드롭다운 로직을 수행한다.
        """
        if self._suppress_name_trace:
            return

        w = self.tabs[market]
        combo: ttk.Combobox = w["name_entry"]
        typed = w["name_var"].get().strip()
        master = self.master_data.get(market, {}) or {}

        if not master:
            return

        if typed:
            typed_lower = typed.lower()
            matches = [(t, n) for t, n in master.items() if typed_lower in n.lower()]
        else:
            matches = list(master.items())

        combo["values"] = [f"{t} - {n}" for t, n in matches[:50]]

        # 주의: 여기서 ttk::combobox::Post를 호출해 드롭다운을 자동으로 열면 안 된다.
        # Post는 popdown 리스트에 키보드 grab을 걸어버리는데, 이 grab은 드롭다운이
        # 떠 있는 동안 계속 유지된다. 타이핑할 때마다 Post를 부르면 매 글자 입력 후
        # grab이 popdown으로 넘어가서 다음 글자가 입력창에 닿지 못하고 씹히는
        # 문제가 생긴다(방향키로 포커스를 되찾아야만 다시 입력되는 증상).
        # 목록(values)만 갱신해두면 사용자가 아래 화살표나 드롭다운 버튼을 눌렀을 때
        # 최신 필터링 결과가 정상적으로 보인다.

        # 입력한 문자열과 정확히 일치하는 종목명이 단 하나뿐이면 티커 자동 채움
        exact = [(t, n) for t, n in master.items() if n.lower() == typed.lower()] if typed else []
        if len(exact) == 1:
            w["ticker_var"].set(exact[0][0])
        else:
            w["ticker_var"].set("")

    def _on_name_selected(self, event: tk.Event, market: str) -> None:
        w        = self.tabs[market]
        selected = w["name_var"].get()
        # "티커 - 종목명" 형태에서 분리
        if " - " in selected:
            ticker, name = selected.split(" - ", 1)
        else:
            ticker, name = "", selected
        w["ticker_var"].set(ticker.strip())
        self._set_name_var(market, name.strip())

    # ── 화면 갱신 ─────────────────────────────────────────────────────────────
    def _refresh(self, market: str = None) -> None:
        targets = [market] if market else list(self.tabs.keys())
        for m in targets:
            w    = self.tabs[m]
            tree: ttk.Treeview = w["tree"]
            tree.delete(*tree.get_children())
            for ticker, name in self.stock_tickers.get(m, {}).items():
                tree.insert("", "end", iid=ticker, values=(ticker, name))

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
        self._set_name_var(market, name)

        w["add_btn"].config(state="disabled")
        w["edit_btn"].config(state="normal")
        w["del_btn"].config(state="disabled")
        w["cancel_btn"].config(state="normal")

        w["ticker_entry"].focus_set()
        w["ticker_entry"].selection_range(0, "end")
        self._set_status(f"✎ '{ticker}' 편집 중 — 수정 후 [수정 확정] 또는 Escape 로 취소")

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _add(self, market: str) -> None:
        w      = self.tabs[market]
        ticker = w["ticker_var"].get().strip().upper()
        name   = w["name_var"].get().strip()

        if not ticker:
            messagebox.showwarning("입력 오류", "티커를 입력하세요.", parent=self)
            return

        master = self.master_data.get(market, {})
        if master and ticker not in master:
            messagebox.showwarning(
                "목록에 없는 티커",
                f"'{ticker}'는 종목 목록에서 찾을 수 없습니다.\n"
                "드롭다운에서 종목을 선택해 주세요.",
                parent=self,
            )
            return

        if not name:
            messagebox.showwarning("입력 오류", "종목명을 확인할 수 없습니다. "
                                   "드롭다운에서 종목을 다시 선택해 주세요.", parent=self)
            return

        tickers = self.stock_tickers.setdefault(market, {})

        if ticker in tickers:
            messagebox.showwarning("중복 오류",
                                   f"'{ticker}'는 이미 등록된 티커입니다.", parent=self)
            return

        tickers[ticker] = name
        self._refresh(market)
        w["ticker_var"].set("")
        self._set_name_var(market, "")
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

        if not new_ticker:
            messagebox.showwarning("입력 오류", "티커를 입력하세요.", parent=self)
            return

        master = self.master_data.get(market, {})
        if master and new_ticker not in master:
            messagebox.showwarning(
                "목록에 없는 티커",
                f"'{new_ticker}'는 종목 목록에서 찾을 수 없습니다.\n"
                "드롭다운에서 종목을 선택해 주세요.",
                parent=self,
            )
            return

        if not new_name:
            messagebox.showwarning("입력 오류", "종목명을 확인할 수 없습니다. "
                                   "드롭다운에서 종목을 다시 선택해 주세요.", parent=self)
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
        self._set_name_var(market, "")
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