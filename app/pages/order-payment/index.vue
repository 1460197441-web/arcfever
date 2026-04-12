<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">支付</view>
      <view class="hero-title small">发起 App 支付</view>
      <view class="hero-copy">真实上线时，这里会接入微信 App 支付或支付宝 App 支付。当前工程默认保留演示支付和真实支付两种模式切换。</view>
    </view>

    <view class="detail-block">
      <view class="block-card">
        <view class="row-between">
          <text class="row-label">订单号</text>
          <text class="row-value">{{ paymentInfo.orderId }}</text>
        </view>
        <view class="row-between">
          <text class="row-label">支付金额</text>
          <text class="row-value">¥{{ paymentInfo.amount }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="primary-btn full-btn" @tap="payNow">立即支付</view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'
import { launchPayment } from '../../common/payment'

const orderId = ref('')
const paymentInfo = ref({})

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  orderId.value = current && current.options ? current.options.orderId : ''
  paymentInfo.value = await callService('getPaymentInfo', { orderId: orderId.value })
})

async function payNow() {
  await launchPayment(paymentInfo.value)
  await callService('confirmPayment', { orderId: orderId.value })
  uni.redirectTo({ url: `/pages/order-success/index?orderId=${orderId.value}` })
}
</script>
