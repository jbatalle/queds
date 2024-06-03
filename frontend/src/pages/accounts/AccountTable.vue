<template>
  <div class="card">
    <div class="card-header">
      <div class="row">
        <div class="col-md-6">
          <h5 class="title">{{ title }}</h5>
        </div>
        <div class="col-md-6">
          <div class="text-right mb-3">
            <el-button type="primary" size="small" disabled>Read all</el-button>
            <el-button type="primary" size="small" @click="openCreateDialog(accountType)">Add account</el-button>
          </div>
        </div>
      </div>
    </div>
    <div class="col-sm-12 mt-2">
      <el-table :data="accounts" stripe :cell-style="{padding: '0', height: '20px'}">
        <el-table-column label="Name" property="name"></el-table-column>
        <el-table-column label="Type" property="entity_name"></el-table-column>
        <el-table-column label="Fiat" property="balance">
          <template v-slot:default="scope">
            {{ $filters.toCurrency(scope.row.balance, scope.row.currency) }}
          </template>
        </el-table-column>
        <el-table-column label="Value" property="virtual_balance">
          <template v-slot:default="scope">
            {{ $filters.toCurrency(scope.row.virtual_balance, scope.row.currency) }}
          </template>
        </el-table-column>
        <el-table-column label="Last update" property="updated_on"></el-table-column>
        <el-table-column label="actions">
          <template v-slot:default="scope">
            <el-tooltip content="Read" placement="top">
              <el-button type="primary" size="small" aria-label="read" class=""
                         @click="openReadDialog(scope.$index, scope.row)">
                <i class="nc-icon nc-button-play"></i>
              </el-button>
            </el-tooltip>
            <el-tooltip content="Upload" placement="top">
              <el-button type="success" size="small" aria-label="upload button" icon @click="" disabled>
                <i class="nc-icon nc-cloud-upload-94"></i>
              </el-button>
            </el-tooltip>
            <el-tooltip content="Edit" placement="top">
              <el-button type="warning" size="small" aria-label="read" icon
                         @click="openCreateDialog(accountType, scope.row)">
                <i class="nc-icon nc-settings-gear-65"></i>
              </el-button>
            </el-tooltip>
            <el-tooltip placement="top" content="Remove">
              <el-button type="danger" size="small" aria-label="button" icon @click="openDeleteDialog(scope.row)">
                <i class="nc-icon nc-simple-remove"></i>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    title: String,
    accounts: Array,
    tableColumns: Array,
    accountType: Number
  },
  methods: {
    openCreateDialog(accountType, account) {
      this.$emit('open-create-dialog', accountType, account);
    },
    openReadDialog(index, account) {
      this.$emit('open-read-dialog', index, account);
    },
    openDeleteDialog(account) {
      this.$emit('open-delete-dialog', account);
    }
  }
}
</script>

<style>
/* Your styling here */
</style>