import socket
import os
import re

class FTPClient:
    def __init__(self, host, port=21):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10)
        self.buffer_size = 1024
        self.type = None

    def connect(self):
        self.socket.connect((self.host, self.port))
        return self.read_server_response()


    def read_server_response(self):
        response = b''
        while True:
            data = self.socket.recv(self.buffer_size)
            response += data
            if data.endswith(b'\r\n'):
                break
        return response.decode('utf-8')
               
    def send_command(self, command):
        self.socket.sendall(command.encode('utf-8') + b'\r\n')
        return self.read_server_response()
        
    def user(self, username):
        return self.send_command(f'USER {username}')

    def pass_(self, password):
        return self.send_command(f'PASS {password}')

    def pasv(self):
            try:
                response = self.send_command('PASV')
                # Extraer la dirección IP y el puerto del servidor
                print(response)
                match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
                if match:
                    ip_parts = [int(x) for x in match.groups()[:4]]
                    port = int(match.group(5)) * 256 + int(match.group(6))
                    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    data_socket.connect((socket.inet_ntoa(bytes(ip_parts)), port))
                    return data_socket
                else:
                    print('awacate')
                    return None
            except Exception as e:
                print(f'No se pudo establecer el modo pasivo: {e}')
                return None

    def mkd(self, directory):
        return self.send_command(f'MKD {directory}')

    def list_files(self):
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo")
            return ""
        
        try:
            self.send_command('LIST')
            data = b''
            while True:
                try:
                    chunk = data_socket.recv(self.buffer_size)
                    if not chunk:
                        break # Se sale del bucle cuando no hay más datos para recibir
                    data += chunk
                except socket.timeout:
                    break
            print(self.read_server_response())
        finally:
            # Asegurarse de que el socket de datos se cierre correctamente
            data_socket.close()
    
        decoded_data = data.decode('utf-8')
        return decoded_data

    def retr(self, filename):
        print(filename)
        # Crear la carpeta Downloads si no existe
        if not os.path.exists('Downloads'):
            os.makedirs('Downloads')
        
        if self.type is None:
            print('No se ha establecido un tipo de transferencia')
            return 
        elif self.type == 'A':
            w_mode = 'w'
        else:
            w_mode = 'wb'
        # Conectar pasivamente para recibir el archivo
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo")
            return
        
        try:
            # Enviar el comando RETR
            print(filename)
            response = self.send_command(f'RETR {filename}')
            if response.split()[0] == '550':
                return 'Archivo no encontrado'
            
            # Recibir el archivo y guardarlo en la carpeta Downloads
            with open(f'Downloads/{filename}', w_mode) as file:
                while True:
                    try:
                        print('Pe')
                        chunk = data_socket.recv(self.buffer_size)
                        print(f'chunk: {chunk}.')
                        if not chunk:
                            break
                        if self.type == 'A':
                            file.write(chunk.decode('utf-8'))
                        else:
                            file.write(chunk)

                    except socket.timeout:
                        break
            print(self.read_server_response())
        finally:
            # Asegurarse de que el socket de datos se cierre correctamente
            data_socket.close()
        
        return f"Archivo {filename} descargado en la carpeta Downloads."



    def stor(self, filepath):
        # Verificar si el archivo existe
        if not os.path.exists(filepath):
            print(f"La ruta {filepath} no es una ruta válida.")
            return
        
        if self.type is None:
            print('No se ha establecido un tipo de transferencia')
            return 
        elif self.type == 'A':
            r_mode = 'r'
        else:
            r_mode = 'rb'
        # Extraer el nombre del archivo de la ruta completa
        filename = os.path.basename(filepath)

        # Conectar pasivamente para enviar el archivo
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo")
            return

        try:
            # Enviar el comando STOR
            self.send_command(f'STOR {filename}')

            # Abrir el archivo en modo binario para leer y enviar su contenido
            with open(filepath, r_mode) as file:
                while True:
                    chunk = file.read(self.buffer_size)
                    if not chunk:
                        break # Se sale del bucle cuando no hay más datos para enviar
                    data_socket.sendall(chunk)
        finally:
            # Asegurarse de que el socket de datos se cierre correctamente
            data_socket.close()

        # Leer y retornar la respuesta del servidor
        return self.read_server_response()

    
    def cwd(self, directory):
        """Cambia el directorio actual al especificado."""
        return self.send_command(f'CWD {directory}')

    def pwd(self):
        """Muestra el directorio actual."""
        return self.send_command('PWD')

    def mkd(self, directory):
        """Crea un nuevo directorio con el nombre especificado."""
        return self.send_command(f'MKD {directory}')

    def dele(self, filename):
        """Elimina el archivo especificado."""
        return self.send_command(f'DELE {filename}')

    def rmd(self, directory):
        """Elimina el directorio especificado."""
        return self.send_command(f'RMD {directory}')

    def acct(self, account_info):
        """Proporciona información de cuenta adicional al servidor FTP."""
        return self.send_command(f'ACCT {account_info}')
    
    def cdup(self):
        """Cambia al directorio padre del directorio de trabajo actual."""
        return self.send_command('CDUP')
    
    def smnt(self, remote_system):
        """Monta un sistema de archivos remoto en el servidor FTP."""
        return self.send_command(f'SMNT {remote_system}')
    
    def rein(self):
        """Reinicia la sesión FTP actual."""
        return self.send_command('REIN')
    
    #OJO
    def port_(self, ip, port):
        print('ccc')
        """Envía el comando PORT al servidor FTP para especificar el puerto de datos del cliente."""
        # Validar el tipo de datos
        if not isinstance(ip, str):
            raise TypeError("El argumento 'ip' debe ser una cadena.")
        if not isinstance(port, int):
            raise TypeError("El argumento 'port' debe ser un entero.")
        
        # Validar la dirección IP
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            raise ValueError("La dirección IP debe tener exactamente cuatro partes.")
        
        # Validar el puerto
        if port < 1 or port > 65535:
            raise ValueError("El puerto debe estar en el rango de 1 a 65535.")
        
        # Convertir la dirección IP y el puerto a formato de cadena para el comando PORT
        port_high, port_low = divmod(port, 256)
        port_str = f"{port_high},{port_low}"
        command = f"PORT {','.join(ip_parts)}0,{port_str}"
        
        # Enviar el comando PORT al servidor
        response = self.send_command(command)
        return response


    def active_mode(self, ip, port):
        """Maneja la conexión activa, abriendo un socket de datos y enviando su dirección IP y puerto al servidor FTP."""
        # Crear un socket de datos
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('1111')
        data_socket.bind((ip, int(port)))
        print('aaa')
        data_socket.listen(1)
        
        # Obtener la dirección IP y el puerto del socket de datos
        data_ip, data_port = data_socket.getsockname()
        print('bbb')
        # Enviar el comando PORT al servidor FTP con la dirección IP y el puerto del socket de datos
        response = self.port_(data_ip, data_port)
        print('ddd')
        if response.startswith('227'):
            # Si el servidor responde con un código de éxito, proceder con la transferencia de datos
            print("Conexión activa establecida.")
            if self.data_socket is not None:
                self.data_socket.close()
            self.data_socket = data_socket
        else:
            print("Error al establecer la conexión activa.")
    

    def type_(self, mode):
        """Establece el modo de transferencia de datos (ASCII o BINARY)."""
        if mode.upper() not in ['A', 'I']:
            raise ValueError("El modo debe ser 'ASCII' o 'BINARY'")
        response = self.send_command(f'TYPE {mode.upper()}')
        self.type = mode.upper()
        print(self.type)
        return response
    
    def appe(self, server_filename, data):
        # Conectar pasivamente para enviar los datos
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo")
            return
        try:
            ans = self.send_command(f'APPE {server_filename}')
            print(ans)

            if ans.startswith('150'):
                # Enviar los datos especificados
                data_socket.sendall(data.encode('utf-8'))
                data_socket.close()
                return self.read_server_response()
            else:
                print("Permisos insuficientes o error en la operación")
        finally:
            # Asegurarse de que el socket de datos se cierre correctamente
            data_socket.close()


        
       

    def stou(self, filepath, prefix=''):
        """Envía un archivo al servidor FTP y solicita que el servidor genere un nombre de archivo único.
        
        Args:
            filepath (str): Ruta del archivo local a enviar.
            prefix (str, optional): Prefijo para el nombre del archivo generado por el servidor. Defaults to ''.
        
        Returns:
            str: Respuesta del servidor FTP.
        """
        # Verificar si el archivo existe
        if not os.path.exists(filepath):
            print(f"La ruta {filepath} no es una ruta válida.")
            return
        
        if self.type is None:
            print('No se ha establecido un tipo de transferencia')
            return 
        elif self.type == 'A':
            r_mode = 'r'
        else:
            r_mode = 'rb'

        # Extraer el nombre del archivo de la ruta completa
        filename = os.path.basename(filepath)

        # Conectar pasivamente para enviar el archivo
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo")
            return

        try:
            # Enviar el comando STOU con el prefijo especificado
            ans = self.send_command(f'STOU {prefix}{filename}')
            print(ans)

            # Abrir el archivo en modo binario para leer y enviar su contenido
            with open(filepath, r_mode) as file:
                while True:
                    chunk = file.read(self.buffer_size)
                    if not chunk:
                        break # Se sale del bucle cuando no hay más datos para enviar
                    data_socket.sendall(chunk)
        finally:
            # Asegurarse de que el socket de datos se cierre correctamente
            data_socket.close()

        # Leer y retornar la respuesta del servidor
        return self.read_server_response()
    
    def allo(self, size):
        """Indica al servidor FTP que el cliente está listo para recibir datos."""
        response = self.send_command(f'ALLO {size}')
        return response

    def rest(self, position):
        """Especifica un punto de inicio para la transferencia de datos."""
        response = self.send_command(f'REST {position}')
        return response
    
    def rnfr(self, filename):
        """Inicia el proceso de renombrar un archivo en el servidor FTP."""
        return self.send_command(f'RNFR {filename}')

    def rnto(self, new_filename):
        """Completa el proceso de renombrar un archivo en el servidor FTP."""
        return self.send_command(f'RNTO {new_filename}')

    def abor(self):
        """Cancela el comando actual en el servidor FTP."""
        return self.send_command('ABOR')

    def nlst(self):
        """Lista los nombres de los archivos en el directorio actual del servidor FTP."""
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo")
            return ""
        
        try:
            self.send_command('NLST')
            data = b''
            while True:
                try:
                    chunk = data_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
            print(self.read_server_response())
        finally:
            data_socket.close()
    
        decoded_data = data.decode('utf-8')
        return decoded_data

    def site(self, command):
        """Envía un comando específico del sitio al servidor FTP."""
        return self.send_command(f'SITE {command}')

    def syst(self):
        """Solicita información del sistema operativo del servidor FTP."""
        return self.send_command('SYST')

    def stat(self, filename=None):
        """Solicita el estado del servidor FTP o de un archivo específico."""
        if filename:
            return self.send_command(f'STAT {filename}')
        else:
            return self.send_command('STAT')
    
    def help(self, command=None):
        """Solicita ayuda sobre un comando específico o sobre el servicio FTP en general."""
        if command:
            print(self.send_command(f'HELP {command}'))
            return self.read_server_response()
        else:
            print(self.send_command('HELP')) 
            # return self.send_command('HELP')
            return self.read_server_response()

    def stru(self, structure):
        """Establece la estructura de datos para la transferencia (FILE o RECORD)."""
        if structure.upper() not in ['F', 'R', 'P']:
            raise ValueError("La estructura debe ser 'F' para FILE o 'R' para RECORD")
        response = self.send_command(f'STRU {structure.upper()}')
        return response
    
    def noop(self):
        """Envía un comando NOOP al servidor FTP, que no hace nada pero es útil para mantener la conexión activa."""
        return self.send_command('NOOP')
    
    def quit(self):
        ans = self.send_command('QUIT')
        if not self.socket is None:
            self.socket.close()
        return ans

    def close(self):
        self.socket.close()


