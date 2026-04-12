<template>
  <view class="page-shell">
    <view v-if="!order" class="loading-state">正在加载订单详情...</view>

    <view v-else>
      <view class="hero-panel">
        <view class="hero-tag">订单详情</view>
        <view class="hero-title small">{{ order.instrumentName }}</view>
        <view class="hero-copy">{{ order.id }} · {{ order.createdAt }}</view>
      </view>

      <view class="detail-block">
        <view class="block-card">
          <view class="row-between">
            <text class="row-label">订单状态</text>
            <text class="row-value">{{ order.status }}</text>
          </view>
          <view class="row-between">
            <text class="row-label">交易模式</text>
            <text class="row-value">{{ order.tradeMode }}</text>
          </view>
          <view class="row-between">
            <text class="row-label">买家 / 卖家</text>
            <text class="row-value">{{ order.buyerName }} / {{ order.sellerName }}</text>
          </view>
        </view>
      </view>

      <view class="summary-card">
        <view class="summary-title">费用明细</view>
        <view class="summary-row">
          <text>总额</text>
          <text>¥{{ order.total }}</text>
        </view>
      </view>

      <view class="section list-stack">
        <view class="primary-btn full-btn" @tap="goChat">联系发布方</view>
        <view class="light-btn full-btn" @tap="goAgreement">查看协议</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const order = ref(null)

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const orderId = current && current.options ? current.options.id : ''
  const res = await callService('getOrderDetail', { id: orderId })
  order.value = res.order
})

async function goChat() {
  const res = await callService('ensureInstrumentChat', { instrumentId: order.value.instrumentId })
  uni.navigateTo({ url: `/pages/chat-detail/index?id=${res.chatId}` })
}

function goAgreement() {
  uni.navigateTo({ url: `/pages/agreement/index?instrumentId=${order.value.instrumentId}` })
}
</script>
