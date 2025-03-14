import { createStore } from 'vuex';

import auth from "./modules/auth";
import reset from "./modules/reset";

export default createStore({
  modules: {
    auth,
    reset
  }
});
