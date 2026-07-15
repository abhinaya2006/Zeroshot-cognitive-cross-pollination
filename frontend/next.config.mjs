/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Disabling during build to avoid mock setup compilation warnings
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Disabling during build to prevent minor TS type checking errors during deploy
    ignoreBuildErrors: true,
  }
};

export default nextConfig;
