import store from "../store";

export default function auth({next, router}) {
    if (!store.getters.isLoggedIn) {
        return router.push({name: "Login"});
    }
    return next();
}
