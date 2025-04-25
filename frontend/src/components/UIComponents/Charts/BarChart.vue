<template>
  <div>
    <Bar :data="chartData" :options="extraOptions" />
  </div>
</template>

<script>
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import { reactive } from 'vue';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

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
    Bar,
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
