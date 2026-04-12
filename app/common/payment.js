import env from './env'

export async function launchPayment(paymentInfo) {
  if (env.paymentMode === 'live' && paymentInfo && paymentInfo.provider && paymentInfo.orderInfo) {
    return new Promise((resolve, reject) => {
      uni.requestPayment({
        provider: paymentInfo.provider,
        orderInfo: paymentInfo.orderInfo,
        success: resolve,
        fail: reject
      })
    })
  }

  return Promise.resolve({
    mode: env.paymentMode,
    message: '当前为演示支付模式，已模拟支付成功。'
  })
}
