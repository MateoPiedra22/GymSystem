/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly DEV?: boolean
  readonly PROD?: boolean
  readonly MODE?: string
  // Add other environment variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}