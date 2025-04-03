const networkWidth = 4375.88;
const networkHeight = 2336.97;
const networkRate = networkHeight / networkWidth;

const width = window.innerWidth;
const height = width * networkRate;

const scaleX = width / networkWidth;
const scaleY = height / networkHeight;

const offsetX = 0;
const offsetY = 0;

let generateSec = 2;

let laneIds = [];

let chartAxisLabelFontSize = 12;
let chartLegendFontSize = 11;

let videoUpdate = null;

let chkLoadingMPR30 = false;
let chkLoadingMPR60 = false;
let chkLoadingJunction = false;
let chkCharts = false;

let initFunction = [];

let fullData = [];
let receivedChunks = [];

function receiveDataChunk(chunk, chunkIndex, totalChunks, id) {
    console.log(`Received chunk ${chunkIndex} of ${totalChunks}`);
    
    // 청크가 비어있는지 확인
    if (!Array.isArray(chunk) || chunk.length === 0) {
        console.warn(`Warning: Received an invalid or empty chunk at index ${chunkIndex}`);
        return;  // 유효하지 않은 청크는 추가하지 않음
    }

    // 청크 결합 - fullData가 평평한 배열 형태로 유지되도록 확인
    fullData[id] = fullData[id].concat(chunk); 
    // console.log(`Chunk ${chunkIndex} added to fullData. Current length: ${fullData.length}`);
    receivedChunks[id]++;

    if (receivedChunks[id] === totalChunks) {
        console.log("All chunks received, processing data...");
        
        // fullData가 비어 있지 않은지 확인 후 mprHeatmap 호출
        if (fullData.length > 0) {
            // console.log("Final combined data:", JSON.stringify(fullData, null, 2)); // fullData의 상태 확인
            mprHeatmap(fullData[id], id); // 모든 데이터가 수신된 후 heatmap 함수 호출
        } else {
            console.error("Error: fullData is empty after receiving all chunks.");
        }

        // 데이터 초기화
        fullData = [];
        receivedChunks = [];
    }
}

/**
 * 
 * @param {object} target // 네트워크가 그려질 canvas의 context
 * @param {string} network // 네트워크 파일 경로
 */

function drawNetwork(id, data) {

    console.log(id);

    console.log(`start to darw`);
    // id로 지정된 div에 canvas를 동적으로 생성하여 추가
    const container = document.getElementById(id);
    
    // canvas 추가 (기존 canvas가 있으면 제거)
    container.innerHTML = '';  // 기존 내용을 지우고 새로 그리기 위해 초기화
    const canvas = document.createElement('canvas');
    canvas.setAttribute('width', width);
    canvas.setAttribute('height', height);
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, canvas.width, canvas.height);  // 캔버스를 초기화

    const nodes = data.nodes;
    const edges = data.edges;

    // 엣지 그리기
    edges.forEach(edge => {
        ctx.beginPath();
        ctx.moveTo((edge.source.x + offsetX) * scaleX, edge.source.y * scaleY);
        ctx.lineTo((edge.target.x + offsetX) * scaleX, edge.target.y * scaleY);
        ctx.strokeStyle = 'gray';
        ctx.lineWidth = 1;
        ctx.stroke();
    });

    // 노드 그리기
    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc((node.x + offsetX) * scaleX, node.y * scaleY, 2, 0, 2 * Math.PI, false);  // 노드 크기 2
        ctx.fillStyle = 'gray';
        ctx.fill();
    });
}

function drawHeatmap(target, scale) {
    var t = [];

    for (var j = generateSec; j < generateSec + 10; j++) {
        var rawList = arrData[j];
        // console.log(rawList);

        for (var i = 0; i < rawList.length; i++) {
            var jo = JSON.parse(JSON.stringify(rawList[i]));
            var x = parseInt(jo.X) * scale;
            var y = parseInt(jo.Y) * scale;
            var tm = parseInt(jo.Time);
            t.push({ x: x, y: y, value: 1, radius: 5 });
        }
    }

    target.setData({
        min: 0, max: 3, data: t
    });

    generateSec++;
}

function roundToThirdDecimal(num) {
    return Math.round(num * 1000) / 1000;
}

function roundToTwiceDecimal(num) {
    return Math.round(num * 100) / 100;
}

