/**
 * Whether the signed-in account is on the access list (`GET /api/v1/users/me/access`, ADR 0026),
 * and its daily token limit. The route answers an uninvited account too, so the UI can say so
 * instead of failing on every 403 `ACCESS_DENIED`.
 */

import type { components } from "@/types/generated/core-api";
import { ApiError, request } from "./http";

export type AccessResponse = components["schemas"]["AccessResponse"];

/** The caller's access; `null` on 401 or 404 (no account, or a backend without the route). */
export async function getMyAccess({ signal }: { signal?: AbortSignal } = {}): Promise<AccessResponse | null> {
  try {
    return await request<AccessResponse>("core", "/users/me/access", { auth: true, signal });
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 404)) return null;
    throw err;
  }
}
