<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">AI 工具</view>
      <view class="hero-title small">AI 驱动的智能工具平台</view>
      <view class="hero-copy">把计划书里的专业算法能力做成真实可用的工具台，覆盖数据输入、智能处理、结果沉淀和后续协作。</view>
    </view>

    <view class="section list-stack">
      <view v-for="item in tools" :key="item.id" class="card" @tap="currentToolId = item.id">
        <view class="feature-top">
          <view class="feature-title">{{ item.name }}</view>
          <view class="badge">{{ item.mode }}</view>
        </view>
        <view class="feature-copy">{{ item.subtitle }}</view>
      </view>

      <view class="card">
        <view class="form-label">分析目标</view>
        <input v-model="goal" class="form-input" placeholder="例如：评估海岸带风暴潮风险" />
        <view class="form-label top-gap">数据说明</view>
        <textarea v-model="dataset" class="form-textarea" placeholder="填写数据来源、样本规模、关键变量"></textarea>
        <view class="primary-btn full-btn top-gap" @tap="submitTask">开始分析</view>
      </view>

      <view v-if="result.toolName" class="card">
        <view class="section-title">{{ result.toolName }}</view>
        <view class="feature-copy">{{ result.summary }}</view>
        <view class="line-list top-gap">
          <view v-for="item in result.insights" :key="item" class="line-item">• {{ item }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const tools = ref([])
const currentToolId = ref('')
const goal = ref('')
const dataset = ref('')
const result = ref({})

onMounted(async () => {
  const res = await callService('getAiTools')
  tools.value = res.tools
  currentToolId.value = res.tools[0] ? res.tools[0].id : ''
})

async function submitTask() {
  result.value = await callService('submitAiTask', {
    toolId: currentToolId.value,
    goal: goal.value,
    dataset: dataset.value
  })
}
</script>
