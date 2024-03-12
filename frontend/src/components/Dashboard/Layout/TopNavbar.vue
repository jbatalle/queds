<template>
  <navbar v-model="showNavbar">
    <div class="navbar-wrapper">
      <div class="navbar-toggle">
        <navbar-toggle-button @click.native="toggleSidebar">
        </navbar-toggle-button>
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
import { Navbar } from "../../UIComponents";

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
      this.$router.push({ name: "User Profile" });
    },
    logout() {
      this.$store.dispatch("logout");
    },
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    toggleNotificationDropDown() {
      this.activeNotifications = !this.activeNotifications;
    },
    closeDropDown() {
      this.activeNotifications = false;
    },
    toggleSidebar() {
      this.$sidebar.displaySidebar(!this.$sidebar.showSidebar);
    },
    hideSidebar() {
      this.$sidebar.displaySidebar(false);
    },
    minimizeSidebar() {
      this.$sidebar.toggleMinimize();
    },
    toggleNavbar() {
      this.showNavbar = !this.showNavbar;
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
