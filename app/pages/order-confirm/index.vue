<template>
  <view class="page-shell">
    <view class="hero-panel">
      <view class="hero-tag">订单确认</view>
      <view class="hero-title">确认交易模式、费用结构与风控条款</view>
    </view>

    <view v-if="!preview.instrument" class="loading-state">正在准备订单...</view>

    <view v-else>
      <view class="detail-block">
        <view class="block-card">
          <view class="feature-title">{{ preview.instrument.name }}</view>
          <view class="feature-copy">{{ preview.instrument.desc }}</view>

          <view class="form-label top-gap">交易模式</view>
          <view class="chip-row">
            <view v-for="mode in preview.instrument.tradeModes" :key="mode" class="chip" :class="{ active: tradeMode === mode }" @tap="switchMode(mode)">
              {{ mode }}
            </view>
          </view>

          <view v-if="tradeMode === '租赁'">
            <view class="form-label top-gap">租赁天数</view>
            <input v-model="rentDays" class="form-input" type="number" @input="loadPreview" />
          </view>

          <view class="switch-row top-gap">
            <view>
              <view class="row-label">保险方案</view>
              <view class="subtle-copy">当前演示版统一按基础保险方案估算</view>
            </view>
            <view class="chip" :class="{ active: insuranceAccepted }" @tap="toggleInsurance">
              {{ insuranceAccepted ? '已开启' : '关闭' }}
            </view>
          </view>
        </view>
      </view>

      <view class="summary-card">
        <view class="summary-title">费用明细</view>
        <view class="summary-row" v-if="tradeMode === '租赁'">
          <text>租金</text>
          <text>¥{{ preview.rentalAmount }}</text>
        </view>
        <view class="summary-row" v-if="tradeMode === '出售'">
          <text>买断金额</text>
          <text>¥{{ preview.saleAmount }}</text>
        </view>
        <view class="summary-row">
          <text>保险</text>
          <text>¥{{ preview.insuranceFee }}</text>
        </view>
        <view class="summary-row">
          <text>押金</text>
          <text>¥{{ preview.deposit }}</text>
        </view>
        <view class="summary-row total">
          <text>总额</text>
          <text>¥{{ preview.total }}</text>
        </view>
      </view>

      <view class="section">
        <view class="primary-btn full-btn" @tap="submitOrder">提交并去支付</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const instrumentId = ref('')
const tradeMode = ref('租赁')
const rentDays = ref('1')
const insuranceAccepted = ref(true)
const preview = ref({})

function showError(error) {
  uni.showToast({ title: error && error.message ? error.message : '下单失败，请稍后重试', icon: 'none' })
}

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  instrumentId.value = current && current.options ? current.options.instrumentId : ''
  tradeMode.value = current && current.options && current.options.tradeMode ? current.options.tradeMode : '租赁'
  await loadPreview()
})

async function loadPreview() {
  preview.value = await callService('getOrderPreview', {
    instrumentId: instrumentId.value,
    tradeMode: tradeMode.value,
    rentDays: rentDays.value,
    insuranceAccepted: insuranceAccepted.value
  })
}

async function switchMode(mode) {
  tradeMode.value = mode
  await loadPreview()
}

async function toggleInsurance() {
  insuranceAccepted.value = !insuranceAccepted.value
  await loadPreview()
}

async function submitOrder() {
  try {
    const res = await callService('createOrder', {
      instrumentId: instrumentId.value,
      tradeMode: tradeMode.value,
      rentDays: rentDays.value,
      insuranceAccepted: insuranceAccepted.value
    })
    uni.navigateTo({ url: `/pages/order-payment/index?orderId=${res.orderId}` })
  } catch (error) {
    showError(error)
  }
}
</script>
