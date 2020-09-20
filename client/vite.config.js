module.exports = {
  proxy: {
    '/api': {
      target: 'http://localhost:8100',
      changeOrigin: true,
    },
  },
};
