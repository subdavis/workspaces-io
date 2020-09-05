<template>
  <div class="container mx-auto">
    <div class="grid grid-cols-4">
      <div class="sidebar col-span-1" />
      <div class="col-span-3">
        <div class="text-xl my-5"> workspaces </div>
        <workspaces />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import Workspaces from './components/Workspaces.vue'

export default defineComponent({
  components: {
    Workspaces,
  },
})
</script>
