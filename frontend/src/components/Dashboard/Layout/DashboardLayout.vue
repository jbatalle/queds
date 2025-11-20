<template>
  <div class="wrapper">
    <side-bar
        :active-color="activeColor"
        :background-color="backgroundColor"
        type="sidebar"
        v-show="showSidebar || isDesktop"
        :class="{ 'sidebar-show': showSidebar }"
        @toggle-sidebar="toggleSidebar"
    >
      <ul class="props nav" slot="links">
        <sidebar-item
            :link="{
            name: 'Dashboard',
            icon: 'nc-icon nc-bank',
            path: '/overview',
          }"
        >
        </sidebar-item>

        <sidebar-item
            :link="{
            name: 'Accounts',
            icon: 'nc-icon nc-single-copy-04',
            path: '/pages/accounts',
          }"
        >
        </sidebar-item>
        <sidebar-item
            opened
            class=""
            :link="{ name: 'Stock', icon: 'fab fa-vuejs fa-2x' }"
        >
          <sidebar-item
              :link="{
              name: 'Wallet',
              path: '/stock/balance',
            }"
          />
          <sidebar-item
              :link="{
              name: 'Orders',
              path: '/stock/orders',
            }"
          />
          <sidebar-item
              :link="{
              name: 'Taxes',
              path: '/stock/taxes',
            }"
          />
        </sidebar-item>

        <sidebar-item
            opened
            class=""
            :link="{ name: 'Crypto', icon: 'fab fa-vuejs fa-2x' }"
        >
          <sidebar-item
              :link="{
              name: 'Balance',
              path: '/crypto/balance',
            }"
          />
          <sidebar-item
              :link="{
              name: 'Orders',
              path: '/crypto/orders',
            }"
          />
          <sidebar-item
              :link="{
              name: 'Taxes',
              path: '/crypto/taxes',
            }"
          />
          <!--sidebar-item
              :link="{
              name: 'Report',
              path: '/crypto/taxes',
            }"
          /-->
        </sidebar-item>
        <sidebar-item
            :link="{
            name: 'Analysis',
            icon: 'nc-icon nc-planet',
            path: '/pages/analysis',
          }"
        >
        </sidebar-item>
        <!--sidebar-item
            :link="{
            name: 'Trends',
            icon: 'nc-icon nc-planet',
            path: '/pages/comments',
          }"
        >
        </sidebar-item-->
      </ul>
    </side-bar>
    <!-- Backdrop overlay -->
    <div
      v-show="showSidebar"
      class="sidebar-backdrop"
      @click="toggleSidebar"
    ></div>
    <div class="main-panel">
      <top-navbar @toggle-sidebar="toggleSidebar"></top-navbar>

      <dashboard-content></dashboard-content>

      <content-footer></content-footer>
    </div>
  </div>
</template>
<style lang="scss">
</style>
<script>
import TopNavbar from "./TopNavbar.vue";
import ContentFooter from "./ContentFooter.vue";
import DashboardContent from "./Content.vue";

export default {
  components: {
    TopNavbar,
    ContentFooter,
    DashboardContent
  },
  data() {
    return {
      backgroundColor: "black",
      activeColor: "success",
      showSidebar: false
    };
  },
    computed: {
      isDesktop() {
        return window.innerWidth > 991;
    }
  },
  methods: {
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    }
  }
};
</script>

<style scoped>
/* Base mobile hidden */
.sidebar {
  transition: all 0.3s ease;
}

/* Mobile */
@media (max-width: 991px) {
  .sidebar {
    transform: translateX(-100%);
    position: fixed;
    width: 250px;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 1030;
    background: #000; /* Adjust to your theme */
  }

  .sidebar.sidebar-show {
    transform: translateX(0);
  }
}
.sidebar-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.4);
  z-index: 900;
}
</style>