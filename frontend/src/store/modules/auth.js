import router from "@/router";
import axios from "axios";
const API_URL = "api/users";

export default {
    state: {
        token: localStorage.getItem("access_token") || ''
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
            console.log("Mutation state to null");
            state.status = '';
            state.token = '';
        },
    },

    actions: {
        initialize(context) {
            const token = localStorage.getItem("access_token");
            if (token) {
                axios.defaults.headers.common['Authorization'] = token;
                context.commit("auth_success", token);
            }
        },
        login(context, payload) {
            return axios
                .post(API_URL + '/login', {
                    email: payload.user.email,
                    password: payload.user.password
                })
                .then(response => {
                    let token = "Bearer " + response.data['token'];
                    localStorage.setItem("access_token", token);
                    localStorage.setItem("base_currency", response.data['base_currency']);
                    axios.defaults.headers.common['Authorization'] = token;

                    context.commit("auth_success", token);
                    router.push({path: "/"});
                })/*.catch(function (error) {
                    console.log("Unable to login: " + error);
                    context.commit('logout');
                    router.push({name: "Login"});
                })*/;
        },
        register(context, payload) {
            return axios
                .post(API_URL + '/register', {
                    email: payload.user.email,
                    password: payload.user.password,
                    password_confirmation: payload.user.password_confirmation
                })
                .then(response => {
                    router.push({path: "/"});
                });
        },
        logout(context, payload) {
            return axios
                .post(API_URL + '/logout', {
                    current_user: ""
                })
                .then(response => {
                    context.commit('logout');
                    localStorage.removeItem("access_token");
                    console.log("Redirect to login")
                    router.push({name: "Login"});
                    //return response.data;
                }).catch(function (error) {
                    console.log("Error with logout, redirect to login page");
                    localStorage.removeItem("access_token");
                    //context.commit('logout');
                    console.log("Forward to login");
                    router.push({name: "Login"});
                    console.log("Redirected");
                });
        }
    }
};
