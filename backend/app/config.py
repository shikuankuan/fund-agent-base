"""
配置管理模块
使用 pydantic-settings 从环境变量和 .env 文件加载配置
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""

    # OpenAI配置
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # 服务配置
    APP_ENV: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 日志配置
    LOG_LEVEL: str = "INFO"

    class Config:
        """Pydantic配置"""

        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()

# 方便调试：打印当前配置（注意：不要打印API Key！）
if settings.DEBUG:
    print(f"当前环境: {settings.APP_ENV}")
    print(f"API_KEY: {settings.OPENAI_API_KEY}")
    print(f"使用的模型: {settings.OPENAI_MODEL}")
    print(f"服务端口: {settings.PORT}")
