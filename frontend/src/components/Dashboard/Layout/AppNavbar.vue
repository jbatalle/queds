<template>
  <navbar navbar-menu-classes="navbar-right">
    <div class="navbar-wrapper">
      <a class="navbar-brand" href="/">Queds Dashboard</a>
    </div>
    <template #navbar-menu>
      <router-link to="/register" class="nav-item" tag="li">
        <a class="nav-link register-link">
          <i class="nc-icon nc-book-bookmark"></i> Register
        </a>
      </router-link>
      <router-link to="/login" class="nav-item" tag="li">
        <a class="nav-link">
          <i class="nc-icon nc-tap-01"></i> Login
        </a>
      </router-link>
    </template>
  </navbar>
</template>

<script>
  import {Navbar} from '@/components/UIComponents'
  export default {
    name: 'main-navbar',
    components: {
      Navbar
    },
    data() {
      return {
        showMenu: false
      }
    }
  }
</script>
<style scoped>
/* Add this style to remove the underline */
.register-link {
  text-decoration: none !important;
}

/* Optionally, you can add styles for when the link is hovered */
.register-link:hover {
  text-decoration: none !important;
  /* Add any additional styles for hover state */
}
</style>
