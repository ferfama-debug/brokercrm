from datetime import date
from dateutil.relativedelta import relativedelta

from policies.models import Policy


def generar_pagos_cuponera():

    hoy = date.today()

    pagos = []

    polizas = Policy.objects.filter(
        forma_pago="CUPONERA",
        frecuencia_cuponera__isnull=False,
    ).select_related("client")

    for p in polizas:

        frecuencia = p.frecuencia_cuponera

        if not frecuencia:
            continue

        proximo_pago = p.start_date

        while proximo_pago <= p.end_date:

            dias = (proximo_pago - hoy).days

            if 0 <= dias <= 5:

                telefono = (
                    getattr(p.client, "phone", "")
                    or getattr(p.client, "telefono", "")
                    or ""
                )
                telefono = telefono.replace(" ", "").replace("-", "")

                mensaje = (
                    f"Hola {p.client.first_name}. "
                    f"Te recordamos el pago de la cuponera de tu póliza "
                    f"{p.policy_number} de {p.company}. "
                    f"Vence el {proximo_pago}."
                )

                pagos.append(
                    {
                        "cliente": p.client,
                        "telefono": telefono,
                        "numero": p.policy_number,
                        "company": p.company,
                        "fecha": proximo_pago,
                        "mensaje": mensaje,
                        "pdf": p.cuponera_pdf if p.cuponera_pdf else None,
                    }
                )

            proximo_pago += relativedelta(months=int(frecuencia))

    return pagos