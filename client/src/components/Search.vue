<script lang="ts">
import { defineComponent, ref, watch, watchEffect } from 'vue';
import { search, SearchResult } from '../api';

export default defineComponent({
  setup() {
    const query = ref('');
    const results = ref(undefined as SearchResult | undefined);
    async function dosearch(q: string) {
      results.value = await search(q);
    }
    watchEffect(() => {
      dosearch(query.value);
    });
    return { query, results };
  }
});
</script>

<template functional>
  <div class="flex flex-col">
    <input
      class="my-4 shadow appearance-none border outline-none rounded w-full p-2 focus:shadow-outline"
      type="text"
      placeholder="search"
      v-model="query"
    >
    <div
      class="search-results"
      v-if="results"
    >
      <p>Total results: {{ results.hits.total.value }}</p>
      <ul>
        <li
          v-for="result in results.hits.hits"
          :key="result._source.path"
        >
          <span class="text-gray-800">{{result._source.owner_name}}/</span>
          <span class="font-bold">{{result._source.workspace_name}}</span>
          <span class="text-gray-800">{{ result._source.path }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped lang="postcss">
.search-results li {
  @apply px-2 py-1;
}
.search-results li:nth-child(odd) {
  @apply bg-gray-200 rounded;
}
</style>
