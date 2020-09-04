import axios, { AxiosRequestConfig } from 'axios';
import { reactive } from 'vue';

export const state = reactive({
  token: null,
  user: null,
});

function config(base: AxiosRequestConfig = {}): AxiosRequestConfig {
  return {
    ...base,
    baseURL: '/api',
    headers: {
      'Authorization': `Bearer ${state.token}`,
    },
  };
}

interface User {
  id: string;
  email: string;
  is_active: boolean;
  username: string;
}

async function usersMe(): Promise<User> {
  const { data } = await axios.get<User>('users/me', config());
  return data;
}

export {
  usersMe,
};
