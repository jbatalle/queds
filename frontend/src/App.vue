<template>
  <!--div :class="{'nav-open': $sidebar.showSidebar}"-->
  <div>
    <!--notifications transition-name="notification-list" transition-mode="out-in">

    </notifications-->
    <router-view name="header"></router-view>
    <!--transition name="fade" mode="out-in"-->
      <router-view></router-view>
    <!--/transition-->
    <router-view name="footer"></router-view>
  </div>
</template>

<script>
// Loading some plugin css asynchronously
import axios from "axios";

export default {
  created: function () {
    axios.interceptors.response.use(response => {
      return response;
    }, error => {
      if (error.response.status === 401 && error.response.config.url != "api/users/logout") {
        this.$store.dispatch("logout");
      }
      return Promise.reject(error)
      //return error;
    })
  },
  mounted() {
    axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/version").then(function (d) {
      localStorage.setItem("version", d.data);
    });
  },
  metaInfo() {
    return {
      title: "Queds",
      script: (function () {
        return [];
      })(),
    };
  },
}
</script>
<style lang="scss">

</style>