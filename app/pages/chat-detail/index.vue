<template>
  <view class="page-shell">
    <view class="topbar">
      <text class="topbar-icon" @tap="goBack">‹</text>
      <text class="brand">Message.</text>
      <view class="topbar-actions">
        <text class="topbar-icon" @tap="openInstrument">看设备</text>
      </view>
    </view>

    <view v-if="chat" class="screen-pad">
      <view class="author-row">
        <view class="author-left">
          <view class="avatar a1"></view>
          <view>
            <view class="author-name-row">
              <text class="author-name">{{ chat.counterpartName || chat.sellerName }}</text>
              <view class="verify-badge">V</view>
            </view>
            <text class="author-inst">{{ chat.counterpartRole || chat.sellerRole }} · {{ chat.instrumentName }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="message-board">
      <view v-for="(item, index) in messages" :key="`${item.time}-${index}`" class="message" :class="item.from">
        <view class="message-bubble">{{ item.text }}</view>
        <view class="message-time">{{ item.time }}</view>
      </view>
    </view>

    <view class="composer-bar">
      <textarea v-model="inputText" class="composer-input" placeholder="输入你要确认的设备参数、交付方式或发票需求"></textarea>
      <view class="composer-send" @tap="sendMessage">发送</view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { callService } from '../../common/service'

const chatId = ref('')
const chat = ref(null)
const messages = ref([])
const inputText = ref('')

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  chatId.value = current && current.options ? current.options.id : ''
  const res = await callService('getChatDetail', { id: chatId.value })
  chat.value = res.chat
  messages.value = res.messages
})

async function sendMessage() {
  if (!inputText.value.trim()) return
  await callService('sendChatMessage', { chatId: chatId.value, text: inputText.value })
  const res = await callService('getChatDetail', { id: chatId.value })
  messages.value = res.messages
  inputText.value = ''
}

function goBack() {
  uni.navigateBack()
}

function openInstrument() {
  if (chat.value && chat.value.instrumentId) {
    uni.navigateTo({ url: `/pages/equipment-detail/index?id=${chat.value.instrumentId}` })
  }
}
</script>
