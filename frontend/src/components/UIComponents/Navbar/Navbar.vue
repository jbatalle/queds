<template>
  <nav :class="classes" class="navbar navbar-expand-lg">
    <div class="container-fluid">
      <slot></slot>
      <slot name="toggle-button">
        <button aria-controls="navigation-index"
                @click="toggleMenu"
                aria-expanded="true" aria-label="Toggle navigation"
                class="navbar-toggler" data-toggle="collapse" type="button"><span
          class="navbar-toggler-bar navbar-kebab"></span><span class="navbar-toggler-bar navbar-kebab"></span><span
          class="navbar-toggler-bar navbar-kebab"></span></button>
      </slot>
      <CollapseTransition>
        <div class="collapse navbar-collapse justify-content-end show"
             :class="navbarMenuClasses"
             v-show="showNavbar"
             id="navigation">
          <ul class="navbar-nav">
            <slot name="navbar-menu"></slot>
          </ul>
        </div>
      </CollapseTransition>
    </div>
  </nav>
</template>
<script>
  import { CollapseTransition } from 'vue2-transitions';

  export default {
    name: 'navbar',
    props: {
      showNavbar: {
        type: Boolean,
        description: "Whether navbar is visible"
      },
      navbarMenuClasses: {
        type: [String, Object],
        description: 'Navbar menu css classes'
      },
      transparent: {
        type: Boolean,
        default: true,
        description: 'Whether navbar is transparent'
      },
      position: {
        type: String,
        default: 'absolute',
        description: 'Navbar position (absolute|fixed|relative)'
      },
      type: {
        type: String,
        default: 'white',
        validator(value) {
          return ['white', 'default', 'primary', 'danger', 'success', 'warning', 'info'].includes(value);
        },
        description: 'Navbar type (primary|info|danger|default|warning|success)'
      }
    },
    model: {
      prop: 'showNavbar',
      event: 'change'
    },
    components: {
      CollapseTransition
    },
    computed: {
      classes() {
        let color = `bg-${this.type}`;
        let navPosition = `navbar-${this.position}`;
        return [
          { 'navbar-transparent': !this.showNavbar && this.transparent },
          { [color]: this.showNavbar || !this.transparent },
          navPosition]
      }
    },
    methods: {
      toggleMenu() {
        this.$emit('change', !this.showNavbar);
      }
    }
  }
</script>
<style scoped>
  .navbar-relative {
    position: relative;
  }
</style>
