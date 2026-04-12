<template>
  <view class="page-shell">
    <view class="topbar">
      <text class="topbar-icon" @tap="goBack">‹</text>
      <text class="brand">Instrument.</text>
      <view class="topbar-actions">
        <text class="topbar-icon" @tap="toggleFavorite">{{ isFavorite ? '♥' : '♡' }}</text>
      </view>
    </view>

    <view v-if="loading" class="loading-state">正在加载仪器详情...</view>

    <view v-else-if="instrument">
      <view class="screen-pad">
        <view class="author-row">
          <view class="author-left">
            <view class="avatar" :class="instrument.avatarClass"></view>
            <view>
              <view class="author-name-row">
                <text class="author-name">{{ instrument.sellerName }}</text>
                <view class="verify-badge" :class="{ green: instrument.verifiedType === 'green' }">V</view>
              </view>
              <text class="author-inst">{{ instrument.school }} / {{ instrument.college }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="feed-item">
        <view class="poster-box">
          <view class="poster-bg" :class="instrument.posterTheme"></view>
          <view class="poster-content">
            <view class="poster-topline">
              <view class="remote-pill">{{ tradeMode }}</view>
              <view class="price-chip">{{ tradeMode === '出售' ? instrument.salePriceLabel : instrument.priceLabel }}</view>
            </view>
            <view>
              <view class="poster-title">{{ instrument.name }}</view>
              <view class="poster-meta">{{ instrument.location }} · {{ instrument.condition }}</view>
            </view>
          </view>
        </view>

        <view class="desc-block" style="margin-top: 18rpx;">
          <text class="desc-strong">{{ instrument.sellerName }}</text>
          <text>{{ instrument.desc }}</text>
        </view>

        <view class="chip-row top-gap">
          <view v-for="mode in instrument.tradeModes" :key="mode" class="chip" :class="{ active: tradeMode === mode }" @tap="tradeMode = mode">
            {{ mode }}
          </view>
        </view>

        <view class="micro-note">
          <text>⌘</text>
          <text>{{ instrument.servicePackage }}</text>
        </view>
      </view>

      <view class="section list-stack top-gap">
        <view class="card">
          <view class="section-title">设备参数</view>
          <view class="feature-copy">精度参数：{{ instrument.precision }}</view>
          <view class="feature-copy">适用学科：{{ instrument.disciplines.join(' / ') }}</view>
          <view class="feature-copy">远程实验：{{ instrument.remote ? '支持' : '不支持' }}</view>
        </view>
        <view class="card">
          <view class="section-title">协议与条款</view>
          <view class="feature-copy">平台统一协议 + 发布方违约规则 + 损坏责任会在下单前再次确认。</view>
          <view class="light-btn top-gap" @tap="goAgreement">查看协议</view>
        </view>
      </view>

      <view class="section top-gap">
        <view class="section-head">
          <view>
            <view class="section-title">相关推荐</view>
            <view class="section-subtitle">位置已经放到交易按钮下面，符合你之前的要求。</view>
          </view>
        </view>
        <view class="list-stack">
          <view v-for="item in related" :key="item.id" class="card" @tap="openRelated(item.id)">
            <view class="feature-title">{{ item.name }}</view>
            <view class="feature-copy">{{ item.desc }}</view>
          </view>
        </view>
      </view>

      <view class="composer-bar" style="align-items: center;">
        <view class="soft-button" @tap="goChat">联系发布方</view>
        <view class="soft-button" @tap="addToCart">加入购物车</view>
        <view class="composer-send" @tap="goOrderConfirm">立即下单</view>
      </view>
    </view>

    <view v-else class="section">
      <view class="card empty-panel">
        <view class="empty-title">仪器不存在或已下架</view>
        <view class="empty-copy">你访问的设备可能已被删除或暂停出租，返回列表可查看最新在架仪器。</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const loading = ref(true)
const instrument = ref(null)
const related = ref([])
const isFavorite = ref(false)
const tradeMode = ref('租赁')
const instrumentId = ref('')

function showError(error) {
  uni.showToast({ title: error && error.message ? error.message : '操作失败，请稍后重试', icon: 'none' })
}

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  instrumentId.value = current && current.options ? current.options.id : ''
  const res = await callService('getInstrumentDetail', { id: instrumentId.value })
  instrument.value = res.instrument
  related.value = res.related
  isFavorite.value = res.isFavorite
  tradeMode.value = res.instrument ? res.instrument.defaultTradeMode : '租赁'
  loading.value = false
})

async function toggleFavorite() {
  const res = await callService('toggleFavorite', { id: instrumentId.value })
  isFavorite.value = res.isFavorite
}

async function goChat() {
  try {
    const res = await callService('ensureInstrumentChat', { instrumentId: instrumentId.value })
    uni.navigateTo({ url: `/pages/chat-detail/index?id=${res.chatId}` })
  } catch (error) {
    showError(error)
  }
}

async function addToCart() {
  try {
    await callService('addToCart', { instrumentId: instrumentId.value, tradeMode: tradeMode.value })
    uni.showToast({ title: '已加入购物车', icon: 'success' })
  } catch (error) {
    showError(error)
  }
}

function goOrderConfirm() {
  uni.navigateTo({ url: `/pages/order-confirm/index?instrumentId=${instrumentId.value}&tradeMode=${tradeMode.value}` })
}

function goAgreement() {
  uni.navigateTo({ url: `/pages/agreement/index?instrumentId=${instrumentId.value}` })
}

function openRelated(id) {
  uni.redirectTo({ url: `/pages/equipment-detail/index?id=${id}` })
}

function goBack() {
  uni.navigateBack()
}
</script>
