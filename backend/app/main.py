"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from app.config import settings
from app.api.endpoints import router
from app.api.resume import router as resume_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.agent.graph import init_graph

    await init_graph()
    print("🚀 Fund Agent API 启动完成")
    yield


app = FastAPI(title="Fund Agent API", lifespan=lifespan)
app.include_router(router, prefix="/api")
app.include_router(resume_router, prefix="/api")

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


# 启动命令：python -m uvicorn app.main:app --reload
