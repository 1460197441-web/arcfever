<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">项目协作</view>
      <view class="hero-title small">研发需求、匹配团队与人才评估</view>
      <view class="hero-copy">项目协作页沿用小程序的白底极简结构，把科研合作做成可管理的需求流和候选团队流。</view>
    </view>

    <view class="section chip-row">
      <view v-for="item in filters" :key="item" class="chip" :class="{ active: activeFilter === item }" @tap="activeFilter = item">
        {{ item }}
      </view>
    </view>

    <view class="feed-list">
      <view v-for="(item, index) in filteredList" :key="item.id" class="feed-item" @tap="openProject(item.id)">
        <view class="author-row">
          <view class="author-left">
            <view class="avatar" :class="`a${(index % 4) + 1}`"></view>
            <view>
              <view class="author-name-row">
                <text class="author-name">{{ item.owner }}</text>
                <view class="verify-badge" :class="{ green: index % 2 === 1 }">V</view>
              </view>
              <text class="author-inst">{{ item.domain }} · 协作需求发起方</text>
            </view>
          </view>
        </view>

        <view class="poster-box square">
          <view class="poster-bg" :class="`poster-theme-${(index % 4) + 1}`"></view>
          <view class="poster-content">
            <view class="poster-topline">
              <view class="remote-pill">{{ item.domain }}</view>
              <view class="price-chip">{{ item.status }}</view>
            </view>
            <view>
              <view class="poster-title">{{ item.title }}</view>
              <view class="poster-meta">{{ item.budget }} · {{ item.duration }}</view>
            </view>
          </view>
        </view>

        <view class="desc-block" style="margin-top: 18rpx;">
          <text class="desc-strong">{{ item.owner }}</text>
          <text>{{ item.intro }}</text>
        </view>
        <view class="chip-row top-gap">
          <view v-for="keyword in item.keywords" :key="keyword" class="chip">{{ keyword }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const filters = ref(['全部'])
const list = ref([])
const activeFilter = ref('全部')

const filteredList = computed(() => (activeFilter.value === '全部' ? list.value : list.value.filter((item) => item.domain === activeFilter.value)))

onMounted(async () => {
  const res = await callService('getProjects')
  filters.value = res.filters
  list.value = res.list
})

function openProject(id) {
  uni.navigateTo({ url: `/pages/project-detail/index?id=${id}` })
}
</script>
