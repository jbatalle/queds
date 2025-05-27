<template>

  <el-dialog title="Update ticker" v-model="tickerDialogVisible" width="60%" :close-on-press-escape="true"
             :before-close="handleClose">
    <el-form :model="tickerForm">
      <el-form-item label="Ticker Name">
        <el-input v-model="tickerForm.name"/>
      </el-form-item>
      <el-form-item label="Ticker Symbol">
        <el-input v-model="tickerForm.ticker"/>
      </el-form-item>
      <el-form-item label="Yahoo Ticker Symbol">
        <el-input v-model="tickerForm.ticker_yahoo"/>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="tickerDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="updateTicker">Update</el-button>
      </span>
    </template>
    <span slot="footer" class="dialog-footer"></span>
  </el-dialog>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header">
        <div class="row">
          <div class="col-md-6">
            <h5 class="title">Wallet </h5>
          </div>
          <div class="col-md-6">
            <div class="flex text-right mb-3 gap-4">
              <el-space wrap>
                <el-input class="input-sm" placeholder="Search" v-model="search" width="40%" style="width: 40%;">
                  <template #suffix>
                    <i class="nc-icon nc-zoom-split"></i>
                  </template>
                </el-input>
                <span></span>
                <el-button type="primary" size="small" @click="reload">Reload</el-button>
                <el-button type="warning" size="small" @click="recalculate">Recalculate</el-button>
              </el-space>
            </div>
          </div>
        </div>

        <!--p class="card-category">FX rate: {{ fx_rate }}</p-->
      </div>
      <div class="card-body table-full-width">
        <el-table v-loading="loading"
                  :data="wallet.filter(data => !search || data.ticker.ticker.toLowerCase().includes(search.toLowerCase())
                    || data.ticker.name.toLowerCase().includes(search.toLowerCase()))"
                  :default-sort="{property: 'current_benefit', order: 'descending'}"
                  :cell-class-name="colorClass"
                  :cell-style="{padding: '0', height: '20px'}">
          <el-table-column type="expand" fixed>
            <template #default="props">
              <div style="padding-left: 10px;">
                <h5>Open orders</h5>
              </div>
              <div class="row" style="padding-left: 10px;">
                <div class="col-lg-6 col-md-6 col-sm-12">
                  <el-table :data="props.row.children">
                    <el-table-column label="Date" prop="ticker.ticker"/>
                    <el-table-column v-if="type==='broker'" label="Shares" property="shares"></el-table-column>
                    <el-table-column v-else label="Amount" property="amount">
                      <template v-slot:default="scope">
                        {{ scope.row.amount }}
                      </template>
                    </el-table-column>
                    <el-table-column label="Buy Price" prop="price">
                      <template v-slot:default="scope">
                        <span v-if="type==='broker'">
                          {{ $filters.toCurrency(scope.row.price, scope.row.ticker.currency) }}
                        </span>
                        <span v-else>
                          {{ $filters.toCurrency(scope.row.price, scope.row.current_price_currency, 2) }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column label="Buy Price €" v-if="type==='exchange'" prop="price">
                      <template v-slot:default="scope">
                        {{ $filters.toCurrency(scope.row.price_eur, base_currency, 2) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="Cost" prop="cost">
                      <template v-slot:default="scope">
                        <span v-if="type==='broker'">
                          {{ $filters.toCurrency(scope.row.cost, scope.row.ticker.currency) }}
                        </span>
                        <span v-else>
                          {{ $filters.toCurrency(scope.row.cost, scope.row.current_price_currency, 2) }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column v-if="type==='broker'" label="Rate" prop="currency_rate">
                      <template v-slot:default="scope">
                        {{
                          $filters.toCurrency(scope.row.transaction.currency_rate, scope.row.ticker.currency)
                        }}
                      </template>
                    </el-table-column>
                    <el-table-column v-if="type==='broker'" label="Broker" prop="broker">
                      <template v-slot:default="scope">
                        {{
                          scope.row.transaction.account.name
                        }}
                      </template>
                    </el-table-column>
                    <el-table-column v-if="type==='exchange'" label="Exchange" prop="exchange">
                      <template v-slot:default="scope">
                        {{
                          scope.row.exchange.name
                        }}
                      </template>
                    </el-table-column>
                    <!--el-table-column label="Broker" prop="broker"/-->
                  </el-table>
                </div>
                <div class="col-lg-6 col-md-6 col-sm-12" style="height: 500px">
                  <div v-if="type==='broker'" :id="props.row.ticker.ticker"></div>
                  <div v-else :id="props.row.symbol"></div>
                  <VueTradingView :options="props.row"/>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column v-if="type==='broker'" label="Symbol" prop="ticker.ticker" sortable fixed>
            <template v-slot:default="scope">
          <span @click="openTickerDialog(scope.row.ticker)" style="cursor: pointer; color: #409eff;">
            {{ scope.row.ticker.ticker }}
          </span>
            </template>
          </el-table-column>
          <!--el-table-column v-if="type==='broker'" label="Symbol" property="ticker.ticker" sortable fixed ></el-table-column-->
          <el-table-column v-else label="Coin" property="currency" sortable fixed></el-table-column>
          <el-table-column v-if="type==='broker'" label="Shares" property="shares" width="100px"></el-table-column>
          <el-table-column v-else label="Amount" property="amount">
            <template v-slot:default="scope">
              {{ $filters.toCurrency(scope.row.amount, scope.row.source_currency, 8) }}
            </template>
          </el-table-column>
          <el-table-column label="Price" property="price">
            <template v-slot:default="scope">
                        <span v-if="type==='broker'">
                          {{ $filters.toCurrency(scope.row.price, scope.row.ticker.currency) }}
                        </span>
              <span v-else>
                          {{ $filters.toCurrency(scope.row.price, scope.row.current_price_currency, 2) }}
                        </span>
            </template>
          </el-table-column>
          <el-table-column label="Cost (w. fees)" property="cost">
            <template v-slot:default="scope">
              <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.cost, scope.row.ticker.currency) }}
              </span>
              <span v-else>
                {{ $filters.toCurrency(scope.row.cost, scope.row.current_price_currency, 2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="BEP" property="break_even">
            <template v-slot:default="scope">
              <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.break_even, scope.row.ticker.currency) }}
              </span>
              <span v-else>
                {{ $filters.toCurrency(scope.row.break_even, scope.row.current_price_currency, 2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="Market price" property="current_price">
            <template v-slot:default="scope">
              <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.current_price, scope.row.ticker.currency) }}
              </span>
              <span v-else>
                {{ $filters.toCurrency(scope.row.current_price, scope.row.current_price_currency, 2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="Value" property="base_current_value" sortable>
            <template v-slot:default="scope">
              <span v-if="type==='broker'">
                {{
                  $filters.toCurrency(scope.row.current_value, scope.row.ticker.currency)
                }} <span v-if="scope.row.ticker.currency != 'EUR'">({{ $filters.toCurrency(scope.row.base_current_value, base_currency) }}€)</span>
              </span>
              <span v-else>
                {{ $filters.toCurrency(scope.row.current_value, scope.row.current_price_currency, 2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="W/L" property="current_benefit" sortable>
            <template v-slot:default="scope">
              <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.current_benefit, base_currency) }}
              </span>
              <span v-else>
                {{ $filters.toCurrency(scope.row.current_benefit, scope.row.current_price_currency, 2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column v-if="type==='broker'" label="Day Change" property="day_change" sortable>
            <template v-slot:default="scope"><!-- v-if="scope.row.market.price_change"-->
              <span v-if="scope.row.price_change">
              {{$filters.round(scope.row.day_change, 2)}} ({{ $filters.round(scope.row.price_change, 2) }}%)
              </span>
              <span v-else class="">
                -
              </span>
            </template>
          </el-table-column>
          <el-table-column v-if="type==='broker'" label="Pre" property="pre_change" sortable>
            <template v-slot:default="scope"><!-- v-if="scope.row.market.pre"-->
              {{ $filters.toCurrency(scope.row.pre, scope.row.ticker.currency) }}
              <span v-if="scope.row.pre_change">
                ({{ $filters.round(scope.row.pre_change, 2) }}%)
              </span>
              <span v-else class="">
                -
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import VueTradingView from 'vue-trading-view/src/';

export default {
  props: {
    base_currency: String,
    wallet: Array,
    loading: Boolean,
    accounts: Array,
    type: String,
  },
  components: {
    VueTradingView
  },
  emits: ['recalculate', 'reload'],
  data: () => ({
    filter_accounts: new Set(),
    search: '',
    tickerDialogVisible: false,
    tickerForm: {
      ticker: '',
      name: '',
      ticker_yahoo: ''
    }
  }),

  watch: {
    filter_accounts() {
      this.getData();
    },
  },
  computed: {
    from() {
      return (this.pagination.currentPage - 1) * this.pagination.perPage;
    },
    to() {
      return Math.min(this.pagination.currentPage * this.pagination.perPage, this.pagination.total);
    }
  },
  methods: {
    handleClose() {
      this.tickerDialogVisible = false;
    },
    openTickerDialog(ticker) {
      this.tickerForm = JSON.parse(JSON.stringify(ticker));
      this.tickerDialogVisible = true;
    },
    async updateTicker() {
      await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/stock/ticker", this.tickerForm).then(this.reload);
      this.tickerDialogVisible = false;
    },
    reload() {
      this.$emit('reload');
    },
    recalculate(val) {
      this.$emit('recalculate', val);
    },
    colorClass(item) {
      if (item.column.property == 'price_change' || item.column.property == 'pre_change'
          || item.column.property == 'current_benefit' || item.column.property == 'day_change') {
        let objects = item.column.property.split('.')
        let value = 0;
        if (objects.length > 1) {
          value = objects.reduce((a, prop) => a[prop], item.row);
        } else {
          value = item.row[item.column.property]
        }
        if (parseFloat(value) > 0)
          return "green";
        else if (parseFloat(value) < 0)
          return "red";
      } else
        return "black";
    },
  },
}
</script>

<style scoped>
.example-showcase .el-loading-mask {
  z-index: 9;
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
