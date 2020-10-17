<script lang="ts">
import { defineComponent, computed } from 'vue';
import useCurrentUser from '../use/useCurrentUser';

export default defineComponent({
  setup() {
    const { me } = useCurrentUser();
    const disabled = computed(() => me.value === null);
    const publicRoutes = [
      { name: 'workspaces', title: 'Workspaces' },
      { name: 'token', title: 'Tokens' },
    ];
    return { me, disabled, publicRoutes };
  },
})
</script>

<template>
  <nav>
    <ul>
      <li v-if="me !== null">
        <div class="flex flex-col items-center border border-gray-400 bg-gray-100 p-3 rounded">
          <div class="rounded-full h-16 w-16 bg-teal-500 flex items-center justify-center">
            <p class="text-white text-2xl">
              {{ me.username.slice(0, 1).toUpperCase() }}
            </p>
          </div>
          <p class="text-sm">
            {{ me.username }}
          </p>
        </div>
      </li>
      <li
        v-for="route in publicRoutes"
        :key="route.title"
        class="my-3"
      >
        <a
          v-if="disabled"
          class="link"
          :title="route.title"
          v-text="route.title"
        />
        <router-link
          v-else
          class="link"
          active-class="link--active"
          :title="route.title"
          :to="{ name: route.name }"
          v-text="route.title"
        />
      </li>
      <li>
        <a
          class="link"
          href="/logout"
        >Logout</a>
      </li>
    </ul>
  </nav>
</template>

<style lang="postcss">
.link {
  @apply text-lg text-gray-800 px-3 py-2 block rounded;
}
.link:hover {
  @apply bg-teal-100;
}
.link--active {
  @apply bg-teal-500 text-white;
}
.link--active:hover {
  @apply bg-teal-500;
}
</style>
