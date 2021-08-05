import unittest
from collections import OrderedDict

import numpy as np
from numpy.core.defchararray import center

import oneflow as flow
import oneflow.unittest


@flow.unittest.skip_unless_1n1d()
def compare_with_numpy_rmsprop(
    test_case,
    device,
    x_shape,
    scale,
    learning_rate,
    momentum,
    train_iters,
    alpha,
    eps,
    weight_decay,
    centered,
):
    random_grad_seq = []
    for _ in range(train_iters):
        random_grad_seq.append(np.random.uniform(
            size=x_shape).astype(np.float32))
    init_value = np.random.uniform(size=x_shape).astype(np.float32)

    class CustomModel(flow.nn.Module):
        def __init__(self):
            super().__init__()
            self.param0 = flow.nn.Parameter(flow.Tensor(init_value, device=flow.device(device)))

        def forward(self, mask):
            return self.param0 * mask

    simp_module = CustomModel()
    simp_module.to(flow.device(device))
    simp_module.train()

    rmsprop0 = flow.optim.RMSprop(
        [
            {
                "params": simp_module.parameters(),
                "lr": learning_rate,
                "alpha": alpha,
                "eps": eps,
                "weight_decay": weight_decay,
                "momentum": momentum,
                "centered": centered,
                "scale": scale,
            }
        ]
    )

    class CustomRMSpropGraph(flow.nn.Graph):
        def __init__(self):
            super().__init__()
            self.m = simp_module
            self.add_optimizer("rmsprop", rmsprop0)

        def build(self, mask_tensor):
            loss = flow.sum(self.m(mask_tensor))
            loss.backward()
            return loss

    of_res_list = []
    rmsprop_graph = CustomRMSpropGraph()

    for i in range(train_iters):
        mask_tensor = flow.Tensor(
            random_grad_seq[i], requires_grad=False, device=flow.device(device))
        rmsprop_x = rmsprop_graph(mask_tensor)

        of_res_list.append(simp_module.param0.numpy())

    np_res_list = []

    def train_by_numpy():
        x = init_value
        r = np.zeros_like(x)
        v = np.zeros_like(x)
        g = np.zeros_like(x)

        def np_train_one_iter(grad):
            # ref to: https://github.com/Oneflow-Inc/oneflow/blob/master/python/oneflow/test/modules/test_optim_rmsprop.py#L78-L99
            if weight_decay != 0:
                grad = grad + weight_decay * x
            grad = grad * scale
            if centered:
                r_ = alpha * r + (1 - alpha) * grad * grad
                g_ = alpha * g + (1 - alpha) * grad
                v_ = momentum * v + learning_rate / \
                    np.sqrt(r_ - g_ * g_ + eps) * grad
            else:
                r_ = alpha * r + (1 - alpha) * grad * grad
                g_ = g
                v_ = momentum * v + learning_rate / np.sqrt(r_ + eps) * grad
            param = x - v_
            return (param, r_, g_, v_)

        from ipdb import set_trace; set_trace()
        for i in range(train_iters):
            (x, r, g, v) = np_train_one_iter(random_grad_seq[i])
            np_res_list.append(x)
        return x

    train_by_numpy()

    test_case.assertTrue(
        np.allclose(of_res_list, np_res_list, rtol=1e-4, atol=1e-4)
    )


@flow.unittest.skip_unless_1n1d()
class TestRMSprop(flow.unittest.TestCase):
    def test_rmsprop1(test_case):
        compare_with_numpy_rmsprop(test_case,
                                   device="cuda",
                                   x_shape=(1,),
                                   scale=1.0,
                                   learning_rate=0.1,
                                   momentum=0.,
                                   train_iters=20,
                                   alpha=0.,
                                   eps=1e-8,
                                   weight_decay=0.,
                                   centered=True,
                                   )

    def test_rmsprop2(test_case):
        compare_with_numpy_rmsprop(test_case,
                                   device="cuda",
                                   x_shape=(1,),
                                   scale=1.0,
                                   learning_rate=0.1,
                                   momentum=0.,
                                   train_iters=20,
                                   alpha=0.,
                                   eps=1e-8,
                                   weight_decay=0.,
                                   centered=False,
                                   )

    def test_rmsprop3(test_case):
        compare_with_numpy_rmsprop(test_case,
                                   device="cuda",
                                   x_shape=(1,),
                                   scale=1.0,
                                   learning_rate=0.1,
                                   momentum=0.9,
                                   train_iters=20,
                                   alpha=0.99,
                                   eps=1e-8,
                                   weight_decay=0.0005,
                                   centered=True,
                                   )

    def test_rmsprop4(test_case):
        compare_with_numpy_rmsprop(test_case,
                                   device="cuda",
                                   x_shape=(1,),
                                   scale=1.0,
                                   learning_rate=0.1,
                                   momentum=0.9,
                                   train_iters=20,
                                   alpha=0.99,
                                   eps=1e-8,
                                   weight_decay=0.0005,
                                   centered=False,
                                   )


if __name__ == "__main__":
    unittest.main()
