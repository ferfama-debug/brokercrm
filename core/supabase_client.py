from supabase import create_client, Client
from django.conf import settings
from uuid import uuid4
import mimetypes
import os
import re


def get_supabase():
    try:
        url = getattr(settings, "SUPABASE_URL", None)
        key = getattr(settings, "SUPABASE_KEY", None)

        if not url or not key:
            print("⚠️ Supabase no configurado")
            return None

        print("✅ Supabase configurado correctamente")

        # 🔥 FIX PROXY ERROR
        try:
            return create_client(url, key)
        except TypeError as e:
            print("⚠️ create_client falló, usando fallback:", e)
            return Client(url, key)

    except Exception as e:
        print("❌ Error creando cliente Supabase:", e)
        return None


def _bucket_name():
    bucket = getattr(settings, "SUPABASE_BUCKET", "documents")
    print("🪣 Bucket Supabase:", bucket)
    return bucket


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

    return (
        getattr(public_url_result, "publicUrl", None)
        or getattr(public_url_result, "public_url", None)
    )


def _build_public_url(bucket, file_path):
    base_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
    if not base_url:
        return None

    return f"{base_url}/storage/v1/object/public/{bucket}/{file_path}"


def subir_archivo_supabase(file, folder):
    try:
        print("🚀 Iniciando subida a Supabase")
        print("📁 Folder recibido:", folder)
        print("📄 Archivo recibido:", getattr(file, "name", None))

        supabase = get_supabase()

        if not supabase:
            print("⚠️ Cliente Supabase no disponible")
            return None

        if not file:
            print("⚠️ No se recibió archivo para subir")
            return None

        bucket = _bucket_name()
        safe_filename = _safe_filename(getattr(file, "name", "archivo.pdf"))
        file_path = f"{folder}/{uuid4().hex}_{safe_filename}"
        content_type = _content_type(file, safe_filename)

        print("📝 safe_filename:", safe_filename)
        print("🛣️ file_path:", file_path)
        print("🏷️ content_type:", content_type)

        try:
            file.seek(0)
        except Exception as e:
            print("⚠️ No se pudo hacer seek(0):", e)

        file_bytes = file.read()

        if not file_bytes:
            print("⚠️ Archivo vacío, no se sube a Supabase")
            return None

        print("📦 Tamaño archivo bytes:", len(file_bytes))

        supabase.storage.from_(bucket).upload(
            path=file_path,
            file=file_bytes,
            file_options={
                "content-type": content_type,
            },
        )

        public_url_result = supabase.storage.from_(bucket).get_public_url(file_path)
        print("🌐 get_public_url result:", public_url_result)

        public_url = _extract_public_url(public_url_result)

        if not public_url:
            public_url = _build_public_url(bucket, file_path)
            print("🛠️ URL pública armada manualmente:", public_url)

        if not public_url:
            print("⚠️ No se pudo obtener URL pública del archivo")
            return None

        print("✅ URL final archivo:", public_url)
        return public_url

    except Exception as e:
        print("❌ ERROR SUBIENDO:", e)
        return None