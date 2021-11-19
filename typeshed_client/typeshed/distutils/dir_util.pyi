def mkpath(
    name: str, mode: int = ..., verbose: int = ..., dry_run: int = ...
) -> list[str]: ...
def create_tree(
    base_dir: str,
    files: list[str],
    mode: int = ...,
    verbose: int = ...,
    dry_run: int = ...,
) -> None: ...
def copy_tree(
    src: str,
    dst: str,
    preserve_mode: int = ...,
    preserve_times: int = ...,
    preserve_symlinks: int = ...,
    update: int = ...,
    verbose: int = ...,
    dry_run: int = ...,
) -> list[str]: ...
def remove_tree(directory: str, verbose: int = ..., dry_run: int = ...) -> None: ...
