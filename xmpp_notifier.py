import argparse
import os
import asyncio
import slixmpp


class NotificadorXMPP(slixmpp.ClientXMPP):


    def __init__(self, jid, password, destinatario, mensaje):

        super().__init__(jid, password)


        self.destinatario = destinatario
        self.mensaje = mensaje

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0199')

        self.add_event_handler("session_start", self.al_conectar)


    async def al_conectar(self, event):

        self.send_presence()
        await self.get_roster()

        self.send_message(
            mto=self.destinatario,   
            mbody=self.mensaje,      
            mtype='chat'             
        )

        print(f"  ✓ Notificación enviada a {self.destinatario}")
        self.disconnect()


def contar_correos(carpeta):

    if not os.path.exists(carpeta):
        return 0

    correos = [f for f in os.listdir(carpeta) if f.endswith('.eml')]
    return len(correos)


def notificar(jid_bot, password, jid_destino, carpeta_correos):
    
    cantidad = contar_correos(carpeta_correos)

    if cantidad == 0:
        print("  No hay correos nuevos, no se envía notificación.")
        return

    mensaje = f"Tienes {cantidad} correo(s) sin leer en {carpeta_correos}"
    print(f"  Correos encontrados: {cantidad}")
    print(f"  Enviando notificación a {jid_destino}...")

    notificador = NotificadorXMPP(jid_bot, password, jid_destino, mensaje)
    notificador.connect()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(notificador.disconnected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Notificador XMPP de correos')

    parser.add_argument(
        '--jid',
        required=True,
        help='Tu cuenta XMPP, ej: mibot2026@conversations.im'
    )

    parser.add_argument(
        '--password',
        required=True,
        help='Contraseña de tu cuenta XMPP'
    )

    parser.add_argument(
        '--to',
        required=True,
        help='JID destinatario, ej: mirecepcion2026@conversations.im'
    )

    parser.add_argument(
        '--storage',
        required=True,
        help='Carpeta donde están los correos, ej: /tmp/correos/maria'
    )

    args = parser.parse_args()

    print(f"Bot JID   : {args.jid}")
    print(f"Destino   : {args.to}")
    print(f"Carpeta   : {args.storage}")
    print()

    notificar(args.jid, args.password, args.to, args.storage)

# python xmpp_notifier.py \
#   --jid mibot2026@conversations.im \
#   --password abriloches13 \
#   --to mirecepcion2026@conversations.im \
#   --storage /tmp/correos/maria