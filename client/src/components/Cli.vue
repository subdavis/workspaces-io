<script lang="ts">
import { ref, watchEffect } from 'vue';
import { apikeyList, ApiKey } from '../api';

export default {
  setup() {
    const keys = ref([] as ApiKey[]);

    /* Fetch workspaces */
    watchEffect(async () => {
      keys.value = await apikeyList();
    });

    return { keys };
  }
}
</script>

<template>
  <div class="flex flex-col">
    <p>Install the cli </p>
    <p class="code">pip3 install workspacesio</p>
    <p>Configure for the server </p>
    <p class="code">wio login {token}</p>
  </div>
</template>

<style scoped lang="postcss">
.code {
  @apply bg-gray-800 text-gray-100 rounded p-2 font-mono;
}
p {
  @apply p-2;
}
</style>
