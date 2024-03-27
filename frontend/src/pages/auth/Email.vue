<template>
<div class="login-page">
    <app-navbar></app-navbar>
    <div class="wrapper wrapper-full-page">
      <div class="full-page login-page section-image">
        <!--   you can change the color of the filter page using: data-color="blue | azure | green | orange | red | purple" -->
        <div class="content">
          <div class="container reset-container">
            <div class="col-lg-4 col-md-6 ml-auto mr-auto">
                <form ref="reset_password_form" @submit.prevent="handleSubmit()">
                  <card type="login">
                    <h3 slot="header" class="header text-center">Reset Password</h3>
                     <el-input  v-model="form.data.attributes.password" class="mb-2 mt-1" addon-left-icon="nc-icon nc-key-25" placeholder="Password" type="password"/>
                      <validation-error :errors="apiValidationErrors.password"/>
                      <el-input v v-model="form.data.attributes.password_confirmation" class="mb-2 mt-1" addon-left-icon="nc-icon nc-key-25" placeholder="Password confirmation" type="password"/>
                      <validation-error :errors="apiValidationErrors.password_confirmation"/>

                    <p-button native-type="submit" slot="footer" type="primary" round block class="mb-3">Reset Password</p-button>
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
import ValidationError from "src/components/UIComponents/ValidationError.vue";
import formMixin from "@/mixins/form-mixin";
import AppNavbar from 'src/components/Dashboard/Views/Pages/Layout/AppNavbar'
import AppFooter from 'src/components/Dashboard/Views/Pages/Layout/AppFooter'
export default {
  layout: "AuthLayout",
  mixins: [formMixin],
  components: { 
    ValidationError,
    AppNavbar,
    AppFooter
    },
  data() {
    return {
      form: {
        data: {
          type: "password-reset",
          attributes: {
            password: "",
            password_confirmation: "",
            token: "",
            email: "",
          },
        },
      },
    };
  },
  mounted() {
    this.form.data.attributes.email = this.$route.query.email;
    this.form.data.attributes.token = this.$route.query.token;
  },
  beforeDestroy() {
    this.$router.replace({ query: null });
  },
  methods: {
    async handleSubmit() {
      try {
        await this.$store.dispatch("reset/createNewPassword", this.form.data);
      } catch (error) {
        await this.$notify({
          type: "danger",
          message: "The given data was invalid.",
        });
        this.setApiValidation(error.response.data.errors);
      }
    },
  },
};
</script>
