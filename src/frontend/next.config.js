const backendUrl = process.env.BACKEND_URL;

module.exports = {
  agentRules: false,
  experimental: {
    proxyTimeout: 300_000
  },
  async rewrites() {
    return [
      {
        source: "/api/scout",
        destination: `${backendUrl}/api/scout`
      }
    ];
  }
};
