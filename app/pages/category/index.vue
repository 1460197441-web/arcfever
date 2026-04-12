<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-gradient">
        <view class="hero-chip">Love journal mode</view>
        <view class="hero-title small">Calendar</view>
        <view class="hero-copy">A soft little journal page for anniversaries, dates, and the days you want to remember forever.</view>
        <view class="hero-metric">Day 428 together</view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card hero-metric-card">
        <view class="helper-note">Next anniversary in 7 days</view>
        <view class="big-number">520 days</view>
        <view class="sub-copy">A good day to add a photo, a note, and one more reason to smile.</view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card calendar-card">
        <view class="calendar-head">
          <text class="calendar-arrow">&lt;</text>
          <text class="panel-title">April 2026</text>
          <text class="calendar-arrow">&gt;</text>
        </view>
        <view class="week-row">
          <text v-for="day in weekDays" :key="day" class="week-label">{{ day }}</text>
        </view>
        <view class="calendar-grid">
          <view
            v-for="day in days"
            :key="day"
            class="day-cell"
            :class="{ active: day === selectedDay, marked: markedDays.includes(day) }"
            @tap="selectedDay = day"
          >
            <text class="day-text">{{ day }}</text>
            <view v-if="markedDays.includes(day)" class="day-dot"></view>
          </view>
        </view>
      </view>
    </view>

    <view class="section top-gap">
      <view class="glass-card note-card">
        <view class="panel-title">Memory on this day</view>
        <view v-if="selectedMemories.length" class="list-stack top-gap">
          <view v-for="item in selectedMemories" :key="item.title" class="memory-line">
            <view class="feature-title">{{ item.title }}</view>
            <view class="meta-text">{{ item.place }}</view>
            <view class="sub-copy">{{ item.note }}</view>
          </view>
        </view>
        <view v-else class="sub-copy top-gap">No note yet for this date. Save it for your next sweet little plan.</view>
      </view>
    </view>

    <BottomTabBar current="/pages/category/index" />
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import BottomTabBar from '../../components/BottomTabBar.vue'

const weekDays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
const days = Array.from({ length: 30 }, (_, index) => index + 1)
const markedDays = [3, 7, 10, 14, 18, 24, 29]
const selectedDay = ref(10)

const memoryMap = {
  10: [
    { title: 'Strawberry dessert', place: 'Jingan', note: 'The afternoon light was soft and the dessert felt as sweet as you.' }
  ],
  18: [
    { title: 'Riverside walk', place: 'Riverside', note: 'The wind felt gentle and the whole city looked extra romantic.' }
  ]
}

const selectedMemories = computed(() => memoryMap[selectedDay.value] || [])
</script>

<style scoped lang="scss">
@import '../../common/theme.scss';

.hero-metric-card,
.calendar-card,
.note-card {
  padding: 28rpx;
}

.big-number {
  margin-top: 10rpx;
  font-size: 70rpx;
  font-weight: 900;
  color: #ff6fae;
  text-align: center;
}

.calendar-head,
.week-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.calendar-arrow {
  color: #9b86a6;
  font-size: 34rpx;
  font-weight: 700;
}

.week-row {
  margin-top: 20rpx;
}

.week-label {
  width: 14%;
  text-align: center;
  color: #9b86a6;
  font-size: 22rpx;
}

.calendar-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10rpx;
}

.day-cell {
  aspect-ratio: 1 / 1;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.58);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
}

.day-cell.marked {
  background: rgba(255, 235, 245, 0.96);
}

.day-cell.active {
  background: linear-gradient(135deg, #f8b6d8 0%, #d9b8ff 100%);
  box-shadow: 0 14rpx 32rpx rgba(243, 168, 210, 0.24);
}

.day-text {
  color: #6c4a7e;
  font-size: 24rpx;
  font-weight: 700;
}

.day-cell.active .day-text {
  color: #fff;
}

.day-dot {
  width: 8rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #ff6fae;
}

.day-cell.active .day-dot {
  background: #fff;
}

.memory-line + .memory-line {
  margin-top: 18rpx;
}
</style>
