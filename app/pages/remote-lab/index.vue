<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">远程实验</view>
      <view class="hero-title small">远程实验与数据服务</view>
      <view class="hero-copy">把高端设备能力转化成可订购的数据产品，用户只需要提出需求，平台负责组织实验、交付数据与代码。</view>
    </view>

    <view class="section list-stack">
      <view class="card">
        <view class="section-title">提交远程实验需求</view>
        <view class="form-label top-gap">实验主题</view>
        <input v-model="topic" class="form-input" placeholder="例如：海岸带沉积样本分析" />
        <view class="form-label top-gap">联系方式</view>
        <input v-model="contact" class="form-input" placeholder="姓名 / 手机号 / 微信号" />
        <view class="form-label top-gap">需求说明</view>
        <textarea v-model="requirement" class="form-textarea" placeholder="填写样本情况、指标需求、期望交付物"></textarea>
        <view class="primary-btn full-btn top-gap" @tap="submit">提交远程实验需求</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { callService } from '../../common/service'

const topic = ref('')
const contact = ref('')
const requirement = ref('')

async function submit() {
  const res = await callService('createRemoteOrder', { topic: topic.value, contact: contact.value, requirement: requirement.value })
  uni.showModal({ title: '提交成功', content: `${res.message}\n订单号：${res.orderNo}`, showCancel: false })
}
</script>
