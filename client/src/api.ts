/**
 * Typed Axios shims for interacting with workspace-io backend.
 */

import axios, { AxiosRequestConfig } from 'axios';

function config(base: AxiosRequestConfig = {}): AxiosRequestConfig {
  return {
    ...base,
    baseURL: '/api',
  };
}

interface BaseModel {
  id: string;
  created: string;
}

interface User extends BaseModel {
  email: string;
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

interface ApiKey extends BaseModel {
  key_id: string;
  secret?: string;
  user: User;
}

async function usersMe(): Promise<User> {
  const { data } = await axios.get<User>('users/me', config());
  return data;
}

async function apikeyList(): Promise<ApiKey[]> {
  const { data } = await axios.get<ApiKey[]>('apikey', config());
  return data;
}

async function apikeyCreate(): Promise<ApiKey> {
  const { data } = await axios.request<ApiKey>(config({
    method: 'POST',
    url: 'apikey',
  }));
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
  apikeyCreate,
  apikeyList,
  usersMe,
  workspacesSearch,
  /* Interfaces */
  ApiKey,
  User,
  Root,
  Workspace,
};
