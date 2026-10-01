# Reconstructor Forense de Ataques

**Autor:** JUAN ESTEBAN CUARAN

## Caso de estudio

Un analista forense debe reconstruir la cadena de un ciberataque: reconocimiento, phishing, ejecución, escalada de privilegios, movimiento lateral y exfiltración. A medida que aparece nueva evidencia, el analista la agrega a la línea de tiempo, descarta falsos positivos, reordena eventos cuando los relojes de los equipos no coinciden y recorre la cadena hacia atrás (para encontrar el "paciente cero") o hacia adelante (para medir el impacto del ataque).

## Implementación de la estructura

La línea de tiempo del ataque está implementada como una **lista doblemente enlazada**:

- Cada evento de seguridad es un nodo que conoce el evento anterior y el siguiente.
- La línea de tiempo guarda una referencia al primer y al último evento, además de la cantidad de eventos.
- Los eventos se insertan en orden cronológico: al inicio, al final o en medio de la lista, según su hora.
- Eliminar o mover un evento solo requiere reconectar los enlaces de sus vecinos, sin desplazar los demás.
- Un cursor permite avanzar y retroceder evento por evento, aprovechando los enlaces en ambas direcciones.

## Cómo arrancar la app

1. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecutar la aplicación:
   ```bash
   python run.py
   ```
3. Abrir en el navegador: http://127.0.0.1:5000
