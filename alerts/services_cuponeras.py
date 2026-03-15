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

        proximo_pago = p.start_date

        while proximo_pago <= p.end_date:

            dias = (proximo_pago - hoy).days

            if 0 <= dias <= 5:

                mensaje = (
                    f"Hola {p.client.first_name}. "
                    f"Te recordamos el pago de la cuponera de tu póliza "
                    f"{p.policy_number} de {p.company}. "
                    f"Vence el {proximo_pago}."
                )

                pagos.append(
                    {
                        "cliente": p.client,
                        "telefono": getattr(p.client, "phone", ""),
                        "numero": p.policy_number,
                        "company": p.company,
                        "fecha": proximo_pago,
                        "mensaje": mensaje,
                        "pdf": p.cuponera_pdf.url if p.cuponera_pdf else None,
                    }
                )

            proximo_pago += relativedelta(months=frecuencia)

    return pagos
