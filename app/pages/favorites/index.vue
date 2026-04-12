<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">我的收藏</view>
      <view class="hero-title small">把高意向设备收进收藏夹</view>
    </view>

    <view v-if="!list.length" class="empty-state">还没有收藏任何仪器。</view>

    <view v-else class="section list-stack">
      <view v-for="item in list" :key="item.id" class="card" @tap="openInstrument(item.id)">
        <view class="feature-title">{{ item.name }}</view>
        <view class="feature-copy">{{ item.desc }}</view>
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
  const res = await callService('getFavoriteList')
  list.value = res.list
}

onMounted(loadData)
onShow(loadData)

function openInstrument(id) {
  uni.navigateTo({ url: `/pages/equipment-detail/index?id=${id}` })
}
</script>
