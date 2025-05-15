<template>
  <navbar v-model="showNavbar">
    <div class="navbar-wrapper">
      <div class="navbar-toggle">
        <button @click="$emit('toggle-sidebar')" class="btn btn-link d-lg-none">
          <i class="nc-icon nc-minimal-right"></i>
        </button>
      </div>
      <a class="navbar-brand" href="#">Dashboard </a>
    </div>
    <template #navbar-menu>
      <ul class="navbar-nav">
        <a class="nav-link" @click="logout" href="#">
          <i class="nc-icon nc-single-02"></i>
          <p>Log out</p>
        </a>
      </ul>
    </template>
  </navbar>
</template>
<script>
import {Navbar} from "../../UIComponents";

export default {
  components: {
    Navbar,
  },
  data() {
    return {
      activeNotifications: false,
      showNavbar: false,
    };
  },
  methods: {
    goToProfile() {
      this.$router.push({name: "User Profile"});
    },
    logout() {
      this.$store.dispatch("logout");
    },
  },
};
</script>
<style>
#docs:hover,
#docs:active,
#docs:focus {
  background-color: #6bd098 !important;
}

#downb:hover,
#downb:active,
#downb:focus {
  background-color: #ef8157 !important;
}
</style>
