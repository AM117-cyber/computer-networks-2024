import socket
import os
import re

class FTPClient:
    def __init__(self, host, port=21):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.buffer_size = 1024

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
        # Crear la carpeta Downloads si no existe
        if not os.path.exists('Downloads'):
            os.makedirs('Downloads')
        
        # Conectar pasivamente para recibir el archivo
        data_socket = self.pasv()
        if data_socket is None:
            print("Error al establecer el modo pasivo puta")
            return
        
        try:
            # Enviar el comando RETR
            response = self.send_command(f'RETR {filename}')
            if response.split()[0] == '550':
                return 'Archivo no encontrado'
            # Recibir el archivo y guardarlo en la carpeta Downloads
            with open(f'Downloads/{filename}', 'wb') as file:
                while True:
                    try:
                        print('Pe')
                        chunk = data_socket.recv(self.buffer_size)
                        print(f'chunk: {chunk}.')
                        if not chunk:
                            break
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
            with open(filepath, 'rb') as file:
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



    def quit(self):
        return self.send_command('QUIT')

    def close(self):
        self.socket.close()


if __name__ == "__main__":
    client = FTPClient('ftp.dlptest.com')
    print(client.connect())
    print(client.user('dlpuser'))
    print(client.pass_('rNrKYTX9g7z3RgJRmxWuGHbeu'))


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

            print(f'com{command} args{args}')

            if command == 'user':
                print(client.user(*args))
            elif command == 'pass':
                print(client.pass_(*args))
            elif command == 'pasv':
                print(client.pasv(*args))
            elif command == 'mkd':
                print(client.mkd())
            elif command == 'list':
                print(client.list_files())
            elif command == 'retr':
                print(client.retr(' '.join(args)))
            elif command == 'stor':
                print(client.stor(*args))
            elif command == 'quit':
                print(client.quit(*args))
                break
            else:
                print("Comando no reconocido. Por favor, inténtelo de nuevo.")
        except Exception as e:
            print(f"Error: {e}")


