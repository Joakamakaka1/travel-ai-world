/**
 * The locales and their metadata: the switcher, the formatters and `<html lang>` read them here.
 * A new language needs its file, a member of `Language`, a `locales` entry and a `LANGUAGES` row.
 */

import en from "./en";
import es from "./es";
import type { Language, Translations } from "./types";

export type { Language, Translations } from "./types";
export { interpolate } from "./interpolate";

export const locales: Record<Language, Translations> = { en, es };

export interface LanguageMeta {
  code: Language;
  /** Emoji shown in the switcher. */
  flag: string;
  /** The language's own name for itself, never translated. */
  nativeName: string;
  /** BCP 47 tag handed to `Intl` formatters. */
  locale: string;
}

/** Every supported language, in the order the switcher lists them. */
export const LANGUAGES = [
  { code: "en", flag: "🇬🇧", nativeName: "English", locale: "en-US" },
  { code: "es", flag: "🇪🇸", nativeName: "Español", locale: "es-ES" },
] as const satisfies readonly LanguageMeta[];

// compile-time guard: every member of the Language union has metadata
type ListedLanguage = (typeof LANGUAGES)[number]["code"];
type MissingLanguage = Exclude<Language, ListedLanguage>;
const allLanguagesListed: [MissingLanguage] extends [never] ? true : never = true;
void allLanguagesListed;

export const DEFAULT_LANGUAGE: Language = "en";

export function getLanguageMeta(code: Language): LanguageMeta {
  // the guard above makes the lookup total; the fallback only satisfies TS
  return LANGUAGES.find((l) => l.code === code) ?? LANGUAGES[0];
}
