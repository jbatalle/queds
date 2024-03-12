import DashboardLayout from '../components/Dashboard/Layout/DashboardLayout.vue'

//import middleware
import auth from "../middleware/auth";
import guest from "../middleware/guest";

// Not Found page
import NotFound from '../components/Dashboard/Layout/NotFoundPage.vue'
// Dashboard pages
const Overview = () => import('../components/Dashboard/Views/Overview.vue');

import Login from '../components/Dashboard/Views/Pages/Login.vue';
import Register from '../components/Dashboard/Views/Pages/Register.vue';

//import PasswordReset from "../components/Dashboard/Views/Password/Reset.vue";
//import PasswordEmail from "../components/Dashboard/Views/Password/Email.vue";
//
const Accounts = () => import('../components/Dashboard/Views/Accounts.vue');
const BrokerBalance = () => import('../components/Dashboard/Views/Broker/Balance.vue');
const BrokerOrder = () => import('../components/Dashboard/Views/Broker/Orders.vue');
const BrokerTax = () => import('../components/Dashboard/Views/Broker/Tax.vue');
const CryptoBalance = () => import('../components/Dashboard/Views/Crypto/CryptoBalance.vue');
const CryptoOrder = () => import('../components/Dashboard/Views/Crypto/CryptoOrder.vue');
const CryptoTax = () => import('../components/Dashboard/Views/Crypto/CryptoTax.vue');
const Analysis = () => import('../components/Dashboard/Views/Analysis_old.vue');
const Comments = () => import('../components/Dashboard/Views/Comments.vue');


let pagesMenu = {
    path: '/pages',
    component: DashboardLayout,
    redirect: '/',
    children: [
        {
            path: 'accounts',
            name: 'Accounts',
            component: Accounts,
            meta: {middleware: auth}
        },
        {
            path: 'analysis',
            name: 'Analysis',
            component: Analysis
        },
        {
             path: 'comments',
             name: 'Comments',
             component: Comments
        }
    ]
};
let stockMenu = {
    path: '/stock',
    component: DashboardLayout,
    meta: {middleware: auth},
    //redirect: '/stock',
    children: [
        {
            path: 'balance',
            name: 'Balance',
            component: BrokerBalance,
            meta: {middleware: auth},
        },
        {
            path: 'orders',
            name: 'Orders',
            component: BrokerOrder,
            meta: {middleware: auth},
        },
        {
            path: 'taxes',
            name: 'Taxes',
            component: BrokerTax,
            meta: {middleware: auth},
        }
    ]
};
let cryptoMenu = {
    path: '/crypto',
    component: DashboardLayout,
    meta: {middleware: auth},
    //redirect: '/crypto',
    children: [
        {
            path: 'balance',
            name: 'CryptoBalance',
            component: CryptoBalance,
            meta: {middleware: auth},
        },
        {
            path: 'orders',
            name: 'CryptoOrders',
            component: CryptoOrder
        },
        {
            path: 'taxes',
            name: 'CryptoTax',
            component: CryptoTax
        }
    ]
};
let loginPage = {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {middleware: guest}
}

let registerPage = {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: {middleware: guest}
}

// let forgotPassword = {
//     path: "/password/reset",
//     name: "Password Reset",
//     component: PasswordReset,
//     meta: {middleware: guest}
// }
//
// let resetPassword = {
//     path: "/password/email",
//     name: "Password Reset",
//     component: PasswordEmail,
//     meta: {middleware: guest}
// }


const routes = [
    pagesMenu,
    stockMenu,
    cryptoMenu,
    loginPage,
    registerPage,
    //forgotPassword,
    //resetPassword,
    {
        path: '/',
        component: DashboardLayout,
        redirect: '/overview',
        meta: {middleware: auth},
        children: [
            {
                path: 'overview',
                name: 'Overview',
                component: Overview,
                meta: {middleware: auth},
            }
        ]
    },
    {path: '/:catchAll(.*)', component: NotFound}
];

export default routes
