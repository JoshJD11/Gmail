import argparse
import csv
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twisted.internet import reactor, defer
from twisted.mail.smtp import sendmail


def construir_mensaje(remitente, destinatario, nombre, plantilla):

    cuerpo = plantilla.replace('{{nombre}}', nombre)
    lineas = cuerpo.split('\n')
    asunto = 'Sin asunto'
    inicio_cuerpo = 0

    for i, linea in enumerate(lineas):
        if linea.startswith('Subject:'):
            asunto = linea.replace('Subject:', '').strip()
            inicio_cuerpo = i + 2
            break

    cuerpo_final = '\n'.join(lineas[inicio_cuerpo:])
    mensaje = MIMEMultipart()


    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    parte_texto = MIMEText(cuerpo_final, 'plain', 'utf-8')
    mensaje.attach(parte_texto)

    return mensaje


def enviar_todos(servidor, csv_ruta, mensaje_ruta):

    if not os.path.exists(csv_ruta):
        print(f"Error: no se encontró el archivo CSV: {csv_ruta}")
        reactor.stop()
        return

    if not os.path.exists(mensaje_ruta):
        print(f"Error: no se encontró el archivo de mensaje: {mensaje_ruta}")
        reactor.stop()
        return

    with open(mensaje_ruta, 'r', encoding='utf-8') as f:
        plantilla = f.read()

    deferreds = []

    with open(csv_ruta, 'r', encoding='utf-8') as f:
        lector = csv.DictReader(f)

        for fila in lector:
            email = fila['email']
            nombre = fila['nombre']

            print(f"  Enviando a: {nombre} <{email}>")

            mensaje = construir_mensaje(
                remitente='yo@prueba.com',
                destinatario=email,
                nombre=nombre,
                plantilla=plantilla
            )


            msg_bytes = mensaje.as_bytes()

            d = sendmail(
                smtphost=servidor,        
                from_addr='yo@prueba.com',
                to_addrs=[email],
                msg=msg_bytes,
                port=2525
            )

            d.addCallback(lambda _, e=email: print(f"  ✓ Enviado a {e}"))
            d.addErrback(lambda err, e=email: print(f"  ✗ Error enviando a {e}: {err.getErrorMessage()}"))

            deferreds.append(d)

    if not deferreds:
        print("No hay destinatarios en el CSV.")
        reactor.stop()
        return

    lista = defer.DeferredList(deferreds)
    lista.addCallback(lambda _: terminar())


def terminar(): # python smtpclient.py -H localhost -c destinatarios.csv -m mensaje.txt
    print("\n✓ Todos los correos procesados.")
    reactor.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cliente SMTP masivo')

    parser.add_argument(
        '-H', '--host',
        required=True,
        help='Servidor SMTP al que conectarse (ej: localhost)'
    )

    parser.add_argument(
        '-c', '--csv',
        required=True,
        help='Archivo CSV con columnas: email, nombre'
    )

    parser.add_argument(
        '-m', '--message',
        required=True,
        help='Archivo de texto con la plantilla del mensaje'
    )

    args = parser.parse_args()

    print(f"Servidor SMTP: {args.host}")
    print(f"CSV: {args.csv}")
    print(f"Mensaje: {args.message}")
    print()

    reactor.callWhenRunning(enviar_todos, args.host, args.csv, args.message)
    reactor.run()