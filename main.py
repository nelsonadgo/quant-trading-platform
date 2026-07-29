from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor # Cambiado a Regressor
from datetime import datetime, timedelta

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA API
# ---------------------------------------------------------
app = FastAPI(
    title="Quant Trading API",
    description="Motor de análisis financiero, opciones y predicción con Machine Learning",
    version="2.0.0"
)

# Permitir peticiones desde cualquier Frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Luego lo cambias en deploy atu dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"estado": "API Online", "timestamp": datetime.now()}

# ---------------------------------------------------------
# DATOS DE MERCADO E INDICADORES (PANDAS PURO)
# ---------------------------------------------------------
@app.get("/api/v1/mercado/{ticker}")
def obtener_datos_mercado(ticker: str, periodo: str = "1mo", intervalo: str = "1d"):
    try:
        activo = yf.Ticker(ticker)
        historial = activo.history(period=periodo, interval=intervalo)
        
        if historial.empty:
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para {ticker}")

        # Análisis Técnico con Pandas puro
        if len(historial) >= 20:
            historial['SMA_20'] = historial['Close'].rolling(window=20).mean()
            
            delta = historial['Close'].diff()
            ganancia = delta.clip(lower=0)
            perdida = -1 * delta.clip(upper=0)
            
            ema_ganancia = ganancia.ewm(com=13, adjust=False).mean()
            ema_perdida = perdida.ewm(com=13, adjust=False).mean()
            
            rs = ema_ganancia / ema_perdida
            historial['RSI_14'] = 100 - (100 / (1 + rs))
        
        historial.fillna(0, inplace=True)
        historial.index = historial.index.tz_localize(None).strftime('%Y-%m-%d %H:%M:%S')
        
        precio_actual = float(historial['Close'].iloc[-1])
        precio_anterior = float(historial['Close'].iloc[-2]) if len(historial) > 1 else precio_actual
        variacion_pct = ((precio_actual - precio_anterior) / precio_anterior) * 100

        columnas_exportar = ['Open', 'High', 'Low', 'Close', 'Volume']
        if 'SMA_20' in historial.columns:
            columnas_exportar.extend(['SMA_20', 'RSI_14'])

        respuesta = {
            "ticker": ticker.upper(),
            "precio_actual": round(precio_actual, 2),
            "variacion_pct": round(variacion_pct, 2),
            "datos_historicos": historial[columnas_exportar].to_dict(orient="index")
        }
        
        return respuesta

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# CALCULADORA DE OPCIONES (BLACK-SCHOLES)
# ---------------------------------------------------------
@app.get("/api/v1/opciones/black-scholes")
def calcular_opcion_teorica(S: float, K: float, T: float, r: float, sigma: float, tipo: str = "call"):
    try:
        if T <= 0 or sigma <= 0:
            raise ValueError("El tiempo de expiración (T) y la volatilidad (sigma) deben ser mayores a 0.")

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if tipo.lower() == "call":
            precio = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif tipo.lower() == "put":
            precio = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise HTTPException(status_code=400, detail="El tipo debe ser 'call' o 'put'")
            
        return {
            "tipo_opcion": tipo.upper(),
            "precio_spot": S,
            "strike": K,
            "precio_teorico": round(precio, 4)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# PREDICCIÓN MULTI-STEP (MACHINE LEARNING)
# ---------------------------------------------------------
@app.get("/api/v1/prediccion/{ticker}")
def predecir_precio(ticker: str, dias_futuro: int = 15):
    """
    Entrena un Random Forest Regressor para predecir los próximos 'N' días.
    Utiliza una ventana de historial (lags) para generar la predicción.
    """
    try:
        if dias_futuro not in [1, 15, 30]:
            raise ValueError("dias_futuro debe ser 1, 15 o 30")

        activo = yf.Ticker(ticker)
        # Descargamos 5 años de datos diarios para tener suficiente historial para rezagos de 30 días
        historial = activo.history(period="5y", interval="1d")
        
        if historial.empty:
            raise HTTPException(status_code=404, detail="Datos no encontrados")

        # Ingeniería de Características
        historial['SMA_20'] = historial['Close'].rolling(window=20).mean()
        
        delta = historial['Close'].diff()
        ganancia = delta.clip(lower=0)
        perdida = -1 * delta.clip(upper=0)
        ema_ganancia = ganancia.ewm(com=13, adjust=False).mean()
        ema_perdida = perdida.ewm(com=13, adjust=False).mean()
        rs = ema_ganancia / ema_perdida
        historial['RSI_14'] = 100 - (100 / (1 + rs))
        
        historial.dropna(inplace=True)

        # Creación de variables rezagadas (Lags)
        # Miramos los últimos 30 días para predecir el futuro
        lags = 30
        datos_ml = pd.DataFrame(index=historial.index)
        
        for i in range(lags, 0, -1):
            datos_ml[f'Close_lag_{i}'] = historial['Close'].shift(i)
            datos_ml[f'RSI_lag_{i}'] = historial['RSI_14'].shift(i)

        # Crear el Target Multi-step
        # Queremos predecir el precio exacto en los días 1, 2, ..., N
        target_cols = []
        for i in range(1, dias_futuro + 1):
            col_name = f'Target_day_{i}'
            datos_ml[col_name] = historial['Close'].shift(-i)
            target_cols.append(col_name)

        # Limpiar NaNs (resultado de los shifts)
        datos_ml.dropna(inplace=True)

        # Separar X (features) y Y (targets)
        feature_cols = [c for c in datos_ml.columns if 'lag' in c]
        X = datos_ml[feature_cols].values
        Y = datos_ml[target_cols].values

        if len(X) == 0:
             raise ValueError("No hay suficientes datos después de crear los rezagos.")

        # Entrenar el Modelo Multi-Output
        modelo = RandomForestRegressor(n_estimators=100, random_state=42)
        modelo.fit(X, Y)

        # Preparar el input de "Hoy" para predecir el futuro
        # Tomamos los últimos 'lags' días del historial actual
        ultimos_dias = historial.tail(lags)
        
        # Aplanamos esos datos en el mismo formato de columnas que X
        input_hoy = []
        for i in range(lags, 0, -1):
             # i=30 significa hace 30 días, i=1 significa hoy
             idx = lags - i 
             input_hoy.append(ultimos_dias['Close'].iloc[idx])
             input_hoy.append(ultimos_dias['RSI_14'].iloc[idx])
        
        input_hoy = np.array(input_hoy).reshape(1, -1)

        # Predecir
        predicciones_futuras = modelo.predict(input_hoy)[0]
        
        precio_actual = float(historial['Close'].iloc[-1])
        precio_final_predicho = float(predicciones_futuras[-1])
        
        variacion_estimada = ((precio_final_predicho - precio_actual) / precio_actual) * 100

        # Formatear la respuesta
        # Generar fechas futuras para el frontend (excluyendo fines de semana simplificadamente)
        fechas_futuras = []
        fecha_base = historial.index[-1]
        for i in range(1, dias_futuro + 1):
            # Asumimos días calendario para simplificar la respuesta JSON
            fecha_futura = fecha_base + timedelta(days=i) 
            fechas_futuras.append(fecha_futura.strftime('%Y-%m-%d'))

        lista_predicciones = []
        for i in range(dias_futuro):
             lista_predicciones.append({
                 "dia": i + 1,
                 "fecha": fechas_futuras[i],
                 "precio_estimado": round(float(predicciones_futuras[i]), 2)
             })

        return {
            "ticker": ticker.upper(),
            "precio_cierre_actual": round(precio_actual, 2),
            "dias_proyectados": dias_futuro,
            "tendencia_general": "Alcista" if variacion_estimada > 0 else "Bajista",
            "variacion_total_estimada_pct": round(variacion_estimada, 2),
            "predicciones_diarias": lista_predicciones
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))