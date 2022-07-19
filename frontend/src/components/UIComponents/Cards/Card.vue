<template>
  <div class="card"
       :class="[
         {'card-plain': plain},
         {'card-raised': raised},
         {[`card-${type}`]: type}
       ]"
       :data-background-color="color">
    <h6 class="card-category" v-if="$slots.category || category">{{category}}</h6>
    <div class="card-image" v-if="$slots.image">
      <slot name="image"></slot>
    </div>

    <div class="card-avatar" v-if="$slots.avatar">
      <slot name="avatar"></slot>
    </div>

    <div class="info" v-if="$slots.info">
      <slot name="info"></slot>
    </div>

    <div class="card-header" :class="headerClasses" v-if="$slots.header || title">
      <slot name="header">
        <h1 v-if="title" class="card-title">{{title}}</h1>
        <h3 v-if="subTitle" class="card-category">{{subTitle}}</h3>
        <p v-if="description" class="card-description">{{description}}</p>
      </slot>
    </div>
    <div v-if="$slots.default" class="card-body" :class="cardBodyClasses">
      <slot></slot>
    </div>

    <slot name="raw-content"></slot>

    <hr v-if="$slots.footer && footerLine">
    <div class="card-footer text-center" v-if="$slots.footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>
<script>
  export default {
    name: 'card',
    props: {
      type: {
        type: String,
        description: 'Card type (user|stats|tasks|testimonials|signup|profile|pricing|map|plain|lock|info-area|contribution)'
      },
      title: {
        type: String,
        description: 'Card title'
      },
      subTitle: {
        type: String,
        description: 'Card subtitle'
      },
      category: {
        type: String,
        description: 'Card category title (displayed above normal title)'
      },
      color: {
        type: String,
        description: 'Card color (orange|yellow|red|green|blue|"")'
      },
      description: {
        type: String,
        description: 'Card description'
      },
      footerLine: {
        type: Boolean,
        description: 'Whether footer line should be displayed'
      },
      plain: {
        type: Boolean,
        description: 'Whether card is plain'
      },
      raised: {
        type: Boolean,
        description: 'Whether card is raised'
      },
      cardBodyClasses: {
        type: [String, Object, Array],
        description: 'Card body css classes'
      },
      headerClasses: {
        type: [String, Object, Array],
        description: 'Card header css classes'
      }
    }
  }
</script>
<style>
</style>
