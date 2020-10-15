
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
  <table class="table" v-show="workspaces.length">
    <thead>
      <tr>
        <th>Name</th>
        <th>Owner</th>
        <th>Id</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="workspace in workspaces"
        :key="workspace.id"
      >
        <td>{{workspace.name}}</td>
        <td>{{workspace.owner.username}}</td>
        <td>{{workspace.id}}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped lang="postcss">
.table td {
  @apply px-4 py-1;
}
</style>
