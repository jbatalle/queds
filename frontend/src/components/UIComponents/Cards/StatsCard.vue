<template>
  <div class="card card-stats">
    <div class="card-body">
      <div class="row">
        <div class="col-5 col-md-4">
          <slot name="header">
            <div class="icon-big text-center"
                 :class="`text-${type}`">
              <i :class="icon"></i>
            </div>
          </slot>
        </div>
        <div class="col-7 col-md-8">
          <slot name="content">
            <div class="numbers">
              <p class="card-category">{{smallTitle}}</p>
              <p class="card-title">{{title}}</p>
            </div>
          </slot>
        </div>
      </div>
    </div>
    <div class="card-footer">
      <hr/>
      <slot name="footer"></slot>
    </div>

  </div>
</template>
<script>
  export default {
    name: 'stats-card',
    props:{
      type: {
        type: String,
        description: 'Card text type (primary|info|danger|default|warning|success)'
      },
      title: {
        type: String,
        description: 'Card title'
      },
      smallTitle: {
        type: String,
        description: 'Card small title'
      },
      icon: {
        type: String,
        description: 'Card icon'
      }
    }
  }

</script>
<style scoped>
  .card-content{
    min-height: 85px
  }
</style>
