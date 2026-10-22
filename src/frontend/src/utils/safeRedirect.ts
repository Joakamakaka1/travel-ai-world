/** Any origin will do: only whether a path leaves it matters. */
const BASE = "https://kyrian.invalid";

/**
 * Returns a destination unchanged only if it is a same-origin path once resolved the way the
 * router resolves it: the parser drops tabs and newlines and reads `\` as `/`, so `/\t/evil.com`
 * is `//evil.com`. Takes the path decoded once (as `URLSearchParams.get` returns it).
 */
export function safeRedirectTarget(path: string | null | undefined): string | null {
  if (!path || !path.startsWith("/")) return null;
  if (path.startsWith("//") || path.startsWith("/\\")) return null;
  let resolved: URL;
  try {
    resolved = new URL(path, BASE);
  } catch {
    return null;
  }
  return resolved.origin === BASE ? path : null;
}
