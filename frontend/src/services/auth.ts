/**
 * Authentication against core_api.
 */

import type { components } from "@/types/generated/core-api";
import { apiUrl, readErrorMessage } from "./http";

export type GoogleAuthResponse = components["schemas"]["GoogleAuthResponse"];

/**
 * Sends a Google ID token to core_api for verification.
 * Returns our own JWT + user profile on success.
 */
export async function verifyGoogleToken(
  credential: string
): Promise<GoogleAuthResponse> {
  const body: components["schemas"]["GoogleAuthRequest"] = { credential };
  const res = await fetch(apiUrl("core", "/auth/google"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(await readErrorMessage(res, "Auth failed"));
  }

  return res.json();
}
