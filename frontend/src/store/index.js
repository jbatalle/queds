import Vue from 'vue';
import Vuex from 'vuex';

import auth from "./modules/auth";
import reset from "./modules/reset";

Vue.use(Vuex);

export default new Vuex.Store({
  modules: {
    auth,
    reset
  }
});
