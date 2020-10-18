
<script lang="ts">
import { defineComponent, } from 'vue';
import SearchWidget from '../components/Search.vue';

export default defineComponent({
  name: 'Search',
  components: { SearchWidget },
})
</script>


<template>
  <div class="flex flex-col">
    <h1>Search</h1>
    <SearchWidget />
  </div>
</template>
