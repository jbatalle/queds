import Vue from "vue";
import router from "@/main";
import {VueAuthenticate} from "vue-authenticate";

import axios from "axios";
import VueAxios from "vue-axios";

Vue.use(VueAxios, axios);

const vueAuth = new VueAuthenticate(Vue.prototype.$http, {
    baseUrl: process.env.VUE_APP_BACKEND_URL,
    tokenName: "access_token",
    loginUrl: "/users/login",
    registerUrl: "/users/register"
});

export default {
    state: {
        token: localStorage.getItem("vue-authenticate.vueauth_access_token") || ''
    },

    getters: {
        token: state => state.token,
        isLoggedIn: state => !!state.token,
    },

    mutations: {
        auth_success(state, token) {
            state.status = true;
            state.token = token;
        },
        logout(state) {
            state.status = '';
            state.token = '';
        },
    },

    actions: {
        login(context, payload) {
            return vueAuth.login(payload.user, payload.requestOptions).then(response => {
                let token = response.data['token'];
                localStorage.setItem("vue-authenticate.vueauth_access_token", token);
                axios.defaults.headers.common['Authorization'] = token;
                context.commit("auth_success", token);
                router.push({path: "/"});
            });
        },
        register(context, payload) {
            return vueAuth.register(payload.user, payload.requestOptions).then(response => {
                router.push({path: "/"});
            });
        },
        logout(context, payload) {
            return vueAuth.logout().then(response => {
                commit('logout');
                localStorage.removeItem("vue-authenticate.vueauth_access_token");
                router.push({name: "Login"});
            }).catch(function (error) {
                console.log("Error with logout, redirect to login page");
                localStorage.removeItem("vue-authenticate.vueauth_access_token");
                context.commit('logout');
                router.push({name: "Login"});
            });
        }
    }
};
