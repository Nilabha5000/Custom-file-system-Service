import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import { createWebHistory , createRouter } from 'vue-router'

import fs from '@/components/fs.vue'
import signin from '@/components/signin.vue'
import signup from '@/components/signup.vue'
import maincomp from './App.vue'
const routes = [
  { path: '/',  component : maincomp },
  { path: '/signin', component: signin },
  { path: '/signup', component : signup},
  { path : '/fs' , component : fs}
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
createApp(App)
   .use(router)
   .use(vuetify)
   .mount('#app')
