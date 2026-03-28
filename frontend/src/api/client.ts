const API_PREFIX = "/api/v1";

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const token = localStorage.getItem("opencmo_token");
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (
    init?.body &&
    typeof init.body === "string" &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const resp = await fetch(`${API_PREFIX}${path}`, { ...init, headers });
  if (resp.status === 401) {
    localStorage.removeItem("opencmo_token");
    window.dispatchEvent(new CustomEvent("opencmo:unauthorized"));
  }
  return resp;
}

export async function apiJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const resp = await apiFetch(path, init);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new ApiError(resp.status, body.error ?? resp.statusText, body.error_code);
  }
  return resp.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public errorCode?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
