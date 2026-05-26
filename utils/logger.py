import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

_FMT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str, level=logging.DEBUG) -> logging.Logger:
    """모듈 이름을 받아 콘솔+파일 핸들러가 붙은 로거 반환"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger
    
    logger.setLevel(level)

    fmt = logging.Formatter(_FMT, datefmt=_DATEFMT)

    # 콘솔 핸들러 (INFO 이상만 출력)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # 파일 핸들러 (자정마다 롤링, 30일 보관)
    fh = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / 'app.log', when='midnight', backupCount=30, encoding='utf-8'
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger