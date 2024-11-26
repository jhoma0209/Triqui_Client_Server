import socket  # Biblioteca para manejar conexiones de red (sockets).
import json  # Biblioteca para manejar datos en formato JSON.
import tkinter as tk  # Biblioteca para la interfaz gráfica.
from tkinter import messagebox, simpledialog  # Widgets para mostrar mensajes y capturar entradas del usuario.
import threading  # Biblioteca para manejar hilos concurrentes.
import argparse  # Biblioteca para manejar argumentos de línea de comandos.

class ClienteTriqui:
    """
    Clase principal del cliente del juego Triqui.
    Gestiona la conexión con el servidor y la interfaz gráfica.
    """

    def __init__(self, host, port):
        """
        Constructor del cliente.
        Configura la conexión con el servidor y la interfaz gráfica.
        :param host: Dirección IP del servidor.
        :param port: Puerto del servidor.
        """
        # Configuración del socket cliente
        self.cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 8000

        # Inicializar la ventana principal de la interfaz gráfica.
        self.ventana = tk.Tk()
        self.ventana.title("Triqui")

        # Variables para controlar el estado del juego.
        self.mi_turno = False  # Indica si es el turno del cliente.
        self.mi_simbolo = None  # Símbolo asignado al cliente.
        self.botones = []  # Lista para almacenar los botones del tablero.
        self.cliente_activo = True  # Estado de conexión del cliente.

        # Inicializar los símbolos posibles del juego.
        self.simbolos = ["X", "O"]  # Símbolos asignados a los jugadores.

        # Llamar a la función que configura los elementos gráficos.
        self.configurar_interfaz()


    def configurar_interfaz(self):
        """
        Configura todos los elementos de la interfaz gráfica.
        """
        # Creacion un marco superior para mostrar información de los jugadores.
        self.frame_info = tk.Frame(self.ventana)
        self.frame_info.pack(pady=10)

        # Etiqueta para mostrar información del jugador 1.
        self.label_jugador1 = tk.Label(self.frame_info, text="Jugador 1: 0", font=('Arial', 12))
        self.label_jugador1.pack(side=tk.LEFT, padx=10)
        # Etiqueta para mostrar información del jugador 2
        self.label_jugador2 = tk.Label(self.frame_info, text="Jugador 2: 0", font=('Arial', 12))
        self.label_jugador2.pack(side=tk.LEFT, padx=10)

        # Crear un marco para el tablero de juego.
        self.frame_tablero = tk.Frame(self.ventana)
        self.frame_tablero.pack()

        # Crear los botones para representar las celdas del tablero.
        for i in range(3): # Tres filas.
            for j in range(3): # Tres columnas.
                # Crear cada botón y asignar su acción al presionarlo.
                boton = tk.Button(self.frame_tablero, text="", width=10, height=4,
                                  command=lambda fila=i, col=j: self.hacer_movimiento(fila * 3 + col))
                boton.grid(row=i, column=j, padx=2, pady=2) # Posicionar el botón en la cuadrícula.
                self.botones.append(boton) # Agregar el botón a la lista.

        # Crear una etiqueta para mostrar el estado actual del juego.
        self.label_estado = tk.Label(self.ventana, text="Esperando conexión...", font=('Arial', 12))
        self.label_estado.pack(pady=10)

    # Método para establecer la conexión con el servidor.
    def conectar(self):
        """
        Establece conexión con el servidor.
        """
        try:
            # Conectar al servidor utilizando la dirección y el puerto configurados.            
            self.cliente.connect((self.host, self.port))

            # Solicitar al usuario que ingrese su nombre.
            nombre = simpledialog.askstring("Nombre", "Ingresa tu nombre:")
            if nombre:  # Si el usuario ingresa un nombre válido.
                self.cliente.send(nombre.encode()) # Enviar el nombre al servidor.

                # Crear un hilo para recibir mensajes del servidor.
                hilo_recepcion = threading.Thread(target=self.recibir_mensajes)
                hilo_recepcion.daemon = True # Configurar el hilo como demonio.
                hilo_recepcion.start() # Iniciar el hilo.

                # Configurar el evento para cerrar el cliente al cerrar la ventana.
                self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_cliente)
                self.ventana.mainloop() # Iniciar el bucle principal de la interfaz gráfica.
            else:
                self.cerrar_cliente()   # Cerrar cliente si no se ingresa un nombre.

        # Manejar errores de conexión al servidor.
        except ConnectionRefusedError:
            messagebox.showerror("Error", "No se pudo conectar al servidor. Verifica que el servidor está activo.")
            self.cerrar_cliente()   # Cerrar cliente al fallar la conexión.
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {e}")
            self.cerrar_cliente()   # Cerrar cliente al ocurrir un error inesperado.

    # Método para recibir mensajes del servidor.
    def recibir_mensajes(self):
        while self.cliente_activo:
            try:
                mensaje = self.cliente.recv(1024).decode()
                print(f"Mensaje recibido: {mensaje}")  # Depuración
                if not mensaje:  # Si no hay mensaje, el servidor cerró la conexión.
                    print("El servidor cerró la conexión.")  # Depuración
                    break
                datos = json.loads(mensaje) # Cargar mensaje JSON recibido.
                self.procesar_mensaje(datos) # Procesar el mensaje recibido
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON: {e}, mensaje: {mensaje}")  # Depuración
                break  # Salir si hay un error al decodificar JSON.
            except ConnectionResetError:
                print("La conexión fue cerrada por el servidor.")  # Depuración
                break  # Salir si la conexión fue cerrada por el servidor.
            except Exception as e:
                print(f"Error en la conexión con el servidor: {e}")  # Depuración
                break # Manejar cualquier otro error y salir del bucle.
            
    def procesar_mensaje(self, datos):
        """
        Procesa los mensajes recibidos del servidor según su tipo.
        :param datos: Diccionario con la información del mensaje recibido.
        """
        try:
            # Mostrar el mensaje recibido en la consola para depuración.
            print(f"Procesando mensaje del servidor: {datos}")  # Depuración

            # Si el mensaje es de tipo "inicio_juego".
            if datos["tipo"] == "inicio_juego":
                self.mi_turno = datos["turno"]  # Actualizar si es el turno del cliente.
                self.mi_simbolo = datos["simbolo"]  # Guardar el símbolo asignado al cliente.
                print(f"Inicio del juego. Mi símbolo: {self.mi_simbolo}, ¿Es mi turno?: {self.mi_turno}")  # Depuración
                self.actualizar_nombres(datos["nombres"], datos["puntuaciones"])  # Actualizar nombres y puntuaciones.
                self.actualizar_estado()  # Actualizar el estado del juego en la interfaz gráfica.

            # Si el mensaje es de tipo "estado_juego".
            elif datos["tipo"] == "estado_juego":
                print(f"Estado del juego actualizado: Turno del jugador: {datos['turno']}")  # Depuración
                self.actualizar_tablero(datos["tablero"])  # Actualizar el tablero visualmente.
                self.mi_turno = (datos["turno"] == self.simbolos.index(self.mi_simbolo))  # Actualizar turno.
                print(f"¿Es mi turno ahora?: {self.mi_turno}")  # Depuración
                self.actualizar_puntuaciones(datos["puntuaciones"])  # Actualizar puntuaciones.
                self.actualizar_estado()  # Actualizar estado.

            # Si el mensaje es de tipo "fin_juego".
            elif datos["tipo"] == "fin_juego":
                if datos.get("empate_global", False):  # Verificar si el servidor envía un mensaje de empate global.
                    messagebox.showinfo("Resultado", "El juego terminó en empate global. Se jugará una partida adicional.")
                else:
                    # Mostrar información del ganador en la consola.
                    ganador = datos["ganador"]
                    puntuaciones = datos["puntuaciones"]
                    mensaje = f"Ganador: {ganador}\nPuntuaciones:\n{puntuaciones[0]} - {puntuaciones[1]}"
                    messagebox.showinfo("Fin del juego", mensaje)  # Mostrar mensaje del ganador.
                    self.cerrar_cliente()  # Cerrar el cliente después del juego.

            # Si el mensaje recibido no coincide con los tipos esperados.
            else:
                print(f"Tipo de mensaje desconocido: {datos}")  # Depuración

        except KeyError as e:
            print(f"Clave faltante en el mensaje: {e}")  # Depuración
        except Exception as e:
            print(f"Error al procesar mensaje: {e}")  # Depuración
        
    
    
    '''
    # Método para procesar los mensajes recibidos del servidor.        
    def procesar_mensaje(self, datos):
        """
        Procesa los mensajes recibidos del servidor según su tipo.
        :param datos: Diccionario con la información del mensaje recibido.
        """
        try:
            # Mostrar el mensaje recibido en la consola para depuración.
            print(f"Procesando mensaje del servidor: {datos}")  # Depuración
            # Si el mensaje es de tipo "inicio_juego".
            if datos["tipo"] == "inicio_juego":
                # Actualizar si es el turno del cliente.                
                self.mi_turno = datos["turno"]
                # Guardar el símbolo asignado al cliente.                
                self.mi_simbolo = datos["simbolo"]
                # Mostrar el inicio del juego y los datos relevantes.                
                print(f"Inicio del juego. Mi símbolo: {self.mi_simbolo}, ¿Es mi turno?: {self.mi_turno}")  # Depuración
                # Actualizar los nombres y puntuaciones de los jugadores.
                self.actualizar_nombres(datos["nombres"], datos["puntuaciones"])
                # Actualizar el estado del juego en la interfaz gráfica.
                self.actualizar_estado()
            
            # Si el mensaje es de tipo "fin_juego".
            elif datos["tipo"] == "estado_juego":
                print(f"Estado del juego actualizado: Turno del jugador: {datos['turno']}")  # Depuración
                self.actualizar_tablero(datos["tablero"])
                self.mi_turno = (datos["turno"] == self.simbolos.index(self.mi_simbolo))
                print(f"¿Es mi turno ahora?: {self.mi_turno}")  # Depuración
                self.actualizar_puntuaciones(datos["puntuaciones"])
                self.actualizar_estado()

            # Si el mensaje es de tipo "fin_juego".
            elif datos["tipo"] == "fin_juego":
                # Mostrar información del ganador en la consola.
                print(f"Fin del juego: Ganador: {datos['ganador']}")  # Depuración
                # Mostrar al ganador y las puntuaciones finales en una ventana emergente.
                self.mostrar_ganador(datos["ganador"], datos["puntuaciones"])
            # Si el mensaje recibido no coincide con los tipos esperados.
            else:
                # Mostrar un mensaje de tipo desconocido en la consola para depuración.
                print(f"Tipo de mensaje desconocido: {datos}")  # Depuración
        
        # Manejar casos donde falte una clave en el mensaje recibido.
        except KeyError as e:
            # Mostrar un mensaje de error indicando la clave faltante.         
            print(f"Clave faltante en el mensaje: {e}")  # Depuración

        # Manejar otros errores generales al procesar el mensaje.
        except Exception as e:
            # Mostrar el error inesperado en la consola.            
            print(f"Error al procesar mensaje: {e}")  # Depuración
    '''
    
    # Método para manejar el movimiento del cliente en el tablero.
    def hacer_movimiento(self, posicion):
        """
        Envía un movimiento al servidor si es el turno del cliente.
        :param posicion: Índice de la posición en el tablero (0-8).
        """        
        if self.mi_turno: # Verificar si es el turno del cliente.
            print(f"Intentando mover en la posición {posicion}")  # Depuración
            mensaje = { # Crear un mensaje con el tipo de acción y la posición seleccionada.
                "tipo": "movimiento",
                "posicion": posicion
            }
            try:
                # Enviar el mensaje codificado en formato JSON al servidor.                
                self.cliente.send(json.dumps(mensaje).encode())
                print("Movimiento enviado al servidor.")  # Depuración                
            except:
                # Mostrar error si no se pudo enviar el mensaje.                
                messagebox.showerror("Error", "No se pudo enviar el movimiento al servidor.")
                print("Error al enviar el movimiento.")  # Depuración
                self.cerrar_cliente()  # Cerrar el cliente en caso de error.

    # Método para actualizar el tablero visualmente.
    def actualizar_tablero(self, tablero):
        """
        Actualiza el estado visual del tablero.
        :param tablero: Lista con el estado actual del tablero.
        """
        for i, simbolo in enumerate(tablero):  # Iterar sobre cada celda del tablero.
            # Actualizar el texto del botón correspondiente con el símbolo del tablero.            
            self.botones[i].config(text=simbolo)
            # Activar/desactivar botones en función del turno y si la casilla está vacía
            if self.mi_turno and simbolo == " ":
                self.botones[i].config(state="normal")  # Activar botón si está vacío y es el turno.
            else:
                self.botones[i].config(state="disabled") # Desactivar botón si no es el turno o está ocupado.


    def actualizar_nombres(self, nombres, puntuaciones):
        """
        Actualiza los nombres y puntuaciones mostrados.
        :param nombres: Lista de nombres de los jugadores.
        :param puntuaciones: Lista de puntuaciones de los jugadores.
        """
        # Actualizar la etiqueta del jugador 1 con su nombre y puntuación.        
        self.label_jugador1.config(text=f"{nombres[0]}: {puntuaciones[0]}")
        # Actualizar la etiqueta del jugador 2 con su nombre y puntuación.        
        self.label_jugador2.config(text=f"{nombres[1]}: {puntuaciones[1]}")

    # Método para actualizar las puntuaciones de los jugadores.
    def actualizar_puntuaciones(self, puntuaciones):
        """
        Actualiza las puntuaciones de los jugadores.
        :param puntuaciones: Lista con las puntuaciones de los jugadores.
        """
        # Actualizar la etiqueta del jugador 1 manteniendo su nombre.
        self.label_jugador1.config(text=f"{self.label_jugador1.cget('text').split(':')[0]}: {puntuaciones[0]}")
        # Actualizar la etiqueta del jugador 2 manteniendo su nombre.        
        self.label_jugador2.config(text=f"{self.label_jugador2.cget('text').split(':')[0]}: {puntuaciones[1]}")

    # Método para actualizar el estado en la interfaz gráfica.
    def actualizar_estado(self):
        """
        Actualiza el estado del juego en la interfaz gráfica.
        """
        if self.mi_turno: # Verificar si es el turno del cliente.
            self.label_estado.config(text="Tu turno") # Mostrar mensaje indicando que es su turno.
            # Activar botones disponibles
            for i, boton in enumerate(self.botones): # Iterar sobre los botones del tablero.
                if self.botones[i]["text"] == " ": # Activar los botones vacíos.
                    boton.config(state="normal")
        else:
            self.label_estado.config(text="Esperando al oponente...") # Indicar que se espera al otro jugador.
            # Desactivar todos los botones
            for boton in self.botones: # Desactivar todos los botones.
                boton.config(state="disabled")

    def mostrar_ganador(self, ganador, puntuaciones):
        """
        Muestra el resultado del juego, sea ganador o empate global.
        :param ganador: Nombre del jugador ganador.
        :param puntuaciones: Lista con las puntuaciones finales.
        """
        if ganador == "empate":
            mensaje = "El juego ha terminado en empate global. Se jugará una partida adicional."
            messagebox.showinfo("Empate Global", mensaje)
        else:
            mensaje = f"Ganador: {ganador}\nPuntuaciones:\n{puntuaciones[0]} - {puntuaciones[1]}"
            messagebox.showinfo("Fin del juego", mensaje)
        self.cerrar_cliente()
    
    '''
    # Método para mostrar el ganador y cerrar el cliente.
    def mostrar_ganador(self, ganador, puntuaciones):
        """
        Muestra el ganador del juego.
        :param ganador: Nombre del jugador ganador.
        :param puntuaciones: Lista con las puntuaciones finales.
        """
        # Crear un mensaje con el nombre del ganador y las puntuaciones finales.
        mensaje = f"Ganador: {ganador}\nPuntuaciones:\n{puntuaciones[0]} - {puntuaciones[1]}"
        # Mostrar el mensaje en una ventana emergente.        
        messagebox.showinfo("Fin del juego", mensaje)
        # Cerrar el cliente después de mostrar el ganador.        
        self.cerrar_cliente()
    '''
    
    # Método para cerrar la conexión y la ventana del cliente.
    def cerrar_cliente(self):
        """
        Cierra la conexión con el servidor y la interfaz gráfica.
        """
        self.cliente_activo = False # Cambiar el estado del cliente a inactivo.
        try:
            self.cliente.close() # Intentar cerrar el socket de conexión.
        except:
            pass
        self.ventana.destroy() # Cerrar la ventana gráfica.

# Código principal para ejecutar el cliente.
if __name__ == "__main__":
    # Crear un analizador de argumentos para capturar parámetros desde la línea de comandos.    
    parser = argparse.ArgumentParser(description="Cliente para el juego Triqui.")
    # Argumento para definir la dirección del servidor.    
    parser.add_argument("--host", type=str, default="localhost", help="Dirección IP del servidor (por defecto: localhost).")
    # Argumento para definir el puerto del servidor.    
    parser.add_argument("--port", type=int, default=8000, help="Puerto del servidor (por defecto: 5000).")
    args = parser.parse_args() # Parsear los argumentos proporcionados.

    # Crear una instancia del cliente con los parámetros especificados.
    cliente = ClienteTriqui(args.host, args.port)
    # Intentar conectar al servidor.
    cliente.conectar()
