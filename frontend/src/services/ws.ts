/**
 * WebSocket 消息构造辅助函数
 */

import type { WsMessage } from "@/hooks/useWebSocket";

/** 构造 chat 消息 */
export function buildChatMessage(message: string, sessionId: string): WsMessage {
  return {
    type: "chat",
    payload: { message, session_id: sessionId },
  };
}

/** 构造 approval 消息 */
export function buildApprovalMessage(
  sessionId: string,
  action: "approve" | "reject"
): WsMessage {
  return {
    type: "approval",
    payload: { session_id: sessionId, action },
  };
}
