/**
 * The signed-in account as core_api knows it (`GET /api/v1/users/me`), above all its `role`:
 * the profile cached at sign-in has none, so `AuthContext` asks once per session and merges it.
 */

import type { components } from "@/types/generated/core-api";
import { ApiError, request } from "./http";

export type UserResponse = components["schemas"]["UserResponse"];

/** The account behind the session token; `null` on 401 or 404 (no account to describe). */
export async function getMe({ signal }: { signal?: AbortSignal } = {}): Promise<UserResponse | null> {
  try {
    return await request<UserResponse>("core", "/users/me", { auth: true, signal });
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 404)) return null;
    throw err;
  }
}
