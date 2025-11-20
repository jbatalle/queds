<template>
  <div class="col-sm-12 mt-2">
    <el-table v-loading="loading" name="tax_items" :data="orders"
              :default-sort="{property: 'id', order: 'descending'}"
              row-key="id" :cell-class-name="colorClass" default-expand-all
              :cell-style="{padding: '0', height: '20px'}">
      <el-table-column v-if="type==='broker'" label="Symbol">
        <template v-slot:default="scope">
          <el-tooltip :content="scope.row.name" placement="top">
            <span type="info">{{ scope.row.ticker.ticker }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column v-else label="Symbol" property="symbol" sortable></el-table-column>
      <el-table-column prop="account" label="Account">
      </el-table-column>
      <el-table-column v-if="type==='broker'" label="ISIN" property="ticker.isin"></el-table-column>
      <el-table-column label="Date" property="value_date" sortable></el-table-column>
      <el-table-column v-if="type==='broker'" label="Shares" property="shares" width="100px"></el-table-column>
      <el-table-column v-else label="Amount" property="amount">
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.amount, scope.row.source_currency, 8) }}
        </template>
      </el-table-column>
      <el-table-column label="Price">
        <template v-slot:default="scope">
            <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.price, base_currency) }}
            </span>
            <span v-else>
                {{ $filters.toCurrency(scope.row.price, base_currency, 8) }}
            </span>
        </template>
      </el-table-column>
      <el-table-column label="Fees" property="fees">
        <template v-slot:default="scope">
            <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.fees, base_currency) }}
            </span>
            <span v-else>
                {{ $filters.toCurrency(scope.row.fee, scope.row.target_currency, 8) }}
            </span>
        </template>
      </el-table-column>
      <el-table-column v-if="type==='broker'" label="Currency Rate" property="rate">
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.currency_rate, base_currency) }}
        </template>
      </el-table-column>
      <el-table-column label="Cost" property="cost">
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.cost, base_currency) }}
        </template>
      </el-table-column>
      <el-table-column label="Benefits" property="benefits" sortable>
        <template v-slot:default="scope">
          {{ $filters.toCurrency(scope.row.benefits, base_currency) }}
        </template>
      </el-table-column>
    </el-table>
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
      else
        return 'table-warning';
    },
    iconClassName(item) {
      if (item.type === 'Sell')
        return "nc-minimal-left blue";
      else
        return 'nc-minimal-right red';
    }, colorClass(item) {
      if (item.column.property == 'benefits' || item.column.property == 'shares') {
        if (parseInt(item.row[item.column.property]) > 0)
          return "green";
        else
          return "red"
      } else
        return "black"
    },
  },
}
</script>

<style scoped>
.example-showcase .el-loading-mask {
  z-index: 9;
}

.red {
  color: red
}

.green {
  color: green
}
</style>
