<template>
  <div>
    <canvas ref="chart"></canvas>
  </div>
</template>

<script>
//import { Chart, ArcElement, CategoryScale, Title, Tooltip, Legend } from 'chart.js';
import {ref, onMounted, watch} from 'vue';
import {Pie} from 'vue-chartjs'
import {Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

export default {
  props: {
    data: {
      type: Object
    },
    labels: {
      type: Array
    },
    datasets: {
      type: [Object, Array],
    },
    chartOptions: {
      type: Object,
      default: () => ({}),
    },
    extraOptions: {
      type: Object,
      description: 'Chart.js options'
    },
  },
  setup(props) {
    const chart = ref(null);
    let chartInstance = null;

    onMounted(() => {

      if (props.datasets == undefined) {
        return
      }
      let data = {
        labels: props.labels || [],
        datasets: props.datasets,
        title: props.title
      }
      chartInstance = new ChartJS(chart.value.getContext('2d'), {
        type: 'pie',
        data: data,
        options: props.extraOptions
      });
    });
// watch('data', (newData) => {
//   console.log("WAtch1", newData)
//   this.datasets = newData.datasets.slice(); // Create a copy using slice()
//   // Or: this.datasets = newData.datasets.concat(); // Create a copy using concat()
// });
    // watch(props.data, () => {
    //   console.log("WAtch", props)
    //   if (chartInstance) {
    //     chartInstance.data = props.data;
    //     chartInstance.update();
    //   }
    // });

    return {chart};
  }
};
</script>