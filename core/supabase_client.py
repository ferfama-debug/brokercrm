from supabase import create_client
from django.conf import settings
from uuid import uuid4
import mimetypes
import os
import re


def get_supabase():
    try:
        url = getattr(settings, "SUPABASE_URL", None)
        key = (
            getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
            or getattr(settings, "SUPABASE_KEY", None)
        )

        if not url or not key:
            print("⚠️ Supabase no configurado")
            return None

        return create_client(url, key)

    except Exception as e:
        print("❌ Error creando cliente Supabase:", e)
        return None


def _bucket_name():
    return getattr(settings, "SUPABASE_BUCKET", "polizas_clientes")


def _safe_filename(filename):
    if not filename:
        return f"{uuid4().hex}.pdf"

    base_name = os.path.basename(filename)
    name, ext = os.path.splitext(base_name)

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    if not safe_name:
        safe_name = uuid4().hex

    if not ext:
        ext = ".pdf"

    return f"{safe_name}{ext.lower()}"


def _filename_with_suffix(filename, suffix):
    name, ext = os.path.splitext(filename)
    return f"{name}_{suffix}{ext}"


def _content_type(file, filename):
    content_type = getattr(file, "content_type", None)
    if content_type:
        return content_type

    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def _extract_public_url(public_url_result):
    if not public_url_result:
        return None

    if isinstance(public_url_result, str):
        return public_url_result

    if isinstance(public_url_result, dict):
        return (
            public_url_result.get("publicUrl")
            or public_url_result.get("public_url")
            or (public_url_result.get("data", {}) or {}).get("publicUrl")
            or (public_url_result.get("data", {}) or {}).get("public_url")
        )

    data = getattr(public_url_result, "data", None)
    if isinstance(data, dict):
        return data.get("publicUrl") or data.get("public_url")

    return getattr(public_url_result, "publicUrl", None) or getattr(
        public_url_result, "public_url", None
    )


def _build_public_url(bucket, file_path):
    base_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
    if not base_url:
        return None

    return f"{base_url}/storage/v1/object/public/{bucket}/{file_path}"


def subir_archivo_supabase(file, folder="polizas", cliente=None):
    """
    Sube un archivo a Supabase organizándolo por cliente y subcarpeta.
    Estructura resultante en el bucket: ID_O_NOMBRE_CLIENTE / folder / archivo.pdf
    """
    try:
        if not file:
            print("⚠️ No se recibió archivo para subir")
            return None

        supabase = get_supabase()

        if not supabase:
            print("⚠️ Cliente Supabase no disponible")
            return None

        bucket = _bucket_name()
        safe_filename = _safe_filename(getattr(file, "name", "archivo.pdf"))

        if cliente is not None:
            cliente_str = str(cliente).strip()
            cliente_safe = re.sub(r"[^A-Za-z0-9._-]+", "_", cliente_str).strip("._")
            if not cliente_safe:
                cliente_safe = "cliente_sin_nombre"
            file_path = f"{cliente_safe}/{folder}/{safe_filename}"
        else:
            file_path = f"{folder}/{safe_filename}"

        content_type = _content_type(file, safe_filename)

        try:
            file.seek(0)
        except Exception:
            pass

        file_bytes = file.read()

        if not file_bytes:
            print("⚠️ Archivo vacío, no se sube a Supabase")
            return None

        try:
            supabase.storage.from_(bucket).upload(
                path=file_path,
                file=file_bytes,
                file_options={
                    "content-type": content_type,
                },
            )
        except Exception as e:
            error_text = str(e)
            if "Duplicate" in error_text or "already exists" in error_text:
                nuevo_nombre = _filename_with_suffix(safe_filename, uuid4().hex[:8])
                if cliente is not None:
                    file_path = f"{cliente_safe}/{folder}/{nuevo_nombre}"
                else:
                    file_path = f"{folder}/{nuevo_nombre}"

                supabase.storage.from_(bucket).upload(
                    path=file_path,
                    file=file_bytes,
                    file_options={
                        "content-type": content_type,
                    },
                )
            else:
                raise

        public_url_result = supabase.storage.from_(bucket).get_public_url(file_path)
        public_url = _extract_public_url(public_url_result)

        if not public_url:
            public_url = _build_public_url(bucket, file_path)

        if not public_url:
            print("⚠️ No se pudo obtener URL pública del archivo")
            return None

        return public_url

    except Exception as e:
        print("❌ Error subiendo archivo a Supabase:", e)
        return None


def eliminar_archivo_supabase_por_url(url):
    if not url:
        return
    try:
        supabase = get_supabase()
        if not supabase:
            print("⚠️ No se pudo inicializar Supabase para borrado.")
            return

        if "/storage/v1/object/public/" in url:
            partes = url.split("/storage/v1/object/public/")
            if len(partes) > 1:
                ruta_relativa = partes[1]
                segmentos = ruta_relativa.split("/", 1)
                if len(segmentos) == 2:
                    bkt = segmentos[0]
                    path = segmentos[1]

                    print(f"🗑️ Eliminando de Supabase [Bucket: {bkt}] -> Ruta: {path}")
                    res = supabase.storage.from_(bkt).remove([path])
                    print("✅ Resultado borrado Supabase:", res)
                    return

        print("⚠️ No se pudo parsear limpiamente la URL para eliminar en Supabase:", url)
    except Exception as e:
        print("❌ Error eliminando archivo de Supabase:", e)
