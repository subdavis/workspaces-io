import { AxiosError } from 'axios';
import { ref, onBeforeMount } from 'vue';
import { useRouter } from 'vue-router';
import { User, usersMe } from '../api';

const me = ref(null as User | null);

export default function useCurrentUser() {
  if (me.value === null) {
    const router = useRouter();
    onBeforeMount(async () => {
      try {
        const user = await usersMe();
        console.log(user);
        me.value = user;
      } catch (e) {
        console.log(e.response.status);
        const err = e as AxiosError;
        if (err.response?.status === 401) {
          if (router.currentRoute.value.name !== 'login') {
            console.log('push');
            router.push({ name: 'login' });
          }
        }
      }
    })
  }

  return { me };
}
