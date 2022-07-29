import Vue from 'vue'
import VueRouter from 'vue-router'
import VueRouterPrefetch from 'vue-router-prefetch'
import VueNotify from 'vue-notifyjs'
import lang from 'element-ui/lib/locale/lang/en'
import locale from 'element-ui/lib/locale'
import App from './App.vue'

// Plugins
import GlobalComponents from './globalComponents'
// import GlobalDirectives from './globalDirectives'
import SideBar from './components/UIComponents/SidebarPlugin'
import initProgress from './progressbar';

// router setup
import routes from './router/routes'

// library imports
import './assets/sass/paper-dashboard.scss'
import './assets/sass/demo.scss'
import 'src/assets/custom.css';

import store from "./store";
import VueMeta from 'vue-meta';
import IsDemo from './isDemo';

// plugin setup
Vue.use(VueRouter);
Vue.use(VueRouterPrefetch);
Vue.use(GlobalComponents);
Vue.use(VueNotify);
Vue.use(SideBar);
locale.use(lang);
Vue.use(IsDemo);
Vue.use(VueMeta);


Vue.filter('toCurrency', function (value, currency, digits=2) {
    if (typeof value !== "number") {
        return value;
    }

    var formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        maximumFractionDigits: digits
    });
    return formatter.format(value);
});

Vue.filter('round', function (value) {
    if (typeof value !== "number") {
        return value;
    }
    return Number(value).toFixed(2);
});

// configure router
const router = new VueRouter({
  mode: 'history',
  routes, // short for routes: routes
  linkActiveClass: 'active',
  scrollBehavior: (to) => {
    if (to.hash) {
      return {selector: to.hash}
    } else {
      return { x: 0, y: 0 }
    }
  }
})

// Creates a `nextMiddleware()` function which not only
// runs the default `next()` callback but also triggers
// the subsequent Middleware function.
function nextFactory(context, middleware, index) {
  const subsequentMiddleware = middleware[index];
  // If no subsequent Middleware exists,
  // the default `next()` callback is returned.
  if (!subsequentMiddleware)
    return context.next;

  return (...parameters) => {
    // Run the default Vue Router `next()` callback first.
    context.next(...parameters);
    // Then run the subsequent Middleware with a new
    // `nextMiddleware()` callback.
    const nextMiddleware = nextFactory(context, middleware, index + 1);
    subsequentMiddleware({...context, next: nextMiddleware});
  };
}

router.beforeEach((to, from, next) => {

  if (to.meta.middleware) {
    const middleware = Array.isArray(to.meta.middleware) ? to.meta.middleware : [to.meta.middleware];
    const context = {from, next, to, router};
    const nextMiddleware = nextFactory(context, middleware, 1);
    return middleware[0]({...context, next: nextMiddleware});
  }

  return next();
});

export default router;

initProgress(router);

/* eslint-disable no-new */
new Vue({
  el: '#app',
  render: h => h(App),
  router: router,
  store: store
});
