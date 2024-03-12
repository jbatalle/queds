<template>
  <div class="row">
    <div class="col-md-12 card mt-3">
      <div class="card-header">
        <div class="row">
          <div class="col-md-4">
            <h5 class="title">Orders </h5>
          </div>
          <div class="col-sm-4">
          </div>
          <div class="col-sm-4">
            <div class="pull-right">
              <el-input class="input-sm"
                        placeholder="Search"
                        v-model="search"
                        addon-right-icon="nc-icon nc-zoom-split">
                <template #suffix>
                  <el-icon class="el-input__icon"></el-icon>
                  <i class="nc-icon nc-zoom-split"></i>
                </template>
              </el-input>
            </div>
          </div>
        </div>
      </div>
      <div class="card-body row">
        <div class="col-sm-12 mt-2">
          <el-table v-loading="loading"
                    :data="orders"
                    :default-sort="{property: 'value_date', order: 'descending'}"
                    :row-class-name="tableRowClassName"
                    @filter-change="filterChange"
                    :cell-style="{padding: '0', height: '20px'}">
            <el-table-column label="pair" sortable>
              <template v-slot:default="scope">
                <span type="info"><i class="nc-icon" :class="iconClassName(scope.row)"></i> {{ scope.row.pair }}</span>
              </template>
            </el-table-column>
            <el-table-column
                prop="account"
                label="Exchange"
                :filters="accounts"
                :filter-method="filterTag"
                filter-placement="bottom-end"
            >
            </el-table-column>
            <el-table-column label="Value date" prop="value_date" sortable/>
            <el-table-column label="amount" prop="amount" sortable>
              <template v-slot:default="scope">
                {{ $filters.toCurrency(scope.row.amount, scope.row.currency_source, 8) }}
              </template>
            </el-table-column>
            <el-table-column label="price" prop="price">
              <template v-slot:default="scope">
                {{ $filters.toCurrency(scope.row.price, scope.row.currency_source, 8) }}
              </template>
            </el-table-column>
            <el-table-column label="fees" sortable>
              <template v-slot:default="scope">
                {{ $filters.toCurrency(scope.row.fee, scope.row.currency_source, 8) }}
              </template>
            </el-table-column>
            <el-table-column label="total" sortable>
              <template v-slot:default="scope">
                {{ $filters.toCurrency(scope.row.total, scope.row.currency_source, 8) }}
              </template>
            </el-table-column>
            <el-table-column label="cost" sortable>
              <template v-slot:default="scope">
                {{ $filters.toCurrency(scope.row.cost, scope.row.currency_source, 8) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="col-sm-6 pagination-info">
          <p class="category">Showing {{ from + 1 }} to {{ to }} of {{ total }} entries</p>
        </div>
        <div class="col-sm-6">
          <div class="pull-right">
            <el-pagination small layout="sizes, prev, pager, next"
                           :total="total"
                           :page-sizes="pagination.perPageOptions"
                           :page-size="pagination.perPage"
                           :current-page="pagination.currentPage"
                           @size-change="handleSizeChange"
                           @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import axios from "axios";

export default {
  components: {},

  data: () => ({
    accounts: [],
    orders: [],
    filter_accounts: new Set(),
    sort: "value_date",
    search: '',
    pagination: {
      perPage: 50,
      currentPage: 1,
      perPageOptions: [5, 20, 50, 100, 1000],
    },
    total: 0,
    total_orders: 0,
    loading: true
  }),
  watch: {
    pagination: {
      handler(val) {
        this.getData();
      },
      deep: true
    },
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
  computed: {
    from() {
      return this.pagination.perPage * (this.pagination.currentPage - 1);
    },
    to() {
      let highBound = this.from + this.pagination.perPage;
      if (this.total < highBound) {
        highBound = this.total;
      }
      return highBound;
    },
  },
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
      return row.account === value
    },
    filterChange(e) {
      let propertyName = Object.getOwnPropertyNames(e)[0]
      this.filter_accounts = e[propertyName];
      this.getData()
    },
    fillOrders(res) {
      let vm = this;
      this.orders = res.data.results;
      [...(new Set(this.orders.map(el => el.account))).values()].forEach(function (entry) {
        if (!vm.accounts.some(el => el.text === entry))
          vm.accounts.push({"text": entry, "value": entry});
      });
      this.total = res.data.pagination.count;
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
    tableRowClassName(item) {
      if (item.row.type === 'Sell')
        return 'table-success';
      else
        return 'table-warning';
    },
    iconClassName(item) {
      if (item.type === 'Sell')
        return "nc-minimal-left blue";
      else
        return 'nc-minimal-right red';
    }
  },
}
</script>
<style>
</style>