function getAllLaneIds() {
    let allElements = document.querySelectorAll('[id^="lane-"]');
    allElements.forEach(element => {
        laneIds.push(element.id);
    });

    laneIds.forEach(id => {
        document.getElementById(id).value = null;
    })

    resetClasses();
}

function assignClass(value) {
    if (value <= 5) {
        return 'green';
    } else if (value <= 10) {
        return 'yellow';
    } else {
        return 'red';
    }
}

function applyClassToInputs() {
    const inputs = document.querySelectorAll('input');

    inputs.forEach(input => {
        const value = parseInt(input.value, 10); // 값이 숫자일 경우만 고려
        if (!isNaN(value)) {
            const className = assignClass(value);
            input.classList.add(className);
        }
    });
}

function resetClasses() {
    const inputs = document.querySelectorAll('input');

    inputs.forEach(input => {
        input.classList.remove('green', 'yellow', 'red');
    });
}

function changeSpanText(newText) {
    const spanElements = document.querySelectorAll("h4 > span");
    spanElements.forEach(spanElement => {
        spanElement.textContent = newText;
    });
}

function changeSmallText(newText) {
    const smallElements = document.querySelectorAll("h4 > small");
    smallElements.forEach(smallElement => {
        smallElement.textContent = newText;
    });
}

function setButtonState(clickedButton) {

    let siblings = getSiblings(clickedButton.parentElement);
    siblings.forEach(sibling => {
        if (sibling.querySelector('button')) {
            sibling.querySelector('button').setAttribute('aria-pressed', 'false');
        }
    });

    clickedButton.setAttribute('aria-pressed', 'true');
}

function getSiblings(element) {
    let siblings = [];
    let sibling = element.parentNode.firstChild;

    while (sibling) {
        if (sibling.nodeType === 1 && sibling !== element) {
            siblings.push(sibling);
        }
        sibling = sibling.nextSibling;
    }

    return siblings;
}

function removeLoading() {
    document.body.removeAttribute('data-loading');
}

function setLoading(page) {
    let chkLoadingInterval = "";
    document.body.setAttribute('data-loading', 'Loading');

    chkLoadingInterval = setInterval(function () {
        // if (page == "mobility" && chkLoadingMPR30 && chkLoadingMPR60) {
        if (page == "mobility" && chkLoadingMPR30) {
        // if (page == "mobility") {
            initFunction.forEach(func => {
                func();
            });
            removeLoading();
            clearInterval(chkLoadingInterval);
        } else if (page == "tracking") {
            initFunction.forEach(func => {
                func();
            });
            removeLoading();
            clearInterval(chkLoadingInterval);
        } else if (page == "safety" && chkLoadingJunction) {
            initFunction.forEach(func => {
                func();
            });
            removeLoading();
            clearInterval(chkLoadingInterval);            

        } else if (page == "all" && chkLoadingMPR30 && chkLoadingMPR60 & chkLoadingJunction) {
            initFunction.forEach(func => {
                func();
            });
            removeLoading();
            clearInterval(chkLoadingInterval);

        }
    }, 1000)
}

function setVideo () {
    const videos = document.querySelectorAll('video');
    videos.forEach(function(video) {
        video.muted = true;
        video.play();
        video.addEventListener("ended", function () {

            console.log("end");

            videoUpdate();
            
            videos.forEach(function(all) {

                console.log("all");
                
                all.currentTime = 0;
                all.play();
                all.removeEventListener("ended", function () {
                    console.log(`${all} is removed`);
                });
            });
        });
    });
}

function setRefresh() {
    const refreshInterval = 1000 * 60 * 3;

    setInterval(function () {
        location.reload();
    }, refreshInterval);
}

// 선분에 대한 클릭 검출 함수
function checkPointInArea(point1, point2, clickX, clickY, tolerance = 5) {
    const x1 = point1[0];
    const y1 = point1[1];
    const x2 = point2[0];
    const y2 = point2[1];

    // 직선의 방정식 파라미터 A, B, C 계산 (Ax + By + C = 0)
    const A = y2 - y1;
    const B = x1 - x2;
    const C = x2 * y1 - x1 * y2;

    // 점과 직선 사이의 거리 계산
    const distance = Math.abs(A * clickX + B * clickY + C) / Math.sqrt(A * A + B * B);

    // 거리가 임계값 이내인지 및 클릭한 점이 선분의 경계 내에 있는지 확인
    if (distance <= tolerance) {
        const dotProduct = (clickX - x1) * (x2 - x1) + (clickY - y1) * (y2 - y1);
        const squaredLength = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
        if (dotProduct >= 0 && dotProduct <= squaredLength) {
            return true;
        }
    }
    return false;
}

