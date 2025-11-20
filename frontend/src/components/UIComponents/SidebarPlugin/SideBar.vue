<template>
  <div class="sidebar" :data-color="backgroundColor" :data-active-color="activeColor">
    <div class="logo">
      <a class="simple-text logo-mini" aria-label="sidebar mini logo" href="">
        <div class="logo-img">
          <img :src="logo" alt=""/>
        </div>
      </a>
      <a class="simple-text logo-normal" href="">
        {{ title }}
      </a>
      <button class="d-lg-none close-sidebar-btn" @click="$emit('toggle-sidebar')">✕</button>
    </div>
    <div class="sidebar-wrapper" ref="sidebarScrollArea">
      <slot class="nav"></slot>
    </div>
  </div>
</template>
<script>
import "perfect-scrollbar/css/perfect-scrollbar.css";

export default {
  props: {
    title: {
      type: String,
      default: "Queds",
      description: "Sidebar title",
    },
    backgroundColor: {
      type: String,
      default: "black",
      validator: (value) => {
        let acceptedValues = ["white", "brown", "black"];
        return acceptedValues.indexOf(value) !== -1;
      },
      description: "Sidebar background color (white|brown|black)",
    },
    activeColor: {
      type: String,
      default: "success",
      validator: (value) => {
        let acceptedValues = [
          "primary",
          "info",
          "success",
          "warning",
          "danger",
        ];
        return acceptedValues.indexOf(value) !== -1;
      },
      description:
          "Sidebar active text color (primary|info|success|warning|danger)",
    },
    logo: {
      type: String,
      default: "/img/queds.png",
      description: "Sidebar Logo",
    },
    sidebarLinks: {
      type: Array,
      default: () => [],
      description:
          "Sidebar links. Can be also provided as children components (sidebar-item)",
    },
    autoClose: {
      type: Boolean,
      default: true,
    },
  },
  provide() {
    return {
      autoClose: this.autoClose,
    };
  },
  methods: {
    async initScrollBarAsync() {
      let isWindows = navigator.platform.startsWith("Win");
      if (!isWindows) {
        return;
      }
      const PerfectScroll = await import("perfect-scrollbar");
      PerfectScroll.initialize(this.$refs.sidebarScrollArea);
    },
  },
  mounted() {
  },
  beforeDestroy() {
    if (this.$sidebar.showSidebar) {
      this.$sidebar.showSidebar = false;
    }
  },
};
</script>
<style>
@media (min-width: 992px) {
  .navbar-search-form-mobile,
  .nav-mobile-menu {
    /*display: none;*/
  }
}
@media (max-width: 991px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 250px;
    z-index: 1030;
    background: #000; /* adjust */
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }

  .sidebar.show {
    transform: translateX(0);
  }
}
.close-sidebar-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  border: none;
  background: transparent;
  color: white;
  font-size: 24px;
  cursor: pointer;
  z-index: 1100;
}
</style>
