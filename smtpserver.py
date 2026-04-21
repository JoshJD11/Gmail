import argparse
import os
import time
from twisted.internet import reactor
from twisted.mail import smtp
from twisted.mail.smtp import SMTPFactory
from zope.interface import implementer
from twisted.mail.smtp import IMessageDelivery
from twisted.internet import defer



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
        return defer.succeed(None)

    def connectionLost(self):
        pass


@implementer(IMessageDelivery)
class MailDelivery:

    def __init__(self, mail_storage, domains):
        self.mail_storage = mail_storage
        self.domains = domains

    def validateFrom(self, helo, origin):
        return origin

    def validateTo(self, user):
        dominio = user.dest.domain.decode()
        if dominio not in self.domains:
            raise smtp.SMTPBadRcpt(user)
        return lambda: self._crear_mensaje(user)

    def _crear_mensaje(self, user):
        destinatario = user.dest.local.decode()
        carpeta = os.path.join(self.mail_storage, destinatario)
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
        p.delivery = MailDelivery(self.storage, self.domains)
        p.factory = self
        return p


if __name__ == '__main__': # python smtpserver.py -d prueba.com -s /tmp/correos -p 2525
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domains', nargs='+', required=True)
    parser.add_argument('-s', '--storage', required=True)
    parser.add_argument('-p', '--port', type=int, default=25)
    args = parser.parse_args()

    os.makedirs(args.storage, exist_ok=True)

    factory = MiSMTPFactory(args.domains, args.storage)
    reactor.listenTCP(args.port, factory)

    print(f"✓ Servidor corriendo en puerto {args.port}")
    print(f"✓ Dominios aceptados: {args.domains}")
    print(f"✓ Guardando en: {args.storage}")

    reactor.run()