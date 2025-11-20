<template>
  <div>
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script>
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  CategoryScale
} from 'chart.js'
import { reactive, onMounted } from 'vue'
import { hexToRGB } from './utils'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  CategoryScale
)

export default {
  props: {
    labels: Array,
    datasets: [Object, Array],
    data: [Object, Array],
    color: String,
    title: String,
    extraOptions: {
      type: Object,
      default: () => ({})
    }
  },
  components: { Line },

  setup(props) {
    const defaultColor = props.color || '#FFFFFF'

    // Initial chart data
    const chartData = reactive({
      labels: props.labels || [],
      datasets: props.datasets || [
        {
          label: props.title || '',
          borderColor: defaultColor,
          pointRadius: 0,
          pointHoverRadius: 0,
          fill: false,
          borderWidth: 3,
          data: props.data || []
        }
      ]
    })

    // Default options (converted to Chart.js v3 format)
    let chartOptions = reactive({
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      },
      scales: {
        y: {
          ticks: {
            color: "#9f9f9f",
            maxTicksLimit: 5
          },
          grid: {
            borderColor: 'transparent',
            color: 'rgba(255,255,255,0.05)'
          }
        },
        x: {
          ticks: {
            padding: 20,
            color: "#9f9f9f"
          },
          grid: {
            display: false,
            color: 'rgba(255,255,255,0.1)'
          }
        }
      },
      ...props.extraOptions
    })

    // 🔥 Gradient setup (run after DOM exists)
    onMounted(() => {
      const canvas = document.querySelector("canvas").getContext("2d")
      const gradientStroke = canvas.createLinearGradient(500, 0, 100, 0)
      gradientStroke.addColorStop(0, defaultColor)
      gradientStroke.addColorStop(1, "#FFFFFF")

      const gradientFill = canvas.createLinearGradient(0, 170, 0, 50)
      gradientFill.addColorStop(0, "rgba(128, 182, 244, 0)")
      gradientFill.addColorStop(1, hexToRGB(defaultColor, 0.4))

      chartData.datasets[0].borderColor = gradientStroke
      chartData.datasets[0].backgroundColor = gradientFill
      chartData.datasets[0].fill = true
    })

    return { chartData, chartOptions }
  }
}
</script>
