const backendUrl = process.env.BACKEND_URL;

module.exports = {
  agentRules: false,
  experimental: {
    proxyTimeout: 300_000
  },
  async rewrites() {
    return [
      {
        source: "/api/search",
        destination: `${backendUrl}/api/search`
      },
      {
        source: "/api/companies",
        destination: `${backendUrl}/api/companies`
      }
    ];
  }
};
