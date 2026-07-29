// Constantes globales
const URL_BACKEND = "https://quant-trading-platform-eulw.onrender.com/api/v1"; // Cambiado a la URL de Render
let chart, candlestickSeries, lineSeries; // Añadido lineSeries

// Iniciar el gráfico
document.addEventListener("DOMContentLoaded", () => {
    const chartOptions = { 
        layout: { textColor: '#d1d4dc', background: { type: 'solid', color: '#1e222d' } },
        grid: { vertLines: { color: '#2b2b43' }, horzLines: { color: '#2b2b43' } },
        timeScale: { timeVisible: true, secondsVisible: false }
    };

    const container = document.getElementById('tvchart');
    
    // Crear el gráfico
    chart = LightweightCharts.createChart(container, chartOptions);
    
    // Agregar las velas
    candlestickSeries = chart.addCandlestickSeries({
        upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
        wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });

    // Agregar la línea de predicción
    lineSeries = chart.addLineSeries({
        color: '#2962ff',
        lineWidth: 2,
        lineStyle: 1, // Línea punteada
        crosshairMarkerVisible: true
    });

    // Disparar la primera carga automática
    cargarDashboard();
});

// Funciones de conexión con la API
async function cargarDashboard() {
    const ticker = document.getElementById('tickerInput').value.toUpperCase();
    const plazo = document.getElementById('plazoPrediccion').value; // NUEVO: Capturar el plazo
    
    if (!ticker) return alert("Ingresa un ticker válido");

    try {
        // Limpiar datos anteriores
        lineSeries.setData([]);

        // Fetch de datos históricos
        const resMercado = await fetch(`${URL_BACKEND}/mercado/${ticker}?periodo=6mo`);
        if (!resMercado.ok) throw new Error("Error al obtener datos del mercado");
        
        const dataMercado = await resMercado.json();

        // Formatear los datos para TradingView
        const chartData = Object.entries(dataMercado.datos_historicos).map(([fecha, valores]) => {
            return {
                time: fecha.split(' ')[0],
                open: valores.Open,
                high: valores.High,
                low: valores.Low,
                close: valores.Close
            };
        });
        
        candlestickSeries.setData(chartData);

        // Fetch de la predicción de Machine Learning MULTI-STEP
        const resML = await fetch(`${URL_BACKEND}/prediccion/${ticker}?dias_futuro=${plazo}`);
        if (!resML.ok) throw new Error("Error al obtener predicción");
        
        const dataML = await resML.json();

        // Actualizar el panel lateral
        document.getElementById('precioActual').innerText = `$${dataML.precio_cierre_actual}`;
        
        const spanPrediccion = document.getElementById('prediccionDireccion');
        spanPrediccion.innerText = dataML.tendencia_general;
        spanPrediccion.className = dataML.tendencia_general === "Alcista" ? "alcista" : "bajista";

        const spanVariacion = document.getElementById('variacionEstimada');
        spanVariacion.innerText = dataML.variacion_total_estimada_pct;
        spanVariacion.style.color = dataML.variacion_total_estimada_pct > 0 ? '#26a69a' : '#ef5350';

        // Auto-completar la calculadora
        document.getElementById('bs-spot').value = dataML.precio_cierre_actual;

        // Dibujar la línea de predicción hacia el futuro
        const lastHistoricalData = chartData[chartData.length - 1];
        const predictionLineData = [{
            time: lastHistoricalData.time,
            value: dataML.precio_cierre_actual
        }];

        // Añadimos los días predichos
        dataML.predicciones_diarias.forEach(pred => {
            predictionLineData.push({
                time: pred.fecha,
                value: pred.precio_estimado
            });
        });

        lineSeries.setData(predictionLineData);
        
        // Ajustar el zoom para ver tanto la historia como el futuro
        chart.timeScale().fitContent();

    } catch (error) {
        console.error("Error detallado:", error);
        alert(`Fallo en la conexión: ${error.message}`);
    }
}

async function calcularBlackScholes() {
    const S = document.getElementById('bs-spot').value;
    const K = document.getElementById('bs-strike').value;
    const T = document.getElementById('bs-tiempo').value;
    const r = document.getElementById('bs-tasa').value;
    const sigma = document.getElementById('bs-vol').value;
    const tipo = document.getElementById('bs-tipo').value;

    if (!S || !K || !T || !r || !sigma) {
        return alert("Por favor, completa todos los campos de la calculadora.");
    }

    try {
        const url = new URL(`${URL_BACKEND}/opciones/black-scholes`);
        url.searchParams.append('S', S);
        url.searchParams.append('K', K);
        url.searchParams.append('T', T);
        url.searchParams.append('r', r);
        url.searchParams.append('sigma', sigma);
        url.searchParams.append('tipo', tipo);

        const res = await fetch(url);
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail);

        document.getElementById('bs-resultado').innerText = `$${parseFloat(data.precio_teorico).toFixed(2)}`;
    } catch (error) {
        console.error("Error en Black-Scholes:", error);
        alert(`Error al calcular: ${error.message}`);
    }
}