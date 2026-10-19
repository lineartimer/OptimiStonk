const backendUrl = process.env.BACKEND_URL;

module.exports = {
  agentRules: false,
  experimental: {
    proxyTimeout: 300_000
  },
  async rewrites() {
    return [
      {
        source: "/api/market",
        destination: `${backendUrl}/api/market`
      },
      {
        source: "/api/discover",
        destination: `${backendUrl}/api/discover`
      },
      {
        source: "/api/stock",
        destination: `${backendUrl}/api/stock`
      },
      {
        source: "/api/rag",
        destination: `${backendUrl}/api/rag`
      }
    ];
  }
};
