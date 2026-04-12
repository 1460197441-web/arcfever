<template>
  <view class="love-tabbar-shell">
    <view class="love-tabbar">
      <view
        v-for="item in tabs"
        :key="item.path"
        class="love-tab-item"
        :class="{ active: current === item.path, 'love-tab-center': item.key === 'publish' }"
        @tap="switchTab(item.path)"
      >
        <view v-if="item.key === 'publish'" class="fab-core">+</view>
        <view v-else class="love-tab-pill">
          <text class="love-tab-icon">{{ item.icon }}</text>
          <text class="love-tab-text">{{ item.label }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  current: {
    type: String,
    default: ''
  }
})

const tabs = [
  { path: '/pages/home/index', label: 'Feed', key: 'home', icon: '*' },
  { path: '/pages/category/index', label: 'Calendar', key: 'category', icon: 'o' },
  { path: '/pages/publish/index', label: 'Add', key: 'publish', icon: '+' },
  { path: '/pages/messages/index', label: 'Map', key: 'messages', icon: '@' },
  { path: '/pages/profile/index', label: 'Menu', key: 'profile', icon: '~' }
]

function switchTab(path) {
  if (path === props.current) return
  uni.reLaunch({ url: path })
}
</script>

<style scoped lang="scss">
@import '../common/theme.scss';
</style>
