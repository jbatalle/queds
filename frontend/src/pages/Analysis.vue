<template>
  <div>
    <div class="row">
      <el-tabs v-model="editableTabsValue" type="card" editable @edit="handleTabsEdit">
        <el-tab-pane
            v-for="item in editableTabs"
            :key="item.name"
            :name="item.name"
        >
          <template #label>
            <input
                v-if="item.editing"
                class="input-new-tag"
                type="text"
                v-model="item.title"
                @blur="item.editing = false"
                @keyup.enter="item.editing = false"
            />
            <span v-else @dblclick="item.editing = true">{{ item.title }}</span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>
    <div class="row">
      <el-tabs v-model="editableTabsValue" type="card" editable @edit="handleTabsEdit">
        <el-tab-pane
            v-for="(item, index) in editableTabs"
            :key="item.name"
            :name="item.name"
        >
          <template #label>
            <div v-if="!item.editing" @dblclick="startEdit(item)">
              {{ item.title }}
            </div>
            <el-input v-else v-model="item.title" @blur="finishEdit(item)"/>
          </template>
          {{ item.content }}
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
<script>
import axios from "axios";
//import {Table, TableColumn, Input, Button, Dialog, Tabs, TabPane, Autocomplete} from 'element-uplus'

export default {
  name: "Analysis",
  components: {
    //Tabs, TabPane
  },
  data() {
    return {
      dialogVisible: false,
      input: '',
      search: '',
      options: {},
      comments: [],
      componentKey: 0,
      state1: '',
      deleteDialogVisible: false,
      delete_watchlist: undefined,
      tableData: [
        {value: "Row 1", tags: ["tag1", "tag2"]},
        {value: "Row 2", tags: ["tag2", "tag3"]},
        // Add more rows as needed
      ],
      filteredData: [],
      inputVisible: false,
      inputValue: '',
      activeTab: 'tab1',
      tabs: [
        {name: 'Tab 1', editing: false},
        {name: 'Tab 2', editing: false},
        {name: 'Tab 3', editing: false}
      ], editableTabsValue: '2',
      editableTabs: [
        {
          title: 'Tab 1',
          name: 'tab1',
          content: 'Tab 1 content',
          editing: false
        },
        {
          title: 'Tab 2',
          name: 'tab2',
          content: 'Tab 2 content',
          editing: false
        }
      ],
      tabIndex: 2
    };
  },
  created() {
    //this.getData();
    this.restaurants = {};
    this.restaurants.value = [{value: 'vue', link: 'https://github.com/vuejs/vue'}]
  },
  methods: {
    handleClick(tab) {
      let editableTab = this.editableTabs.find(t => t.name === tab.name);
      if (editableTab) {
        editableTab.editing = true;
      }
    },
    startEdit(item) {
      item.editing = true;
    },
    finishEdit(item) {
      item.editing = false;
      // This method will be called when the user finishes editing a tab name
      // You can add your own logic here to update the tab name on the server, etc.
    },
    handleTabsEdit(targetName, action) {
      if (action === 'add') {
        this.tabIndex += 1
        const newTabName = `newTab${this.tabIndex}`
        this.editableTabs.push({
          title: 'New Tab',
          name: newTabName,
          editing: true,
          content: 'New Tab content ' + newTabName,
        })
        
        this.editableTabsValue = newTabName;
      } else if (action === 'remove') {
        const tabs = this.editableTabs;
        let activeName = this.editableTabsValue;
        if (activeName === targetName) {
          tabs.forEach((tab, index) => {
            if (tab.name === targetName) {
              const nextTab = tabs[index + 1] || tabs[index - 1]
              if (nextTab) {
                activeName = nextTab.name
              }
            }
          })
        }
        this.editableTabsValue = activeName
        this.editableTabs = tabs.filter((tab) => tab.name !== targetName)
      }
    }, filterTable() {
      if (this.filterTag === "") {
        this.filteredData = this.tableData;
        return;
      }
      const filteredData = this.tableData.filter(row => {
        return row.tags.includes(this.filterTag);
      });
      
      this.$refs.tagTable.setCurrentRow(null);
      this.$refs.tagTable.clearSort();
      this.filteredData = filteredData;
    },
    handleSelect(item) {
      console.log("Handle Selected:", item);
    }, 
    createFilter(queryString) {
      console.log("Create filter");
      return this.restaurants.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
    },
    querySearch(queryString, cb) {
      let filteredData = this.tableData.filter(row => {
        return row.tags.includes(queryString);
      });
      // call callback function to return suggestions
      console.log(filteredData);
      cb(filteredData);
    }, handleTagConfirm() {
      console.log("Tag confirm");
      console.log(this.inputValue);
      if (this.inputValue) {
        this.selectedTags.push(this.inputValue);
        this.inputValue = '';
      }
    }
  }
};
</script>
<style>
.demo-tabs {
  border-radius: inherit;
}

.demo-tabs > .el-tabs__header .el-tabs__item.is-active {
  background-color: #212120;
  color: #3cab79 !important;
}

.demo-tabs > .el-tabs__item.is-closable:hover {
  color: #3cab79 !important;
}

.demo-tabs .custom-tabs-label .el-icon {
}

.tags-input-container {
  display: inline-block;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 4px;
  background-color: #fff;
}

.tags {
  display: flex;
  flex-wrap: wrap;
}

.tag {
  background-color: #f2f2f2;
  color: #333;
  border-radius: 4px;
  padding: 2px 8px;
  display: flex;
  align-items: center;
  margin: 2px;
}

.remove-icon {
  cursor: pointer;
  margin-left: 4px;
}

.input-new-tag {
  border: none;
  outline: none;
  padding: 4px;
}
</style>
