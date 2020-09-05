/**
 * Typed Axios shims for interacting with workspace-io backend.
 */

import axios, { AxiosRequestConfig } from 'axios';
import { reactive } from 'vue';

export const state = reactive({
  token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMGEyNTM2NmQtMGY1Mi00MjQ3LTk4YjMtZTE0ODNmYzczNzIyIiwiYXVkIjoiZmFzdGFwaS11c2VyczphdXRoIiwiZXhwIjoxNTk5MzI2OTg0fQ.lpsjyZF25RRaUXueUwsFObd6wRYs9AxkqOCBiux0c3s",
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

interface BaseModel {
  id: string;
  created: string;
}

interface User extends BaseModel {
  id: string;
  email: string;
  is_active: boolean;
  username: string;
}

interface Root extends BaseModel {
  root_type: 'public' | 'private' | 'unmanaged';
  bucket: string;
  base_path: string;
  node_id: string;
}

interface Workspace extends BaseModel {
  name: string;
  base_path?: string;
  owner_id: string;
  root_id: string;
  owner: User;
  root: Root;
}

async function usersMe(): Promise<User> {
  const { data } = await axios.get<User>('users/me', config());
  return data;
}

async function workspacesSearch(name?: string, owner_id?: string): Promise<Workspace[]> {
  const { data } = await axios.get<Workspace[]>('workspace', config({
    params: { name, owner_id },
  }));
  return data;
}

export {
  /* methods */
  usersMe,
  workspacesSearch,
  /* Interfaces */
  User,
  Root,
  Workspace,
};
