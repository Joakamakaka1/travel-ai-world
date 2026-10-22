/**
 * Sign-in with a Google credential when there is no Cognito pool (`services/cognito.ts`).
 * With `NEXT_PUBLIC_API_URL` core_api verifies it and issues our own JWT; without it (static mode)
 * the Google ID token is decoded for display only and stored as the token.
 */

import type { components } from "@/types/generated/core-api";
import type { User } from "@/types/user";
import { isApiAvailable, request } from "./http";
import { userFromIdToken, writeSession } from "./session";

export type GoogleAuthResponse = components["schemas"]["GoogleAuthResponse"];

/** Raised when a credential cannot be turned into a session. */
export class InvalidCredentialError extends Error {
  constructor(message = "Invalid credential") {
    super(message);
    this.name = "InvalidCredentialError";
  }
}

/** Sends a Google ID token to core_api, which answers with our own JWT and the profile. */
export async function verifyGoogleToken(
  credential: string
): Promise<GoogleAuthResponse> {
  const body: components["schemas"]["GoogleAuthRequest"] = { credential };
  return request<GoogleAuthResponse>("core", "/auth/google", {
    method: "POST",
    json: body,
  });
}

/**
 * core_api ids are UUID strings and profile fields nullable; the UI type
 * has optional fields, so normalise at the boundary.
 */
export function userFromAuthResponse(response: GoogleAuthResponse): User {
  return {
    id: String(response.user.id),
    email: response.user.email,
    name: response.user.name ?? "",
    picture: response.user.picture ?? undefined,
  };
}

/** A Google credential is an OpenID Connect ID token; decode it for display. */
export const userFromGoogleCredential = userFromIdToken;

/**
 * Signs in with a Google credential and persists the session.
 * Rejects (leaving storage untouched) when the credential is not accepted.
 */
export async function loginWithGoogle(credential: string): Promise<User> {
  if (isApiAvailable()) {
    const response = await verifyGoogleToken(credential);
    const user = userFromAuthResponse(response);
    writeSession(response.access_token, user);
    return user;
  }

  const user = userFromGoogleCredential(credential);
  if (!user) throw new InvalidCredentialError();
  writeSession(credential, user);
  return user;
}
