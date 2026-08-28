import uuid
import boto3
from api.supabase_client import supabase
from utils.config import B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME, B2_ENDPOINT_URL

# S3-compatible client pointed at Backblaze B2 (used for video storage only)
b2_client = boto3.client(
    "s3",
    endpoint_url=B2_ENDPOINT_URL,
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APPLICATION_KEY,
)


def upload_video(user_id: str, filename: str, file_bytes: bytes, content_type: str = "video/mp4") -> str:
    """
    Uploads a video file to Backblaze B2 under the user's folder.
    Returns the storage path (to be saved in the lectures table).
    """
    # Prefix with a random id to avoid filename collisions if the same
    # filename is uploaded twice by the same user
    unique_name = f"{uuid.uuid4()}_{filename}"
    storage_path = f"{user_id}/{unique_name}"

    b2_client.put_object(
        Bucket=B2_BUCKET_NAME,
        Key=storage_path,
        Body=file_bytes,
        ContentType=content_type,
    )

    return storage_path


def get_video_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generates a temporary signed URL to access a private video file.
    Default expiry: 1 hour.
    """
    url = b2_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": B2_BUCKET_NAME, "Key": storage_path},
        ExpiresIn=expires_in,
    )
    return url


def download_video(storage_path: str, local_path: str) -> str:
    """
    Downloads a video from Backblaze B2 to a local path.
    """
    b2_client.download_file(B2_BUCKET_NAME, storage_path, local_path)
    return local_path


def copy_video(source_path: str, dest_path: str) -> str:
    """
    Copies a video file within the B2 bucket from one user's folder to another.
    Used for cross-user deduplication.
    """
    b2_client.copy_object(
        Bucket=B2_BUCKET_NAME,
        CopySource={"Bucket": B2_BUCKET_NAME, "Key": source_path},
        Key=dest_path,
    )
    return dest_path


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


def copy_output(source_path: str, dest_path: str) -> str:
    """
    Copies a file within the 'outputs' bucket from one path to another.
    Used for cross-user deduplication — reuses already-generated outputs
    instead of regenerating them via the AI pipeline.
    """
    file_bytes = supabase.storage.from_("outputs").download(source_path)
    supabase.storage.from_("outputs").upload(
        path=dest_path,
        file=file_bytes,
        file_options={"content-type": "application/json"},
    )
    return dest_path