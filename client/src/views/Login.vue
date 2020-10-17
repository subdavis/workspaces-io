<script lang="ts">
import { defineComponent } from 'vue';
import useCurrentUser from '../use/useCurrentUser';

export default defineComponent({
  setup() {
    console.log('loginSetup');
    const { me } = useCurrentUser();
    const loginHref = process.env.NODE_ENV === 'production'
      ? '/login'
      : 'http://localhost:8100/login';
    return { loginHref };
  },
})
</script>

<template>
  <div>
    <img
      src="../assets/logo.png"
      style="width: 500px"
    >
    <a
      :href="loginHref"
      class="button my-10"
    >
      Log in via Auth0
    </a>
  </div>
</template>
