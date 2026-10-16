const target = process.env.SAAS_API_ORIGIN || "http://127.0.0.1:8001";
const url = new URL(target);
if (!["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) || url.protocol !== "http:" || url.pathname !== "/" || url.username || url.password || url.search || url.hash) {
  throw new Error("CORE-001 API proxy must target a local HTTP origin.");
}
export default {
  poweredByHeader: false,
  transpilePackages: ["@portfolio/content-contracts"],
  async headers() {
    return [{source: '/:path*', headers: [
      {key:'Referrer-Policy',value:'no-referrer'},
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'X-Frame-Options',value:'DENY'},
      {key:'Cache-Control',value:'no-store'},
    ]}];
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${url.origin}/api/:path*` }];
  },
};
