import store from "../store";

export default function auth({next, router}) {
    console.log("MIddleware auth");
    if (!store.getters.isLoggedIn) {
        return router.push({name: "Login"});
    }
    return next();
}
