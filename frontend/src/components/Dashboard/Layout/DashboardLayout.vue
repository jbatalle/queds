<template>
  <div class="wrapper">
    <side-bar
        :active-color="activeColor"
        :background-color="backgroundColor"
        type="sidebar"
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
            class="example"
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
        </sidebar-item>
        <sidebar-item
            :link="{
            name: 'Analysis',
            icon: 'nc-icon nc-planet',
            path: '/pages/analysis',
          }"
        >
        </sidebar-item>
        <sidebar-item
            :link="{
            name: 'Trends',
            icon: 'nc-icon nc-planet',
            path: '/pages/comments',
          }"
        >
        </sidebar-item>
      </ul>
    </side-bar>

    <div class="main-panel">
      <top-navbar></top-navbar>

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
    };
  },

  methods: {
  },
};
</script>
