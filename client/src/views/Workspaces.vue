
<script lang="ts">
import { defineComponent, ref, watchEffect } from 'vue'
import { workspacesSearch, Workspace } from '../api';

export default defineComponent({
  name: 'Workspaces',
  setup() {
    const workspaces = ref([] as Workspace[]);

    /* Fetch workspaces */
    watchEffect(async () => {
      workspaces.value = await workspacesSearch();
    });

    return { workspaces };
  },
})
</script>


<template>
  <div class="flex flex-col">
    <h1>Workspaces</h1>
    <div
      class="workspace-list"
      v-show="workspaces.length"
    >
      <ul>
        <li
          v-for="workspace in workspaces"
          :key="workspace.id"
        >
          <span class="text-gray-800">
            {{workspace.owner.username}}/</span><span class="font-bold">{{workspace.name}}
          </span>
          <span class="text-gray-500 pl-3">
            ({{ workspace.root.root_type }})
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped lang="postcss">
.workspace-list li {
  @apply px-2 py-1;
}
.workspace-list li:nth-child(odd) {
  @apply bg-gray-200 rounded;
}
</style>
