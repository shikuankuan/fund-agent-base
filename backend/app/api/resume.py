"""API 路由定义"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.agent.graph import get_graph


class ResumeRequest(BaseModel):
    """恢复/审批请求"""

    session_id: str
    action: str  # "approve" 通过放行 / "reject" 驳回
    modified_result: Optional[dict] = None  # 驳回时，可选提供修正后的合规结果


router = APIRouter()


@router.post("/approval")
async def approve_or_reject(request: ResumeRequest):
    """人工审批接口 — 支持 pass/warn/block 分级

    approve: 放行，继续执行 response_generator
    reject:  驳回，覆盖 final_response 为拦截提示
    """
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        # 1. 读取当前中断状态
        current = await get_graph().aget_state(config)
        compliance = current.values.get("compliance_result", {})
        grade = compliance.get("grade", "pass")

        # 2. 审批逻辑
        if request.action == "approve":
            # 人工放行：继续往下执行
            print(f"[审批] {request.session_id}: ✅ 人工放行 (原评级: {grade})")
            result = await get_graph().ainvoke(None, config=config)

        elif request.action == "reject":
            # 人工驳回：覆盖最终回复
            print(f"[审批] {request.session_id}: ❌ 人工驳回 (原评级: {grade})")

            # 收集所有未通过的检查项
            failed_checks = [
                c["detail"] for c in compliance.get("checks", []) if not c["passed"]
            ]

            reject_msg = (
                "⚠️ **合规审查未通过**\n\n"
                + "\n".join(f"- {c}" for c in failed_checks)
                + "\n\n请修改您的问题后重试。投资有风险，过往业绩不预示未来表现。"
            )

            # 修改状态，注入拦截回复
            await get_graph().aupdate_state(
                config,
                {
                    "compliance_result": {**compliance, "human_override": "rejected"},
                    "final_response": reject_msg,
                },
            )
            return {
                "reply": reject_msg,
                "session_id": request.session_id,
                "status": "rejected",
                "grade": grade,
            }

        else:
            return {
                "error": f"未知操作: {request.action}",
                "valid_actions": ["approve", "reject"],
            }

        # 3. 返回结果
        final_response = result.get("final_response", "")
        return {
            "reply": final_response,
            "session_id": request.session_id,
            "status": "resumed",
            "grade": grade,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
