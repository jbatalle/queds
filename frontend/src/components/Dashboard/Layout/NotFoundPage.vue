<template>
  <div class="login-page">
    <app-navbar></app-navbar>
    <div class="wrapper wrapper-full-page">
      <div class="full-page login-page section-image">
        <!--   you can change the color of the filter page using: data-color="blue | azure | green | orange | red | purple" -->
        <div class="content">
          <div class="container">
            <div class="col-lg-4 col-md-6 ml-auto mr-auto">
              <info-section class="mt-5"
                            type="danger"
                            title="Marketing"
                            description="We've created the marketing campaign of the website. It was a very interesting collaboration."
                            icon="nc-icon nc-alert-circle-i">
                <h2 class="text-white mt-3">Page Not Found</h2>
                <small class="text-white">Oops! It seems that this page does not exist.
                  <br>
                  You can navigate back <router-link to="/">to main page</router-link>
                </small>
              </info-section>
            </div>
          </div>
        </div>
        <app-footer></app-footer>
      </div>
    </div>
  </div>
</template>
<script>
  import {Card, Button, InfoSection} from '../../UIComponents';
  import AppNavbar from '../Views/Pages/Layout/AppNavbar'
  import AppFooter from '../Views/Pages/Layout/AppFooter'
  export default {
    components: {
      Card,
      AppNavbar,
      AppFooter,
      InfoSection,
      [Button.name]: Button
    },
    methods: {
      toggleNavbar () {
        document.body.classList.toggle('nav-open')
      },
      closeMenu () {
        document.body.classList.remove('nav-open')
        document.body.classList.remove('off-canvas-sidebar')
      }
    },
    beforeDestroy () {
      this.closeMenu()
    }
  }
</script>
<style>
</style>
