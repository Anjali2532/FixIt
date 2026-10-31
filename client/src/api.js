let csrfToken = null;
export class ApiError extends Error {
  constructor(message, status, errors = {}) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}
export async function api(path, { method = "GET", body } = {}, retry = true) {
  try {
    if (method !== "GET" && !csrfToken) {
      const response = await fetch("/api/auth/csrf", {
        credentials: "same-origin",
        signal: AbortSignal.timeout(10000),
      });
      if (!response.ok)
        throw new ApiError(
          "Security check unavailable. Please try again.",
          response.status,
        );
      csrfToken = (await response.json()).csrf_token;
    }
    const headers = method === "GET" ? {} : { "X-CSRFToken": csrfToken };
    if (body) headers["Content-Type"] = "application/json";
    const response = await fetch(path, {
      method,
      headers,
      credentials: "same-origin",
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(10000),
    });
    let data = {};
    if (response.status !== 204) {
      try {
        data = await response.json();
      } catch {
        throw new ApiError(
          "FixIt is temporarily unavailable. Please try again.",
          response.status,
        );
      }
    }
    if (data.csrf_token) csrfToken = data.csrf_token;
    if (!response.ok) {
      if (data.code === "CSRF_FAILED" && retry) {
        csrfToken = null;
        return api(path, { method, body }, false);
      }
      if (
        data.code === "SESSION_EXPIRED" ||
        (response.status === 401 &&
          (path.includes("/dashboard") || path.startsWith("/api/issues")))
      ) {
        csrfToken = null;
        window.dispatchEvent(new Event("fixit:session-expired"));
      }
      throw new ApiError(
        data.message || "Something went wrong. Please try again.",
        response.status,
        data.errors,
      );
    }
    if (path.endsWith("/logout")) csrfToken = null;
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      "We couldn’t reach FixIt. Check your connection and try again.",
      0,
    );
  }
}
