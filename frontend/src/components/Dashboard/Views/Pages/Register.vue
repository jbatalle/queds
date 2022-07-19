<template>
  <div class="register-page">
    <app-navbar></app-navbar>
    <div class="wrapper wrapper-full-page ">
      <div class="full-page register-page section-image" filter-color="black">
        <div class="content">
          <div class="container">
            <div class="row">
              <div class="col-lg-5 col-md-5 ml-auto">
                <info-section class="mt-5"
                              type="primary"
                              title="Stocks"
                              description="Portfolio for different Brokers."
                              icon="nc-icon nc-tv-2">

                </info-section>
                <info-section type="primary"
                              title="Crypto"
                              description="Portfolio for different Exchanges."
                              icon="nc-icon nc-html5">

                </info-section>

                <info-section type="primary"
                              title="Bank statements"
                              description="List of Bank statements."
                              icon="nc-icon nc-atom">

                </info-section>
              </div>
              <div class="col-lg-4 col-md-6 mr-auto">
                <form @submit.prevent="register">
                <card type="signup">
                  <template slot="header">
                    <h4 class="card-title text-center">Register</h4>
                  </template>

                  <el-input v-model="email" class="mb-2 mt-1" addon-left-icon="nc-icon nc-email-85" placeholder="Email"/>
                  <validation-error :errors="apiValidationErrors.email"/>
                  <el-input v-model="password" class="mb-2 mt-1" addon-left-icon="nc-icon nc-key-25" placeholder="Password" type="password"/>
                  <validation-error :errors="apiValidationErrors.password"/>
                  <el-input v-model="password_confirmation" class="mb-2 mt-1" addon-left-icon="nc-icon nc-key-25" placeholder="Password confirmation" type="password"/>
                  <p-button native-type="submit" slot="footer" type="info" round>Get Started</p-button>
                </card>
                </form>
              </div>
            </div>
          </div>
        </div>
        <app-footer></app-footer>
      </div>
    </div>
  </div>
</template>
<script>
  import {Input} from 'element-ui';
  import AppNavbar from './Layout/AppNavbar'
  import AppFooter from './Layout/AppFooter'
  import { Card, Button, InfoSection} from 'src/components/UIComponents';
  import formMixin from "@/mixins/form-mixin";
  import ValidationError from "src/components/UIComponents/ValidationError.vue";
  export default {
    mixins: [formMixin],
    components: {
      Card,
      AppNavbar,
      AppFooter,
      InfoSection,
      [Button.name]: Button,
      ValidationError,
      [Input.name]: Input
    },
    data() {
      return {
        name: null,
        email: null,
        password: null,
        password_confirmation: null,
      };
    },
    methods: {
      async register() {
        const user = {
              email: this.email,
              password: this.password,
              password_confirmation: this.password_confirmation,
        };
        const requestOptions = {
          headers: {
            Accept: "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
          },
        };
        try {
          await this.$store.dispatch("register", { user, requestOptions });
          this.$notify({
            type: 'success',
            message: 'Successfully registered.',
          })
        } catch (error) {
          this.$notify({
            type: 'danger',
            message: 'Oops, something went wrong!',
          })
          this.setApiValidation(error.response.data.errors);
        }
      },
      toggleNavbar() {
        document.body.classList.toggle('nav-open')
      },
      closeMenu() {
        document.body.classList.remove('nav-open')
        document.body.classList.remove('off-canvas-sidebar')
      }
    },
    beforeDestroy() {
      this.closeMenu()
    }
  }
</script>
<style>
</style>