<template>
  <div>
    <div class="row">
      <el-tabs v-model="editableTabsValue" type="card" editable @edit="handleTabsEdit">
        <el-tab-pane
            v-for="(item, index) in editableTabs"
            :key="index"
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
    <div class="row">
      <div class="col-md-12">
        <div class="tag-filter">
          <!-- Input field to filter by tags -->
          <el-input v-model="filterTag" placeholder="Enter a tag"></el-input>
          <el-button @click="filterTable">Filter</el-button>
          <el-table :data="filteredData" ref="tagTable" style="width: 100%">
            <!-- Define your table columns here -->
            <el-table-column prop="name" label="Name"></el-table-column>
            <el-table-column prop="tags" label="Tags"></el-table-column>
          </el-table>
        </div>
      </div>
      <div>
        <el-autocomplete
            v-model="state1"
            :fetch-suggestions="querySearch"
            clearable
            class="inline-input w-50"
            placeholder="Please Input"
            @select="handleSelect"
        />
      </div>
    </div>
    <div class="row">
      Tags:
      <div class="col-md-12">
        <el-tag
            :key="tag"
            v-for="tag in dynamicTags"
            closable
            :disable-transitions="false"
            @close="handleClose(tag)">
          {{ tag }}
        </el-tag>
      </div>
      <div class="row">
        Input:
        <el-input
            class="input-new-tag"
            v-if="inputVisible"
            v-model="inputValue"
            ref="saveTagInput"
            size="mini"
            @keyup.enter.native="handleInputConfirm"
            @blur="handleInputConfirm"
        >
        </el-input>
        <el-button v-else class="button-new-tag" size="small" @click="showInput">+ New Tag</el-button>
      </div>
    </div>
    <br/><br/>
    <div class="row">
      Tags:
      <div class="col-md-12">
        <!-- Display the existing tags as el-tag components -->
        <el-tag
            :key="tag"
            v-for="tag in dynamicTags"
            closable
            :disable-transitions="false"
            @close="handleClose(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>
      <div class="row">
        Input:
        <!-- Show the el-autocomplete input field for new tags -->
        <el-autocomplete
            v-model="state1"
            :fetch-suggestions="querySearch"
            class="inline-input w-50"
            placeholder="Please Input"
            @select="handleSelect"
        />
        <!--el-button v-else class="button-new-tag" size="small" @click="showInput">+ New Tag</1--el-button-->
      </div>
    </div>
    <br/><br/><br/> FInal stuff
    <div class="row">
      <div class="tags-input-container">
        <div class="tags">
      <span
          class="tag"
          v-for="(tag, index) in selectedTags"
          :key="index"
      >
        {{ tag }}
        <span class="remove-icon" @click="removeTag(index)">&times;</span>
      </span>
        </div>
        <el-autocomplete
            v-model="inputValue"
            :fetch-suggestions="querySearch"
            class="inline-input w-50"
            placeholder="Please Input"
            v-bind:select-when-unmatched=true
            @select="handleSelect"
            @keydown.enter="handleTagConfirm"
            @blur="handleTagConfirm"
            @keydown.delete="deleteTag"
        />
        <input
            ref="saveTagInput"
            class="input-new-tag"
            v-model="inputValue"
            @keydown.enter="handleTagConfirm"
            @blur="handleTagConfirm"
            @keydown.tab.prevent
            @keydown.delete="deleteTag"
        />
      </div>
    </div>
  </div>
</template>
<script>
import axios from "axios";
import {Table, TableColumn, Input, Button, Dialog, Tabs, TabPane, Tag, Autocomplete} from 'element-ui'
import Vue from 'vue';

Vue.use(Table);
Vue.use(TableColumn);
Vue.use(Input);
Vue.use(Button);
Vue.use(Dialog);
Vue.use(Tabs);
Vue.use(TabPane);
Vue.use(Tag);
Vue.use(Autocomplete);

export default {
  name: "Analysis",
  components: {
    Tabs, TabPane
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
      filterTag: "",
      dynamicTags: ['Tag 1', 'Tag 2', 'Tag 3'],
      inputVisible: false,
      inputValue: '',
      selectedTags: [],
      activeTab: 'tab1',
      tabs: [
        {name: 'Tab 1', editing: false},
        {name: 'Tab 2', editing: false},
        {name: 'Tab 3', editing: false}
      ], editableTabsValue: '2',
      editableTabs: [
        {
          title: 'Tab 1',
          name: '1',
          content: 'Tab 1 content',
          editing: false
        },
        {
          title: 'Tab 2',
          name: '2',
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
      console.log("Handle click")
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
      console.log(action);
      if (action === 'add') {
        console.log("Add tab");
        const newTabName = ++this.tabIndex;
        console.log(newTabName);
        this.editableTabs.push({
          title: 'New Tab',
          name: newTabName,
          editing: true,
          content: 'New Tab content',
        })
        console.log(this.editableTabs);
        this.editableTabsValue = newTabName
        console.log(this.editableTabsValue);
      } else if (action === 'remove') {
        const tabs = this.editableTabs
        let activeName = this.editableTabsValue
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
    },
    handleClose(tag) {
      this.dynamicTags.splice(this.dynamicTags.indexOf(tag), 1);
    },
    showInput() {
      this.inputVisible = true;
      this.$nextTick(_ => {
        this.$refs.saveTagInput.$refs.input.focus();
      });
    },
    handleInputConfirm() {
      let inputValue = this.inputValue;
      if (inputValue) {
        this.dynamicTags.push(inputValue);
      }
      this.inputVisible = false;
      this.inputValue = '';
    }, filterTable() {
      console.log(this.filterTag);
      console.log(this.filterTag === "");
      console.log(this.filterTag == "");
      console.log(this.filterTag == undefined);
      if (this.filterTag === "") {
        this.filteredData = this.tableData;
        return;
      }
      console.log("FIlter table");
      console.log(this.filterTag)
      const filteredData = this.tableData.filter(row => {
        return row.tags.includes(this.filterTag);
      });
      console.log(this.tableData);
      console.log(filteredData);
      this.$refs.tagTable.setCurrentRow(null);
      this.$refs.tagTable.clearSort();
      this.filteredData = filteredData;
    },
    handleSelect(item) {
      console.log("handle selectg " + item);
      console.log("Craete here new tag")
    }, createFilter(queryString) {
      console.log()
      return this.restaurants.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
    },
    querySearch(queryString, cb) {
      console.log(queryString);
//const results = queryString;
      console.log(this.tableData);
      let filteredData = this.tableData.filter(row => {
        console.log(row.tags);
        console.log(row.tags.includes(queryString));
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
    },
    removeTag(index) {
      this.selectedTags.splice(index, 1);
    },
    deleteTag(event) {
      if (this.inputValue === "" && this.selectedTags.length > 0) {
        this.selectedTags.splice(this.selectedTags.length - 1, 1);
        this.$refs.saveTagInput.focus();
      }
    },
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
