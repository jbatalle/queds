<template>
  <div class="login-page">
    <app-navbar></app-navbar>
    <div class="wrapper wrapper-full-page">
      <div class="full-page login-page section-image">
        <!--   you can change the color of the filter page using: data-color="blue | azure | green | orange | red | purple" -->
        <div class="content">
          <div class="container">
            <div class="header-body text-center" style="margin-bottom: 15px;">
              <div class="row justify-content-center">
                <div class="text-center">
                  <div class="text-white" v-if="$isDemo">
                    <h3 class="text-white"></h3>
                    <div><strong>You can log in with:</strong></div>
                    <div>Username: <b>demo@queds.com</b> Password: <b>supersecret</b></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-lg-4 col-md-6 ml-auto mr-auto">
              <form @submit.prevent="login">
                <card type="login">
                  <h3 slot="header" class="header text-center">Login</h3>

                  <el-input v-model="email" addon-left-icon="nc-icon nc-single-02" placeholder="Email"
                          class="mb-2 mt-1"/>
                  <validation-error :errors="apiValidationErrors.email"/>
                  <el-input v-model="password" addon-left-icon="nc-icon nc-key-25" placeholder="Password"
                            type="password"
                          class="mb-2 mt-1"/>
                  <validation-error :errors="apiValidationErrors.password"/>
                  <div slot="footer">
                    <p-button native-type="submit" slot="footer" type="warning" round block class="mb-3">Get started
                    </p-button>

                    <div class="pull-left">
                      <h6><a href="/password/reset" class="link footer-link">Forgot Password?</a></h6>
                    </div>
                  </div>
                </card>
              </form>
            </div>
          </div>
        </div>
        <app-footer></app-footer>
        <div class="full-page-background" style="background-image: url(/static/img/background/background-2.jpg) "></div>
      </div>
    </div>
  </div>
</template>
<script>
import {Input} from 'element-ui';
import {Card, Button} from 'src/components/UIComponents';
import AppNavbar from './Layout/AppNavbar'
import AppFooter from './Layout/AppFooter'
import formMixin from "@/mixins/form-mixin";
import ValidationError from "src/components/UIComponents/ValidationError.vue";
import IsDemo from 'src/isDemo.js';

export default {
  mixins: [formMixin],
  components: {
    Card,
    AppNavbar,
    AppFooter,
    [Button.name]: Button,
    ValidationError,
    IsDemo,
    [Input.name]: Input
  },
  data() {
    return {
      email: '',
      password: ''
    }
  },
  created() {
    if (this.$isDemo) {
      this.email = "demo@queds.com";
      this.password = "supersecret";
    }
  },
  methods: {
    toggleNavbar() {
      document.body.classList.toggle('nav-open')
    },
    closeMenu() {
      document.body.classList.remove('nav-open')
      document.body.classList.remove('off-canvas-sidebar')
    },
    async login() {
      const user = {
        email: this.email,
        password: this.password
      }

      const requestOptions = {
        headers: {}
      }

      try {
        await this.$store.dispatch("login", {user, requestOptions})
      } catch (e) {
        this.$notify({
          message: 'Invalid credentials!',
          type: 'danger',
        });
        this.setApiValidation(e.response.data.errors)
      }
    }
  },
  beforeDestroy() {
    this.closeMenu()
  }
}
</script>
<style>
</style>
