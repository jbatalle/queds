import DashboardLayout from '../components/Dashboard/Layout/DashboardLayout.vue'

//import middleware
import auth from "../middleware/auth";
import guest from "../middleware/guest";

// Not Found page
import NotFound from '../components/Dashboard/Layout/NotFoundPage.vue'
// Dashboard pages
const Overview = () => import('../pages/Overview.vue');

import Login from '../pages/auth/Login.vue';
import Register from '../pages/auth/Register.vue';

//import PasswordReset from "../pages/auth/Reset.vue";
//import PasswordEmail from "../pages/auth/Email.vue";
const Accounts = () => import('../pages/accounts/Accounts.vue');
const BrokerBalance = () => import('../pages/broker/BrokerBalance.vue');
const BrokerOrder = () => import('../pages/broker/BrokerOrders.vue');
const BrokerTax = () => import('../pages/broker/BrokerTax.vue');
const CryptoBalance = () => import('../pages/crypto/CryptoBalance.vue');
const CryptoOrder = () => import('../pages/crypto/CryptoOrders.vue');
const CryptoTax = () => import('../pages/crypto/CryptoTax.vue');
const Analysis = () => import('../pages/Analysis_old.vue');
const Comments = () => import('../pages/Comments.vue');


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
