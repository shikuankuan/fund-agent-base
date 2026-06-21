/**
 * HTTP 基础封装
 * - 统一 BASE_URL（经 Vite proxy → localhost:8000）
 * - 统一错误处理
 * - 请求/响应拦截
 */

const BASE_URL = "/api";

interface RequestOptions {
    timeout?: number;
    signal?: AbortSignal;
}

class HttpError extends Error {
    public status: number;
    public data?: unknown;

    constructor(status: number, message: string, data?: unknown) {
        super(message);
        this.name = "HttpError";
        this.status = status;
        this.data = data;
    }
}

/** 基础 request */
async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    options: RequestOptions = {},
): Promise<T> {
    const { timeout = 30000, signal } = options;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // signal 合并
    if (signal) {
        signal.addEventListener("abort", () => controller.abort());
    }

    try {
        const res = await fetch(`${BASE_URL}${path}`, {
            method,
            headers: { "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : undefined,
            signal: controller.signal,
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => null);
            throw new HttpError(res.status, `请求失败: ${res.statusText}`, errorData);
        }

        return res.json();
    } catch (err) {
        if (err instanceof HttpError) throw err;
        if ((err as Error).name === "AbortError") {
            throw new HttpError(0, "请求超时");
        }
        throw new HttpError(0, `网络错误: ${(err as Error).message}`);
    } finally {
        clearTimeout(timeoutId);
    }
}

/** HTTP 方法快捷函数 */
export const http = {
    get<T>(path: string, options?: RequestOptions) {
        return request<T>("GET", path, undefined, options);
    },
    post<T>(path: string, body?: unknown, options?: RequestOptions) {
        return request<T>("POST", path, body, options);
    },
    put<T>(path: string, body?: unknown, options?: RequestOptions) {
        return request<T>("PUT", path, body, options);
    },
    delete<T>(path: string, options?: RequestOptions) {
        return request<T>("DELETE", path, undefined, options);
    },
};

export { HttpError };
export default http;
