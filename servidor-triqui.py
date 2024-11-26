import socket  # Biblioteca para manejar conexiones de red (sockets).
import threading  # Biblioteca para manejar hilos concurrentes.
import json  # Biblioteca para manejar datos en formato JSON.
import random  # Biblioteca para generar valores aleatorios (turnos, símbolos, etc.).
import time  # Biblioteca para manejar pausas y temporización.
from datetime import datetime  # Biblioteca para trabajar con fechas y tiempos.

class ServidorTriqui:
    """
    Clase principal del servidor del juego Triqui.
    Gestiona las conexiones de los clientes y la lógica del juego.
    """

    def __init__(self, host='localhost', port=8000):
        """
        Constructor del servidor.
        Inicializa las variables y configura el socket del servidor.
        :param host: Dirección IP del servidor.
        :param port: Puerto de escucha.
        """
        # Crear un socket TCP/IP.
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Asignar dirección y puerto al socket.
        self.servidor.bind((host, port))

        # Habilitar el socket para escuchar conexiones (máximo 2 clientes).
        self.servidor.listen(2)

        # Variables para almacenar el estado del juego.
        self.clientes = []  # Lista de sockets de los clientes conectados.
        self.nombres = []  # Lista de nombres de los jugadores.
        self.puntuaciones = [0, 0]  # Puntuaciones de los dos jugadores.
        self.tablero = [" " for _ in range(9)]  # Representación del tablero (3x3 como lista).
        self.turno_actual = None  # Índice del jugador que tiene el turno actual.
        self.partidas_jugadas = 0  # Contador de partidas jugadas.
        self.simbolos = ["X", "O"]  # Símbolos asignados a los jugadores.
        self.ultima_actividad = datetime.now()  # Registro de la última actividad en el servidor.
        self.servidor_activo = True  # Estado del servidor (activo o no).

        # Crear un hilo para verificar la inactividad del servidor.
        self.hilo_inactividad = threading.Thread(target=self.verificar_inactividad)
        self.hilo_inactividad.daemon = True  # Configurar hilo como demonio (se cierra al terminar el programa).
        self.hilo_inactividad.start()  # Iniciar el hilo.

    def verificar_inactividad(self):
        """
        Verifica si han pasado 2 minutos sin actividad y cierra el servidor.
        """
        while self.servidor_activo:  # Ejecutar mientras el servidor esté activo.
            # Calcular tiempo de inactividad.
            tiempo_inactivo = (datetime.now() - self.ultima_actividad).seconds
            if tiempo_inactivo > 120:  # Si han pasado más de 2 minutos.
                print("Servidor cerrado por inactividad.")  # Mensaje en la consola.
                self.detener_servidor()  # Detener el servidor.
                break
            time.sleep(10)  # Esperar 10 segundos antes de verificar nuevamente.

    def detener_servidor(self):
        """
        Detiene el servidor y cierra todas las conexiones activas.
        """
        self.servidor_activo = False  # Cambiar el estado del servidor a inactivo.

        # Crear mensaje para notificar a los clientes del cierre del servidor.
        mensaje_cierre = {
            "tipo": "servidor_cerrado",
            "mensaje": "El servidor ha sido cerrado por inactividad."
        }
        self.enviar_a_todos(mensaje_cierre)  # Enviar mensaje a todos los clientes.

        # Cerrar conexiones de los clientes.
        for cliente in self.clientes:
            try:
                cliente.close()  # Intentar cerrar cada conexión.
            except:
                pass

        # Cerrar el socket del servidor.
        try:
            self.servidor.close()
        except:
            pass

        print("Servidor detenido correctamente.")  # Confirmar el cierre del servidor.

    def iniciar_servidor(self):
        """
        Inicia el servidor y espera conexiones de clientes.
        """
        print(f"Servidor iniciado en {self.servidor.getsockname()}")  # Mostrar dirección y puerto del servidor.
        try:
            while self.servidor_activo and len(self.clientes) <= 2:  # Aceptar máximo 2 clientes.
                cliente, direccion = self.servidor.accept()  # Aceptar conexión de un cliente.
                print(f"Cliente conectado desde {direccion}")  # Mostrar dirección del cliente conectado.

                # Crear un hilo para manejar la conexión del cliente.
                hilo = threading.Thread(target=self.manejar_cliente, args=(cliente,))
                hilo.daemon = True  # Configurar hilo como demonio.
                self.clientes.append(cliente)  # Agregar cliente a la lista.
                hilo.start()  # Iniciar el hilo.
        except KeyboardInterrupt:
            print("\nInterrupción manual. Cerrando servidor...")  # Mensaje al detener el servidor manualmente.
            self.detener_servidor()  # Detener el servidor.
        except Exception as e:
            print(f"Error inesperado: {e}")  # Mostrar errores no previstos.
            self.detener_servidor()  # Detener el servidor en caso de error.

    def manejar_cliente(self, cliente):
        """
        Maneja la conexión individual con cada cliente.
        :param cliente: Socket del cliente.
        """
        try:
            self.ultima_actividad = datetime.now()  # Actualizar última actividad del servidor.
            nombre = cliente.recv(1024).decode()  # Recibir el nombre del cliente.
            if not nombre:  # Si no se recibe nombre.
                print("Cliente se desconectó antes de enviar su nombre.")  # Notificar desconexión.
                self.eliminar_cliente(cliente)  # Eliminar cliente.
                return

            self.nombres.append(nombre)  # Agregar nombre del cliente a la lista.
            print(f"Jugador registrado: {nombre}")  # Mostrar nombre del jugador registrado.

            if len(self.nombres) == 2:  # Iniciar juego cuando hay dos jugadores.
                self.iniciar_juego()

            while self.servidor_activo:  # Mantener conexión activa mientras el servidor esté activo.
                mensaje = cliente.recv(1024).decode()  # Recibir mensaje del cliente.
                self.ultima_actividad = datetime.now()  # Actualizar última actividad.
                if not mensaje:  # Si no hay mensaje, desconectar cliente.
                    break
                datos = json.loads(mensaje)  # Decodificar mensaje JSON.
                if datos["tipo"] == "movimiento":  # Si el mensaje es un movimiento.
                    self.procesar_movimiento(datos["posicion"], self.clientes.index(cliente))  # Procesar movimiento.
        except (ConnectionResetError, ConnectionAbortedError):
            print("El cliente cerró la conexión abruptamente.")  # Notificar cierre abrupto.
        except Exception as e:
            print(f"Error con cliente: {e}")  # Mostrar error con cliente.
        finally:
            self.eliminar_cliente(cliente)  # Eliminar cliente al finalizar la conexión.

    def eliminar_cliente(self, cliente):
        """
        Elimina un cliente de la lista y cierra su conexión.
        :param cliente: Socket del cliente.
        """
        if cliente in self.clientes:  # Verificar si el cliente está en la lista.
            indice = self.clientes.index(cliente)  # Obtener el índice del cliente.
            nombre = self.nombres[indice] if indice < len(self.nombres) else "Desconocido"  # Obtener su nombre.
            print(f"Desconexión de cliente: {nombre}")  # Mostrar mensaje de desconexión.
            self.clientes.pop(indice)  # Eliminar el cliente de la lista de sockets.
            if indice < len(self.nombres):  # Verificar que el índice sea válido para nombres.
                self.nombres.pop(indice)  # Eliminar el nombre asociado al cliente.
        try:
            cliente.close()  # Intentar cerrar la conexión del cliente.
        except Exception as e:
            print(f"Error al cerrar la conexión del cliente: {e}")  # Mostrar error si ocurre.

    def enviar_a_todos(self, mensaje):
        """
        Envía un mensaje a todos los clientes conectados.
        :param mensaje: Mensaje en formato JSON a enviar.
        """
        for cliente in self.clientes[:]:  # Iterar sobre una copia de la lista de clientes.
            try:
                cliente.send(json.dumps(mensaje).encode())  # Enviar el mensaje codificado a cada cliente.
                print(f"Mensaje enviado a cliente.")  # Confirmar el envío en consola.
            except BrokenPipeError:  # Manejar error si el cliente se ha desconectado.
                print(f"Cliente desconectado (BrokenPipeError). Eliminando cliente.")  # Notificar desconexión.
                self.eliminar_cliente(cliente)  # Eliminar cliente de la lista.
            except Exception as e:  # Manejar otros errores.
                print(f"Error al enviar mensaje a cliente: {e}")  # Mostrar el error.
                self.eliminar_cliente(cliente)  # Eliminar cliente problemático.

    def iniciar_juego(self):
        """
        Inicializa el juego y envía la información inicial a los clientes.
        """
        self.turno_actual = random.randint(0, 1)  # Elegir al azar qué jugador comienza.
        random.shuffle(self.simbolos)  # Asignar símbolos aleatoriamente.

        for i in range(2):  # Enviar información inicial a los dos jugadores.
            info_inicial = {
                "tipo": "inicio_juego",  # Tipo de mensaje.
                "turno": i == self.turno_actual,  # Indicar si es el turno del jugador.
                "simbolo": self.simbolos[i],  # Símbolo asignado al jugador.
                "nombres": self.nombres,  # Lista de nombres de los jugadores.
                "puntuaciones": self.puntuaciones  # Puntuaciones actuales.
            }
            self.clientes[i].send(json.dumps(info_inicial).encode())  # Enviar la información al jugador.

    def procesar_movimiento(self, posicion, jugador):
        """
        Procesa un movimiento realizado por un jugador.
        :param posicion: Posición en el tablero (0-8).
        :param jugador: Índice del jugador que realiza el movimiento.
        """
        print(f"Movimiento recibido: Jugador {jugador}, Posición: {posicion}")  # Mensaje de depuración.
        if jugador == self.turno_actual and self.tablero[posicion] == " ":  # Validar turno y posición disponible.
            self.tablero[posicion] = self.simbolos[jugador]  # Actualizar el tablero con el símbolo del jugador.
            print(f"Tablero actualizado: {self.tablero}")  # Mostrar el tablero actualizado.

            ganador = self.verificar_ganador()  # Verificar si hay un ganador.
            if ganador:
                print(f"Ganador detectado: Jugador {jugador}")  # Mensaje si hay ganador.
            elif " " not in self.tablero:  # Verificar si el tablero está lleno.
                print("El tablero está lleno, empate.")  # Mensaje de empate.

            if ganador or " " not in self.tablero:  # Si hay ganador o empate.
                if ganador:
                    self.puntuaciones[jugador] += 1  # Incrementar la puntuación del ganador.
                self.partidas_jugadas += 1  # Incrementar el contador de partidas jugadas.
                self.tablero = [" " for _ in range(9)]  # Reiniciar el tablero.
                print(f"Partidas jugadas: {self.partidas_jugadas}, Puntuaciones: {self.puntuaciones}")  # Depuración.

                # Evaluar condiciones de empate o continuación del juego.
                if self.partidas_jugadas >= 3:
                    # Calcular la diferencia de puntos.
                    diferencia = abs(self.puntuaciones[0] - self.puntuaciones[1])
                    
                    if self.puntuaciones[0] == self.puntuaciones[1]:  # Si las puntuaciones están empatadas.
                        print("Empate general. Continuando con una partida adicional.")  # Mensaje de desempate.
                        self.iniciar_nueva_partida()  # Iniciar una nueva partida para desempatar.
                    elif diferencia >= 2:  # Si un jugador tiene ventaja de al menos 2 puntos.
                        print("El juego termina. Hay un ganador por ventaja de 2 puntos.")  # Fin del juego.
                        self.enviar_fin_juego()  # Notificar el fin del juego.
                    else:
                        print("El juego termina con las 3 partidas jugadas.")  # Fin tras 3 partidas sin desempate.
                        self.enviar_fin_juego()  # Notificar el fin del juego.
                else:
                    self.iniciar_nueva_partida()  # Iniciar una nueva partida si no se han jugado 3 aún.
            else:
                self.turno_actual = 1 - self.turno_actual  # Cambiar turno al otro jugador.
                print(f"Cambio de turno a jugador {self.turno_actual}")  # Depuración.
                self.enviar_estado_juego()  # Enviar el estado actualizado a los jugadores.
        else:
            print("Movimiento inválido o fuera de turno.")  # Notificar un movimiento inválido.

    '''
    def procesar_movimiento(self, posicion, jugador):
        """
        Procesa un movimiento realizado por un jugador.
        :param posicion: Posición en el tablero (0-8).
        :param jugador: Índice del jugador que realiza el movimiento.
        """
        print(f"Movimiento recibido: Jugador {jugador}, Posición: {posicion}")  # Mensaje de depuración.
        if jugador == self.turno_actual and self.tablero[posicion] == " ":  # Validar turno y posición disponible.
            self.tablero[posicion] = self.simbolos[jugador]  # Actualizar el tablero con el símbolo del jugador.
            print(f"Tablero actualizado: {self.tablero}")  # Mostrar el tablero actualizado.

            ganador = self.verificar_ganador()  # Verificar si hay un ganador.
            if ganador:
                print(f"Ganador detectado: Jugador {jugador}")  # Mensaje si hay ganador.
            elif " " not in self.tablero:  # Verificar si el tablero está lleno.
                print("El tablero está lleno, empate.")  # Mensaje de empate.

            if ganador or " " not in self.tablero:  # Si hay ganador o empate.
                if ganador:
                    self.puntuaciones[jugador] += 1  # Incrementar la puntuación del ganador.
                self.partidas_jugadas += 1  # Incrementar el contador de partidas jugadas.
                self.tablero = [" " for _ in range(9)]  # Reiniciar el tablero.
                print(f"Partidas jugadas: {self.partidas_jugadas}, Puntuaciones: {self.puntuaciones}")  # Depuración.

                if self.puntuaciones[jugador] == 2 or self.partidas_jugadas == 3:  # Condiciones para finalizar el juego.
                    self.enviar_fin_juego()  # Notificar el fin del juego.
                else:
                    self.iniciar_nueva_partida()  # Iniciar una nueva partida.
            else:
                self.turno_actual = 1 - self.turno_actual  # Cambiar turno al otro jugador.
                print(f"Cambio de turno a jugador {self.turno_actual}")  # Depuración.
                self.enviar_estado_juego()  # Enviar el estado actualizado a los jugadores.
        else:
            print("Movimiento inválido o fuera de turno.")  # Notificar un movimiento inválido.
    '''

    def verificar_ganador(self):
        """
        Verifica si hay un ganador en el tablero actual.
        :return: True si hay un ganador, False en caso contrario.
        """
        combinaciones = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Combinaciones horizontales.
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Combinaciones verticales.
            [0, 4, 8], [2, 4, 6]              # Combinaciones diagonales.
        ]

        for linea in combinaciones:  # Iterar sobre todas las combinaciones.
            if self.tablero[linea[0]] != " " and \
               self.tablero[linea[0]] == self.tablero[linea[1]] == self.tablero[linea[2]]:
                return True  # Hay ganador si se cumple una combinación.
        return False  # No hay ganador.

    def enviar_estado_juego(self):
        """
        Envía el estado actual del juego a todos los clientes.
        """
        estado = {
            "tipo": "estado_juego",  # Tipo de mensaje.
            "tablero": self.tablero,  # Estado actual del tablero.
            "turno": self.turno_actual,  # Índice del jugador con el turno actual.
            "puntuaciones": self.puntuaciones  # Puntuaciones de los jugadores.
        }
        print(f"Enviando estado del juego: {estado}")  # Depuración.
        self.enviar_a_todos(estado)  # Enviar estado a todos los clientes.

    def enviar_fin_juego(self):
        """
        Envía el mensaje de fin de juego a todos los clientes.
        """
        ganador = self.nombres[0] if self.puntuaciones[0] > self.puntuaciones[1] else self.nombres[1]  # Determinar ganador.
        resultado = {
            "tipo": "fin_juego",  # Tipo de mensaje.
            "puntuaciones": self.puntuaciones,  # Puntuaciones finales.
            "ganador": ganador  # Nombre del jugador ganador.
        }
        self.enviar_a_todos(resultado)  # Enviar resultado a todos los clientes.

    def iniciar_nueva_partida(self):
        """
        Inicializa una nueva partida dentro del mismo juego.
        """
        self.tablero = [" " for _ in range(9)]  # Reiniciar el tablero.
        self.turno_actual = random.randint(0, 1)  # Elegir al azar quién comienza.
        self.enviar_estado_juego()  # Enviar estado inicial del juego.

if __name__ == "__main__":
    # Crear una instancia del servidor y arrancarlo.
    servidor = ServidorTriqui()
    servidor.iniciar_servidor()

