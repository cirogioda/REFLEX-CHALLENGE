import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import queue
import json
import os
import glob
import random

# ================= CONFIGURACIÓN =================
BAUDIOS = 9600
TOTAL_RONDAS = 5
ARCHIVO_RANKING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ranking_reflex.json"
)

BG_FONDO = "#090d16"
BG_PANEL = "#111827"
BG_TARJETA = "#1f2937"
BORDE_PANEL = "#374151"
TEXTO_BLANCO = "#f9fafb"
TEXTO_GRIS = "#9ca3af"
COLOR_ACENTO = "#3b82f6"
COLOR_VERDE = "#10b981"
COLOR_AMARILLO = "#f59e0b"
COLOR_ROJO = "#ef4444"


class ReflexChallengeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("REFLEX CHALLENGE")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=BG_FONDO)

        self.estado = "inicio"
        self.ronda = 0
        self.tiempos = []
        self.puntos_totales = 0
        self.nombre_actual = ""
        self.jugadores = self.cargar_ranking()
        self.record = self.obtener_record_global()

        self.arduino = None
        self.cola_serial = queue.Queue()
        self.modo_simulacion = tk.BooleanVar(value=False)
        self.sim_inicio_tiempo = 0
        self.sim_timer_id = None

        self.construir_interfaz()
        self.actualizar_lista_puertos()
        self.actualizar_tabla_ranking()

        self.root.bind("<Escape>", lambda e: self.cerrar_programa())
        self.root.bind("<Return>", self.accion_boton_principal)
        self.root.bind("<space>", self.accion_espacio_simulacion)

        self.root.after(300, lambda: self.conectar_arduino(silencioso=True))
        self.root.after(40, self.procesar_mensajes)

    def construir_interfaz(self):
        header = tk.Frame(self.root, bg=BG_PANEL, height=54, highlightbackground=BORDE_PANEL, highlightthickness=1)
        header.pack(fill="x", padx=12, pady=(10, 6))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="REFLEX CHALLENGE",
            font=("Arial", 13, "bold"),
            bg=BG_PANEL,
            fg=TEXTO_BLANCO
        ).pack(side="left", padx=12)

        frame_conexion = tk.Frame(header, bg=BG_PANEL)
        frame_conexion.pack(side="right", padx=10)

        self.chk_sim = tk.Checkbutton(
            frame_conexion,
            text="Simulación (Espacio)",
            variable=self.modo_simulacion,
            command=self.alternar_simulacion,
            bg=BG_PANEL,
            fg=TEXTO_GRIS,
            selectcolor=BG_TARJETA,
            activebackground=BG_PANEL,
            activeforeground=TEXTO_BLANCO,
            font=("Arial", 9)
        )
        self.chk_sim.pack(side="left", padx=8)

        self.combo_puertos = ttk.Combobox(frame_conexion, width=15, font=("Arial", 9))
        self.combo_puertos.pack(side="left", padx=4)

        tk.Button(
            frame_conexion,
            text="↻",
            command=self.actualizar_lista_puertos,
            bg=BG_TARJETA,
            fg=TEXTO_BLANCO,
            relief="flat",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            width=2
        ).pack(side="left", padx=2)

        self.btn_conectar = tk.Button(
            frame_conexion,
            text="CONECTAR",
            command=lambda: self.conectar_arduino(silencioso=False),
            bg=COLOR_ACENTO,
            fg="white",
            relief="flat",
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=10
        )
        self.btn_conectar.pack(side="left", padx=4)

        self.lbl_estado_conexion = tk.Label(
            frame_conexion,
            text="● DESCONECTADO",
            font=("Arial", 9, "bold"),
            bg=BG_PANEL,
            fg=COLOR_ROJO
        )
        self.lbl_estado_conexion.pack(side="left", padx=6)

        contenedor = tk.Frame(self.root, bg=BG_FONDO)
        contenedor.pack(fill="both", expand=True, padx=12, pady=6)
        contenedor.columnconfigure(0, weight=3, uniform="grupo")
        contenedor.columnconfigure(1, weight=2, uniform="grupo")
        contenedor.rowconfigure(0, weight=1)

        # ---------- COLUMNA IZQUIERDA ----------
        panel_juego = tk.Frame(contenedor, bg=BG_PANEL, highlightbackground=BORDE_PANEL, highlightthickness=1)
        panel_juego.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.banner_estado = tk.Label(
            panel_juego,
            text="INGRESÁ TU NOMBRE PARA COMENZAR",
            font=("Arial", 12, "bold"),
            bg=BG_TARJETA,
            fg=TEXTO_GRIS,
            pady=10
        )
        self.banner_estado.pack(fill="x", padx=15, pady=(15, 5))

        self.lbl_tiempo = tk.Label(
            panel_juego,
            text="0.000 s",
            font=("Arial", 52, "bold"),
            bg=BG_PANEL,
            fg=TEXTO_BLANCO
        )
        self.lbl_tiempo.pack(pady=(8, 2))

        self.canvas_led = tk.Canvas(panel_juego, width=105, height=105, bg=BG_PANEL, highlightthickness=0)
        self.canvas_led.pack(pady=6)
        self.canvas_led.create_oval(4, 4, 101, 101, outline=BORDE_PANEL, width=2)
        self.led_circulo = self.canvas_led.create_oval(12, 12, 93, 93, fill=COLOR_AMARILLO, outline="")

        frame_rondas = tk.Frame(panel_juego, bg=BG_PANEL)
        frame_rondas.pack(pady=10)

        self.tarjetas_ronda = []
        for i in range(TOTAL_RONDAS):
            tarjeta = tk.Frame(frame_rondas, bg=BG_TARJETA, width=82, height=52, highlightbackground=BORDE_PANEL, highlightthickness=1)
            tarjeta.pack(side="left", padx=4)
            tarjeta.pack_propagate(False)

            tk.Label(tarjeta, text=f"R{i+1}", font=("Arial", 8, "bold"), bg=BG_TARJETA, fg=TEXTO_GRIS).pack(pady=(4, 1))
            lbl_val = tk.Label(tarjeta, text="--", font=("Arial", 10, "bold"), bg=BG_TARJETA, fg=TEXTO_BLANCO)
            lbl_val.pack()

            self.tarjetas_ronda.append((tarjeta, lbl_val))

        frame_stats = tk.Frame(panel_juego, bg=BG_TARJETA, pady=10)
        frame_stats.pack(fill="x", padx=15, pady=8)

        self.lbl_ronda = tk.Label(frame_stats, text="Ronda: 0 / 5", font=("Arial", 11, "bold"), bg=BG_TARJETA, fg=TEXTO_BLANCO)
        self.lbl_ronda.pack(side="left", expand=True)

        self.lbl_puntos = tk.Label(frame_stats, text="Puntos: 0", font=("Arial", 11, "bold"), bg=BG_TARJETA, fg=COLOR_ACENTO)
        self.lbl_puntos.pack(side="left", expand=True)

        texto_rec = f"Récord: {self.record:.3f} s" if self.record else "Récord: --"
        self.lbl_record = tk.Label(frame_stats, text=texto_rec, font=("Arial", 11, "bold"), bg=BG_TARJETA, fg=COLOR_VERDE)
        self.lbl_record.pack(side="left", expand=True)

        frame_controles = tk.Frame(panel_juego, bg=BG_PANEL)
        frame_controles.pack(pady=(12, 15))

        tk.Label(
            frame_controles,
            text="JUGADOR:",
            font=("Arial", 10, "bold"),
            bg=BG_PANEL,
            fg=TEXTO_GRIS
        ).pack(side="left", padx=(0, 8))

        self.entrada_nombre = tk.Entry(
            frame_controles,
            font=("Arial", 12, "bold"),
            width=14,
            justify="center",
            bg=TEXTO_BLANCO,
            fg="#111827",
            relief="flat"
        )
        self.entrada_nombre.pack(side="left", ipady=5, padx=(0, 10))
        self.entrada_nombre.focus()

        self.btn_principal = tk.Button(
            frame_controles,
            text="INICIAR PARTIDA",
            font=("Arial", 11, "bold"),
            bg=COLOR_ACENTO,
            fg="white",
            activebackground="#2563eb",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self.accion_boton_principal
        )
        self.btn_principal.pack(side="left")

        # ---------- COLUMNA DERECHA: RANKING ----------
        panel_ranking = tk.Frame(contenedor, bg=BG_PANEL, highlightbackground=BORDE_PANEL, highlightthickness=1)
        panel_ranking.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        header_rank = tk.Frame(panel_ranking, bg=BG_TARJETA, pady=10)
        header_rank.pack(fill="x", padx=12, pady=(12, 8))

        tk.Label(
            header_rank,
            text="CLASIFICACIÓN",
            font=("Arial", 11, "bold"),
            bg=BG_TARJETA,
            fg=TEXTO_BLANCO
        ).pack(side="left", padx=10)

        tk.Button(
            header_rank,
            text="Limpiar",
            command=self.borrar_ranking,
            bg=BG_PANEL,
            fg=TEXTO_GRIS,
            relief="flat",
            font=("Arial", 8),
            cursor="hand2"
        ).pack(side="right", padx=8)

        self.frame_lista_ranking = tk.Frame(panel_ranking, bg=BG_PANEL)
        self.frame_lista_ranking.pack(fill="both", expand=True, padx=12, pady=4)

        tk.Label(
            panel_ranking,
            text="ESC: Salir | ENTER: Iniciar / Siguiente",
            font=("Arial", 9),
            bg=BG_PANEL,
            fg=TEXTO_GRIS
        ).pack(side="bottom", pady=10)

    # ================= GESTIÓN DE PUERTOS =================

    def actualizar_lista_puertos(self):
        puertos = [p.device for p in serial.tools.list_ports.comports()]
        for extra in glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"):
            if extra not in puertos:
                puertos.append(extra)

        self.combo_puertos["values"] = puertos
        if puertos:
            seleccionado = puertos[0]
            for p in puertos:
                if "ACM" in p or "USB" in p or "COM" in p:
                    seleccionado = p
                    break
            self.combo_puertos.set(seleccionado)
        else:
            self.combo_puertos.set("/dev/ttyACM0")

    def conectar_arduino(self, silencioso=False):
        if self.modo_simulacion.get():
            return

        puerto = self.combo_puertos.get().strip()
        if not puerto:
            puerto = "/dev/ttyACM0"

        try:
            if self.arduino and self.arduino.is_open:
                self.arduino.close()

            self.arduino = serial.Serial(puerto, BAUDIOS, timeout=1)
            time.sleep(2)
            self.arduino.reset_input_buffer()

            self.lbl_estado_conexion.config(text=f"● {puerto}", fg=COLOR_VERDE)
            self.btn_conectar.config(text="RECONECTAR", bg=BG_TARJETA)

            hilo = threading.Thread(target=self.leer_datos_serial, daemon=True)
            hilo.start()

        except serial.SerialException as e:
            self.arduino = None
            self.lbl_estado_conexion.config(text="● DESCONECTADO", fg=COLOR_ROJO)
            if not silencioso:
                messagebox.showerror(
                    "Error de conexión",
                    f"No se pudo abrir {puerto}.\n\nDetalle: {e}\n\n"
                    "Verificá en terminal con: ls /dev/ttyACM* /dev/ttyUSB*"
                )

    def leer_datos_serial(self):
        while True:
            try:
                if self.arduino is None or not self.arduino.is_open:
                    break
                linea = self.arduino.readline().decode("utf-8", errors="ignore").strip()
                if linea:
                    self.cola_serial.put(linea)
            except (serial.SerialException, OSError):
                self.cola_serial.put("ERROR_CONEXION")
                break

    def enviar_comando(self, cmd):
        if self.modo_simulacion.get():
            if cmd == "P":
                self.iniciar_largada_simulada(1)
            elif cmd == "S":
                self.iniciar_ronda_simulada()
            return True

        if self.arduino is None or not self.arduino.is_open:
            messagebox.showwarning("Arduino desconectado", "Conectá el Arduino arriba o activá 'Simulación'.")
            return False

        try:
            self.arduino.write(cmd.encode("utf-8"))
            return True
        except (serial.SerialException, OSError) as e:
            self.arduino = None
            self.lbl_estado_conexion.config(text="● DESCONECTADO", fg=COLOR_ROJO)
            messagebox.showerror("Error Serial", str(e))
            return False

    # ================= MODO SIMULACIÓN =================

    def alternar_simulacion(self):
        if self.modo_simulacion.get():
            self.lbl_estado_conexion.config(text="● SIMULACIÓN", fg=COLOR_AMARILLO)
        else:
            if self.arduino and self.arduino.is_open:
                self.lbl_estado_conexion.config(text=f"● {self.arduino.port}", fg=COLOR_VERDE)
            else:
                self.lbl_estado_conexion.config(text="● DESCONECTADO", fg=COLOR_ROJO)

    def iniciar_largada_simulada(self, paso):
        if self.estado != "largada":
            return
        if paso <= 3:
            self.cola_serial.put(f"PARPADEO:{paso}")
            self.sim_timer_id = self.root.after(400, lambda: self.apagar_largada_simulada(paso))
        else:
            self.iniciar_ronda_simulada()

    def apagar_largada_simulada(self, paso):
        if self.estado != "largada":
            return
        self.cola_serial.put("PARPADEO_OFF")
        self.sim_timer_id = self.root.after(400, lambda: self.iniciar_largada_simulada(paso + 1))

    def iniciar_ronda_simulada(self):
        self.cola_serial.put("ESPERANDO")
        demora_ms = random.randint(1500, 4000)
        self.sim_timer_id = self.root.after(demora_ms, self.encender_led_simulado)

    def encender_led_simulado(self):
        if self.estado == "esperando":
            self.sim_inicio_tiempo = time.perf_counter()
            self.cola_serial.put("LED_ON")

    def accion_espacio_simulacion(self, event=None):
        if not self.modo_simulacion.get():
            return
        if self.estado == "esperando":
            if self.sim_timer_id:
                self.root.after_cancel(self.sim_timer_id)
            self.cola_serial.put("FALSA")
        elif self.estado == "encendido":
            ms = int((time.perf_counter() - self.sim_inicio_tiempo) * 1000)
            self.cola_serial.put(f"TIEMPO:{ms}")

    # ================= PROCESAMIENTO DE MENSAJES =================

    def procesar_mensajes(self):
        try:
            while True:
                linea = self.cola_serial.get_nowait()

                if linea.startswith("PARPADEO:"):
                    num = linea.split(":")[1]
                    self.estado = "largada"
                    self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_ROJO)
                    self.banner_estado.config(text=f"ATENTO... SEÑAL {num} / 3", bg=COLOR_ROJO, fg="white")

                elif linea == "PARPADEO_OFF":
                    self.canvas_led.itemconfig(self.led_circulo, fill=BG_TARJETA)

                elif linea == "ESPERANDO":
                    self.estado = "esperando"
                    self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_AMARILLO)
                    self.banner_estado.config(text="ESPERÁ A QUE EL LED SE PONGA VERDE...", bg=COLOR_AMARILLO, fg="#111827")

                elif linea == "LED_ON":
                    self.estado = "encendido"
                    self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_VERDE)
                    self.banner_estado.config(text="¡AHORA! PRESIONÁ EL BOTÓN", bg=COLOR_VERDE, fg="#111827")

                elif linea == "FALSA":
                    self.estado = "falsa"
                    self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_ROJO)
                    self.banner_estado.config(text="¡FALSA SALIDA! APRETASTE ANTES DE TIEMPO", bg=COLOR_ROJO, fg="white")
                    self.btn_principal.config(text="REINTENTAR", state="normal", bg=COLOR_ROJO)

                elif linea.startswith("TIEMPO:") and self.estado == "encendido":
                    try:
                        ms = int(linea.split(":")[1])
                        if ms < 0:
                            continue
                        self.registrar_tiempo(ms)
                    except ValueError:
                        pass

                elif linea == "ERROR_CONEXION":
                    self.arduino = None
                    self.lbl_estado_conexion.config(text="● CONEXIÓN PERDIDA", fg=COLOR_ROJO)
                    self.btn_principal.config(text="REINTENTAR", state="normal")

        except queue.Empty:
            pass

        self.root.after(40, self.procesar_mensajes)

    # ================= LÓGICA DEL JUEGO =================

    def accion_boton_principal(self, event=None):
        if str(self.btn_principal["state"]) == "disabled":
            return

        if self.estado == "inicio":
            nombre = self.entrada_nombre.get().strip().upper()
            if not nombre:
                messagebox.showwarning("Falta nombre", "Ingresá el nombre del jugador antes de empezar.")
                self.entrada_nombre.focus()
                return

            if not self.modo_simulacion.get() and (self.arduino is None or not self.arduino.is_open):
                messagebox.showwarning("Sin conexión", "Conectá el Arduino arriba o activá 'Simulación'.")
                return

            self.nombre_actual = nombre
            self.ronda = 1
            self.tiempos = []
            self.puntos_totales = 0
            self.limpiar_tarjetas_ronda()
            self.entrada_nombre.config(state="disabled")
            self.comenzar_ronda()

        elif self.estado == "falsa":
            self.comenzar_ronda()

        elif self.estado == "resultado":
            if self.ronda < TOTAL_RONDAS:
                self.ronda += 1
                self.comenzar_ronda()
            else:
                self.preparar_nuevo_jugador()

    def comenzar_ronda(self):
        comando = "P" if self.ronda == 1 else "S"
        if not self.enviar_comando(comando):
            return

        self.estado = "largada" if self.ronda == 1 else "esperando"
        self.btn_principal.config(text="ESPERANDO...", state="disabled", bg=BG_TARJETA)
        self.lbl_tiempo.config(text="0.000 s", fg=TEXTO_BLANCO)
        self.lbl_ronda.config(text=f"Ronda: {self.ronda} / {TOTAL_RONDAS}")
        if self.ronda == 1:
            self.canvas_led.itemconfig(self.led_circulo, fill=BG_TARJETA)
            self.banner_estado.config(text="LARGADA EN 3 PARPADEOS...", bg=BG_TARJETA, fg=TEXTO_BLANCO)
        else:
            self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_AMARILLO)
            self.banner_estado.config(text="PREPARADO... ESPERÁ LA SEÑAL VERDE", bg=COLOR_AMARILLO, fg="#111827")

    def registrar_tiempo(self, ms):
        segundos = ms / 1000.0
        self.tiempos.append(segundos)

        puntos = max(0, 1000 - ms)
        self.puntos_totales += puntos

        if self.record is None or segundos < self.record:
            self.record = segundos
            self.lbl_record.config(text=f"Récord: {self.record:.3f} s")

        tarjeta, lbl_val = self.tarjetas_ronda[self.ronda - 1]
        tarjeta.config(highlightbackground=COLOR_VERDE)
        lbl_val.config(text=f"{segundos:.3f}s", fg=COLOR_VERDE)

        self.estado = "resultado"
        self.lbl_tiempo.config(text=f"{segundos:.3f} s", fg=COLOR_VERDE)
        self.lbl_puntos.config(text=f"Puntos: {self.puntos_totales}")
        self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_ACENTO)
        self.banner_estado.config(text=f"¡EXCELENTE! +{puntos} PUNTOS", bg=COLOR_ACENTO, fg="white")

        if len(self.tiempos) == TOTAL_RONDAS:
            self.finalizar_partida()
        else:
            self.btn_principal.config(text="SIGUIENTE RONDA ➔", state="normal", bg=COLOR_ACENTO)

    def finalizar_partida(self):
        promedio = sum(self.tiempos) / len(self.tiempos)
        mejor = min(self.tiempos)

        self.jugadores.append({
            "nombre": self.nombre_actual,
            "promedio": promedio,
            "mejor": mejor,
            "puntos": self.puntos_totales
        })

        self.jugadores.sort(key=lambda x: x["promedio"])
        self.guardar_ranking()
        self.actualizar_tabla_ranking()

        self.banner_estado.config(
            text=f"FINALIZADO — PROMEDIO: {promedio:.3f} s",
            bg=COLOR_VERDE,
            fg="#111827"
        )
        self.btn_principal.config(text="NUEVO JUGADOR", state="normal", bg=COLOR_VERDE)

        messagebox.showinfo(
            "Resultados Finales",
            f"Jugador: {self.nombre_actual}\n\n"
            f"• Promedio: {promedio:.3f} s\n"
            f"• Mejor reacción: {mejor:.3f} s\n"
            f"• Puntaje total: {self.puntos_totales} pts"
        )

    def preparar_nuevo_jugador(self):
        self.estado = "inicio"
        self.ronda = 0
        self.tiempos = []
        self.puntos_totales = 0

        self.limpiar_tarjetas_ronda()
        self.entrada_nombre.config(state="normal")
        self.entrada_nombre.delete(0, tk.END)
        self.entrada_nombre.focus()

        self.lbl_tiempo.config(text="0.000 s", fg=TEXTO_BLANCO)
        self.lbl_ronda.config(text=f"Ronda: 0 / {TOTAL_RONDAS}")
        self.lbl_puntos.config(text="Puntos: 0")
        self.canvas_led.itemconfig(self.led_circulo, fill=COLOR_AMARILLO)
        self.banner_estado.config(text="INGRESÁ EL SIGUIENTE JUGADOR", bg=BG_TARJETA, fg=TEXTO_GRIS)
        self.btn_principal.config(text="INICIAR PARTIDA", state="normal", bg=COLOR_ACENTO)

    def limpiar_tarjetas_ronda(self):
        for tarjeta, lbl_val in self.tarjetas_ronda:
            tarjeta.config(highlightbackground=BORDE_PANEL)
            lbl_val.config(text="--", fg=TEXTO_BLANCO)

    # ================= PERSISTENCIA =================

    def cargar_ranking(self):
        if os.path.exists(ARCHIVO_RANKING):
            try:
                with open(ARCHIVO_RANKING, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def guardar_ranking(self):
        try:
            with open(ARCHIVO_RANKING, "w", encoding="utf-8") as f:
                json.dump(self.jugadores[:20], f, indent=4, ensure_ascii=False)
        except OSError:
            pass

    def obtener_record_global(self):
        mejores = [j.get("mejor", j["promedio"]) for j in self.jugadores]
        return min(mejores) if mejores else None

    def actualizar_tabla_ranking(self):
        for widget in self.frame_lista_ranking.winfo_children():
            widget.destroy()

        if not self.jugadores:
            tk.Label(
                self.frame_lista_ranking,
                text="Aún no hay registros guardados.\n¡Sé el primero en jugar!",
                font=("Arial", 10),
                bg=BG_PANEL,
                fg=TEXTO_GRIS,
                pady=40
            ).pack()
            return

        for idx, j in enumerate(self.jugadores[:10]):
            fila = tk.Frame(self.frame_lista_ranking, bg=BG_TARJETA, pady=6, padx=10)
            fila.pack(fill="x", pady=3)

            color_puesto = COLOR_AMARILLO if idx == 0 else TEXTO_BLANCO

            tk.Label(
                fila,
                text=f"#{idx + 1}  {j['nombre']}",
                font=("Arial", 10, "bold"),
                bg=BG_TARJETA,
                fg=color_puesto
            ).pack(side="left")

            tk.Label(
                fila,
                text=f"{j['promedio']:.3f} s ({j['puntos']} pts)",
                font=("Arial", 10, "bold"),
                bg=BG_TARJETA,
                fg=COLOR_VERDE
            ).pack(side="right")

    def borrar_ranking(self):
        if messagebox.askyesno("Confirmar", "¿Querés borrar todo el historial?"):
            self.jugadores = []
            self.record = None
            self.lbl_record.config(text="Récord: --")
            self.guardar_ranking()
            self.actualizar_tabla_ranking()

    def cerrar_programa(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.root.destroy()


if __name__ == "__main__":
    ventana = tk.Tk()
    app = ReflexChallengeApp(ventana)
    ventana.mainloop()
if __name__ == "__main__":
    ventana = tk.Tk()
    app = ReflexChallengeApp(ventana)
    ventana.mainloop()
