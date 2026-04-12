<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">购物车</view>
      <view class="hero-title small">统一管理待结算仪器</view>
    </view>

    <view v-if="!list.length" class="empty-state">购物车里还没有仪器。</view>

    <view v-else class="section list-stack">
      <view v-for="item in list" :key="item.id" class="card">
        <view class="feature-top">
          <view>
            <view class="feature-title">{{ item.instrument.name }}</view>
            <view class="meta-text">{{ item.tradeMode }} · {{ item.instrument.school }}</view>
          </view>
          <view class="feature-price">{{ item.instrument.priceLabel }}</view>
        </view>
        <view class="action-group top-gap">
          <view class="soft-button" @tap="removeItem(item.id)">移除</view>
          <view class="primary-btn" @tap="settle(item)">去结算</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { callService } from '../../common/service'

const list = ref([])

async function loadData() {
  const res = await callService('getCart')
  list.value = res.list
}

onMounted(loadData)
onShow(loadData)

async function removeItem(id) {
  await callService('removeCartItem', { id })
  loadData()
}

function settle(item) {
  uni.navigateTo({ url: `/pages/order-confirm/index?instrumentId=${item.instrumentId}&tradeMode=${item.tradeMode}` })
}
</script>
