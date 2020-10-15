<script lang="ts">
import { ref, watchEffect } from 'vue';
import { apikeyList, apikeyCreate, ApiKey } from '../api';

export default {
  setup() {
    const keys = ref([] as ApiKey[]);

    /* Fetch workspaces */
    watchEffect(async () => {
      keys.value = await apikeyList();
    });

    async function newKey() {
      const newkey = await apikeyCreate();
      keys.value.push(newkey);
    }

    return { keys, newKey };
  }
}
</script>

<template>
  <div class="flex flex-col">
    <h1>API Keys</h1>
    <template v-if="keys.length">
      <div
        v-for="key in keys"
        :key="key.id"
        class="bg-gray-200 rounded px-4 my-2"
      >
        <p class="py-2">
          <span class="key-header">Key ID</span>
          <span class="code">{{ key.key_id }}</span>
        </p>
        <p
          class="py-2"
          v-if="key.secret"
        >
          <span class="key-header">Secret</span>
          <span class="code">{{ key.secret }}</span>
        </p>
        <p class="py-2">
          <span class="key-header">Created</span>
          <span>{{ (new Date(key.created)).toLocaleString() }}</span>
        </p>
      </div>
    </template>
    <template v-else>
      <p>You don't have any keys :(</p>
    </template>
    <div class="my-2">
      <button
        class="button"
        @click="newKey"
      >Generate New API Key</button>
      <button class="button warning mx-2">Revoke All</button>
    </div>
    <h1>Install the CLI</h1>
    <p>With pip</p>
    <p class="code">pip3 install workspacesio</p>
    <p>With pipx</p>
    <p class="code">pipx install workspacesio</p>
    <p>Configure for the server </p>
    <p class="code">wio login {token}</p>
  </div>
</template>

<style scoped lang="postcss">
.key-header {
  @apply mr-4 text-sm inline-block;
  width: 80px;
}
</style>
