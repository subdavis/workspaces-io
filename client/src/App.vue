<template>
  <div class="flex flex-row m-4">
    <div class="flex flex-col content m-4">
      <img
        class="w-3/4"
        src="./assets/logo.png"
      >
      <div class="flex flex-row justify-center">
        <button class="button">Login</button>
      </div>
      <Workspaces />
    </div>
    <div class="flex flex-col sidebar m-4">
      <Cli />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'

import useCurrentUser from './use/useCurrentUser';
import Workspaces from './components/Workspaces.vue'
import Cli from './components/Cli.vue';

export default defineComponent({
  components: {
    Workspaces,
    Cli,
  },
  setup() {
    const { me } = useCurrentUser();
    return { me };
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

<style lang="postcss">
.button {
  @apply px-4 py-2 rounded bg-teal-500 inline w-32 text-white;
}
</style>
