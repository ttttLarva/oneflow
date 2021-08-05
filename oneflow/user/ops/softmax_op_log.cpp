/*
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
*/
#include "oneflow/core/framework/framework.h"

namespace oneflow {

namespace {

REGISTER_USER_OP("logsoftmax")
    .Input("in")
    .Output("prob")
    .Output("out")
    .SetTensorDescInferFn([](user_op::InferContext* ctx) -> Maybe<void> {
      *ctx->OutputShape("out", 0) = ctx->InputShape("in", 0);
      *ctx->OutputShape("prob",0) = ctx->InputShape("in", 0);
      return Maybe<void>::Ok();
    })
    .SetGetSbpFn([](user_op::SbpContext* ctx) -> Maybe<void> {
      const user_op::TensorDesc& in_tensor = ctx->LogicalTensorDesc4InputArgNameAndIndex("in", 0);
      FOR_RANGE(int64_t, axis, 0, in_tensor.shape().NumAxes() - 1) {
        ctx->NewBuilder()
            .Split(user_op::OpArg("in", 0), axis)
            .Split(user_op::OpArg("prob", 0), axis)
            .Split(user_op::OpArg("out", 0), axis)
            .Build();
      }
      return Maybe<void>::Ok();
    })
    .SetDataTypeInferFn([](user_op::InferContext* ctx) -> Maybe<void> {
        *ctx->OutputDType("prob", 0) = ctx->InputDType("in", 0);
      *ctx->OutputDType("out", 0) = ctx->InputDType("in", 0);
      return Maybe<void>::Ok();
    });

REGISTER_USER_OP("logsoftmax_grad")
    .Input("prob")
    .Input("dy")
    .Output("dx")
    .SetTensorDescInferFn([](user_op::InferContext* ctx) -> Maybe<void> {
      const Shape& y_shape = ctx->InputShape("prob", 0);
      const Shape& dy_shape = ctx->InputShape("dy", 0);
      Shape* dx_shape = ctx->OutputShape("dx", 0);
      CHECK_OR_RETURN(dy_shape == y_shape);
      *dx_shape = dy_shape;
      return Maybe<void>::Ok();
    })
    .SetDataTypeInferFn([](user_op::InferContext* ctx) -> Maybe<void> {
      CHECK_EQ_OR_RETURN(ctx->InputDType("prob", 0), ctx->InputDType("dy", 0));
      *ctx->OutputDType("dx", 0) = ctx->InputDType("prob", 0);
      return Maybe<void>::Ok();
    })
    .SetGetSbpFn([](user_op::SbpContext* ctx) -> Maybe<void> {
      const user_op::TensorDesc& y_tensor = ctx->LogicalTensorDesc4InputArgNameAndIndex("prob", 0);
      FOR_RANGE(int64_t, axis, 0, y_tensor.shape().NumAxes() - 1) {
        ctx->NewBuilder()
            .Split(user_op::OpArg("prob", 0), axis)
            .Split(user_op::OpArg("dy", 0), axis)
            .Split(user_op::OpArg("dx", 0), axis)
            .Build();
      }
      return Maybe<void>::Ok();
    });

REGISTER_USER_OP_GRAD("logsoftmax").SetGenBackwardOpConfFn([](const user_op::UserOpWrapper& op,
                                                           user_op::AddOpFn AddOp) -> Maybe<void> {
  if (op.NeedGenGradTensor4OpInput("in", 0)) {
    user_op::UserOpConfWrapperBuilder builder(op.op_name() + "_grad");
    user_op::UserOpConfWrapper logsoftmax_grad_op =
        builder.Op("logsoftmax_grad")
            .Input("prob", op.output("prob", 0))
            .Input("dy", op.GetGradTensorWithOpOutput("out", 0))
            .Output("dx")
            .Build();
    op.BindGradTensorWithOpInput(logsoftmax_grad_op.output("dx", 0), "in", 0);
    AddOp(logsoftmax_grad_op);
  }
  return Maybe<void>::Ok();
});

}  // namespace

}  // namespace oneflow
