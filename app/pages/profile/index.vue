<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-gradient">
        <view class="hero-chip">Date menu</view>
        <view class="hero-title small">What should we eat today?</view>
        <view class="hero-copy">A cute little date-night menu board instead of a delivery app, with soft cards and sweet choices.</view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card panel">
        <view class="chip-row">
          <view
            v-for="item in categories"
            :key="item"
            class="category-pill"
            :class="{ active: item === selected }"
            @tap="selected = item"
          >
            {{ item }}
          </view>
        </view>
      </view>
    </view>

    <view class="section top-gap list-stack">
      <view v-for="item in menuList" :key="item.name" class="glass-card menu-card">
        <image class="menu-cover" :src="item.image" mode="aspectFill" />
        <view class="feature-title top-gap">{{ item.name }}</view>
        <view class="chip-row top-gap">
          <view v-for="tag in item.tags" :key="tag" class="mood-chip">{{ tag }}</view>
        </view>
        <view class="menu-meta top-gap">{{ item.price }}</view>
        <view class="sub-copy top-gap">{{ item.craving }}</view>
        <view class="button-row top-gap">
          <view class="secondary-btn">Want this</view>
          <view class="primary-btn">Pick this now</view>
        </view>
      </view>
    </view>

    <BottomTabBar current="/pages/profile/index" />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import BottomTabBar from '../../components/BottomTabBar.vue'

const categories = ['Milk tea', 'Dessert', 'Hotpot', 'BBQ', 'Japanese', 'Korean', 'Late night']
const selected = ref('Milk tea')

const menuList = [
  {
    name: 'Strawberry cloud ice',
    tags: ['Sweet', 'Date mood'],
    price: '$4 - $6',
    craving: 'Craving score 97%',
    image: 'https://images.unsplash.com/photo-1551024601-bec78aea704b?q=80&w=800&auto=format&fit=crop'
  },
  {
    name: 'Late-night hotpot',
    tags: ['Warm', 'Cozy'],
    price: '$12 - $18',
    craving: 'Craving score 95%',
    image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=800&auto=format&fit=crop'
  }
]
</script>

<style scoped lang="scss">
@import '../../common/theme.scss';

.menu-card {
  padding: 24rpx;
}

.menu-cover {
  width: 100%;
  height: 320rpx;
  border-radius: 26rpx;
  background: #f6eefc;
}

.menu-meta {
  color: #ff6fae;
  font-size: 24rpx;
  font-weight: 700;
}

.button-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}
</style>
