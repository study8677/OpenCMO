/**
 * User API Keys — stored in localStorage, injected per-request.
 *
 * Each user's keys stay in their own browser. They are sent to the backend
 * via the `X-User-Keys` header on every API call, where the backend
 * middleware injects them into `os.environ` for the duration of that request.
 */

const STORAGE_KEY = "opencmo_user_keys";

/** Keys that the backend reads from X-User-Keys header */
export const USER_KEY_NAMES = [
  "OPENAI_API_KEY",
  "OPENAI_BASE_URL",
  "OPENCMO_MODEL_DEFAULT",
  "TAVILY_API_KEY",
  "ANTHROPIC_API_KEY",
  "GOOGLE_AI_API_KEY",
  "PAGESPEED_API_KEY",
] as const;

export type UserKeyName = (typeof USER_KEY_NAMES)[number];
export type UserKeys = Partial<Record<UserKeyName, string>>;

/** Read all user keys from localStorage */
export function getUserKeys(): UserKeys {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

/** Save all user keys to localStorage */
export function setUserKeys(keys: UserKeys): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  // Dispatch event so SetupBanner and other components can react
  window.dispatchEvent(new CustomEvent("opencmo:keys-changed"));
}

/** Get a single key */
export function getUserKey(name: UserKeyName): string {
  return getUserKeys()[name] ?? "";
}

/** Set a single key (merges with existing) */
export function setUserKey(name: UserKeyName, value: string): void {
  const keys = getUserKeys();
  if (value) {
    keys[name] = value;
  } else {
    delete keys[name];
  }
  setUserKeys(keys);
}

/** Build the base64-encoded header value for X-User-Keys */
export function buildUserKeysHeader(): string | null {
  const keys = getUserKeys();
  // Only include non-empty values
  const filtered: Record<string, string> = {};
  for (const [k, v] of Object.entries(keys)) {
    if (v) filtered[k] = v;
  }
  if (Object.keys(filtered).length === 0) return null;
  return btoa(JSON.stringify(filtered));
}

/** Quick check: does the user have essential keys configured? */
export function hasEssentialKeys(): { llm: boolean; tavily: boolean } {
  const keys = getUserKeys();
  return {
    llm: !!keys.OPENAI_API_KEY,
    tavily: !!keys.TAVILY_API_KEY,
  };
}
