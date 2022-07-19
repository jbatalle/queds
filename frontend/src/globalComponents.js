import {Button, Card } from 'src/components/UIComponents';
import { ValidationProvider } from "vee-validate";
import { ValidationObserver } from "vee-validate";
import VueTradingView from 'vue-trading-view';
/**
 * You can register global components here and use them as a plugin in your main Vue instance
 * Ideally, only small components that are re-used many times across your application should be registered here.
 * For plugins and bigger components local registration is preferable because it will allow you to do code splitting easier :)
 */

const GlobalComponents = {
  install (Vue) {
    Vue.component(Button.name, Button);
    Vue.component(Card.name, Card);
    // Vue.component(ValidationError)
    Vue.component("ValidationProvider", ValidationProvider);
    Vue.component("ValidationObserver", ValidationObserver);
    Vue.component("VueTradingView", VueTradingView);
  }
}

export default GlobalComponents
