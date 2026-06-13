"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from app.config import settings
from app.api.endpoints import router

app = FastAPI(title="Fund Agent API")
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    # 如果在开发模式下启用重载，需要以字符串形式传递应用
    if settings.DEBUG:
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            reload_dirs=["./"],
        )
    else:
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
        )
