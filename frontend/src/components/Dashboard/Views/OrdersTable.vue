<template>
  <div class="col-sm-12 mt-2">
    <el-table v-loading="loading"
              :data="orders"
              :default-sort="{property: 'value_date', order: 'descending'}"
              :row-class-name="tableRowClassName"
              @filter-change="filterChange"
              :cell-style="{padding: '0', height: '20px'}">
      <el-table-column label="type" width="60px">
        <template v-slot:default="scope">
          <el-tooltip :content="scope.row.type" placement="top">
            <span type="info"><i class="nc-icon" :class="iconClassName(scope.row)"></i></span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column v-if="type==='broker'" label="ticker">
        <template v-slot:default="scope">
          <el-tooltip v-if="scope.row.ticker" :content="scope.row.ticker.name" placement="top">
            <span type="info"> {{ scope.row.ticker.ticker }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column v-else label="pair" sortable>
        <template v-slot:default="scope">
          <span type="info"> {{ scope.row.pair }}</span>
        </template>
      </el-table-column>
      <el-table-column
          prop="account"
          label="Account"
          :filters="accounts"
          :filter-method="filterTag"
          filter-placement="bottom-end"
      >
      </el-table-column>
      <el-table-column label="Value date" prop="value_date" sortable/>
      <!--el-table-column label="type" property="type" sortable></el-table-column-->
      <el-table-column v-if="type==='broker'" label="Shares" property="shares" width="100px"></el-table-column>
      <el-table-column v-else label="Amount" property="amount"></el-table-column>
      <el-table-column label="price" width="">
        <template v-slot:default="scope">
          <span v-if="scope.row.ticker">
          {{ $filters.toCurrency(scope.row.price, scope.row.ticker.currency) }}
            </span>
          <span v-else>
            {{ $filters.toCurrency(scope.row.price, scope.row.currency_source, 8) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="fee" property="fee">
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.fee, base_currency) }}
        </template>
      </el-table-column>
      <el-table-column v-if="type==='broker'" label="Exchange Fee" property="exchange_fee">
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.exchange_fee, base_currency) }}
        </template>
      </el-table-column>
      <el-table-column label="Total" property="total" sortable>
        <template v-slot:default="scope"><!-- v-if="scope.row.ticker.currency !== undefined">-->
          <span v-if="scope.row.ticker">
          {{ $filters.toCurrency(scope.row.total, scope.row.ticker.currency, 8) }}
            </span>
        </template>
      </el-table-column>
      <el-table-column label="Cost" property="cost" sortable>
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.cost, base_currency) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
  <div class="col-sm-6 pagination-info">
    <p class="category">Showing {{ from + 1 }} to {{ to }} of {{ pagination.total }} entries</p>
  </div>
  <div class="col-sm-6">
    <div class="pull-right">
      <el-pagination small layout="sizes, prev, pager, next"
                     :total="pagination.total"
                     :page-sizes="pagination.perPageOptions"
                     :page-size="pagination.perPage"
                     :current-page="pagination.currentPage"
                     @size-change="handleSizeChange"
                     @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script>
export default {
  props: {
    base_currency: String,
    orders: Array,
    loading: Boolean,
    pagination: Object,
    accounts: Array,
    type: String,
  },
  emits: ['handleSizeChange', 'handlePageChange', 'filterChange'],
  data: () => ({
    filter_accounts: new Set(),
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
    handleSizeChange(val) {
      this.$emit('handleSizeChange', val);
    },
    handlePageChange(val) {
      this.$emit('handlePageChange', val);
    },
    filterTag(value, row) {
      // we cannot emit because this filter is executed when rendering
      return row.account === value;
    },
    filterChange(e) {
      this.$emit('filterChange', e);
    },
    tableRowClassName(item) {
      if (item.row.type === 'Sell')
        return 'table-success';
      else if (item.row.type === 'Reverse_buy' || item.row.type === 'Reverse_sell' || item.row.type === 'OTC_buy' | item.row.type === 'OTC_sell')
        return "table-danger";
      else
        return 'table-information';
    },
    iconClassName(item) {
      if (item.type === 'Sell')
        return "nc-minimal-left blue";
      else if (item.type === 'Reverse_buy' || item.type === 'Reverse_sell' || item.type === 'OTC_buy' | item.type === 'OTC_sell')
        return "nc-refresh-69 orange";
      else
        return 'nc-minimal-right red';
    }
  },
}
</script>

<style scoped>
.example-showcase .el-loading-mask {
  z-index: 9;
}
</style>
