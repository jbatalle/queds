import DashboardLayout from '../components/Dashboard/Layout/DashboardLayout.vue'

//import middleware
import auth from "@/middleware/auth";
import guest from "@/middleware/guest";

// Not Found page
import NotFound from '../components/Dashboard/Layout/NotFoundPage.vue'
// Dashboard pages
const Overview = () => import(/* webpackChunkName: "widgets" */ 'src/components/Dashboard/Views/Dashboard/Overview.vue');

import Login from 'src/components/Dashboard/Views/Pages/Login.vue'
import Register from 'src/components/Dashboard/Views/Pages/Register.vue'

import PasswordReset from "src/components/Dashboard/Views/Password/Reset.vue";
import PasswordEmail from "src/components/Dashboard/Views/Password/Email.vue";

// Example pages
const Accounts = () => import('src/components/Dashboard/Views/Accounts/Accounts.vue');
const BrokerBalance = () => import('src/components/Dashboard/Views/Broker/Balance.vue');
const BrokerOrder = () => import('src/components/Dashboard/Views/Broker/Orders.vue');
const BrokerTax = () => import('src/components/Dashboard/Views/Broker/Tax.vue');
const CryptoBalance = () => import('src/components/Dashboard/Views/Crypto/CryptoBalance.vue');
const CryptoOrder = () => import('src/components/Dashboard/Views/Crypto/CryptoOrder.vue');
const CryptoTax = () => import('src/components/Dashboard/Views/Crypto/CryptoTax.vue');
const Analysis = () => import('src/components/Dashboard/Views/Analysis.vue');
const Comments = () => import('src/components/Dashboard/Views/Comments.vue');


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
    redirect: '/stock',
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
    redirect: '/crypto',
    children: [
        {
            path: 'balance',
            name: 'Balance',
            component: CryptoBalance,
            meta: {middleware: auth},
        },
        {
            path: 'orders',
            name: 'Orders',
            component: CryptoOrder
        },
        {
            path: 'taxes',
            name: 'Tax',
            component: CryptoTax
        }
    ]
}
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

let forgotPassword = {
    path: "/password/reset",
    name: "Password Reset",
    component: PasswordReset,
    meta: {middleware: guest}
}

let resetPassword = {
    path: "/password/email",
    name: "Password Reset",
    component: PasswordEmail,
    meta: {middleware: guest}
}


const routes = [
    pagesMenu,
    stockMenu,
    cryptoMenu,
    loginPage,
    registerPage,
    forgotPassword,
    resetPassword,
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
    {path: '*', component: NotFound}
];

export default routes
