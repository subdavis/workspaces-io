declare module '*.vue' {
  import { Component } from 'vue'
  const _default: Component
  export default _default
}

declare var process: {
  env: {
    NODE_ENV: string
  }
}
