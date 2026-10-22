import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // replaces eslint-config-next's default ignores, so they are repeated here
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // MapLibre worker copied in by scripts/copy-maplibre-worker.mjs
    "public/maplibre/**",
  ]),

  // project boundaries, see src/frontend/AGENTS.md
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-globals": [
        "error",
        {
          name: "fetch",
          message: "Network calls live in src/services/ only. Call a service function.",
        },
      ],
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/types/generated/*"],
              message:
                "Import generated contract types only from src/services/ or src/types/.",
            },
          ],
        },
      ],
      "import/first": "error",
      "no-console": "warn",
    },
  },
  {
    files: ["src/services/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-globals": "off",
      "no-restricted-imports": "off",
    },
  },
  {
    files: ["src/types/**/*.ts"],
    rules: {
      "no-restricted-imports": "off",
    },
  },
]);

export default eslintConfig;
