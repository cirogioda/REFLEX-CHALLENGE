# ⚡ REFLEX CHALLENGE

Aplicación de escritorio para medir el tiempo de reacción. Diseñada para funcionar con un Arduino (botón + LED) o en modo simulación con el teclado.

---

## 📋 Descripción

**Reflex Challenge** es un juego competitivo de reflejos:

1. El jugador ingresa su nombre.
2. Se juegan **5 rondas**.
3. En cada ronda el LED se pone **amarillo** (espera) y luego **verde**.
4. El jugador debe presionar el botón lo más rápido posible cuando el LED se pone verde.
5. Se registra el tiempo de reacción, se suman puntos y se actualiza el ranking.

Al finalizar las 5 rondas se guarda el promedio, el mejor tiempo y el puntaje total del jugador.

---

## ✨ Características

- Interfaz fullscreen con diseño oscuro moderno
- Conexión serial con Arduino (9600 baudios)
- **Modo Simulación** (sin hardware) usando la tecla **Espacio**
- Ranking persistente (guarda los mejores 20 jugadores)
- Cálculo de puntos: `máximo(0, 1000 - milisegundos)`
- Récord global de mejor tiempo de reacción
- Soporte para puertos `/dev/ttyACM*` y `/dev/ttyUSB*` (Linux) y `COM*` (Windows)

---

## 🛠️ Requisitos

### Software
- Python 3.8 o superior
- Librerías:
  ```bash
  pip install pyserial
