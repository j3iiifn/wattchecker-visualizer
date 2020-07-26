function createData(json) {
    var result = []
    for (var i = 0; i < json['index'].length; i++) {
        result.push({
            x: moment.utc(json['index'][i]),
            y: json['data'][i]
        })
    }
    return result
}

function drawChartLast24Hours(wattPerMinuteLast24Hours) {
    var ctx = document.getElementById('chartLast24Hours').getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Average W/min',
                data: wattPerMinuteLast24Hours,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            elements: {
                line: {
                    tension: 0
                },
                point:{
                    radius: 0
                }
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    distribution: 'linear',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                          hour: 'M/DD H:mm'
                        }
                    }
                }],
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'W'
                    },
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
    });
}

function drawChartLast3Days(wattHourLast3Days, sumBillsPer12HoursLast3Days) {
    var ctx = document.getElementById('chartLast3Days').getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Total bills/12h',
                    yAxisID: 'Yen',
                    data: sumBillsPer12HoursLast3Days,
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    borderWidth: 1,
                    steppedLine: 'before'
                },
                {
                    type: 'line',
                    label: 'Wh',
                    yAxisID: 'Wh',
                    data: wattHourLast3Days,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            elements: {
                line: {
                    tension: 0
                },
                point:{
                    radius: 0
                }
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    distribution: 'linear',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            hour: 'M/DD H:mm'
                        },
                        unitStepSize: 12
                    }
                }],
                yAxes: [
                    {
                        id: 'Wh',
                        scaleLabel: {
                            display: true,
                            labelString: 'Wh'
                        },
                        type: 'linear',
                        position: 'left',
                        ticks: {
                            beginAtZero: true
                        }
                    },
                    {
                        id: 'Yen',
                        scaleLabel: {
                            display: true,
                            labelString: 'Yen'
                        },
                        type: 'linear',
                        position: 'right',
                        ticks: {
                            beginAtZero: true
                        }
                    }
                ]
            }
        }
    });
}

fetch('/data')
    .then(function(response) {
        if(response.ok) {
            return response.json();
        }
        throw new Error('Network response was not ok.');
    })
    .then(function(responseJson) {
        wattPerMinuteLast24Hours = createData(responseJson['wattPerMinuteLast24Hours']);
        wattHourLast3Days = createData(responseJson['wattHourLast3Days'])
        sumBillsPer12HoursLast3Days = createData(responseJson['sumBillsPer12HoursLast3Days']);
        drawChartLast24Hours(wattPerMinuteLast24Hours);
        drawChartLast3Days(wattHourLast3Days, sumBillsPer12HoursLast3Days);
    }).catch(function(error) {
        console.log('There has been a problem with your fetch operation: ', error.message);
    });
