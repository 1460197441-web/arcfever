<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-gradient">
        <view class="hero-chip">Save this moment</view>
        <view class="hero-title small">Add Memory</view>
        <view class="hero-copy">Wrap the place, the date, the photos, and the feeling into one soft pink candy card.</view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card form-card">
        <view class="field-label">Title</view>
        <input v-model="form.title" class="input-soft" placeholder="A sweet little afternoon" />

        <view class="field-label top-gap">Date</view>
        <input v-model="form.date" class="input-soft" placeholder="2026-04-10" />

        <view class="field-label top-gap">Place</view>
        <input v-model="form.place" class="input-soft" placeholder="Jingan" />

        <view class="field-label top-gap">Note</view>
        <textarea v-model="form.note" class="textarea-soft" placeholder="Write a soft little note about this day..." />

        <view class="field-label top-gap">Photo stickers</view>
        <view class="poster-grid">
          <view v-for="item in photos" :key="item" class="polaroid">
            <image class="polaroid-image" :src="item" mode="aspectFill" />
          </view>
        </view>

        <view class="button-row top-gap">
          <view class="secondary-btn">Pick photos</view>
          <view class="secondary-btn">Use location</view>
        </view>

        <view class="primary-btn full-btn top-gap">Save memory</view>
      </view>
    </view>

    <BottomTabBar current="/pages/publish/index" />
  </view>
</template>

<script setup>
import { reactive } from 'vue'
import BottomTabBar from '../../components/BottomTabBar.vue'

const form = reactive({
  title: '',
  date: '2026-04-10',
  place: '',
  note: ''
})

const photos = [
  'https://images.unsplash.com/photo-1518199266791-5375a83190b7?q=80&w=800&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=800&auto=format&fit=crop'
]
</script>

<style scoped lang="scss">
@import '../../common/theme.scss';

.form-card {
  padding: 28rpx;
}

.button-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}
</style>
