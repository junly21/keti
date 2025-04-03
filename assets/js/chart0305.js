//전체 네트워크 이동성 지표 차트

const chart0305Dom = document.getElementById('content-03-05-01');
let chart0305 = echarts.init(chart0305Dom);

let option0305 = {
    tooltip: {
        trigger: 'axis',
        formatter: function (params) {
            let text = "";

            for (let i = 0; i < params.length; i++) {
                const date = new Date();

                text +=
                params[i].name +
                    ' : ' +
                    params[i].value[1] + '\n';

                if (i + 1 == params.length) {

                    return text;
                }
            }
        },
        axisPointer: {
            animation: false
        }
    },
    xAxis: {
        type: 'time',
        axisLabel: {
            color: 'rgba(255,255,255, .5)',
            fontSize: chartAxisLabelFontSize,
            formatter: `{s}`,
        },
        splitLine: {
            // lineStyle: {
            //     color: 'rgba(255,255,255, .06)',
            // },
            show: false
        },
    },
    yAxis: {
        type: 'value',
        axisPointer: {
            snap: true
        },
        // boundaryGap: [0, '100%'],
        splitLine: {
            lineStyle: {
                color: 'rgba(255,255,255, .06)',
            }
        },
        axisLabel: {
            fontSize: chartAxisLabelFontSize,
            color: 'rgba(255,255,255, .5)',
        },
    },
    visualMap: {
        show: false,
        dimension: 0,
    },
    series: [
        {
            name: 'MPR 30',
            type: 'line',
            showSymbol: false,
        },
        {
            name: 'MPR 60',
            type: 'line',
            showSymbol: false,
        }
    ]
};

option0305 && chart0305.setOption(option0305);
