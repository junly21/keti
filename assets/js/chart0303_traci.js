// chart0303_traci.js

// 차트가 그려질 DOM 요소를 가져오고 차트 인스턴스 초기화
const chartDom = document.getElementById('content-03-03-01');
let chart = echarts.init(chartDom);

let option = {
    tooltip: {
        trigger: 'axis',
        formatter: function(params) {
            let result = '';
            params.forEach(function(param) {
                result += param.seriesName + ': ' + param.value[1] + '<br/>';
            });
            return result;
        },
        axisPointer: {
            animation: false
        }
    },
    legend: {
        data: ['MPR 30', 'MPR 60'],
        left: 'left',
        textStyle: { color: 'rgba(255,255,255,0.5)', fontSize: 12 }
    },
    xAxis: {
        type: 'time',
        axisLabel: {
            fontSize: 12,
            color: 'rgba(255,255,255,0.5)'
        },
        splitLine: {
            show: false
        }
    },
    yAxis: {
        type: 'value',
        axisLabel: {
            fontSize: 12,
            color: 'rgba(255,255,255,0.5)'
        },
        splitLine: {
            lineStyle: {
                color: 'rgba(255,255,255,0.06)'
            }
        }
    },
    series: [
        {
            name: 'MPR 30',
            type: 'line',
            smooth: true,
            showSymbol: false,
            data: [] // 초기 데이터는 빈 배열
        },
        {
            name: 'MPR 60',
            type: 'line',
            smooth: true,
            showSymbol: false,
            data: [] // 초기 데이터는 빈 배열
        }
    ]
};

chart.setOption(option);

// traci 시뮬레이션에서 전달받은 데이터로 차트를 업데이트하는 함수
// newData: [{ time: <timestamp>, mpr30: <value>, mpr60: <value> }, ... ]
function updateChart_traci(newData) {
    let seriesData30 = [];
    let seriesData60 = [];
    
    newData.forEach(item => {
        seriesData30.push([item.time, item.mpr30]);
        seriesData60.push([item.time, item.mpr60]);
    });
    
    chart.setOption({
        series: [
            { name: 'MPR 30', data: seriesData30 },
            { name: 'MPR 60', data: seriesData60 }
        ]
    });
    
    console.log("chart0303_traci updated with new data", newData);
}

// 전역으로 노출하여 다른 스크립트나 Python 호출에서 사용할 수 있도록 함
window.updateChart_traci = updateChart_traci;
