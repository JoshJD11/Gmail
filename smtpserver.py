import argparse
import os
import time
from twisted.internet import reactor, ssl
from twisted.mail import smtp
from twisted.mail.smtp import SMTPFactory
from zope.interface import implementer
from twisted.mail.smtp import IMessageDelivery


@implementer(smtp.IMessage)
class MensajeHandler:

    def __init__(self, ruta_archivo):
        self.ruta = ruta_archivo
        self.lineas = []

    def lineReceived(self, line):
        self.lineas.append(line)

    def eomReceived(self):
        with open(self.ruta, 'wb') as f:
            for linea in self.lineas:
                f.write(linea + b'\n')
        from twisted.internet import defer
        return defer.succeed(None)

    def connectionLost(self):
        pass


@implementer(IMessageDelivery)
class MailDelivery:

    def __init__(self, dominios, carpeta):
        self.dominios = dominios
        self.carpeta = carpeta

    def validateFrom(self, helo, origin):
        return origin

    def validateTo(self, user):
        dominio = user.dest.domain.decode()
        print(f"  validateTo llamado: dominio={dominio}, dominios={self.dominios}")
        if dominio not in self.dominios:
            raise smtp.SMTPBadRcpt(user)
        return lambda: self._crear_mensaje(user)

    def _crear_mensaje(self, user):
        destinatario = user.dest.local.decode()
        carpeta = os.path.join(self.carpeta, destinatario)
        os.makedirs(carpeta, exist_ok=True)
        nombre_archivo = os.path.join(carpeta, f"{int(time.time())}.eml")
        return MensajeHandler(nombre_archivo)

    def receivedHeader(self, helo, origin, recipients):
        return b"Received: by mi-servidor"


class MiSMTPFactory(SMTPFactory):

    def __init__(self, domains, storage):
        SMTPFactory.__init__(self)
        self.domains = domains
        self.storage = storage

    def buildProtocol(self, addr):
        p = smtp.ESMTP()
        p.delivery = MailDelivery(self.domains, self.storage)
        p.factory = self
        return p


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Servidor SMTP con Twisted')
    parser.add_argument('-d', '--domains', nargs='+', required=True)
    parser.add_argument('-s', '--storage', required=True)
    parser.add_argument('-p', '--port', type=int, default=25)
    args = parser.parse_args()

    os.makedirs(args.storage, exist_ok=True)
    factory = MiSMTPFactory(args.domains, args.storage)

    reactor.listenTCP(args.port, factory)
    print(f"✓ SMTP corriendo en puerto {args.port} (sin SSL)")

    if os.path.exists('servidor.key') and os.path.exists('servidor.crt'):
        contexto_ssl = ssl.DefaultOpenSSLContextFactory(
            'servidor.key',
            'servidor.crt'
        )
        puerto_ssl = args.port + 1
        reactor.listenSSL(puerto_ssl, factory, contexto_ssl)
        print(f"✓ SMTP corriendo en puerto {puerto_ssl} (con SSL)")
    else:
        print("  Sin SSL (no se encontraron servidor.key y servidor.crt)")

    print(f"✓ Dominios: {args.domains}")
    print(f"✓ Storage:  {args.storage}")
    reactor.run()