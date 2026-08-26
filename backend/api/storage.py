import uuid
from api.supabase_client import supabase


def upload_video(user_id: str, filename: str, file_bytes: bytes, content_type: str = "video/mp4") -> str:
    """
    Uploads a video file to the 'videos' bucket under the user's folder.
    Returns the storage path (to be saved in the lectures table).
    """
    # Prefix with a random id to avoid filename collisions if the same
    # filename is uploaded twice by the same user
    unique_name = f"{uuid.uuid4()}_{filename}"
    storage_path = f"{user_id}/{unique_name}"

    supabase.storage.from_("videos").upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )

    return storage_path


def get_video_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generates a temporary signed URL to access a private video file.
    Default expiry: 1 hour.
    """
    result = supabase.storage.from_("videos").create_signed_url(storage_path, expires_in)
    return result["signedURL"]

def download_video(storage_path: str, local_path: str) -> str:
    """
    Downloads a video from the 'videos' bucket to a local path.
    """
    file_bytes = supabase.storage.from_("videos").download(storage_path)
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    return local_path


def upload_output(local_path: str, storage_path: str, content_type: str = "application/octet-stream") -> str:
    """
    Uploads a generated output file (subtitle/summary/quiz) to the 'outputs' bucket.
    """
    with open(local_path, "rb") as f:
        file_bytes = f.read()

    supabase.storage.from_("outputs").upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return storage_path

def get_output_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generates a temporary signed URL to access a private output file
    (subtitle, summary, or quiz JSON) in the 'outputs' bucket.
    Default expiry: 1 hour.
    """
    result = supabase.storage.from_("outputs").create_signed_url(storage_path, expires_in)
    return result["signedURL"]

def download_output(storage_path: str) -> bytes:
    """
    Downloads a file from the 'outputs' bucket and returns its raw bytes.
    Used to pull the generated quiz.json back for grading.
    """
    return supabase.storage.from_("outputs").download(storage_path)