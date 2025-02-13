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
#include "oneflow/core/actor/compute_actor.h"

namespace oneflow {

class AccCompActor final : public CompActor {
 public:
  OF_DISALLOW_COPY_AND_MOVE(AccCompActor);
  AccCompActor() = default;
  ~AccCompActor() override = default;

 private:
  void Act() override;
  void VirtualAsyncSendNaiveProducedRegstMsgToConsumer() override;

  void VirtualCompActorInit(const TaskProto& proto) override;
  void Init(const TaskProto&, int32_t max_acc_cnt);

  std::function<void(DeviceCtx*, void* dst, const void* src, size_t)> cpy_func_;
  int32_t acc_cnt_;
  int32_t max_acc_cnt_;
};

void AccCompActor::VirtualCompActorInit(const TaskProto& proto) {
  const Shape& in_time_shape = Global<RegstMgr>::Get()
                                   ->RegstDesc4RegstDescId(Name2SoleRegstDescId("in"))
                                   .data_regst_time_shape();
  const Shape& out_time_shape = Global<RegstMgr>::Get()
                                    ->RegstDesc4RegstDescId(Name2SoleRegstDescId("out"))
                                    .data_regst_time_shape();
  CHECK_GE(in_time_shape.elem_cnt(), out_time_shape.elem_cnt());
  Init(proto, in_time_shape.elem_cnt() / out_time_shape.elem_cnt());
}

void AccCompActor::Init(const TaskProto& task_proto, int32_t max_acc_cnt) {
  using namespace std::placeholders;
  if (GetDeviceType() == DeviceType::kCPU) {
    cpy_func_ = std::bind(Memcpy<DeviceType::kCPU>, _1, _2, _3, _4);
  } else {
#ifdef WITH_CUDA
    cpy_func_ = std::bind(Memcpy<DeviceType::kGPU>, _1, _2, _3, _4);
#else
    UNIMPLEMENTED();
#endif
  }
  OF_SET_MSG_HANDLER(&AccCompActor::HandlerNormal);
  acc_cnt_ = 0;
  max_acc_cnt_ = max_acc_cnt;
}

void AccCompActor::Act() {
  Regst* out_regst = GetNaiveCurWriteable("out");
  Regst* in_regst = GetNaiveCurReadable("in");
  KernelCtx kernel_ctx = GenDefaultKernelCtx();
  if (acc_cnt_ == 0) {
    const Blob* in_blob = in_regst->GetMutSoleBlob();
    Blob* out_blob = out_regst->GetMutSoleBlob();
    if (GetDeviceType() == DeviceType::kCPU) {
      Memcpy<DeviceType::kCPU>(kernel_ctx.device_ctx, out_blob->ForceMutDptr(), in_blob->dptr(),
                               out_blob->ByteSizeOfBlobBody());
    } else if (GetDeviceType() == DeviceType::kGPU) {
#ifdef WITH_CUDA
      Memcpy<DeviceType::kGPU>(kernel_ctx.device_ctx, out_blob->ForceMutDptr(), in_blob->dptr(),
                               out_blob->ByteSizeOfBlobBody());
#else
      UNIMPLEMENTED();
#endif
    } else {
      UNIMPLEMENTED();
    }
  } else {
    AsyncLaunchKernel(kernel_ctx);
  }
  acc_cnt_ += 1;
}

void AccCompActor::VirtualAsyncSendNaiveProducedRegstMsgToConsumer() {
  if (acc_cnt_ == max_acc_cnt_) {
    HandleProducedNaiveDataRegstToConsumer();
    acc_cnt_ = 0;
  }
}

REGISTER_ACTOR(TaskType::kAcc, AccCompActor);

}  // namespace oneflow
