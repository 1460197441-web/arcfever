<template>
  <view class="page-shell">
    <view v-if="loading" class="loading-state">正在加载文章...</view>

    <view v-else-if="post" class="hero-panel">
      <view class="chip">{{ post.tag }}</view>
      <view class="hero-title small">{{ post.title }}</view>
      <view class="hero-copy">{{ post.author }} · {{ post.likes }} 赞 · {{ post.comments }} 评论</view>
    </view>

    <view v-else class="section">
      <view class="card empty-panel">
        <view class="empty-title">文章不存在或已下线</view>
        <view class="empty-copy">当前分享内容可能已失效，你可以返回社区页查看最新内容。</view>
      </view>
    </view>

    <view v-if="post" class="section">
      <view class="card">
        <view class="post-content">{{ post.content }}</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const loading = ref(true)
const post = ref(null)

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const postId = current && current.options ? current.options.id : ''
  const res = await callService('getPostDetail', { id: postId })
  post.value = res.post || null
  loading.value = false
})
</script>
