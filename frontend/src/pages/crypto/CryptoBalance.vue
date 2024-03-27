<template>
  <div>
    <div class="row">
      <div class="col-lg-12 col-md-6 col-sm-6">
        <div class="row">
          <div class="col-lg-4 col-md-6 col-sm-6">
            <stats-card type="warning"
                        icon="nc-icon nc-money-coins"
                        small-title="Cost"
                        :title="$filters.toCurrency(total_cost, base_currency)">
            </stats-card>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <stats-card type="success"
                        icon="nc-icon nc-money-coins"
                        small-title="Wallet Value"
                        :title="$filters.toCurrency(value, base_currency)">
            </stats-card>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Current wallet value. Benefits vs cost and benefits from previous day
                </div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="nc-icon nc-globe"
                            small-title="Current W/L"
                            :title="$filters.toCurrency(benefits, base_currency)">
                </stats-card>
                </template>
            </el-popover>
          </div>
        </div>
      </div>
    </div>
    <el-tabs class="demo-tabs" type="card" v-model="activeName">
      <el-tab-pane class="sidebar-wrapper" label="Wallet" name="first">
        <div class="row">
          <balance-table :base_currency="base_currency" :wallet="wallet" :loading="loading" type="exchange"
                         @recalculate="recalculate" @reload="reload"
          />
        </div>
      </el-tab-pane>
      <el-tab-pane label="Distribution" name="second">

        <balance-dist :wallet="wallet" :total_value="total_value" type="exchange"/>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script>
import axios from "axios";
import BalanceTable from "@/components/Dashboard/Views/BalanceTable.vue";
import BalanceDist from "@/components/Dashboard/Views/BalanceDist.vue";

export default {
  name: "Wallet",
  components: {
    BalanceTable, BalanceDist
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      activeName: 'first',
      loading: true,
      search: '',
      wallet: [],
      value: 0,
      total_value: 0,
      benefits: 0,
      total_cost: 0,
      investKey: 0,
    };
  },
  created() {
    this.getData();
  },
  methods: {
    async recalculate() {
      let vm = this;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/calculate").then(
          vm.$notify({
            message: 'Recalculating balances/taxes!',
            type: 'info',
          })
      );
    },
    async reload() {
      await this.getData();
    },
    fillWallet(res) {
      this.wallet = res.data;
      let vm = this;
      this.wallet = []
      this.total_cost = 0;
      this.benefits = 0;
      this.value = 0;
      this.total_value = 0;

      let bar = new Promise((resolve, reject) => {
        res.data.forEach(function (t, index, array) {
          console.log(t);
          t.children = t.open_orders;
          t.symbol = t.currency + "USD"; // change here the symbol by trading_view symbol
          t.container_id = t.symbol; // div id for trading view
          t.style = "3";
          if (t.currency === undefined) {
            return;
          }
          t.children.forEach(function (c) {
            c.ticker = {
              "ticker": c.order.value_date.split(' ')[0],
            }
            c.id = t.id + "_" + c.id;
            c.price = c.order.price;
            //c.amount =
          });
          vm.total_cost += t.price * t.amount;
          vm.wallet.push(t)
          vm.total_value += t.current_value;
          // vm.benefits += t.benefits;
          vm.benefits += t.current_benefit;
        });

      });

      let wallet_value = Number(this.wallet.reduce((a, b) => a + b.amount, 0)).toFixed(2);
      //this.createInvestChart(wallet_value);

      this.wallet.forEach(function (t) {
        t['percentage'] = Number(t.current_value / wallet_value * 100).toFixed(2);
      });
      this.loading = false;
    },
    async getData() {
      this.loading = true;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/wallet").then(this.fillWallet);
    },
    colorClass(item) {
      if (item.column.property == 'current_benefit') {
        if (parseFloat(item.row[item.column.property]) > 0)
          return "green";
        else
          return "red"
      } else
        return "black"
    },
  },
};
</script>
<style>
.Chart {
  max-width: 200px;
  padding: 20px;
  /* box-shadow: 0px 0px 20px 2px rgba(0, 0, 0, 0.4); */
  border-radius: 20px;
  margin: 50px 0;
}

.el-tabs__item.is-active {
  background-color: #ffffff;
  color: #3cab79 !important;
}

.el-tabs__item:hover {
  background-color: #ffffff;
  color: #3cab79 !important;
}
</style>
