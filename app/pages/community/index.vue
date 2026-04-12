<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">科研社区</view>
      <view class="hero-title small">仪器经验、协作记录与真实交流</view>
      <view class="hero-copy">社区模块延续小程序的科研专业感，让仪器交易不只是撮合，还能沉淀方法论和信任内容。</view>
    </view>

    <view class="section chip-row">
      <view v-for="tag in tags" :key="tag" class="chip" :class="{ active: activeTag === tag }" @tap="activeTag = tag">
        {{ tag }}
      </view>
    </view>

    <view class="feed-list">
      <view v-for="(item, index) in filteredList" :key="item.id" class="feed-item" @tap="openPost(item.id)">
        <view class="author-row">
          <view class="author-left">
            <view class="avatar" :class="`a${(index % 4) + 1}`"></view>
            <view>
              <view class="author-name-row">
                <text class="author-name">{{ item.author }}</text>
                <view class="verify-badge">V</view>
              </view>
              <text class="author-inst">科研社区作者 · {{ item.tag }}</text>
            </view>
          </view>
        </view>

        <view class="poster-box square">
          <view class="poster-bg" :class="`poster-theme-${(index % 4) + 1}`"></view>
          <view class="poster-content">
            <view class="poster-topline">
              <view class="remote-pill">{{ item.tag }}</view>
              <view class="price-chip">{{ item.likes }} 赞</view>
            </view>
            <view>
              <view class="poster-title">{{ item.title }}</view>
              <view class="poster-meta">{{ item.comments }} 条评论 · 方法经验沉淀</view>
            </view>
          </view>
        </view>

        <view class="desc-block" style="margin-top: 18rpx;">
          <text class="desc-strong">{{ item.author }}</text>
          <text>{{ item.excerpt }}</text>
        </view>
        <view class="time-note">科研社区 · 内容可沉淀为后续合作信任记录</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const tags = ref(['全部'])
const list = ref([])
const activeTag = ref('全部')

const filteredList = computed(() => (activeTag.value === '全部' ? list.value : list.value.filter((item) => item.tag === activeTag.value)))

onMounted(async () => {
  const res = await callService('getCommunity')
  tags.value = res.tags
  list.value = res.list
})

function openPost(id) {
  uni.navigateTo({ url: `/pages/post-detail/index?id=${id}` })
}
</script>
