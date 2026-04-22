import argparse
import os
from twisted.internet import reactor, ssl
from twisted.mail import pop3
from twisted.internet.protocol import ServerFactory
from zope.interface import implementer


@implementer(pop3.IMailbox)
class BuzonUsuario:
    """Representa el buzón de un usuario específico"""

    def __init__(self, carpeta):
        self.carpeta = carpeta
        if os.path.exists(carpeta):
            todos = os.listdir(carpeta)
            self.correos = sorted([f for f in todos if f.endswith('.eml')])
        else:
            self.correos = []
        self.a_borrar = set()

    def listMessages(self, index=None):
        if index is None:
            tamaños = []
            for i, nombre in enumerate(self.correos):
                if i in self.a_borrar:
                    tamaños.append(0)
                else:
                    ruta = os.path.join(self.carpeta, nombre)
                    tamaños.append(os.path.getsize(ruta))
            return tamaños
        else:
            if index in self.a_borrar:
                return 0
            ruta = os.path.join(self.carpeta, self.correos[index])
            return os.path.getsize(ruta)

    def getMessage(self, index):
        ruta = os.path.join(self.carpeta, self.correos[index])
        return open(ruta, 'rb')

    def getUidl(self, index):
        return self.correos[index].encode()

    def deleteMessage(self, index):
        self.a_borrar.add(index)

    def undeleteMessages(self):
        self.a_borrar.clear()

    def sync(self):
        for index in self.a_borrar:
            ruta = os.path.join(self.carpeta, self.correos[index])
            if os.path.exists(ruta):
                os.remove(ruta)
                print(f"  Borrado: {ruta}")

    def getMessageCount(self):
        return len([i for i in range(len(self.correos)) if i not in self.a_borrar])

    def getMailboxSize(self):
        total = 0
        for i, nombre in enumerate(self.correos):
            if i not in self.a_borrar:
                ruta = os.path.join(self.carpeta, nombre)
                total += os.path.getsize(ruta)
        return total


class ServidorPOP3(pop3.POP3):
    """Maneja la autenticación y las sesiones POP3"""

    def authenticateUserPASS(self, usuario, contrasena):
        usuario_str = usuario.decode('utf-8')
        contrasena_str = contrasena.decode('utf-8')

        usuarios = {
            'maria': 'secreto123',
            'juan': 'clave456'
        }

        if usuario_str not in usuarios:
            raise pop3.POP3Error(b"Usuario no encontrado")

        if contrasena_str != usuarios[usuario_str]:
            raise pop3.POP3Error(b"Contrasena incorrecta")

        print(f"  Usuario autenticado: {usuario_str}")
        carpeta = os.path.join(self.factory.storage, usuario_str)
        os.makedirs(carpeta, exist_ok=True)
        buzon = BuzonUsuario(carpeta)
        return (pop3.IMailbox, buzon, lambda: None)


class POP3Factory(ServerFactory):

    def __init__(self, storage):
        self.storage = storage

    def buildProtocol(self, addr):
        p = ServidorPOP3()
        p.factory = self
        return p


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Servidor POP3 con Twisted')
    parser.add_argument('-s', '--storage', required=True)
    parser.add_argument('-p', '--port', type=int, default=110)
    args = parser.parse_args()

    os.makedirs(args.storage, exist_ok=True)
    factory = POP3Factory(args.storage)

    reactor.listenTCP(args.port, factory)
    print(f"✓ POP3 corriendo en puerto {args.port} (sin SSL)")

    if os.path.exists('servidor.key') and os.path.exists('servidor.crt'):
        contexto_ssl = ssl.DefaultOpenSSLContextFactory(
            'servidor.key',
            'servidor.crt'
        )
        puerto_ssl = args.port + 1
        reactor.listenSSL(puerto_ssl, factory, contexto_ssl)
        print(f"✓ POP3 corriendo en puerto {puerto_ssl} (con SSL)")
    else:
        print("  Sin SSL (no se encontraron servidor.key y servidor.crt)")

    print(f"✓ Storage: {args.storage}")
    reactor.run()