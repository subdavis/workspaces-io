<script lang="ts">
import { defineComponent } from 'vue';
import useCurrentUser from '../use/useCurrentUser';

export default defineComponent({
  setup() {
    const { me } = useCurrentUser();
    return { me };
  },
})
</script>

<template>

</template>
