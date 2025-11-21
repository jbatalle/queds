// isDemo.js
export default {
  install: (app) => {
    console.log("Demo mode:", import.meta.env.VITE_APP_IS_DEMO);
    app.config.globalProperties.$isDemo = import.meta.env.VITE_APP_IS_DEMO == 'true';
  }
}
