<template>
  <div class="flex flex-row m-4">
    <div class="flex flex-col content m-4">
      <img
        class="w-3/4"
        src="./assets/logo.png"
      >
      <input
        class="my-4 shadow appearance-none border outline-none rounded w-full p-2 focus:shadow-outline"
        type="text"
        placeholder="search"
      >
      <Workspaces />
    </div>
    <div class="flex flex-col sidebar m-4">
      <Cli />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import Workspaces from './components/Workspaces.vue'
import Cli from './components/Cli.vue';

export default defineComponent({
  components: {
    Workspaces,
    Cli,
  },
})
</script>

<style scoped>
.content {
  width: 800px;
}
.sidebar {
  width: 300px;
}
</style>
