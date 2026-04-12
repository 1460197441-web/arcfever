<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">我的仪器</view>
      <view class="hero-title small">管理你自己发布的设备</view>
      <view class="hero-copy">这里只显示你自己发布的仪器，没有就显示空状态，不再用示例设备占位。</view>
    </view>

    <view v-if="!list.length" class="section">
      <view class="card">
        <view class="empty-title">你还没有发布过仪器</view>
        <view class="empty-copy">当前就是空的，等你自己发布第一台仪器后，这里才会出现列表。</view>
      </view>
    </view>

    <view v-else class="section list-stack">
      <view v-for="item in list" :key="item.id" class="card">
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
  const res = await callService('getMyInstruments')
  list.value = res.list
}

onMounted(loadData)
onShow(loadData)
</script>
