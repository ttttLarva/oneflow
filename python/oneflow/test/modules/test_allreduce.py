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
import os
import unittest

import numpy as np

import oneflow as flow
import oneflow.unittest


@unittest.skipIf(os.getenv("ONEFLOW_TEST_CPU_ONLY"), "only test cpu cases")
class TestAllReduce(flow.unittest.TestCase):
    @flow.unittest.skip_unless_1n2d()
    def test_all_reduce(test_case):
        arr_rank1 = np.array([1, 2])
        arr_rank2 = np.array([3, 4])
        if flow.distributed.get_rank() == 0:
            x = flow.Tensor(arr_rank1)
        elif flow.distributed.get_rank() == 1:
            x = flow.Tensor(arr_rank2)
        else:
            raise ValueError
        x = x.to(f"cuda:{flow.distributed.get_local_rank()}")
        nccl_allreduce_op = (
            flow.builtin_op("eager_nccl_all_reduce")
            .Input("in")
            .Output("out")
            .Attr("parallel_conf", f'device_tag: "gpu", device_name: "0:0-1"')
            .Build()
        )
        y = nccl_allreduce_op(x)[0]
        test_case.assertTrue(np.allclose(y.numpy(), arr_rank1 + arr_rank2))

    @flow.unittest.skip_unless_2n2d()
    def test_all_reduce_2nodes(test_case):
        np_arr = np.array([1, 2])
        x = flow.Tensor(np_arr * flow.distributed.get_rank())
        x = x.to(f"cuda:{flow.distributed.get_local_rank()}")
        nccl_allreduce_op = (
            flow.builtin_op("eager_nccl_all_reduce")
            .Input("in")
            .Output("out")
            .Attr("parallel_conf", f'device_tag: "gpu", device_name: "0-1:0-1"')
            .Build()
        )
        y = nccl_allreduce_op(x)[0]
        test_case.assertTrue(np.allclose(y.numpy(), np_arr * 10))


if __name__ == "__main__":
    unittest.main()
