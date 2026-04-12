<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">平台统一协议</view>
      <view class="hero-title small">{{ agreement.title }}</view>
      <view class="hero-copy">{{ agreement.version }} · {{ agreement.summary }}</view>
    </view>

    <view class="detail-block">
      <view class="block-card">
        <view class="section-title">平台统一条款</view>
        <view class="line-list">
          <view v-for="item in agreement.items" :key="item" class="line-item">• {{ item }}</view>
        </view>
      </view>
    </view>

    <view v-if="instrument" class="detail-block">
      <view class="block-card">
        <view class="section-title">{{ instrument.name }}</view>
        <view class="feature-copy">违约规则：{{ instrument.breachRules.join('；') }}</view>
        <view class="feature-copy">损坏责任：{{ instrument.damageRules.join('；') }}</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const agreement = ref({ title: '', version: '', summary: '', items: [] })
const instrument = ref(null)

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const instrumentId = current && current.options ? current.options.instrumentId : ''
  agreement.value = await callService('getAgreementContent')
  if (instrumentId) {
    const res = await callService('getInstrumentDetail', { id: instrumentId })
    instrument.value = res.instrument
  }
})
</script>
