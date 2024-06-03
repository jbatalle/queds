import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from './store';
import { toCurrency, round } from './filters';
import ElementPlus from 'element-plus';

import IsDemo from './isDemo';

import './assets/sass/paper-dashboard.scss';
import './assets/sass/demo.scss';
import './assets/custom.css';

const app = createApp(App);

app.config.globalProperties.$filters = {
  toCurrency,
  round
};
app.use(ElementPlus);

store.dispatch('initialize')

app.use(IsDemo).use(router).use(store).mount("#app");
