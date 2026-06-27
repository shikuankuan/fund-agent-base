/**
 * useWebSocket — React WebSocket 管理 Hook
 *
 * 功能：
 * - 自动连接 / 断开
 * - 心跳保活（每 30 秒 ping，10 秒内无 pong 则重连）
 * - 自动重连（指数退避：1s → 2s → 4s → ... → 最大 30s）
 * - 消息类型注册回调
 * - 暴露 send() 发送方法
 */

import { useEffect, useRef, useCallback, useState } from "react";

// ════════════════════════════════════════
// 类型定义
// ════════════════════════════════════════

/** WebSocket 连接状态 */
export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "reconnecting";

/** 消息协议（与后端一致） */
export interface WsMessage {
  type: string;
  payload: Record<string, unknown>;
}

/** 消息处理器 */
type MessageHandler = (msg: WsMessage) => void;

/** Hook 配置 */
interface UseWebSocketOptions {
  /** WebSocket 服务端地址 */
  url: string;
  /** 是否自动连接（默认 true） */
  autoConnect?: boolean;
  /** 心跳间隔（毫秒，默认 30_000） */
  heartbeatIntervalMs?: number;
  /** 心跳超时（毫秒，默认 10_000） */
  heartbeatTimeoutMs?: number;
  /** 最大重连次数（默认 10，超过后停止） */
  maxReconnectAttempts?: number;
  /** 重连基础延迟（毫秒，默认 1000，指数退避起点） */
  reconnectBaseMs?: number;
  /** 最大重连延迟（毫秒，默认 30_000） */
  reconnectMaxMs?: number;
}

/** Hook 返回值 */
interface UseWebSocketReturn {
  /** 当前连接状态 */
  status: ConnectionStatus;
  /** 发送消息到服务端 */
  send: (msg: WsMessage) => void;
  /** 注册消息处理器（返回取消注册函数） */
  on: (type: string, handler: MessageHandler) => () => void;
  /** 手动连接 */
  connect: () => void;
  /** 手动断开 */
  disconnect: () => void;
}

