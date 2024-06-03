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
                  <h3 slot="header" class="header text-center">Register</h3>

                  <!--el-input v-model="email" addon-left-icon="nc-icon nc-single-02" placeholder="Email" class="mb-2 mt-1"/-->

                  <el-input v-model="email" class="mb-2 mt-1" addon-left-icon="nc-icon nc-email-85" placeholder="Email"/>
                  <validation-error :errors="apiValidationErrors.email"/>
                  <el-input v-model="password" class="mb-2 mt-1" addon-left-icon="nc-icon nc-key-25" placeholder="Password" type="password"/>
                  <validation-error :errors="apiValidationErrors.password"/>
                  <el-input v-model="password_confirmation" class="mb-2 mt-1" addon-left-icon="nc-icon nc-key-25" placeholder="Password confirmation" type="password"/>
                  <el-button native-type="submit" slot="footer" type="primary" round block class="mb-3">Get started</el-button>
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
import {ElInput, ElNotification, ElButton} from 'element-plus';
import AppNavbar from '@/components/Dashboard/Layout/AppNavbar.vue';
import AppFooter from '@/components/Dashboard/Layout/AppFooter.vue';
import {Card} from '@/components/UIComponents';
import formMixin from "@/mixins/form-mixin";
  export default {
    mixins: [formMixin],
    components: {
      Card,
      AppNavbar,
      AppFooter,
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
          let error_msg = error.response.data.errors || error.response.data.message;
          this.$notify({
            type: 'danger',
            message: error.response.data.message,
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