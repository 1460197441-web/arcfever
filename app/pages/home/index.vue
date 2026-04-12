<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-gradient">
        <view class="hero-row">
          <view class="avatar-stack">
            <image class="hero-avatar" src="https://i.pravatar.cc/100?img=32" mode="aspectFill" />
            <image class="hero-avatar" src="https://i.pravatar.cc/100?img=47" mode="aspectFill" />
          </view>
          <view class="hero-chip">Pink bubble mode</view>
        </view>
        <view class="hero-title">Our Love Universe</view>
        <view class="hero-copy">A private little feed for the two of you, filled with soft memories and sweet notes.</view>
        <view class="hero-metric">Day 428 together</view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card composer-card">
        <view class="panel-title">What do you want to remember today?</view>
        <view class="composer-box" @tap="goAdd">
          <text class="composer-icon">*</text>
          <text class="sub-copy">Write a tiny post just for the two of you...</text>
        </view>
      </view>
    </view>

    <view class="section top-gap">
      <view v-for="post in posts" :key="post.id" class="glass-card post-card">
        <view class="post-top">
          <view class="post-user">
            <image class="post-avatar" :src="post.avatar" mode="aspectFill" />
            <view>
              <view class="feature-title">{{ post.name }}</view>
              <view class="meta-text">{{ post.time }}</view>
            </view>
          </view>
          <view class="mood-chip">{{ post.mood }}</view>
        </view>

        <view class="post-copy">{{ post.content }}</view>

        <view class="poster-grid top-gap">
          <view v-for="img in post.images" :key="img" class="polaroid">
            <image class="polaroid-image" :src="img" mode="aspectFill" />
          </view>
        </view>

        <view class="post-meta">
          <text class="meta-text">Place: {{ post.place }}</text>
          <text class="meta-highlight">{{ post.tag }}</text>
        </view>

        <view class="post-actions">
          <view class="soft-button action-pill">Heart it</view>
          <view class="soft-button action-pill">Reply</view>
        </view>
      </view>
    </view>

    <BottomTabBar current="/pages/home/index" />
  </view>
</template>

<script setup>
import BottomTabBar from '../../components/BottomTabBar.vue'

const posts = [
  {
    id: '1',
    name: 'You',
    time: 'Today 14:20',
    mood: 'Sweet',
    place: 'Jingan',
    tag: 'Dessert date',
    avatar: 'https://i.pravatar.cc/100?img=32',
    content: 'I missed you again today, so I wanted to save this dessert moment. The sunlight by the window felt extra soft.',
    images: [
      'https://images.unsplash.com/photo-1518199266791-5375a83190b7?q=80&w=800&auto=format&fit=crop',
      'https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?q=80&w=800&auto=format&fit=crop'
    ]
  },
  {
    id: '2',
    name: 'Her',
    time: 'Yesterday 21:06',
    mood: 'Need a hug',
    place: 'Riverside',
    tag: 'Night walk',
    avatar: 'https://i.pravatar.cc/100?img=47',
    content: 'The evening breeze felt so good. I want another slow walk together, with lights, wind, and tiny pink bubbles everywhere.',
    images: [
      'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=800&auto=format&fit=crop'
    ]
  }
]

function goAdd() {
  uni.reLaunch({ url: '/pages/publish/index' })
}
</script>

<style scoped lang="scss">
@import '../../common/theme.scss';

.composer-card,
.post-card {
  padding: 28rpx;
}

.composer-box {
  margin-top: 18rpx;
  min-height: 88rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.72);
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 0 22rpx;
}

.composer-icon {
  color: #ff6fae;
  font-size: 28rpx;
  font-weight: 800;
}

.post-top,
.post-user,
.post-meta,
.post-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.post-user {
  justify-content: flex-start;
}

.post-avatar {
  width: 82rpx;
  height: 82rpx;
  border-radius: 999rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.86);
}

.post-copy {
  margin-top: 18rpx;
  color: #6c4a7e;
  font-size: 26rpx;
  line-height: 1.8;
}

.mood-chip {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #ffe3f1;
  color: #ff6fae;
  font-size: 22rpx;
  font-weight: 700;
}

.post-meta {
  margin-top: 18rpx;
}

.meta-highlight {
  color: #ff6fae;
  font-size: 22rpx;
  font-weight: 700;
}

.post-actions {
  margin-top: 20rpx;
}

.action-pill {
  flex: 1;
  min-height: 82rpx;
}
</style>
