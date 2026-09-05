from importlib.resources import files

from y5n.sdk import Resource


async def content(capability: str, variant: str, **params) -> Resource:
    """Provide a static content resource relative to the package root."""
    path = params.get("path")
    if not isinstance(path, str) or not path:
        raise LookupError(f"content: variant '{variant}' requires a 'path' parameter")
    return Resource.traversable(files(__package__) / path)
