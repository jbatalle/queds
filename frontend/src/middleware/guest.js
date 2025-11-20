import store from "../store";

export default function guest({next, router}) {
    console.log("Middleware guest");
    if (store.getters.isLoggedIn) {
        return router.push({path: "/"});
    }
    return next();
}
