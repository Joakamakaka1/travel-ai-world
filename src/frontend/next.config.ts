import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";
// production is served from the domain root (S3 + CloudFront, ADR 0009); only CI's PR build sets a base path
const basePath = isProd ? (process.env.NEXT_PUBLIC_BASE_PATH ?? "") : "";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,   // /plan/ is plan/index.html: CloudFront's index function and nginx serve it
  basePath,
  images: {
    // next/image optimisation needs a server, which a static export doesn't have
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
    ],
  },
};

export default nextConfig;
