"""Starlette defaults multipart parts to 1 MB — raise for admin/media uploads."""

from starlette.requests import Request


# Keep in sync with r2_service.MAX_VIDEO_BYTES (50 MB).
MAX_MULTIPART_PART_BYTES = 50 * 1024 * 1024


class LargeUploadRequest(Request):
    async def form(
        self,
        *,
        max_files: int | float = 1000,
        max_fields: int | float = 1000,
        max_part_size: int = MAX_MULTIPART_PART_BYTES,
    ):
        return await super().form(
            max_files=max_files,
            max_fields=max_fields,
            max_part_size=max_part_size,
        )
