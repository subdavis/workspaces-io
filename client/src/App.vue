<template>
  <div class="flex flex-row m-4">
    <div class="flex flex-col sidebar m-4">
      <Nav />
    </div>
    <div class="flex flex-col container m-4">
      <keep-alive>
        <router-view />
      </keep-alive>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import Nav from './components/Nav.vue';
import useCurrentUser from './use/useCurrentUser';

export default defineComponent({
  components: { Nav },
  setup() {
    const { me } = useCurrentUser();
    return { me };
  },
})
</script>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
}
</style>

<style lang="postcss">
.button {
  @apply px-12 py-2 rounded bg-teal-500 text-white inline-block;
}
.warning {
  @apply bg-orange-600 !important;
}
.code {
  @apply bg-gray-800 text-gray-100 rounded p-2 font-mono whitespace-no-wrap;
}
p {
  @apply my-1;
}
h1 {
  @apply text-4xl my-6;
}
h1:first-child {
  @apply mt-0;
}
</style>
