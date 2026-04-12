<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">交易完成</view>
      <view class="hero-title">支付成功</view>
      <view class="hero-copy">订单 {{ orderId }} 已完成支付，后续可在订单列表查看状态。</view>
      <view class="hero-actions">
        <view class="primary-btn" @tap="goOrderList">查看订单</view>
        <view class="ghost-btn" @tap="goHome">返回首页</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const orderId = ref('')

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  orderId.value = current && current.options && current.options.orderId ? current.options.orderId : ''
})

function goOrderList() {
  uni.redirectTo({ url: '/pages/order-list/index' })
}

function goHome() {
  uni.reLaunch({ url: '/pages/home/index' })
}
</script>
