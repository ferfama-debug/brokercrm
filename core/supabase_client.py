from supabase import create_client
from django.conf import settings
import uuid
import os


def get_supabase_client():
    # 🔥 SI ESTAMOS EN GITHUB ACTIONS → NO USAR SUPABASE
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("⚠️ Supabase desactivado en GitHub Actions")
        return None

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise Exception("Supabase no configurado correctamente")

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def subir_archivo_supabase(file, carpeta):
    try:
        supabase = get_supabase_client()

        # 🔥 SI NO HAY SUPABASE (GITHUB) → SALIR LIMPIO
        if supabase is None:
            return None

        nombre_unico = f"{uuid.uuid4()}_{file.name}"
        path = f"{carpeta}/{nombre_unico}"

        print("SUBIENDO A SUPABASE:", path)

        supabase.storage.from_("polizas").upload(
            path,
            file.read(),
            {"content-type": file.content_type},
        )

        public_url = supabase.storage.from_("polizas").get_public_url(path)

        print("URL GENERADA:", public_url)

        return public_url

    except Exception as e:
        print("ERROR SUBIENDO:", str(e))
        return None