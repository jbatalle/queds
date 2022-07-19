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
                    <el-input v-model="form.data.attributes.email" addon-left-icon="nc-icon nc-single-02" placeholder="Email"/>
                    <validation-error :errors="apiValidationErrors.email" />

                    <p-button native-type="submit" slot="footer" type="primary" round block class="mb-3" disabled>Send Password Reset Link</p-button>
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
      AppNavbar,
      AppFooter,
     ValidationError,
     },
  data() {
    return {
      form: {
        data: {
          type: "password-forgot",
          attributes: {
            email: "",
            redirect_url: process.env.VUE_APP_BASE_URL + "/password/email",
          },
        },
      },
    };
  },
  methods: {
    async handleSubmit() {
       if (this.$isDemo) {
        await this.$notify({
          type: "danger",
          message: "Password reset is disabled in the demo.",
        });
        return;
      }
      try {
        await this.$store.dispatch("reset/forgotPassword", this.form.data);
        await this.$notify({
          type: "success",
          message: "An email with reset password link was sent.",
        });
        this.$refs['reset_password_form'].reset()
      } catch (error) {
        await this.$notify({
          type: "danger",
          message: "We can't find a user with that e-mail address.",
        });
        this.setApiValidation(error.response.data.errors);
      }
    },
  },
};
</script>
