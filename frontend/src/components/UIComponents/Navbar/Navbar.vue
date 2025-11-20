<template>
  <nav :class="classes" class="navbar navbar-expand-lg" >
    <div class="container-fluid">
      <div class="navbar-wrapper">
        <slot></slot>
      </div>

      <button aria-controls="navigation-index"
              @click="toggleMenu"
              aria-label="Toggle navigation"
              class="navbar-toggler"
              type="button">
        <span class="navbar-toggler-bar navbar-kebab"></span>
        <span class="navbar-toggler-bar navbar-kebab"></span>
        <span class="navbar-toggler-bar navbar-kebab"></span>
      </button>

      <div class="collapse navbar-collapse justify-content-end"
           :class="{ show: showNavbar }"
           id="navigation">
        <ul class="navbar-nav">
          <slot name="navbar-menu"></slot>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'navbar',
  props: {
    navbarMenuClasses: {
      type: [String, Object],
      default: ''
    },
    transparent: {
      type: Boolean,
      default: true
    },
    position: {
      type: String,
      default: 'absolute'
    },
    type: {
      type: String,
      default: 'white',
      validator(value) {
        return ['white', 'default', 'primary', 'danger', 'success', 'warning', 'info'].includes(value);
      }
    }
  },
  data() {
    return {
      showNavbar: false
    }
  },
  computed: {
    classes() {
      let color = `bg-${this.type}`;
      let navPosition = `navbar-${this.position}`;
      return [
        {'navbar-transparent': !this.showNavbar && this.transparent},
        {[color]: this.showNavbar || !this.transparent},
        {'show': this.showNavbar},
        navPosition
      ]
    }
  },
  methods: {
    toggleMenu() {
      this.showNavbar = !this.showNavbar;
    }
  }
}
</script>

<style scoped>
.navbar-relative {
  position: relative;
}

nav.show {
  position: relative;
}

@media (max-width: 991px) {
  .navbar {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  .navbar-toggler {
    display: block;
  }
  .navbar-collapse {
    display: none;
    width: 100%;
  }
  .navbar-collapse.show {
    position: relative;
    display: flex;
    flex-direction: column;
  }
}
</style>