// 클릭 이벤트 처리 함수
function handleCanvasClick(event, network) {
    let rect = event.target.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;

    // 클릭된 위치를 기반으로 해당 lane을 찾기
    d3.xml(network).then(data => {
        const edges = data.querySelectorAll("edge");
        edges.forEach(edge => {
            const lanes = edge.querySelectorAll("lane");
            lanes.forEach(lane => {
                const shape = lane.getAttribute("shape");
                const points = shape.split(" ").map(point => point.split(",").map(Number));

                // 각 선분을 검사하고 클릭 위치가 해당 선분에 있는지 확인
                for (let i = 1; i < points.length; i++) {
                    if (checkPointInArea(points[i - 1], points[i], x, y)) {
                        console.log(`Clicked Lane ID: ${lane.getAttribute("id")}`);  // 콘솔에 클릭된 lane의 ID 출력
                        return; // 해당 선분을 찾으면 더 이상의 검사를 중단
                    }
                }
            });
        });
    });
}

function mprHeatmap(data, id) {
    // JSON 데이터가 정상적으로 전달되었는지 로그 출력
    console.log("Received data for mprHeatmap:");

    const jdata = data;

    const container = document.getElementById(id);
    const containerWidthPer = container.offsetWidth / window.innerWidth;
    const scale = roundToThirdDecimal(window.innerWidth / networkWidth * containerWidthPer);
    const preloadCount = 1;        
    const arrData = [];

    let tmp = 1210;
    let rawArr = [];

    for(let i = 0; i < jdata.length; i++) { 
        let jo = jdata[i];
        let tm = parseInt(jo.Time);
        
        // 데이터를 클러스터링 (시간을 기준으로)
        if (tm == tmp) {
            rawArr.push(jo);
        } else {
            arrData.push(rawArr);
            rawArr = [];
            rawArr.push(jo);
        }

        // 실행
        if (i === jdata.length - 1) {
            initFunction.push(setHeatmap);

            if (id === "content-03-01-01") {
                chkLoadingMPR30 = true;
            } else if (id === "content-03-02-01") {
                chkLoadingMPR60 = true;
            }
        }

        tmp = tm;
    }

    function setHeatmap() {
        // 히트맵 생성
        let heatmap = h337.create({
            container: container,
            maxOpacity: .5,
            radius: 5,
            blur: .35,
        });

        setInterval(function () {
            let t = [];

            for (let j = generateSec; j < generateSec + preloadCount; j++) {
                let rawList = arrData[j];

                for (let i = 0; i < rawList.length; i++) {
                    let jo = rawList[i];
                    let x = parseInt(jo.X) * scale;
                    let y = parseInt(jo.Y) * scale;
                    t.push({ x: x, y: y, value: 1, radius: 5 });
                }
            }

            heatmap.setData({
                min: 0, max: 5, data: t
            });

            generateSec++;
        }, 1000);
    }
}

