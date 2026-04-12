<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-gradient">
        <view class="hero-chip">Memory bubbles</view>
        <view class="hero-title small">Map / Globe</view>
        <view class="hero-copy">A dreamy map surface for the places you visited together, with glowing little memory bubbles.</view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card switch-card">
        <view class="switch-row">
          <view class="tag-pill active">Map</view>
          <view class="tag-pill">Globe</view>
        </view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card map-card">
        <view class="map-surface">
          <view
            v-for="bubble in bubbles"
            :key="bubble.title"
            class="bubble-anchor"
            :style="{ left: bubble.left, top: bubble.top }"
          >
            <view class="memory-bubble"></view>
            <view class="bubble-label">
              <text class="bubble-title">{{ bubble.title }}</text>
              <text class="bubble-date">{{ bubble.date }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card love-sheet">
        <view class="panel-title">Recent memory bubbles</view>
        <view v-for="item in bubbles" :key="item.title" class="bubble-line">
          <view class="bubble-dot"></view>
          <view class="bubble-copy">
            <view class="feature-title">{{ item.place }}</view>
            <view class="meta-text">{{ item.date }} · {{ item.title }}</view>
            <view class="sub-copy">{{ item.note }}</view>
          </view>
        </view>
      </view>
    </view>

    <BottomTabBar current="/pages/messages/index" />
  </view>
</template>

<script setup>
import BottomTabBar from '../../components/BottomTabBar.vue'

const bubbles = [
  {
    title: 'Strawberry dessert',
    place: 'Jingan',
    date: '2026-04-10',
    note: 'This bubble holds sugar, sunlight, and a very soft afternoon.',
    left: '24%',
    top: '34%'
  },
  {
    title: 'Night walk',
    place: 'Riverside',
    date: '2026-04-08',
    note: 'The breeze felt gentle and the city looked like it was helping us fall in love again.',
    left: '68%',
    top: '54%'
  }
]
</script>

<style scoped lang="scss">
@import '../../common/theme.scss';

.switch-card,
.map-card {
  padding: 24rpx;
}

.map-surface {
  height: 620rpx;
  border-radius: 30rpx;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 240, 247, 0.92) 0%, rgba(242, 231, 255, 0.86) 100%);
}

.bubble-anchor {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.memory-bubble {
  width: 36rpx;
  height: 36rpx;
  border-radius: 999rpx;
  background: rgba(255, 111, 174, 0.95);
  border: 6rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10rpx 28rpx rgba(243, 168, 210, 0.28);
}

.bubble-label {
  min-width: 120rpx;
  max-width: 180rpx;
  padding: 12rpx 16rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 1rpx solid rgba(255, 255, 255, 0.7);
}

.bubble-title {
  display: block;
  color: #6c4a7e;
  font-size: 20rpx;
  font-weight: 800;
}

.bubble-date {
  display: block;
  margin-top: 4rpx;
  color: #9b86a6;
  font-size: 18rpx;
}

.bubble-line {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  margin-top: 18rpx;
}

.bubble-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 999rpx;
  margin-top: 10rpx;
  background: #ff6fae;
  box-shadow: 0 8rpx 18rpx rgba(243, 168, 210, 0.26);
}

.bubble-copy {
  flex: 1;
}
</style>
