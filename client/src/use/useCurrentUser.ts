import { ref } from 'vue'
import { User, usersMe } from '../api';

const me = ref(null as User | null);
usersMe().then((user) => {
  me.value = user;
});

export default function () {
  return { me };
}
