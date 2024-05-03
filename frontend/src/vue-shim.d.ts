// src/vue-shim.d.ts
declare module "*.vue" {
    import type { DefineComponent } from 'vue';
    const component: DefineComponent<{}, {}, any>;
    export default component;
  }
  
declare module '@/store/auth' {
  import { Store } from 'pinia';

  interface AuthStore {
    isAuthenticated: boolean;
  }

  export const useAuthStore: () => Store<AuthStore>;
}