// ════════════════════════════════════════
// Hook 实现
// ════════════════════════════════════════

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    autoConnect = true,
    heartbeatIntervalMs = 30_000,
    heartbeatTimeoutMs = 10_000,
    maxReconnectAttempts = 10,
    reconnectBaseMs = 1000,
    reconnectMaxMs = 30_000,
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>("disconnected");

  // ── Refs（跨渲染保持引用，避免闭包陷阱） ──
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const heartbeatTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map());
  const mountedRef = useRef(true);

  // ── 清理所有定时器 ──
  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  // ── 处理收到的消息 ──
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const msg: WsMessage = JSON.parse(event.data);
      const type = msg.type;

      // 只对非 ping/pong 消息打印日志
      if (type !== "ping" && type !== "pong") {
        console.log(`[useWebSocket] 📥 收到: type=${type} payload=`, msg.payload);
      }

      // pong 用来清除心跳超时
      if (type === "pong") {
        if (heartbeatTimeoutRef.current) {
          clearTimeout(heartbeatTimeoutRef.current);
          heartbeatTimeoutRef.current = null;
        }
        return;
      }

      // 分发给所有注册了该 type 的处理器
      const typeHandlers = handlersRef.current.get(type);
      if (typeHandlers) {
        typeHandlers.forEach((fn) => {
          try {
            fn(msg);
          } catch (e) {
            console.error(`[useWebSocket] handler error for type="${type}":`, e);
          }
        });
      }

      // 也分发给通配符 "*" 处理器（监听所有消息）
      const wildcardHandlers = handlersRef.current.get("*");
      if (wildcardHandlers) {
        wildcardHandlers.forEach((fn) => {
          try {
            fn(msg);
          } catch (e) {
            console.error(`[useWebSocket] wildcard handler error:`, e);
          }
        });
      }

    } catch {
      // 忽略解析失败的消息
    }
  }, []);

  // ── 启动心跳 ──
  const startHeartbeat = useCallback(() => {
    // 清理旧的心跳
    if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
    if (heartbeatTimeoutRef.current) clearTimeout(heartbeatTimeoutRef.current);

    // 每 heartbeatIntervalMs 发一次 ping
    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));

        // 设置超时：如果 10s 内没收到 pong → 断线重连
        heartbeatTimeoutRef.current = setTimeout(() => {
          console.warn("[useWebSocket] ⚠️ 心跳超时，断开重连");
          wsRef.current?.close();
        }, heartbeatTimeoutMs);
      }
    }, heartbeatIntervalMs);
  }, [heartbeatIntervalMs, heartbeatTimeoutMs]);

  // ── 建立连接 ──
  const connect = useCallback(() => {
    // 避免重复连接
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    setStatus(reconnectCountRef.current > 0 ? "reconnecting" : "connecting");

    const ws = new WebSocket(url);

    ws.onopen = () => {
      if (!mountedRef.current) return;

      console.log("[useWebSocket] ✅ 已连接");
      setStatus("connected");
      reconnectCountRef.current = 0; // 重置重连计数
      startHeartbeat();
    };

    ws.onmessage = handleMessage;

    ws.onclose = (event) => {
      if (!mountedRef.current) return;

      console.log(`[useWebSocket] ⚠️ 连接关闭 (code=${event.code})`);
      setStatus("disconnected");
      clearTimers();

      // 非正常关闭 → 尝试重连
      if (event.code !== 1000 && reconnectCountRef.current < maxReconnectAttempts) {
        const delay = Math.min(
          reconnectBaseMs * Math.pow(2, reconnectCountRef.current),
          reconnectMaxMs
        );
        console.log(`[useWebSocket] 🔄 ${delay}ms 后第 ${reconnectCountRef.current + 1} 次重连...`);
        reconnectCountRef.current++;

        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, delay);
      } else if (reconnectCountRef.current >= maxReconnectAttempts) {
        console.error(`[useWebSocket] ❌ 已达最大重连次数 (${maxReconnectAttempts})，停止重连`);
      }
    };

    ws.onerror = (err) => {
      console.error("[useWebSocket] ❌ 连接错误:", err);
    };

    wsRef.current = ws;
  }, [url, handleMessage, startHeartbeat, clearTimers, maxReconnectAttempts, reconnectBaseMs, reconnectMaxMs]);

  // ── 断开连接 ──
  const disconnect = useCallback(() => {
    clearTimers();
    reconnectCountRef.current = maxReconnectAttempts; // 阻止自动重连

    if (wsRef.current) {
      wsRef.current.close(1000, "客户端主动断开");
      wsRef.current = null;
    }
    setStatus("disconnected");
  }, [clearTimers, maxReconnectAttempts]);

  // ── 发送消息 ──
  const send = useCallback((msg: WsMessage) => {
    console.log(`[useWebSocket] 📤 发送: type=${msg.type} readyState=${wsRef.current?.readyState}`);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const raw = JSON.stringify(msg);
      console.log(`[useWebSocket] 📤 发送内容: ${raw.slice(0, 100)}`);
      wsRef.current.send(raw);
    } else {
      console.warn("[useWebSocket] ⚠️ 未连接，消息未发送:", msg.type, "readyState:", wsRef.current?.readyState);
    }
  }, []);

  // ── 注册消息处理器 ──
  const on = useCallback((type: string, handler: MessageHandler) => {
    if (!handlersRef.current.has(type)) {
      handlersRef.current.set(type, new Set());
    }
    handlersRef.current.get(type)!.add(handler);

    // 返回取消注册函数
    return () => {
      handlersRef.current.get(type)?.delete(handler);
    };
  }, []);

  // ── 生命周期 ──
  useEffect(() => {
    mountedRef.current = true;

    if (autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return { status, send, on, connect, disconnect };
}
