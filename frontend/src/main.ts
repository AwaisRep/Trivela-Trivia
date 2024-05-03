import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';

// We import bootstrap for regular styling and data tables for our leaderboard data
import 'bootstrap/dist/css/bootstrap.min.css';
import Vue3EasyDataTable from 'vue3-easy-data-table';
import 'vue3-easy-data-table/dist/style.css';


const app = createApp(App);
const pinia = createPinia(); // Create a pinia store to hold states amongst pages

app.use(pinia);
app.use(router);
app.component('EasyDataTable', Vue3EasyDataTable); // Provide the data for custom tables

app.mount('#app');
