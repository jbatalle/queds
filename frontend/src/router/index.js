import { createRouter, createWebHistory } from "vue-router";


import routes from "./routes";
//
// const routes = [
//   {
//     path: "/:pathMatch(.*)*",
//     redirect: "/404",
//   },
//   {
//     path: "/",
//     component: () => import("../pages/Home.vue"),
//   },
//   {
//     path: "/home",
//     component: () => import("../pages/Home.vue"),
//   },
//   {
//     path: "/404",
//     component: () => import("../pages/404.vue"),
//   },
// ];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
