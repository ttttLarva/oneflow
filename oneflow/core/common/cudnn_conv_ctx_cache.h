#ifndef ONEFLOW_CORE_COMMON_CUDNN_CONV_CTX_CACHE_H_
#define ONEFLOW_CORE_COMMON_CUDNN_CONV_CTX_CACHE_H_

#ifdef WITH_CUDA

#include "oneflow/core/device/cudnn_util.h"
#include "oneflow/core/register/blob_desc.h"

namespace oneflow {

struct CudnnConvAlgoCtx final {
  cudnnConvolutionFwdAlgo_t fwd_algo;
  cudnnConvolutionBwdFilterAlgo_t bwd_filter_algo;
  cudnnConvolutionBwdDataAlgo_t bwd_data_algo;
  size_t fwd_ws_size;
  size_t bwd_filter_ws_size;
  size_t bwd_data_ws_size;
};

class CudnnConvCtxCache final {
 public:
  OF_DISALLOW_COPY_AND_MOVE(CudnnConvCtxCache);
  CudnnConvCtxCache() = default;
  ~CudnnConvCtxCache() = default;

  bool FindCudnnConvAlgoCtxWithConfig(const BlobDesc& in_desc, const BlobDesc& out_desc,
                                      const BlobDesc& filter_desc, const std::string& format,
                                      CudnnConvAlgoCtx* conv_algo_ctx) const;
  void AddCudnnConvAlgoCtxWithConfig(const BlobDesc& in_desc, const BlobDesc& out_desc,
                                     const BlobDesc& filter_desc, const std::string& format,
                                     const CudnnConvAlgoCtx& conv_algo_ctx);

 private:
  friend class Global<CudnnConvCtxCache>;
  std::string GetKey(const BlobDesc& in_desc, const BlobDesc& out_desc, const BlobDesc& filter_desc,
                     const std::string& format) const;

  HashMap<std::string, CudnnConvAlgoCtx> conv_config2algo_ctx_;
};

}  // namespace oneflow

#endif  // WITH_CUDA

#endif  // ONEFLOW_CORE_COMMON_CUDNN_CONV_CTX_CACHE_H_
