<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">订单列表</view>
      <view class="hero-title small">查看租赁、买断和远程实验进度</view>
    </view>

    <view class="section list-stack">
      <view v-for="item in list" :key="item.id" class="card" @tap="openOrder(item.id)">
        <view class="feature-top">
          <view>
            <view class="feature-title">{{ item.instrumentName }}</view>
            <view class="meta-text">{{ item.tradeMode }} · {{ item.id }}</view>
          </view>
          <view class="badge">{{ item.status }}</view>
        </view>
        <view class="feature-copy">{{ item.createdAt }}</view>
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
  const res = await callService('getOrderList')
  list.value = res.list
}

onMounted(loadData)
onShow(loadData)

function openOrder(id) {
  uni.navigateTo({ url: `/pages/order-detail/index?id=${id}` })
}
</script>
