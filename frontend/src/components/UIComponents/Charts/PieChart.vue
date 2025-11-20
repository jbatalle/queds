<template>
  <div>
    <Pie :data="chartData" :options="extraOptions" />
  </div>
</template>

<script>
import { Pie } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { reactive } from 'vue';

ChartJS.register(Title, Tooltip, Legend, ArcElement);

export default {
  props: {
    labels: Array,
    datasets: [Object, Array],
    extraOptions: {
      type: Object,
      default: () => ({}),
    },
  },
  components: {
    Pie,
  },
  setup(props) {
    const chartData = reactive({
      labels: props.labels || [],
      datasets: props.datasets || [],
    });

    return {
      chartData,
      extraOptions: props.extraOptions,
    };
  },
};
</script>
