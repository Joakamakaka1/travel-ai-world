/**
 * The signed-in person, as the UI shows them. `role` is what core_api reports on
 * `GET /users/me`, merged in after sign-in; no role means not an administrator.
 */
export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  role?: UserRole;
}

export type UserRole = "user" | "admin";
