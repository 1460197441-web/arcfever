<template>
  <view class="page-shell">
    <view v-if="loading" class="loading-state">正在加载项目...</view>

    <view v-else-if="project" class="hero-panel">
      <view class="hero-title small">{{ project.title }}</view>
      <view class="hero-copy">{{ project.domain }} · {{ project.owner }}</view>
      <view class="chip-row top-gap">
        <view v-for="item in project.targetRoles" :key="item" class="chip">{{ item }}</view>
      </view>
    </view>

    <view v-else class="section">
      <view class="card empty-panel">
        <view class="empty-title">项目不存在或已结束</view>
        <view class="empty-copy">当前链接可能已失效，你可以返回项目协作页查看最新需求。</view>
      </view>
    </view>

    <view v-if="project" class="section list-stack">
      <view class="card">
        <view class="section-title">项目信息</view>
        <view class="feature-copy">预算区间：{{ project.budget }}</view>
        <view class="feature-copy">合作周期：{{ project.duration }}</view>
      </view>
      <view class="card">
        <view class="section-title">评估维度</view>
        <view class="feature-copy">硬指标：{{ project.evaluation.hard }}</view>
        <view class="feature-copy">软评价：{{ project.evaluation.soft }}</view>
      </view>
      <view class="card">
        <view class="section-title">推荐人才</view>
        <view v-for="item in project.matches" :key="item.name" class="feature-copy">{{ item.name }} · {{ item.title }} · {{ item.score }} 分</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const loading = ref(true)
const project = ref(null)

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const projectId = current && current.options ? current.options.id : ''
  const res = await callService('getProjectDetail', { id: projectId })
  project.value = res.project || null
  loading.value = false
})
</script>
