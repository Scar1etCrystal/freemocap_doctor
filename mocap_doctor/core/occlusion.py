"""Hand occlusion cues from the GVHMR preprocessing output.

HaMeR predicts a hand from a cropped image.  When the hand is hidden behind the
body, in a pocket, or out of frame, there is no evidence in that crop - the
prediction is a guess, and it can come out either spiky (scored by the motion
signals) or perfectly smooth (invisible to them, measured on the 0001-1499
take).  Motion statistics therefore cannot find these frames; visibility can.

ViTPose runs before GVHMR and writes one confidence per body keypoint, wrists
included, to ``gvhmr/preprocess/vitpose.pt``.  A wrist that stops being visible
shows up there as a sustained confidence dip, which is a direct "do not trust
the hand data here" signal.

This module is deliberately Blender-free so it can be unit tested, and it reads
the ``.pt`` archive without importing torch.
"""

from __future__ import annotations

import io
import pickle
import zipfile
from typing import Any, Iterable, Sequence

# COCO-17 keypoint order used by ViTPose.
KEYPOINT_NAMES = (
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
)
LEFT_WRIST = KEYPOINT_NAMES.index("left_wrist")
RIGHT_WRIST = KEYPOINT_NAMES.index("right_wrist")

# torch storage dtype codes -> numpy
_TORCH_DTYPES = {
    0: "?", 1: "b", 2: "B", 3: "h", 4: "H", 5: "i", 6: "l",
    7: "q", 8: "f", 9: "d", 11: "e", 12: "I",
}


class _Storage:
    """One raw tensor buffer inside the archive."""

    prefix = "archive"

    def __init__(self, key: str, numel: int, path: str) -> None:
        self.key, self.numel, self.path = key, numel, path

    def array(self, dtype_code: int | None):
        import numpy as np

        with zipfile.ZipFile(self.path) as archive:
            raw = archive.read(f"{self.prefix}/data/{self.key}")
        dtype = np.dtype(_TORCH_DTYPES.get(dtype_code, "f")).newbyteorder("<")
        return np.frombuffer(raw, dtype=dtype, count=self.numel)


class _Tensor:
    """A tensor view: storage plus offset/size, without torch."""

    def __init__(self, storage: _Storage, offset: int, size, dtype_code) -> None:
        self.storage, self.offset = storage, int(offset)
        self.size = tuple(int(value) for value in size)
        self.dtype_code = dtype_code

    def numpy(self):
        import numpy as np

        count = 1
        for value in self.size:
            count *= value
        flat = self.storage.array(self.dtype_code)[self.offset:self.offset + count]
        return flat.reshape(self.size)


_STORAGE_DTYPE_CODES = {
    "BoolStorage": 0, "CharStorage": 1, "ByteStorage": 2, "ShortStorage": 3,
    "IntStorage": 5, "LongStorage": 7, "FloatStorage": 8, "DoubleStorage": 9,
    "HalfStorage": 11, "BFloat16Storage": 11,
}


def _storage_type(dtype_code: int):
    """A stand-in for torch's storage classes, carrying only the dtype code."""

    return type("_StorageType", (), {"dtype_code": dtype_code})


class _Unpickler(pickle.Unpickler):
    prefix = "archive"
    path = ""

    def find_class(self, module, name):
        if module.startswith("torch"):
            if name == "_rebuild_tensor_v2":
                return self._rebuild
            if name == "Size":
                return tuple
            code = _STORAGE_DTYPE_CODES.get(name)
            if code is not None:
                return _storage_type(code)
            # torch's newer archives wrap storages in torch.storage.* classes.
            return _storage_type(8)
        return super().find_class(module, name)

    def persistent_load(self, pid):
        kind = pid[0]
        if kind != "storage":
            raise pickle.UnpicklingError(f"unsupported persistent id: {kind}")
        storage_type, key, _location, numel = pid[1], pid[2], pid[3], pid[4]
        code = getattr(storage_type, "dtype_code", None)
        storage = _Storage(str(key), int(numel), self.path)
        storage.prefix = self.prefix
        storage.dtype_code = code
        return storage

    @staticmethod
    def _rebuild(storage, offset, size, stride, *rest):
        return _Tensor(storage, offset, size, getattr(storage, "dtype_code", 8))


def read_tensor_dict(path: str, prefix: str = "archive") -> dict[str, Any]:
    """Read a ``torch.save``d dict of tensors without importing torch."""

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if f"{prefix}/data.pkl" not in names:
            candidates = {name.split("/", 1)[0] for name in names if name.endswith("/data.pkl")}
            if len(candidates) != 1:
                raise RuntimeError(f"{path} 不是预期的 torch 归档：{sorted(names)[:4]}")
            prefix = candidates.pop()
        payload = archive.read(f"{prefix}/data.pkl")
    unpickler = _Unpickler(io.BytesIO(payload))
    unpickler.prefix = prefix
    unpickler.path = path
    return unpickler.load()


def wrist_confidence(path: str, prefix: str = "vitpose"):
    """Return ``(left, right)`` per-frame wrist confidence from vitpose.pt."""

    import numpy as np

    data = read_tensor_dict(path, prefix)
    tensor = data.get("data") if isinstance(data, dict) else data
    if tensor is None:
        raise RuntimeError(f"{path} 里没有关键点张量")
    scores = tensor.numpy() if isinstance(tensor, _Tensor) else np.asarray(tensor)
    if scores.ndim != 3 or scores.shape[1] <= RIGHT_WRIST or scores.shape[2] < 3:
        raise RuntimeError(f"关键点张量形状不符合预期：{scores.shape}")
    if float(np.nanmax(scores[:, :, 2])) > 2.0:
        raise RuntimeError("第三列不像置信度（最大值 > 2）")
    return scores[:, LEFT_WRIST, 2].astype(float), scores[:, RIGHT_WRIST, 2].astype(float)


def confidence_floor(series, *, percentile: float = 5.0) -> float:
    """The video's own "wrist is not really visible" level."""

    import numpy as np

    values = np.asarray(series, dtype=float)
    return float(np.percentile(values, percentile))


def low_confidence_ranges(
    series: Sequence[float],
    *,
    threshold: float,
    min_length: int = 5,
    merge_gap: int = 4,
) -> list[tuple[int, int]]:
    """Frames below ``threshold``, merged and filtered, as inclusive ranges."""

    flagged = [index for index, value in enumerate(series) if float(value) < float(threshold)]
    if not flagged:
        return []
    ranges: list[list[int]] = [[flagged[0], flagged[0]]]
    for index in flagged[1:]:
        if index - ranges[-1][1] <= merge_gap + 1:
            ranges[-1][1] = index
        else:
            ranges.append([index, index])
    return [(start, end) for start, end in ranges if end - start + 1 >= min_length]


def merge_ranges(ranges: Iterable[Sequence[int]], *, gap: int = 0) -> list[tuple[int, int]]:
    """Sort and coalesce inclusive ranges whose gap is at most ``gap`` frames."""

    ordered = sorted((int(a), int(b)) for a, b in ranges if int(b) >= int(a))
    merged: list[list[int]] = []
    for start, end in ordered:
        if merged and start - merged[-1][1] <= gap + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]