if __name__ == "__main__":
    # client = FTPClient('ftp.dlptest.com')
    # print(client.connect())
    # print(client.user('dlpuser'))
    # print(client.pass_('rNrKYTX9g7z3RgJRmxWuGHbeu'))
    client = FTPClient('127.0.0.1')
    print(client.connect())
    print(client.user('user1'))
    print(client.pass_('password1'))


    # client = FTPClient('test.rebex.net')
    # print(client.connect())
    # print(client.user('demo'))
    # print(client.pass_('password'))

    # print(client.pasv())
    # print(client.list())
    # client.quit()
    # client.close()


    while True:
        try:

            user_input = input("ftp>> ")

            command_parts = user_input.strip().split(" ")
            command = command_parts[0].lower()
            args = command_parts[1:]
            for nombre in args:
                print(nombre)



            print(f'com{command} ')
            
            if command == 'user':
                print(client.user(*args))
            elif command == 'pass':
                print(client.pass_(*args))
            # elif command == 'acct':
            #     print(client.acct(*args))
            elif command == 'cwd':
                print(client.cwd(*args))
            elif command == 'cdup':
                print(client.cdup())
            # elif command == 'smnt':
            #     print(client.smnt(*args))
            elif command == 'quit':
                print(client.quit())
                break
            elif command == 'rein':
                print(client.rein())
            elif command == 'port':
                print(client.active_mode(*args))
            elif command == 'pasv':
                print(client.pasv())
            elif command == 'type':
                print(client.type_(*args))
            #Probar en otro servidor
            elif command == 'stru':
                print(client.stru(*args))
            elif command == 'retr':
                print(client.retr(*args))
            elif command == 'stor':
                print(client.stor(*args))
            elif command == 'stou':
                print(client.stou(*args))
            elif command == 'appe':
                print(client.appe(*args))
            elif command == 'allo':
                print(client.allo(*args))
            elif command == 'rest':
                print(client.rest(*args))
            elif command == 'rnfr':
                print(client.rnfr(*args))
            elif command == 'rnto':
                print(client.rnto(*args))
            elif command == 'abor':
                #OJO HILOS
                print(client.abor(*args))
            elif command == 'dele':
                print(client.dele(*args))
            elif command == 'rmd':
                print(client.rmd(*args))
            elif command == 'mkd':
                print(client.mkd(*args))
            elif command == 'pwd':
                print(client.pwd())
            elif command == 'list':
                print(client.list_files())
            elif command == 'nlst':
                print(client.nlst())
            elif command == 'site':
                print(client.site(*args))
            elif command == 'syst':
                print(client.syst())
            elif command == 'stat':
                print(client.stat(*args))
            elif command == 'help':
                print(client.help(*args))
            elif command == 'noop':
                print(client.noop())
            else:
                print("Comando no reconocido. Por favor, inténtelo de nuevo.")
        except Exception as e:
            print(f"Error: {e}")

            
            
            


