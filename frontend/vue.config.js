const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // Lintチェックを無効化
  publicPath: './', // 相対パスでの配信を有効化
});
