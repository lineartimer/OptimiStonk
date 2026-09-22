const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:5000";

module.exports = {
  agentRules: false,
  experimental: {
    // Scout collects external data and runs agents before returning a response.
    proxyTimeout: 300_000,
  },
  async rewrites() {
    return [
      {
        source: "/api/scout",
        destination: `${backendUrl}/api/scout`,
      },
    ];
  },
};
