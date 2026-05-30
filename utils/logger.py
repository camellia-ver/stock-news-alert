import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_initialized = False

def setup_logging(level=logging.DEBUG):
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger()  # 루트 로거
    root.setLevel(level)

    fmt = logging.Formatter(_FMT, datefmt=_DATEFMT)

    # 콘솔 핸들러 (INFO 이상만 출력)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    date_str = datetime.now().strftime('%Y-%m-%d')
    # 파일 핸들러 (자정마다 롤링, 30일 보관)
    fh = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / f'app_{date_str}.log', when='midnight', backupCount=30, encoding='utf-8', delay=True
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    root.addHandler(ch)
    root.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)