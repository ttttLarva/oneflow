"""
Copyright 2020 The OneFlow Authors. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from typing import Optional, Union

import oneflow as flow
from oneflow.framework.tensor import register_tensor_op
from oneflow.nn.module import Module


class To(Module):
    def __init__(self, copy):
        super().__init__()
        self.copy = copy

    def forward(self, x, device, dtype):
        result = x
        if device is not None:
            if x.device != device or self.copy:
                result = flow.F.copy(x, device_type=device.type, device_id=device.index)
        if dtype is not None:
            if x.dtype != dtype or self.copy:
                result = flow.F.cast(result, dtype=dtype)
        return result


def ConsistentTo(input, device):
    assert device in (
        "cuda",
        "cpu",
    ), 'consistent tensor only support to("cuda") or to("cpu")'
    if device == input.placement.device_type:
        return input
    out_placement = flow._oneflow_internal._ReplacePlacementDeviceTag(
        input.placement, device
    )
    sbp = input.sbp
    input_local_tensor = input.to_local()
    device = flow.device(device)
    output_local_tensor = To(False)(input_local_tensor, device, None)
    return output_local_tensor.to_consistent(out_placement, sbp)


@register_tensor_op("to")
def to_op(input, *args, **kwargs):
    """Performs Tensor dtype and/or device conversion. 
        A flow.dtype and flow.device are inferred from the arguments of `input.to(*args, **kwargs)`.
    
    .. note::
        If the ``input`` Tensor already
        has the correct :class:`flow.dtype` and :class:`flow.device`, then ``input`` is returned.
        Otherwise, the returned tensor is a copy of ``input`` with the desired.

    Args:
        input (oneflow.Tensor): An input tensor.
        *args (oneflow.Tensor or oneflow.device or oneflow.dtype): Positional arguments
        **kwargs (oneflow.device or oneflow.dtype) : Key-value arguments

    Returns:
        oneflow.Tensor: A Tensor.
    
    For example:

    .. code-block:: python

        >>> import numpy as np
        >>> import oneflow as flow
        
        >>> arr = np.random.randint(1, 9, size=(1, 2, 3, 4))
        >>> input = flow.Tensor(arr)
        >>> output = input.to(dtype=flow.float32)
        >>> np.array_equal(arr.astype(np.float32), output.numpy())
        True

    """
    copy = kwargs.get("copy", False)
    device = kwargs.get("device", None)
    dtype = kwargs.get("dtype", None)
    if input.is_consistent:
        input.check_meta_consistency()
        if len(args) > 0:
            assert args[0] in (
                "cuda",
                "cpu",
            ), 'consistent tensor only support to("cuda") or to("cpu")'
            return ConsistentTo(input, args[0])
        if device in ("cuda", "cpu"):
            return ConsistentTo(input, device)
        raise TypeError("to() received an invalid combination of arguments")

    if len(args) > 0:
        if isinstance(args[0], flow.Tensor):
            if len(args) == 2:
                copy = args[1]
            return To(copy)(input, args[0].device, args[0].dtype)
        elif isinstance(args[0], flow.dtype):
            if len(args) == 2:
                copy = args[1]
            return To(copy)(input, None, args[0])
        else:
            device = flow.device(args[0]) if isinstance(args[0], str) else args[0]
            if len(args) > 1:
                dtype = args[1]
                assert isinstance(dtype, flow.dtype)
            if len(args) > 2:
                copy = args[2]
            assert isinstance(device, flow.device)
            return To(copy)(input, device, dtype)
    if isinstance(device, flow.device) or isinstance(dtype, flow.dtype):
        return To(copy)(input, device, dtype)
    raise TypeError("to() received an invalid combination of arguments")


if __name__ == "__main__":
    import doctest

    doctest.testmod(raise_on_error=True)
