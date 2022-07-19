import { Pie } from 'vue-chartjs'

const defaultOptions = {
  legend: {

    display: false
  },

  tooltips: {
    enabled: false
  },
  scales: {
    yAxes: [{

      ticks: {
        display: false
      },
      gridLines: {
        drawBorder: false,
        zeroLineColor: "transparent",
        color: 'rgba(255,255,255,0.05)'
      }

    }],
    xAxes: [{
      barPercentage: 1.6,
      gridLines: {
        drawBorder: false,
        color: 'rgba(255,255,255,0.1)',
        zeroLineColor: "transparent"
      },
      ticks: {
        display: false,
      }
    }]
  },

};

export default {
  name: 'pie-chart',
  extends: Pie,
  props: {
    labels: {
      type: [Object, Array],
      description: 'Chart labels. This is overridden when `data` is provided'
    },
    datasets: {
      type: [Object, Array],
      description: 'Chart datasets. This is overridden when `data` is provided'
    },
    data: {
      type: [Object, Array],
      description: 'Chart.js chart data (overrides all default data)'
    },
    color: {
      type: String,
      description: 'Chart color. This is overridden when `data` is provided'
    },
    extraOptions: {
      type: Object,
      description: 'Chart.js options'
    },
    title: {
      type: String,
      description: 'Chart title'
    },
  },
  methods: {
    assignChartData() {
      return {
        labels: this.labels || [],
        datasets: this.datasets ? this.datasets : [{
          pointRadius: 0,
          pointHoverRadius: 0,
          backgroundColor: [
            '#e3e3e3',
            '#4acccd',
            '#fcc468'
          ],
          borderWidth: 0,
          data: this.data || []
        }]
      }
    },
    assignChartOptions(initialConfig) {
      let extraOptions = this.extraOptions || {};
      return {
        ...initialConfig,
        ...extraOptions
      };
    }
  },
  mounted() {
    this.chartData = this.assignChartData({});
    this.options = this.assignChartOptions(defaultOptions);
    this.renderChart(this.chartData, this.options);
  }
}