function setChart (data) {
    const csvData = Papa.parse(data, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
    });

    let now = new Date(2023, 10, 10);
    let oneMin = 1000;
    let jj = 0;
    let averageTravelTimeArr = [];
    let averageTravelTimeArr2 = [];

    let averageSpeedArr = [];
    let averageSpeedArr2 = [];

    let averageAccelerationArr = [];
    let averageAccelerationArr2 = [];

    let averageDepartDelayArr = [];
    let averageDepartDelayArr2 = [];


    for (jj; jj < 10; jj++) {

        setCsvData();

    }

    initFunction.push(drawChart);

    function drawChart () {

        setInterval(function () {

            setCsvData();

            jj++;

            chart0303.setOption({
                legend: {
                    show: true,
                    left: 'left',
                    textStyle: {
                        color: 'rgba(255,255,255, .5)',
                        fontSize: chartAxisLabelFontSize,
                    },
                },
                xAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                series: [
                    {
                        data: averageTravelTimeArr,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#D9D200',
                            width: 1,
                        },
                        // areaStyle: {

                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(217, 210, 0, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(217, 210, 0, 0)'
                        //         }
                        //     ]),
                        // },
                    },
                    {
                        data: averageTravelTimeArr2,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#0076c9',
                            width: 1,
                        },
                        // areaStyle: {
                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(0, 118, 201, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(0, 118, 201, 0)'
                        //         }
                        //     ])
                        // },
                    }
                ]
            });

            chart0304.setOption({
                legend: {
                    show: true,
                    left: 'left',
                    textStyle: {
                        color: 'rgba(255,255,255, .5)',
                        fontSize: chartLegendFontSize,
                    },
                },
                xAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                series: [
                    {
                        data: averageSpeedArr,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#D9D200',
                            width: 1,
                        },
                        // areaStyle: {

                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(217, 210, 0, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(217, 210, 0, 0)'
                        //         }
                        //     ]),
                        // },
                    },
                    {
                        data: averageSpeedArr2,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#0076c9',
                            width: 1,
                        },
                        // areaStyle: {
                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(0, 118, 201, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(0, 118, 201, 0)'
                        //         }
                        //     ])
                        // },
                    }
                ]
            });

            chart0305.setOption({
                legend: {
                    show: true,
                    left: 'left',
                    textStyle: {
                        color: 'rgba(255,255,255, .5)',
                        fontSize: chartLegendFontSize,
                    },
                },
                xAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                series: [
                    {
                        data: averageAccelerationArr,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#D9D200',
                            width: 1,
                        },
                        // areaStyle: {

                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(217, 210, 0, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(217, 210, 0, 0)'
                        //         }
                        //     ]),
                        // },
                    },
                    {
                        data: averageAccelerationArr2,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#0076c9',
                            width: 1,
                        },
                        // areaStyle: {
                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(0, 118, 201, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(0, 118, 201, 0)'
                        //         }
                        //     ])
                        // },
                    }
                ]
            });

            chart0306.setOption({
                legend: {
                    show: true,
                    left: 'left',
                    textStyle: {
                        color: 'rgba(255,255,255, .5)',
                        fontSize: chartLegendFontSize,
                    },
                },
                xAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: chartAxisLabelFontSize,
                    }
                },
                series: [
                    {
                        data: averageDepartDelayArr,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#D9D200',
                            width: 1,
                        },
                        // areaStyle: {

                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(217, 210, 0, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(217, 210, 0, 0)'
                        //         }
                        //     ]),
                        // },
                    },
                    {
                        data: averageDepartDelayArr2,
                        type: 'line',
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {
                            color: '#0076c9',
                            width: 1,
                        },
                        // areaStyle: {
                        //     color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        //         {
                        //             offset: 0,
                        //             color: 'rgba(0, 118, 201, .8)'
                        //         },
                        //         {
                        //             offset: 1,
                        //             color: 'rgba(0, 118, 201, 0)'
                        //         }
                        //     ])
                        // },
                    }
                ]
            });
        }, 1000);

    }

    function setCsvData() {

        now = new Date(+now + oneMin);

        // averageTravelTime

        averageTravelTime = {
            name: "MPR 30",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageTravelTime
            ]
        };

        averageTravelTime2 = {
            name: "MPR 60",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageTravelTime2
            ]
        };

        averageTravelTimeArr.push(averageTravelTime);
        averageTravelTimeArr2.push(averageTravelTime2);

        // averageSpeed

        averageSpeed = {
            name: "MPR 30",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageSpeed
            ]
        };

        averageSpeed2 = {
            name: "MPR 60",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageSpeed2
            ]
        };

        averageSpeedArr.push(averageSpeed);
        averageSpeedArr2.push(averageSpeed2);

        // averageAcceleration

        averageAcceleration = {
            name: "MPR 30",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageAcceleration
            ]
        };

        averageAcceleration2 = {
            name: "MPR 60",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageAcceleration2
            ]
        };

        averageAccelerationArr.push(averageAcceleration);
        averageAccelerationArr2.push(averageAcceleration2);

        // averageDepartDelay

        averageDepartDelay = {
            name: "MPR 30",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageDepartDelay
            ]
        };

        averageDepartDelay2 = {
            name: "MPR 60",
            value: [
                [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('-') + " " + [now.getHours(), now.getMinutes(), now.getSeconds()].join(':'),
                csvData.data[jj].AverageDepartDelay2
            ]
        };

        averageDepartDelayArr.push(averageDepartDelay);
        averageDepartDelayArr2.push(averageDepartDelay2);
    }
}