// isDemo.js
export default {
  install: (app) => {
    app.config.globalProperties.$isDemo = import.meta.env.VUE_APP_IS_DEMO == 'true';
  }
}
