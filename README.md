Quant Trading Platform 📈

Una plataforma web full-stack para el análisis de mercados financieros, cálculo de primas de opciones y predicción de precios a futuro utilizando modelos de Machine Learning.

🚀 Características Principales

Extracción de Datos en Tiempo Real: Obtención de datos históricos de activos financieros (acciones, ETFs, futuros) mediante la API de Yahoo Finance.

Análisis Técnico Automatizado: Cálculo de indicadores técnicos clave como la Media Móvil Simple (SMA) y el Índice de Fuerza Relativa (RSI).

Calculadora de Opciones (Black-Scholes): Implementación matemática del modelo de Black-Scholes para estimar el precio teórico o "justo" de contratos de opciones financieras (Calls y Puts).

Motor Predictivo de Machine Learning: Un modelo de regresión entrenado con datos históricos para proyectar la trayectoria del precio a corto y mediano plazo (1, 15 y 30 días).

Visualización Profesional: Gráficos interactivos de velas japonesas impulsados por TradingView Lightweight Charts, integrados en una interfaz institucional modo oscuro.

🧠 Arquitectura del Sistema

El proyecto está dividido en dos ecosistemas principales:

Backend (Python/FastAPI): Motor de cálculo de alto rendimiento que se encarga de la descarga de datos, procesamiento matemático de la matriz de precios, cálculos estocásticos (Black-Scholes) y entrenamiento del modelo de Machine Learning.

Frontend (HTML/JS/CSS): Interfaz de usuario ligera servida a través de Node.js, que consume la API REST del backend para renderizar los datos de forma dinámica.

🔮 El Modelo Predictivo: Random Forest Regressor

Para las proyecciones de precio, la herramienta emplea un algoritmo Random Forest Regressor de scikit-learn.

¿Por qué Random Forest?

A diferencia de modelos secuenciales puros como las LSTM, Random Forest maneja muy bien el ruido inherente a los mercados financieros, no requiere un escalado exhaustivo de los datos y es capaz de capturar relaciones no lineales complejas sin el riesgo extremo de sobreajuste (overfitting) en conjuntos de datos ruidosos.

¿Cómo funciona la predicción (Multi-step)?

Generación de Rezagos (Lags): El modelo no mira el precio como un valor aislado, sino como una secuencia temporal. Genera una matriz de características (features) analizando el comportamiento del precio de cierre y el RSI de los últimos 30 días.

Entrenamiento: Busca patrones entre la matriz de rezagos y los precios futuros reales (Targets a 1, 15 o 30 días).

Inferencia: Toma los datos de mercado de hoy y los evalúa contra las "reglas" aprendidas por sus 100 árboles de decisión para emitir una estimación probabilística del precio a futuro.

🧮 Calculadora de Opciones (Modelo Black-Scholes)

El panel de opciones de la plataforma resuelve la ecuación diferencial estocástica de Black-Scholes. Los parámetros requeridos son:

S (Spot Price): Precio actual del activo en el mercado (se autocompleta basado en la última vela del gráfico).

K (Strike Price): Precio de ejercicio del contrato.

T (Time to Expiration): Tiempo restante hasta el vencimiento del contrato, expresado en fracciones de año (ej. 30 días = 30/365 ≈ 0.082).

r (Risk-Free Rate): Tasa de interés libre de riesgo anualizada (ej. rendimiento de los bonos del tesoro de EE.UU. a 10 años).

σ (Volatility): Volatilidad implícita del activo (desviación estándar anualizada de los retornos).

🛠️ Instalación y Uso

1. Clonar el repositorio

git clone https://github.com/tu-usuario/quant-trading-platform.git
cd quant-trading-platform


2. Levantar el Backend (Python)

Se recomienda utilizar un entorno virtual (venv).

# Crear y activar entorno
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate

# Instalar dependencias
pip install fastapi uvicorn pandas numpy scipy scikit-learn yfinance

# Iniciar servidor
uvicorn main:app --reload


La API estará disponible en http://127.0.0.1:8000. Puedes consultar la documentación interactiva (Swagger) en http://127.0.0.1:8000/docs.

3. Levantar el Frontend (Node.js)

cd quant-frontend
npm install -g serve
serve


La aplicación web se ejecutará, por defecto, en http://localhost:3000.

💡 Ventajas de la Herramienta

Velocidad y Agilidad: FastAPI y Random Forest permiten realizar re-entrenamientos e inferencias bajo demanda en cuestión de milisegundos.

Sinergia Quant: Unifica el análisis técnico visual, proyecciones basadas en datos (Machine Learning) y cálculos teóricos de derivados (Black-Scholes) en una sola terminal de operaciones.

Arquitectura Desacoplada: El frontend y el backend operan de forma independiente, facilitando escalar cualquiera de las dos partes sin romper el sistema completo.

Desarrollado como MVP para la exploración de modelos cuantitativos en finanzas.