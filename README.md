# 🚛 Sentinel - AD010

App de registro de turnos de trabajo para conductor de camión de asfalto en Atlanta, GA.

## Descripción

Sentinel es una aplicación web construida con Streamlit que permite registrar turnos de trabajo diarios, generar reportes para el Foreman, y mantener un historial estructurado en Google Sheets.

## Stack Tecnológico

- **Frontend/Backend:** Python + Streamlit
- **Base de Datos:** Google Sheets (gspread)
- **Seguridad:** Streamlit Secrets + Google Service Account

## Funcionalidades V1

- Registro de turnos (field y shop)
- Campos dinámicos según tipo de camión (AD = galones de tack)
- Alerta de cambio de aceite
- Generador de reporte para Foreman (formato iMessage)

## Autoría

Diseñado y arquitectado por Roman Olarte. Código generado con asistencia de IA (Claude Sonnet / Gemini) como herramienta de desarrollo. El objetivo a largo plazo es reconstruir estas soluciones de forma independiente a medida que mis habilidades en Python avanzan.

## Seguridad

Las credenciales de Google Cloud se manejan via `st.secrets` y nunca se exponen en el repositorio.