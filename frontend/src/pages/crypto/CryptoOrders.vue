<template>
  <div class="row">
    <div class="col-md-12 card mt-3">
      <div class="card-header">
        <div class="row">
          <div class="col-md-6">
            <h5 class="title">Orders </h5>
          </div>
          <div class="col-md-6">
            <div class="flex text-right mb-3 gap-4">
              <el-space wrap>
                <el-input class="input-sm" placeholder="Search" v-model="search"
                          addon-right-icon="nc-icon nc-zoom-split">
                  <template #suffix>
                    <el-icon class="el-input__icon"></el-icon>
                    <i class="nc-icon nc-zoom-split"></i>
                  </template>
                </el-input>
                <span></span>
                <el-button type="primary" size="small" @click="addOrder">Add order</el-button>
              </el-space>
            </div>
          </div>

          <div class="col-sm-4">
            <div class="pull-right">

            </div>
          </div>
        </div>
      </div>
      <div class="card-body row">
        <orders-table :base_currency="base_currency" :orders="orders" :loading="loading" :pagination="pagination"
                      :accounts="accounts"
                      type="exchange"
                      @handleSizeChange="handleSizeChange"
                      @handlePageChange="handlePageChange"
                      @filterChange="filterChange"
        />
      </div>
    </div>
  </div>
</template>
<script>
import axios from "axios";
import OrdersTable from "@/components/Dashboard/Views/OrdersTable.vue";

export default {
  components: {OrdersTable},

  data: () => ({
    base_currency: localStorage.getItem('base_currency'),
    accounts: [],
    orders: [],
    filter_accounts: new Set(),
    sort: "value_date",
    search: '',
    pagination: {
      perPage: 50,
      currentPage: 1,
      perPageOptions: [5, 20, 50, 100, 1000],
      total: 0
    },
    total: 0,
    total_orders: 0,
    loading: true,
    initialData: false
  }),
  watch: {
    // pagination: {
    //   handler(val) {
    //     if (this.dataLoaded) {
    //       this.getData();
    //     }
    //   },
    //   deep: true
    // },
    search: {
      handler(val) {
        if (this.search_loading) {
          return;
        }
        // wait 2 seconds before make the request
        this.search_loading = true;
        setTimeout(() => {
          this.getData();
          this.search_loading = false;
        }, 2000);
      }
    }
  },
  computed: {},
  created() {
    this.getData();
  },
  methods: {
    handleSizeChange(val) {
      this.pagination.perPage = val;
    },
    handlePageChange(val) {
      this.pagination.currentPage = val;
    },
    filterTag(value, row) {
      return row.account === value;
    },
    filterChange(e) {
      let propertyName = Object.getOwnPropertyNames(e)[0]
      this.filter_accounts = e[propertyName];
      this.getData();
    },
    fillOrders(res) {
      let vm = this;
      this.orders = res.data.results;
      [...(new Set(this.orders.map(el => el.account))).values()].forEach(function (entry) {
        if (!vm.accounts.some(el => el.text === entry))
          vm.accounts.push({"text": entry, "value": entry});
      });
      this.pagination.total = res.data.pagination.count;
      this.orders.forEach(function (s) {
        if (s.type === 0) {
          s.type = "Buy";
          s.cost = s.amount * s.price + s.fee;
        } else {
          s.type = "Sell";
          s.cost = s.amount * s.price - s.fee;
        }
        s.total = s.amount * s.price;
        s.value_date = s.value_date.split(' ')[0];
      });
      this.loading = false;
      if (!this.initialData) {
        this.$watch('pagination', this.getData, {deep: true});
      }
      this.initialData = true;
    },
    async getData() {
      this.loading = true;
      let f = ""
      if (this.filter_accounts.length > 0)
        f = "&exchange=" + this.filter_accounts.join();
      if (this.search.length > 0)
        f += "&search=" + this.search.toLowerCase();
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/orders?page=" + this.pagination.currentPage + "&limit=" + this.pagination.perPage + f).then(this.fillOrders);
    },
  },
}
</script>
<style>
</style>
