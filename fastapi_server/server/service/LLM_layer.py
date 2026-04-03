import logging
import os

from openai import OpenAI


logger = logging.getLogger(__name__)
class LLMAnalyzer:
    def __init__(self):
        """
        初始化大模型分析层
        """
        logger.info("正从.env中读取api_keys")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        chatGPT_api_key = os.getenv("CHATGPT_API_KEY")


