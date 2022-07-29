<template>
  <div class="row">
    <div class="col-md-12 card mt-3">
      <div class="card-header">
        <div class="row">
          <div class="col-md-4">
            <h5 class="title">Orders </h5>
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
          <div class="col-sm-4">
            <div class="pull-right">
              <el-select class="select-default" v-model="pagination.perPage" placeholder="Per page">
                <el-option
                    class="select-default"
                    v-for="item in pagination.perPageOptions"
                    :key="item"
                    :label="item"
                    :value="item">
                </el-option>
              </el-select>
            </div>
          </div>
        </div>
      </div>
      <div class="card-body row">
        <div class="col-sm-12 mt-2">
          <el-table :data="orders.filter(data => !search || data.pair.toLowerCase().includes(search.toLowerCase()))"
                    :default-sort="{property: 'value_date', order: 'descending'}"
                    :row-class-name="tableRowClassName"
                    @filter-change="filterChange"
                    :cell-style="{padding: '0', height: '20px'}">
            <el-table-column label="pair" sortable>
              <template #default="scope">
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
            <el-table-column label="value date" prop="value_date" sortable/>
            <el-table-column label="amount" prop="amount" sortable>
              <template slot-scope="scope">
                {{ scope.row.amount | toCurrency(scope.row.currency_source, 8) }}
              </template>
            </el-table-column>
            <el-table-column label="price" prop="price">
              <template slot-scope="scope">
                {{ scope.row.price | toCurrency(scope.row.currency_target) }}
              </template>
            </el-table-column>
            <el-table-column label="fees" sortable>
              <template slot-scope="scope">
                {{ scope.row.fee | toCurrency(scope.row.currency_target) }}
              </template>
            </el-table-column>
            <el-table-column label="total" sortable>
              <template slot-scope="scope">
                {{ scope.row.total | toCurrency(scope.row.currency_target, 8) }}
              </template>
            </el-table-column>
            <el-table-column label="cost" sortable>
              <template slot-scope="scope">
                {{ scope.row.cost | toCurrency(scope.row.currency_target, 8) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="col-sm-6 pagination-info">
          <p class="category">Showing {{ from + 1 }} to {{ to }} of {{ total }} entries</p>
        </div>
        <div class="col-sm-6">
          <p-pagination class="pull-right"
                        v-model="pagination.currentPage"
                        :per-page="pagination.perPage"
                        :total="total">
          </p-pagination>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import {Table, TableColumn, Select, Option, Tooltip, Tag, Icon, Input} from 'element-ui';
import PPagination from 'src/components/UIComponents/Pagination.vue'
import axios from "axios";

export default {
  components: {
    PPagination,
    [Select.name]: Select,
    [Option.name]: Option,
    [Table.name]: Table,
    [Tooltip.name]: Tooltip,
    [TableColumn.name]: TableColumn,
    [Tag.name]: Tag,
    [Input.name]: Input,
    [Icon.name]: Icon,
  },

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
    total: 0
  }),
  watch: {
    pagination: {
      handler(val) {
        this.getData();
      },
      deep: true
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
    filterTag(value, row) {
      return row.account === value
    },
    filterChange(e) {
      let propertyName = Object.getOwnPropertyNames(e)[0]
      this.filter_accounts = e[propertyName];
      this.getData()
    },
    fillOrders(res) {
      var vm = this;
      let resStatus = res.status === 200 ? true : false;
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
    },
    async getData() {
      let f = ""
      if (this.filter_accounts.length > 0)
        f = "&exchange=" + this.filter_accounts.join();
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/crypto/orders?page=" + this.pagination.currentPage + "&limit=" + this.pagination.perPage + f).then(this.fillOrders);
    },
    tableRowClassName(item) {
      if (item.row.type == 'Sell')
        return 'table-success';
      else
        return 'table-warning';
    },
    iconClassName(item) {
      if (item.type == 'Sell')
        return "nc-minimal-left blue";
      else
        return 'nc-minimal-right red';
    }
  },
}
</script>
<style>
.red {
  color: red
}

.blue {
  color: blue
}
</style>
