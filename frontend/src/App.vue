<template>
  <div id="app">
    <header class="app-header">
      <h1>MixedNuts ファイル共有システム</h1>
    </header>
    <main>
      <!-- FileManager を呼び出し -->
      <FileManager />
    </main>
    <footer class="app-footer">
      <p>© 2025 MixedNuts ファイル共有システム. All rights reserved.</p>
    </footer>
  </div>
</template>

<script>
import FileManager from "./components/FileManager/FileManager.vue";

export default {
  name: "App",
  components: {
    FileManager,
  },
};
</script>

<style>
/* 全体的なスタイル */
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--background-color);
  color: var(--text-color);
}

.app-header {
  background-color: var(--primary-color);
  color: white;
  padding: 1rem;
  text-align: center;
}

main {
  flex: 1;
  padding: 1rem;
}

.app-footer {
  background-color: var(--secondary-color);
  color: var(--text-color);
  text-align: center;
  padding: 0.5rem;
}
</style>
