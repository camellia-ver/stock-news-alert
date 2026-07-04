from google import genai
from google.genai import errors as genai_errors
from utils.logger import get_logger
from settings import GEMINI_API_KEY

logger = get_logger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
PROMPT_TEMPLATE = "{data}\n\n이 내용들을 참고로 주식 인사이트를 생성해줘"

class Summarizer:
    def __init__(self, model: str = DEFAULT_MODEL):
        self._model = model
        self._client = genai.Client(api_key=GEMINI_API_KEY)

    def summarizer_by_gemini(self, data: str) -> str | None:
        if not data:
            logger.warning("summarize_by_gemini called with empty data")
            return
        
        prompt = PROMPT_TEMPLATE.format(data = data)

        try:
            response = self._client.models.generate_content(
                model= self._model,
                contents= prompt
            )
        except genai_errors.APIError as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            return None
        
        if not response.text:
            logger.warning("Gemini 응답에 텍스트가 없음")
            return None
        
        return response.text